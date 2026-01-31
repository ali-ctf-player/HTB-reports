## 🏆 Recent Pwns

A log of the machines I have recently compromised.

| Machine | OS | Difficulty | Tags | Write-up |
| :--- | :---: | :---: | :---: | :---: |
| **Example Box** | 🐧 | ![](https://img.shields.io/badge/-Easy-2ea44f) | `Web` `CVE-2023-XXXX` | [Read ➜](./Machines/Easy/README.md) |
| **Another Box** | 🪟 | ![](https://img.shields.io/badge/-Medium-dbab09) | `Active Directory` `Kerberoasting` | [Read ➜](./Machines/Medium/README.md) |
| **Hard Box** | 🐧 | ![](https://img.shields.io/badge/-Hard-bd2c00) | `Buffer Overflow` `Custom Exploit` | [Read ➜](./Machines/Hard/README.md) |

<br>

## ⚔️ My Arsenal

The tools and frameworks I frequently utilize during engagements.

<p align="left">
  <img src="https://img.shields.io/badge/Nmap-000000?style=for-the-badge&logo=nmap&logoColor=white" />
  <img src="https://img.shields.io/badge/Wireshark-000000?style=for-the-badge&logo=wireshark&logoColor=white" />
  <img src="https://img.shields.io/badge/Burp%20Suite-000000?style=for-the-badge&logo=burpsuite&logoColor=orange" />
  <img src="https://img.shields.io/badge/Gobuster-000000?style=for-the-badge&logo=go&logoColor=white" />
  <img src="https://img.shields.io/badge/Metasploit-000000?style=for-the-badge&logo=metasploit&logoColor=white" />
  <img src="https://img.shields.io/badge/Ghidra-000000?style=for-the-badge&logo=c&logoColor=white" />
  <img src="https://img.shields.io/badge/Kali_Linux-000000?style=for-the-badge&logo=kalilinux&logoColor=white" />
</p>

## 🧠 Methodology

My general workflow for approaching a new target.

<details>
<summary><strong>1. Reconnaissance & Enumeration</strong> (Click to Expand)</summary>

* **Port Scanning:** Identifying open ports and running services (Nmap, Masscan).
* **Web Enumeration:** Directory brute-forcing, sub-domain enumeration, and checking for known CMS vulnerabilities (Gobuster, Nikto, Wappalyzer).
* **SMB/RPC:** Checking for null sessions, listing shares, and enumerating users.

</details>

<details>
<summary><strong>2. Initial Access (Foothold)</strong> (Click to Expand)</summary>

* **Exploitation:** leveraging CVEs, misconfigurations, or weak credentials.
* **Reverse Shells:** Establishing a stable connection back to my attack box.

</details>

<details>
<summary><strong>3. Privilege Escalation</strong> (Click to Expand)</summary>

* **Enumeration:** Running scripts like `LinPEAS` or `WinPEAS`.
* **Kernel Exploits:** Checking for outdated kernel versions.
* **Misconfigurations:** Checking SUID binaries, cron jobs, or weak file permissions.

</details>

<br>

## 📈 Stats & Progress

![HTB Stats](http://www.hackthebox.com/badge/image/3022666)

---

<div align="center">

**[ ⭐ Star this Repo ](https://github.com/ali-ctf-player/HTB-reports)** if you found these write-ups helpful!
  
<sub><i>"The only true wisdom is in knowing you know nothing."</i> — Socrates</sub>

</div>
