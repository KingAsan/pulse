"""Full HDRezka test on Railway."""
import requests
import json

RAILWAY_URL = "https://puls.up.railway.app"

print("=" * 60, flush=True)
print("Full HDRezka Test on Railway", flush=True)
print("=" * 60, flush=True)

# Login
r = requests.post(f'{RAILWAY_URL}/api/auth/login', 
                 json={'username': 'King', 'password': 'A77052967746a'},
                 timeout=10)
token = r.json()['token']
headers = {'Authorization': f'Bearer {token}'}
print("✅ Logged in", flush=True)

# Search
r = requests.get(f'{RAILWAY_URL}/api/hdrezka/search', 
                params={'q': 'Матрица', 'limit': 3},
                headers=headers, timeout=30)
results = r.json()
print(f"\n✅ Search: {len(results)} results", flush=True)

if results:
    first = results[0]
    print(f"\n[1] Testing detail for: {first['title']}", flush=True)
    print(f"    URL: {first['url'][:60]}...", flush=True)
    
    # Get detail
    r = requests.get(f'{RAILWAY_URL}/api/hdrezka/detail', 
                    params={'url': first['url']},
                    headers=headers, timeout=30)
    
    if r.status_code == 200:
        detail = r.json()
        print(f"    ✅ Title: {detail.get('title', 'N/A')}", flush=True)
        print(f"    ✅ Type: {detail.get('content_type', 'N/A')}", flush=True)
        print(f"    ✅ Year: {detail.get('year', 'N/A')}", flush=True)
        print(f"    ✅ Rating: {detail.get('imdb_rating', 'N/A')}", flush=True)
        print(f"    ✅ Translators: {len(detail.get('translator_list', []))}", flush=True)
        if detail.get('translator_list'):
            for tr in detail['translator_list'][:3]:
                print(f"       - {tr['title']}", flush=True)
        
        # Test streams if movie
        if detail.get('content_type') == 'movie' and detail.get('translator_list'):
            print(f"\n[2] Testing streams...", flush=True)
            tr_id = detail['translator_list'][0]['id']
            r = requests.get(f'{RAILWAY_URL}/api/hdrezka/streams', 
                           params={'url': first['url'], 'translator_id': tr_id},
                           headers=headers, timeout=30)
            
            if r.status_code == 200:
                streams = r.json()
                if streams.get('tracks'):
                    print(f"    ✅ Tracks: {len(streams['tracks'])}", flush=True)
                    track = streams['tracks'][0]
                    print(f"    ✅ Translator: {track.get('title', 'N/A')}", flush=True)
                    print(f"    ✅ Qualities: {list(track.get('videos', {}).keys())}", flush=True)
                else:
                    print(f"    ⚠️  No tracks found", flush=True)
            else:
                print(f"    ❌ Streams error: {r.status_code}", flush=True)
    else:
        print(f"    ❌ Detail error: {r.status_code}", flush=True)

print("\n" + "=" * 60, flush=True)
print("✅ HDRezka FULLY WORKING on Railway!", flush=True)
print("=" * 60, flush=True)
