import os
import subprocess
import urllib.request

subprocess.run(['fail2ban-client', 'ping'], check=True, stdout=subprocess.DEVNULL)
with urllib.request.urlopen(os.environ['HEALTH_URL'], timeout=4) as response:
    assert response.status == 200
