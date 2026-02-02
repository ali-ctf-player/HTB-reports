# 🟢 Easy Machines

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-2ea44f?style=for-the-badge&logo=hack-the-box&logoColor=white)
![Count](https://img.shields.io/badge/Total%20Pwned-4-blue?style=for-the-badge)

## ℹ️ Overview

"Easy" difficulty machines on Hack The Box serve as the entry point to penetration testing. They usually involve:
* **Publicly known CVEs** (Common Vulnerabilities and Exposures).
* **Weak Credentials** or default passwords.
* **Basic Enumeration** skills (Web, SMB, FTP).
* **Simple Privilege Escalation** (Kernel exploits or clear misconfigurations).

## 🗂️ Write-ups Index

| Machine Name | OS | Key Techniques | Link |
| :--- | :---: | :--- | :---: |
| **Armageddon** | 🐧 | `Drupalgeddon2` `Snapd` `Dirty Sock` | [📄 View PDF](./Armageddon-HTB.pdf) |
| **Facts** | 🐧 | `LFI` `Camaleon` `Facter` | [📄 View PDF](./Facts-HTB.pdf) |
| **TwoMillions** | 🐧 | `JavaScript` `RCE` `OverlayFS` | [📄 View PDF](./TwoMillions-HTB.pdf) |
| **CodePartTwo** | 🐧 | `js2py` `npbackup-cli` | [📄 View PDF](./CodePartTwo-HTB.pdf) |

## 💡 General Tips for Easy Boxes

1.  **Enumerate Everything:** Don't stop at the first open port. Check version numbers carefully.
2.  **Google is King:** Found a version number? Google `Service 1.2.3 exploit`.
3.  **Check Defaults:** Always try `admin:admin`, `root:password`, or `guest` accounts.
4.  **Read the Errors:** Sometimes the error message tells you exactly what technology is running.

---

[🔙 Return to Main Repository](../../README.md)
