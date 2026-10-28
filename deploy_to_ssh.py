import os
import paramiko
import time

HOST = "10.1.75.53"
PORT = 2213
USER = "student"
PASS = "sunil925742"

print(f"Connecting to {HOST}:{PORT}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
print("Connected!")

sftp = ssh.open_sftp()
remote_dir = "/home/student/assignment-7"

startup_script = """#!/bin/bash
cd /home/student/assignment-7

# Kill previous instances
fuser -k 5213/tcp 2>/dev/null || true
pkill -9 -f "uvicorn.*5213" 2>/dev/null || true
sleep 1

# Start API on port 5213 with 1 worker
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5213 --workers 1 > /home/student/assignment-7/api_5213.log 2>&1 &

sleep 3
echo "=== LISTENING PORTS ==="
ss -tulpn | grep 5213 || true
"""

script_path = f"{remote_dir}/start_api.sh"
with sftp.file(script_path, "w") as f:
    f.write(startup_script)
sftp.chmod(script_path, 0o755)

watchdog_script = """#!/bin/bash
cd /home/student/assignment-7

if ! ss -tulpn | grep -q ":5213 "; then
    echo "$(date): Restarting API on 5213" >> /home/student/assignment-7/watchdog.log
    nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 5213 --workers 1 >> /home/student/assignment-7/api_5213.log 2>&1 &
fi
"""

watchdog_path = f"{remote_dir}/watchdog_5213.sh"
with sftp.file(watchdog_path, "w") as f:
    f.write(watchdog_script)
sftp.chmod(watchdog_path, 0o755)

sftp.close()

print("Restarting uvicorn on port 5213...")
stdin, stdout, stderr = ssh.exec_command("bash /home/student/assignment-7/start_api.sh")
print(stdout.read().decode())
print(stderr.read().decode())

time.sleep(3)
stdin, stdout, stderr = ssh.exec_command("cat /home/student/assignment-7/api_5213.log | tail -n 10")
print("Log:\n", stdout.read().decode())

ssh.close()
print("Done!")
