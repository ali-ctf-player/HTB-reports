
# 🚩 Hack The Box Write-ups

![Banner](https://img.shields.io/badge/Hack%20The%20Box-Writeups-9fef00?style=for-the-badge&logo=hack-the-box&logoColor=black)

[![HTB Profile](https://img.shields.io/badge/HTB-Profile-202225?style=flat&logo=hack-the-box&logoColor=9fef00)](https://app.hackthebox.com/users/3022666)
![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)

## 📖 Introduction

Welcome to my repository of write-ups for [Hack The Box](https://www.hackthebox.com/) machines and challenges. 

I created this repository to document my learning journey, refine my methodology, and share knowledge with the InfoSec community. Each write-up details the reconnaissance, scanning, enumeration, and exploitation steps I took to capture the flags.

> **Note:** These write-ups are for educational purposes only.

## 📂 Repository Structure

The repository is organized by category and difficulty:

```text
├── Machines
│   ├── Easy
│   ├── Medium
│   ├── Hard
│   └── Insane
```

## 🏆 Recent Pwns

A log of the machines I have recently compromised.

| Machine | OS | Difficulty | Tags | Write-up |
| :--- | :---: | :---: | :---: | :---: |
| **Giveback** | 🐧 | ![](https://img.shields.io/badge/-Medium-dbab09) | `GiveWP` `Mariadb` `Kubernetes` | [Read ➜](./Machines/Easy/README.md) |
| **Pterodactyl** | 🪟 | ![](https://img.shields.io/badge/-Medium-dbab09) | `Race Conditions` `Motherland` `LFI to RCE` | [Read ➜](./Machines/Medium/README.md) |
| **WingData** | 🐧 | ![](https://img.shields.io/badge/-Easy-2ea44f) | `RCE` `Tarfile Path Traversal` | [Read ➜](./Machines/Easy/README.md) |
| **Interpreter** | 🪟 | ![](https://img.shields.io/badge/-Medium-dbab09) | `Mirth` `SSTI`  | [Read ➜](./Machines/Medium/README.md) |

<br>

## ⚔️ My Arsenal

The tools and frameworks I frequently utilize during engagements.

<p align="left">
  <img src="https://img.shields.io/badge/Nmap-000000?style=for-the-badge&logo=nmap&logoColor=white" />
  <img src="https://img.shields.io/badge/RustScan-000000?style=for-the-badge&logo=rust&logoColor=white" />
  <img src="https://img.shields.io/badge/Ffuf-000000?style=for-the-badge&logo=kali-linux&logoColor=white" />

  <img src="https://img.shields.io/badge/Burp%20Suite-000000?style=for-the-badge&logo=burpsuite&logoColor=orange" />
  <img src="https://img.shields.io/badge/Metasploit-000000?style=for-the-badge&logo=metasploit&logoColor=white" />
  
  <img src="https://img.shields.io/badge/John%20the%20Ripper-000000?style=for-the-badge&logo=hack-the-box&logoColor=white" />

  <img src="https://img.shields.io/badge/Netcat-000000?style=for-the-badge&logo=gnu-bash&logoColor=white" />
  <img src="https://img.shields.io/badge/PowerShell-000000?style=for-the-badge&logo=powershell&logoColor=white" />
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
