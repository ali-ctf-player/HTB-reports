

# HTB Write-Up: Logging

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Logging)    |
| Difficulty | Medium                                                         |
| OS         | Windows                                                        |
| Author     | samurai                                                        |
| Date       | April 20, 2026                                                 |


**As is common in real life pentests, you will start the Logging box with credentials for the following account wallace.everette / Welcome2026@**

## Reconnaissance

First , we have to do scanning techniques to know which services running and its version. Lets use nmap and rustscan together ->

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Logging]
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
🌍HACK THE PLANET🌍

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[~] Automatically increasing ulimit value to 5000.
Open 10.129.35.76:53
Open 10.129.35.76:80
Open 10.129.35.76:88
Open 10.129.35.76:135
Open 10.129.35.76:139
Open 10.129.35.76:389
Open 10.129.35.76:445
Open 10.129.35.76:464
Open 10.129.35.76:593
Open 10.129.35.76:636
Open 10.129.35.76:5985
Open 10.129.35.76:8530
Open 10.129.35.76:8531
Open 10.129.35.76:47001
Open 10.129.35.76:49664
Open 10.129.35.76:49665
Open 10.129.35.76:49668
Open 10.129.35.76:49666
Open 10.129.35.76:49671
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-20 00:36 +0400
Initiating Ping Scan at 00:36
Scanning 10.129.35.76 [4 ports]
Completed Ping Scan at 00:36, 0.13s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 00:36
Completed Parallel DNS resolution of 1 host. at 00:36, 0.50s elapsed
DNS resolution of 1 IPs took 0.50s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 00:36
Scanning 10.129.35.76 [19 ports]
Discovered open port 139/tcp on 10.129.35.76
Discovered open port 80/tcp on 10.129.35.76
Discovered open port 135/tcp on 10.129.35.76
Discovered open port 445/tcp on 10.129.35.76
Discovered open port 53/tcp on 10.129.35.76
Discovered open port 49665/tcp on 10.129.35.76
Discovered open port 389/tcp on 10.129.35.76
Discovered open port 49671/tcp on 10.129.35.76
Discovered open port 49666/tcp on 10.129.35.76
Discovered open port 593/tcp on 10.129.35.76
Discovered open port 49664/tcp on 10.129.35.76
Discovered open port 8531/tcp on 10.129.35.76
Discovered open port 88/tcp on 10.129.35.76
Discovered open port 464/tcp on 10.129.35.76
Discovered open port 8530/tcp on 10.129.35.76
Discovered open port 47001/tcp on 10.129.35.76
Discovered open port 5985/tcp on 10.129.35.76
Discovered open port 49668/tcp on 10.129.35.76
Discovered open port 636/tcp on 10.129.35.76
Completed SYN Stealth Scan at 00:36, 0.20s elapsed (19 total ports)
Nmap scan report for 10.129.35.76
Host is up, received reset ttl 127 (0.085s latency).
Scanned at 2026-04-20 00:36:22 +04 for 1s

PORT      STATE SERVICE        REASON
53/tcp    open  domain         syn-ack ttl 127
80/tcp    open  http           syn-ack ttl 127
88/tcp    open  kerberos-sec   syn-ack ttl 127
135/tcp   open  msrpc          syn-ack ttl 127
139/tcp   open  netbios-ssn    syn-ack ttl 127
389/tcp   open  ldap           syn-ack ttl 127
445/tcp   open  microsoft-ds   syn-ack ttl 127
464/tcp   open  kpasswd5       syn-ack ttl 127
593/tcp   open  http-rpc-epmap syn-ack ttl 127
636/tcp   open  ldapssl        syn-ack ttl 127
5985/tcp  open  wsman          syn-ack ttl 127
8530/tcp  open  unknown        syn-ack ttl 127
8531/tcp  open  unknown        syn-ack ttl 127
47001/tcp open  winrm          syn-ack ttl 127
49664/tcp open  unknown        syn-ack ttl 127
49665/tcp open  unknown        syn-ack ttl 127
49666/tcp open  unknown        syn-ack ttl 127
49668/tcp open  unknown        syn-ack ttl 127
49671/tcp open  unknown        syn-ack ttl 127

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 0.96 seconds
           Raw packets sent: 23 (988B) | Rcvd: 377 (15.180KB)

                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Logging]
└─$ cat nmap.out    
Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-20 00:36 +0400
Nmap scan report for 10.129.35.76
Host is up (0.16s latency).
Not shown: 987 closed tcp ports (reset)
PORT     STATE SERVICE           VERSION
53/tcp   open  domain            Simple DNS Plus
80/tcp   open  http              Microsoft IIS httpd 10.0
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-title: IIS Windows Server
|_http-server-header: Microsoft-IIS/10.0
88/tcp   open  kerberos-sec      Microsoft Windows Kerberos (server time: 2026-04-20 03:36:30Z)
135/tcp  open  msrpc             Microsoft Windows RPC
139/tcp  open  netbios-ssn       Microsoft Windows netbios-ssn
389/tcp  open  ldap              Microsoft Windows Active Directory LDAP (Domain: logging.htb, Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.logging.htb, DNS:logging.htb, DNS:logging
| Not valid before: 2026-04-17T03:20:01
|_Not valid after:  2106-04-17T03:20:01
|_ssl-date: 2026-04-20T03:37:49+00:00; +7h00m00s from scanner time.
445/tcp  open  microsoft-ds?
464/tcp  open  kpasswd5?
593/tcp  open  ncacn_http        Microsoft Windows RPC over HTTP 1.0
636/tcp  open  ssl/ldap          Microsoft Windows Active Directory LDAP (Domain: logging.htb, Site: Default-First-Site-Name)
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.logging.htb, DNS:logging.htb, DNS:logging
| Not valid before: 2026-04-17T03:20:01
|_Not valid after:  2106-04-17T03:20:01
|_ssl-date: 2026-04-20T03:37:49+00:00; +7h00m00s from scanner time.
3268/tcp open  ldap              Microsoft Windows Active Directory LDAP (Domain: logging.htb, Site: Default-First-Site-Name)
|_ssl-date: 2026-04-20T03:37:49+00:00; +7h00m00s from scanner time.
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.logging.htb, DNS:logging.htb, DNS:logging
| Not valid before: 2026-04-17T03:20:01
|_Not valid after:  2106-04-17T03:20:01
3269/tcp open  globalcatLDAPssl?
| ssl-cert: Subject: 
| Subject Alternative Name: DNS:DC01.logging.htb, DNS:logging.htb, DNS:logging
| Not valid before: 2026-04-17T03:20:01
|_Not valid after:  2106-04-17T03:20:01
|_ssl-date: 2026-04-20T03:37:49+00:00; +7h00m00s from scanner time.
5985/tcp open  http              Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
No exact OS matches for host (If you know what OS is running on it, see https://nmap.org/submit/ ).
TCP/IP fingerprint:
OS:SCAN(V=7.98%E=4%D=4/20%OT=53%CT=1%CU=33783%PV=Y%DS=2%DC=T%G=Y%TM=69E53D1
OS:D%P=x86_64-pc-linux-gnu)SEQ(SP=102%GCD=1%ISR=106%TI=I%CI=I%II=I%SS=S%TS=
OS:U)SEQ(SP=104%GCD=1%ISR=109%TI=I%CI=I%TS=U)SEQ(SP=108%GCD=1%ISR=107%TI=I%
OS:CI=I%II=I%SS=S%TS=U)SEQ(SP=FE%GCD=1%ISR=10B%TI=I%CI=I%II=I%SS=S%TS=U)SEQ
OS:(SP=FE%GCD=1%ISR=110%TI=RD%CI=I%TS=U)OPS(O1=M552NW8NNS%O2=M552NW8NNS%O3=
OS:M552NW8%O4=M552NW8NNS%O5=M552NW8NNS%O6=M552NNS)WIN(W1=FFFF%W2=FFFF%W3=FF
OS:FF%W4=FFFF%W5=FFFF%W6=FF70)ECN(R=Y%DF=Y%T=80%W=FFFF%O=M552NW8NNS%CC=Y%Q=
OS:)T1(R=Y%DF=Y%T=80%S=O%A=S+%F=AS%RD=0%Q=)T2(R=N)T3(R=N)T4(R=Y%DF=Y%T=80%W
OS:=0%S=A%A=O%F=R%O=%RD=0%Q=)T5(R=Y%DF=Y%T=80%W=0%S=Z%A=S+%F=AR%O=%RD=0%Q=)
OS:T6(R=Y%DF=Y%T=80%W=0%S=A%A=O%F=R%O=%RD=0%Q=)T7(R=N)U1(R=Y%DF=N%T=80%IPL=
OS:164%UN=0%RIPL=G%RID=G%RIPCK=G%RUCK=G%RUD=G)IE(R=Y%DFI=N%T=80%CD=Z)

Network Distance: 2 hops
Service Info: Host: DC01; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 6h59m59s, deviation: 0s, median: 6h59m59s
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2026-04-20T03:37:28
|_  start_date: N/A

TRACEROUTE (using port 23/tcp)
HOP RTT       ADDRESS
1   156.51 ms 10.10.14.1
2   156.65 ms 10.129.35.76

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 92.98 seconds
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Logging]
└─$ 

```


Perfect , also we have valid credentials provided in description field which is `wallace.everette / Welcome2026@`

## Enumeration

Lets do some smb share enumeration with **netexec** -> 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Logging]
└─$ netexec smb 10.129.35.76 -u 'wallace.everette' -p 'Welcome2026@' --shares
SMB         10.129.35.76    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:logging.htb) (signing:True) (SMBv1:False) 
SMB         10.129.35.76    445    DC01             [+] logging.htb\wallace.everette:Welcome2026@ 
SMB         10.129.35.76    445    DC01             [*] Enumerated shares
SMB         10.129.35.76    445    DC01             Share           Permissions     Remark
SMB         10.129.35.76    445    DC01             -----           -----------     ------
SMB         10.129.35.76    445    DC01             ADMIN$                          Remote Admin
SMB         10.129.35.76    445    DC01             C$                              Default share
SMB         10.129.35.76    445    DC01             IPC$            READ            Remote IPC
SMB         10.129.35.76    445    DC01             Logs            READ            
SMB         10.129.35.76    445    DC01             NETLOGON        READ            Logon server share 
SMB         10.129.35.76    445    DC01             SYSVOL          READ            Logon server share 
SMB         10.129.35.76    445    DC01             WSUSTemp                        A network share used by Local Publishing from a Remote WSUS Console Instance.
```

Also we can do user enumeration because of valid credentials we have

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Logging]
└─$ netexec smb 10.129.35.76 -u 'wallace.everette' -p 'Welcome2026@' --users
SMB         10.129.35.76    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:logging.htb) (signing:True) (SMBv1:False) 
SMB         10.129.35.76    445    DC01             [-] Error checking if user is admin on 10.129.35.76: Error occurs while reading from remote(104)
SMB         10.129.35.76    445    DC01             [+] logging.htb\wallace.everette:Welcome2026@ 
SMB         10.129.35.76    445    DC01             -Username-                    -Last PW Set-       -BadPW- -Description-                                               
SMB         10.129.35.76    445    DC01             Administrator                 2026-04-16 14:41:53 0       Built-in account for administering the computer/domain 
SMB         10.129.35.76    445    DC01             Guest                         <never>             0       Built-in account for guest access to the computer/domain 
SMB         10.129.35.76    445    DC01             krbtgt                        2026-04-16 14:47:15 0       Key Distribution Center Service Account 
SMB         10.129.35.76    445    DC01             svc_recovery                  2026-04-16 23:09:49 0        
SMB         10.129.35.76    445    DC01             jaylee.clifton                2026-04-16 23:09:49 0        
SMB         10.129.35.76    445    DC01             monique.chip                  2026-04-16 23:09:49 0        
SMB         10.129.35.76    445    DC01             kyson.abel                    2026-04-16 23:09:50 0        
SMB         10.129.35.76    445    DC01             fable.milford                 2026-04-16 23:09:50 0        
SMB         10.129.35.76    445    DC01             wellington.kylan              2026-04-16 23:09:50 0        
SMB         10.129.35.76    445    DC01             serina.philander              2026-04-16 23:09:50 0        
SMB         10.129.35.76    445    DC01             wallace.everette              2026-04-16 23:09:50 0        
SMB         10.129.35.76    445    DC01             toby.brynleigh                2026-04-16 23:09:50 0        
SMB         10.129.35.76    445    DC01             [*] Enumerated 12 local users: logging
```


Perfect.! Now lets see what Logs share contains useful for us.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Logging]
└─$ smbclient //10.129.35.76/Logs -U 'wallace.everette%Welcome2026@'   
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Fri Apr 17 03:10:09 2026
  ..                                  D        0  Fri Apr 17 03:10:09 2026
  Audit_Heartbeat.log                 A     1294  Fri Apr 17 03:10:09 2026
  IdentitySync_Trace_20260219.log      A     8488  Fri Apr 17 03:10:09 2026
  Service_State.log                   A      468  Fri Apr 17 03:10:09 2026
  TaskMonitor.log                     A     1170  Fri Apr 17 03:10:09 2026

		6657279 blocks of size 4096. 1042360 blocks available
smb: \> RECURSE ON
smb: \> PROMPT OFF
smb: \> mget *
getting file \Audit_Heartbeat.log of size 1294 as Audit_Heartbeat.log (1.0 KiloBytes/sec) (average 1.0 KiloBytes/sec)
getting file \IdentitySync_Trace_20260219.log of size 8488 as IdentitySync_Trace_20260219.log (6.0 KiloBytes/sec) (average 3.6 KiloBytes/sec)
getting file \Service_State.log of size 468 as Service_State.log (0.4 KiloBytes/sec) (average 2.6 KiloBytes/sec)
getting file \TaskMonitor.log of size 1170 as TaskMonitor.log (0.7 KiloBytes/sec) (average 2.0 KiloBytes/sec)
smb: \> exit
```


Once we got all log files from target share , We can analyze these to get some useful info.

```bash
[2026-02-09 03:00:03.125] [PID:4102] [Thread:04] VERBOSE - ConnectionContext Dump: { Domain: "logging.htb", Server: "DC01", SSL: "False", BindUser: "LOGGING\svc_recovery", BindPass: "Em3rg3ncyPa$$2025", Timeout: 30 }
[2026-02-19 03:00:03.488] [PID:4102] [Thread:04] ERROR - System.DirectoryServices.Protocols.LdapException: A local error occurred.
   at System.DirectoryServices.Protocols.LdapConnection.Bind(NetworkCredential credential)
   at logging.IdentitySync.Engine.LdapProvider.Connect()
   --- Server Error Details ---
   Server error: 8009030C: LdapErr: DSID-0C090569, comment: AcceptSecurityContext error, data 52e, v4563
   Hex Error: 0x31 (LDAP_INVALID_CREDENTIALS)
   Win32 Error: 49 (Invalid Credentials)
```


in **logs/IdentitySync_Trace_20260219.log** file , we got this but this error says invalid credentials . Somehow this might be useful for us down the road.

We can try the same enumeration process with new credentials found on log file

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Logging]
└─$ netexec smb 10.129.35.76 -u 'svc_recovery' -p 'Em3rg3ncyPa$$2025' --shares
SMB         10.129.35.76    445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:logging.htb) (signing:True) (SMBv1:False) 
SMB         10.129.35.76    445    DC01             [-] logging.htb\svc_recovery:Em3rg3ncyPa$$2025 STATUS_ACCOUNT_RESTRICTION 
```

But it says account restriction error((.


