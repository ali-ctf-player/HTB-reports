# 🔴 Hard Machines

![Difficulty](https://img.shields.io/badge/Difficulty-Hard-e03c31?style=for-the-badge&logo=hack-the-box&logoColor=white)
![Count](https://img.shields.io/badge/Total%20Pwned-1-red?style=for-the-badge)

## ℹ️ Overview

"Hard" difficulty machines on Hack The Box test your advanced penetration testing methodologies and ability to think outside the box. They typically involve:
* **Vulnerability Chaining** (combining multiple minor flaws, like SSRF to LFI, to achieve execution).
* **Custom Exploitation** (writing custom scripts, modifying public exploits, or bypassing filters/WAFs).
* **Advanced Enumeration** (deep Active Directory enumeration, obscure services, or digging through large codebases).
* **Complex Privilege Escalation** (Reverse engineering, custom binary exploitation, or bypassing modern defenses).

## 🗂️ Write-ups Index

| Machine Name | OS | Key Techniques | Link |
| :--- | :---: | :--- | :---: |
| **Pirate** | 🪟 | `RBCD` `LDAP` `gMSA` | [📄 View PDF](./Pirate-HTB.pdf) |


## 💡 General Tips for Hard Boxes

1.  **Beware of Rabbit Holes:** Hard machines are actively designed to distract you. Timebox your enumeration on specific vectors and move on if a path feels like a dead end.
2.  **Review Source Code:** If you get access to custom code, read it carefully. Look for logic flaws, insecure deserialization, or weak cryptographic implementations rather than just searching for known CVEs.
3.  **Chain Your Exploits:** You will rarely find a straight 1-click exploit. Think about how a low-impact bug you found can be combined with another feature to elevate your access.
4.  **Enumerate Internally:** Once you have a foothold, treat the internal environment as a brand new network. Run tools like `netstat` or `ss` to look for locally bound ports, and dig deep into running processes and cron jobs.

---

[🔙 Return to Main Repository](../../README.md)
