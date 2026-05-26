# HTB Write-Up: Delivery

| Field      | Details                                                            |
|------------|--------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Delivery)       |
| Difficulty | Easy                                                               |
| OS         | Linux                                                              |
| Author     | ippsec                                                             |
| Date       | May 26, 2026                                                       |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — osTicket & Mattermost](#2-enumeration--osticket--mattermost)
3. [Initial Access — Ticket Email Abuse](#3-initial-access--ticket-email-abuse)
4. [Privilege Escalation — Database Credentials & Hash Cracking](#4-privilege-escalation--database-credentials--hash-cracking)
5. [Summary](#5-summary)

---

## 1. Reconnaissance

Port scanning was performed with **Nmap**:

```bash
nmap -sV -p- -T4 10.10.10.222
```

**Open Ports:**

| Port | Service | Details |
|------|---------|---------|
| 22   | SSH     | OpenSSH 7.9p1 Debian |
| 80   | HTTP    | nginx — delivery.htb |
| 8065 | HTTP    | Mattermost application |

The homepage at `http://delivery.htb` revealed two important clues:
- A helpdesk link pointing to `helpdesk.delivery.htb` (osTicket)
- A note: *"Once you have an @delivery.htb email address, you'll be able to have access to our MatterMost server"*

Both hostnames were added to `/etc/hosts`:

```
10.10.10.222  delivery.htb  helpdesk.delivery.htb
```

---

## 2. Enumeration — osTicket & Mattermost

### 2.1 — osTicket Support System

Browsing to `http://helpdesk.delivery.htb` revealed an **osTicket** instance — an open-source support ticketing system. It allows anyone to open a support ticket as a guest without registering an account.

Upon submitting a new ticket, the system returned:

```
Your ticket has been created. Ticket ID: 7885467
If you want to add more information to your ticket, just email 7885467@delivery.htb
```

This ticket-specific email (`7885467@delivery.htb`) is the key to the attack — any email sent to it appears in the ticket's status page, readable by anyone who knows the ticket ID and the original submission email.

### 2.2 — Mattermost (Port 8065)

Port 8065 runs a **Mattermost** instance — an open-source team messaging platform similar to Slack. Registration requires email verification, and the application only allows `@delivery.htb` email addresses to access internal channels.

---

## 3. Initial Access — Ticket Email Abuse

The attack chain exploits the fact that `7885467@delivery.htb` is both a valid delivery address and readable via the osTicket status page — effectively giving us a temporary `@delivery.htb` inbox.

**Steps:**

1. Open a new ticket on `helpdesk.delivery.htb` using any guest email (e.g. `test@test.com`) and note the assigned ticket email: `7885467@delivery.htb`

2. Register a new Mattermost account at `http://delivery.htb:8065` using `7885467@delivery.htb` as the registration email

3. Mattermost sends a verification link to `7885467@delivery.htb` — which is delivered to the osTicket ticket thread

4. Navigate to **Check Ticket Status** on osTicket (Ticket ID: `7885467`, email: `test@test.com`) — the Mattermost verification email appears in the ticket thread

5. Click the verification link to confirm the Mattermost account

6. Log in to Mattermost and browse the **Internal** channel — the admin left the following message:

```
@developers Please update credentials. 
Also please create a program to help us use a hashing format that can find variations of PleaseSubscribe!
```

This reveals the **base password word** used for the root account.

**User flag retrieved** from `/home/maildeliverer/user.txt` after logging into Mattermost and finding SSH credentials in the internal channel.

```
37f4e87c93a9a77c410aa133fa94c263
```

---

## 4. Privilege Escalation — Database Credentials & Hash Cracking

### 4.1 — Mattermost Configuration File

As `maildeliverer`, the Mattermost configuration file was located:

```bash
find / -name "config.json" 2>/dev/null
# /opt/mattermost/config/config.json
```

The config contained plaintext **MySQL credentials**, which were used to connect to the local database:

```bash
mysql -u mmuser -p -D mattermost
```

### 4.2 — Extracting the Root Hash

Querying the Mattermost users table:

```sql
SELECT Username, Password, Email FROM Users;
```

The `root` user's bcrypt hash was recovered:

```
$2a$10$VM6EeymRxJ29r8Wjkr8Dtev0O.1STWb4.4ScG.anuu7v0EFJwgjjO
```

### 4.3 — Rule-Based Hash Cracking

Based on the admin's Mattermost message about "variations of PleaseSubscribe!", a targeted wordlist was created and cracked with **Hashcat** using rule-based mutation (bcrypt = mode 3200):

```bash
echo 'PleaseSubscribe!' > wordlist.txt

hashcat -m 3200 hash.txt wordlist.txt -r /usr/share/hashcat/rules/best64.rule --force
```

**Result:**

```
$2a$10$VM6EeymRxJ29r8Wjkr8Dtev0O.1STWb4.4ScG.anuu7v0EFJwgjjO:PleaseSubscribe!21

Status: Cracked
Time: ~6 seconds
```

Administrator credentials recovered:

| Account | Password |
|---------|----------|
| `root` | `PleaseSubscribe!21` |

### 4.4 — Root Shell

```bash
su root
# Password: PleaseSubscribe!21

cat /root/root.txt
```

**Root flag retrieved.**

---

## 5. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | Nmap port scan + homepage enumeration | Ports 22, 80, 8065 — osTicket + Mattermost identified |
| Enumeration | osTicket guest ticket creation | Ticket email `7885467@delivery.htb` obtained |
| Initial Access | Mattermost registration with ticket email | Verification link intercepted via osTicket thread |
| Foothold | Mattermost Internal channel | SSH credentials + base password hint discovered |
| PrivEsc Step 1 | Mattermost `config.json` → MySQL | Root's bcrypt hash extracted from database |
| PrivEsc Step 2 | Hashcat mode 3200 + best64 rules | `root:PleaseSubscribe!21` cracked in ~6 seconds |
| Root | `su root` | Root flag from `/root/root.txt` |

### Key Takeaways

- **Ticket-based email aliases are powerful attack primitives.** osTicket's per-ticket inbox feature allowed us to receive email at a `@delivery.htb` address without ever controlling the mail server — bypassing Mattermost's email domain restriction entirely. Any application that grants trust based solely on email domain is vulnerable to this pattern when a co-hosted service creates internal-domain aliases for untrusted users.

- **Sensitive hints in internal chat are still sensitive.** The admin's message in the Mattermost Internal channel revealed the base string for the root password. Credential-adjacent information (base words, patterns, formats) shared in team chat should be treated with the same sensitivity as the credentials themselves.

- **Rule-based cracking is highly effective against "complex" passwords.** `PleaseSubscribe!21` is a password that passes most complexity requirements (uppercase, lowercase, special character, numbers, length). It was cracked in seconds because it is a predictable transformation of a dictionary word. Long random passphrases or a password manager are the only reliable defenses against offline cracking.

- **bcrypt is slow by design — but only buys time, not safety.** bcrypt's cost factor slows cracking significantly, but a short, rule-derivable password can still be cracked in seconds on modern hardware. The real lesson is that password strength matters independently of the hashing algorithm.
