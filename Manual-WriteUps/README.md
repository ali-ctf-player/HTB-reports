# 🎯 HackTheBox Write-ups

A comprehensive collection of my **HackTheBox** machine write-ups, documenting my journey through various machines with detailed explanations, methodologies, and lessons learned.

## 📖 About

This repository contains detailed walkthroughs for HackTheBox machines I've completed. Each write-up includes:

- **Enumeration** steps with reasoning
- **Exploitation** techniques and vulnerability analysis
- **Privilege Escalation** paths
- **Flags** and key takeaways
- **Mitigation** strategies

These write-ups are created for educational purposes to help others learn penetration testing methodologies.

## 🏷️ Machine Categories

> Auto-generated from each `<MachineName>/README.md` — do not edit by hand, just push a new write-up directory and GitHub Actions updates this automatically.

<!-- STATS:START -->
| Difficulty | Count | Description |
|------------|-------|-------------|
| 🟢 **Easy** | 0 | Beginner-friendly machines with straightforward paths |
| 🟡 **Medium** | 0 | Moderate complexity, requiring intermediate skills |
| 🔴 **Hard** | 1 | Complex machines requiring advanced techniques |
| ⚫ **Insane** | 0 | Expert-level challenges with multiple layers |

**Total machines documented: 1**
<!-- STATS:END -->

## 🖥️ All Write-ups

<!-- MACHINES:START -->
| Machine | Difficulty | OS | Date | Write-up |
|---------|------------|----|------|----------|
| [Checkpoint](Checkpoint/README.md) | 🔴 Hard | Windows | June 16, 2026 | [Read more](Checkpoint/README.md) |
<!-- MACHINES:END -->

## 📝 Write-up Format

Every machine gets its own top-level directory named after the machine, containing a `README.md`:

```
Checkpoint/
└── README.md
```

That `README.md` must start with a metadata table — this is what the generator script reads:

```markdown
# HTB Write-Up: Machine Name

| Field      | Details                                                  |
|------------|-----------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Name)  |
| Difficulty | Easy / Medium / Hard / Insane                              |
| OS         | Linux / Windows                                            |
| Author     | Your Name                                                  |
| Date       | Month DD, YYYY                                             |

---

## Table of Contents
...

## 1. Reconnaissance
- Nmap scan results
- Service enumeration
- Directory fuzzing

## 2. Initial Access / Exploitation
- Vulnerability identification
- Exploit development/modification
- Initial access

## 3. Privilege Escalation
- Enumeration steps
- Vulnerability chaining
- Root/Administrator access

## Summary
- Key takeaways
- New techniques discovered
- Common pitfalls
```

## ➕ Adding a New Write-up

1. Create a new folder named after the machine, e.g. `Lame/`, with a `README.md` inside following the format above.
2. Commit and push to `main`.
3. GitHub Actions automatically re-runs the generator and commits the updated stats/table back to this top-level `README.md` — no manual edits needed.

You can also run it locally any time:

```bash
python3 scripts/generate_readme.py
```
