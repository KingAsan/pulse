"""Test HDRezka on Railway server."""
import requests
import json
import time

RAILWAY_URL = "https://puls.up.railway.app"

print("=" * 60, flush=True)
print(f"Testing HDRezka on Railway: {RAILWAY_URL}", flush=True)
print("=" * 60, flush=True)

# 1. Health check
print("\n[1] Health check...", flush=True)
try:
    r = requests.get(f'{RAILWAY_URL}/api/health', timeout=10)
    print(f"   Status: {r.status_code}", flush=True)
    print(f"   Response: {r.json()}", flush=True)
except Exception as e:
    print(f"   ❌ Error: {e}", flush=True)
    exit(1)

# 2. Login
print("\n[2] Login as King...", flush=True)
try:
    r = requests.post(f'{RAILWAY_URL}/api/auth/login', 
                     json={'username': 'King', 'password': 'A77052967746a'},
                     timeout=10)
    data = r.json()
    if 'token' not in data:
        print(f"   ❌ Login failed: {data}", flush=True)
        exit(1)
    
    token = data['token']
    print(f"   ✅ Logged in as {data['user']['username']} (admin={data['user']['is_admin']})", flush=True)
except Exception as e:
    print(f"   ❌ Error: {e}", flush=True)
    exit(1)

headers = {'Authorization': f'Bearer {token}'}

# 3. Test HDRezka categories
print("\n[3] HDRezka categories...", flush=True)
try:
    r = requests.get(f'{RAILWAY_URL}/api/hdrezka/categories', 
                    headers=headers, timeout=15)
    print(f"   Status: {r.status_code}", flush=True)
    if r.status_code == 200:
        cats = r.json()
        print(f"   ✅ Categories: {len(cats)}", flush=True)
        for cat in cats:
            print(f"      - {cat['name']}", flush=True)
    else:
        print(f"   ❌ Response: {r.text[:200]}", flush=True)
except Exception as e:
    print(f"   ❌ Error: {e}", flush=True)

# 4. Test HDRezka search
print("\n[4] HDRezka search (Матрица)...", flush=True)
start = time.time()
try:
    r = requests.get(f'{RAILWAY_URL}/api/hdrezka/search', 
                    params={'q': 'Матрица', 'limit': 5},
                    headers=headers, timeout=60)
    elapsed = time.time() - start
    print(f"   Status: {r.status_code} ({elapsed:.1f}s)", flush=True)
    
    if r.status_code == 200:
        results = r.json()
        if isinstance(results, list):
            print(f"   {'✅' if results else '⚠️ '} Results: {len(results)}", flush=True)
            if results:
                for i, item in enumerate(results[:3], 1):
                    print(f"   {i}. {item.get('title', 'N/A')} ({item.get('type', '?')})", flush=True)
                    if i == 1:
                        first_item = item
        else:
            print(f"   Response: {str(results)[:200]}", flush=True)
    else:
        print(f"   ❌ Response: {r.text[:300]}", flush=True)
except requests.exceptions.Timeout:
    print(f"   ❌ Timeout ({elapsed:.1f}s)", flush=True)
except Exception as e:
    print(f"   ❌ Error: {e}", flush=True)

# 5. Test HDRezka browse
print("\n[5] HDRezka browse (films)...", flush=True)
try:
    r = requests.get(f'{RAILWAY_URL}/api/hdrezka/browse', 
                    params={'category': 'films'},
                    headers=headers, timeout=30)
    print(f"   Status: {r.status_code}", flush=True)
    if r.status_code == 200:
        results = r.json()
        if isinstance(results, list):
            print(f"   {'✅' if results else '⚠️ '} Films: {len(results)}", flush=True)
            if results:
                print(f"   Example: {results[0].get('title', 'N/A')}", flush=True)
    else:
        print(f"   ❌ Response: {r.text[:200]}", flush=True)
except Exception as e:
    print(f"   ❌ Error: {e}", flush=True)

print("\n" + "=" * 60, flush=True)
print("Test complete!", flush=True)
print("=" * 60, flush=True)
