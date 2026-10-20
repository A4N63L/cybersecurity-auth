"""PID 1: fail closed if ANY critical process exits; forward signals to groups."""
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

children = []
stopping = False


def stop(signum, frame):
    global stopping
    stopping = True


def capture(pipe, path):
    # slapd's real ACCEPT events; timestamp them without its hexadecimal clock.
    with open(path, 'a', buffering=1) as log:
        for line in iter(pipe.readline, ''):
            if ' ACCEPT from IP=' in line:
                event = line[line.index('conn='):].rstrip()
                log.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + event + '\n')


def spawn(command, log=None):
    process = subprocess.Popen(command, start_new_session=True,
                               stderr=subprocess.PIPE if log else None,
                               text=True)
    children.append(process)
    if log:
        threading.Thread(target=capture, args=(process.stderr, log), daemon=True).start()
    return process


def main():
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    for name in ('/run/fail2ban', '/var/log/security'):
        Path(name).mkdir(parents=True, exist_ok=True)
    for name in ('fail2ban.sock', 'fail2ban.pid'):
        try:
            Path('/run/fail2ban', name).unlink()
        except FileNotFoundError:
            pass
    config = json.loads(Path('/etc/security-processes.json').read_text())
    Path(os.environ.get('ACCESS_LOG', '/var/log/security/access.log')).touch(exist_ok=True)
    status = 1
    try:
        spawn(['fail2ban-server', '-f', '-x', 'start'])
        for _ in range(100):
            if children[0].poll() is not None:
                raise RuntimeError('Fail2Ban exited at startup')
            if subprocess.run(['fail2ban-client', 'ping'], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Fail2Ban startup timeout')
        for spec in config:
            spawn(spec['command'], spec.get('log'))
        while not stopping:
            if any(child.poll() is not None for child in children):
                print('Critical process exited; stopping container.', flush=True)
                break
            time.sleep(.2)
        else:
            status = 0
    finally:
        for child in reversed(children):
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
        deadline = time.monotonic() + 15
        for child in children:
            try:
                child.wait(timeout=max(.1, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    return status


if __name__ == '__main__':
    sys.exit(main())
