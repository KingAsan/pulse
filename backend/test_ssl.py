"""Test HDRezka with SSL verification disabled."""
import requests
import urllib3
import time

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Testing HDRezka.ag with SSL verification disabled...", flush=True)

# Test with verify=False
try:
    start = time.time()
    r = requests.get('https://hdrezka.ag/', 
                    timeout=15,
                    verify=False,
                    headers={'User-Agent': 'Mozilla/5.0'})
    elapsed = time.time() - start
    print(f"Status: {r.status_code} ({elapsed:.1f}s)", flush=True)
    
    if r.status_code == 200:
        print(f"✅ HDRezka accessible! ({len(r.text)} bytes)", flush=True)
        # Check content
        if 'фильм' in r.text.lower() or 'movie' in r.text.lower() or 'регистра' in r.text.lower():
            print("✅ Got valid HDRezka page!", flush=True)
    else:
        print(f"❌ Status: {r.status_code}", flush=True)
        print(f"Response: {r.text[:200]}", flush=True)
except Exception as e:
    print(f"❌ Error: {e}", flush=True)

# Check our IP
print("\nChecking IP...", flush=True)
try:
    r = requests.get('https://api.ipify.org?format=json', timeout=10)
    print(f"IP: {r.json().get('ip', 'Unknown')}", flush=True)
except Exception as e:
    print(f"IP check error: {e}", flush=True)
