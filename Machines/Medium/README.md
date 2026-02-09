# 🟠 Medium Machines

![Difficulty](https://img.shields.io/badge/Difficulty-Medium-orange?style=for-the-badge&logo=hack-the-box&logoColor=white)
![Count](https://img.shields.io/badge/Total%20Pwned-3-purple?style=for-the-badge)

## ℹ️ Overview

"Medium" difficulty machines on Hack The Box bridge the gap between basic exploitation and advanced red teaming. They usually involve:
* **Chaining Vulnerabilities** (using one exploit to facilitate another).
* **Custom Exploitation** (modifying public PoCs or writing simple scripts).
* **Deeper Enumeration** (analyzing source code, subdomains, or internal services).
* **Complex Privilege Escalation** (Abusing SUID binaries, cron jobs, or path hijacking).

## 🗂️ Write-ups Index

| Machine Name | OS | Key Techniques | Link |
| :--- | :---: | :--- | :---: |
| **Dogcat** | 🐧 | `LFI` `Docker` | [📄 View PDF](./Dogcat-THM.pdf) |
| **Imagery** | 🐧 | `LFI` `pyAesCrypt` `Charcol` | [📄 View PDF](./Imagery-HTB.pdf) |
| **Pterodactyl** | 🐧 | `Race Conditions` `PAM` `PHP-PEAR` | [📄 View PDF](./Pterodactyl-HTB.pdf) |

## 💡 General Tips for Medium Boxes

1.  **Enumerate Harder:** If standard scans return nothing, look for UDP ports, subdomains, or hidden web directories.
2.  **Modify the Code:** Public exploits rarely work out of the box. Be ready to change IP addresses, ports, or payload formatting in Python/Bash scripts.
3.  **Think Laterally:** Sometimes the entry point isn't the final target. You might need to pivot or find credentials in a database to move forward.
4.  **Process Enumeration:** For privilege escalation, look at running processes (pspy64) and internal network connections, not just SUID bits.

---

[🔙 Return to Main Repository](../../README.md)
