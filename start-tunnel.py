#!/usr/bin/env python3
"""Start localhost.run tunnel in background."""
import subprocess, time, re, sys

logfile = open('/tmp/localtunnel.log', 'w')
proc = subprocess.Popen([
    'ssh',
    '-o', 'StrictHostKeyChecking=no',
    '-o', 'ServerAliveInterval=15',
    '-o', 'ServerAliveCountMax=6',
    '-o', 'ExitOnForwardFailure=yes',
    '-o', 'TCPKeepAlive=yes',
    '-o', 'ConnectTimeout=10',
    '-R', '80:localhost:6999',
    'nvii@localhost.run'
], stdout=logfile, stderr=logfile, stdin=subprocess.DEVNULL, start_new_session=True)

time.sleep(10)
logfile.close()

with open('/tmp/localtunnel.log') as f:
    content = f.read()

urls = re.findall(r'https://[a-f0-9]+\.lhr\.life', content)
if urls:
    print(urls[0])
    sys.exit(0)
else:
    print('NO_URL')
    sys.exit(1)
