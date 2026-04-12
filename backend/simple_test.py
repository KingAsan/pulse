"""Simple HDRezka test."""
import requests
import time

print("=" * 50)
print("HDRezka Direct Test", flush=True)
print("=" * 50, flush=True)

# 1. Test direct access
print("\n[1] Direct HDRezka.ag...", flush=True)
try:
    start = time.time()
    r = requests.get('https://hdrezka.ag/', timeout=15)
    elapsed = time.time() - start
    print(f"    Status: {r.status_code} ({elapsed:.1f}s)", flush=True)
    if r.status_code == 200:
        print(f"    ✅ SUCCESS - {len(r.text)} bytes", flush=True)
    else:
        print(f"    ❌ Failed", flush=True)
except Exception as e:
    print(f"    ❌ Error: {e}", flush=True)

# 2. Login
print("\n[2] Login...", flush=True)
try:
    r = requests.post('http://localhost:5000/api/auth/login', 
                     json={'username': 'King', 'password': 'A77052967746a'},
                     timeout=10)
    data = r.json()
    token = data['token']
    print(f"    ✅ {data['user']['username']}", flush=True)
except Exception as e:
    print(f"    ❌ {e}", flush=True)
    exit(1)

headers = {'Authorization': f'Bearer {token}'}

# 3. Search
print("\n[3] Search...", flush=True)
try:
    start = time.time()
    r = requests.get('http://localhost:5000/api/hdrezka/search', 
                    params={'q': 'Матрица', 'limit': 3},
                    headers=headers, timeout=60)
    elapsed = time.time() - start
    print(f"    Status: {r.status_code} ({elapsed:.1f}s)", flush=True)
    print(f"    Response: {r.text[:300]}", flush=True)
except Exception as e:
    print(f"    ❌ {e}", flush=True)

# 4. Browse
print("\n[4] Browse films...", flush=True)
try:
    start = time.time()
    r = requests.get('http://localhost:5000/api/hdrezka/browse', 
                    params={'category': 'films'},
                    headers=headers, timeout=60)
    elapsed = time.time() - start
    print(f"    Status: {r.status_code} ({elapsed:.1f}s)", flush=True)
    if r.status_code == 200:
        data = r.json()
        print(f"    ✅ {len(data) if isinstance(data, list) else 0} results", flush=True)
except Exception as e:
    print(f"    ❌ {e}", flush=True)

print("\n" + "=" * 50, flush=True)
