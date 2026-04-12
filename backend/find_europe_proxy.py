"""Find working proxy for HDRezka - Ukraine/Europe region."""
import requests
import time
import json

print("=" * 60, flush=True)
print("Finding working proxy for HDRezka.ag", flush=True)
print("=" * 60, flush=True)

# Free proxy lists - Ukraine/Europe proxies
PROXY_SOURCES = [
    # Get fresh proxies from public APIs
    'https://api.proxyscrape.com/v4/free-proxy-recent',
]

# HDRezka test
HDREZKA_URL = 'https://hdrezka.ag/'

def test_proxy(proxy_addr, protocol='http'):
    """Test if proxy can access HDRezka."""
    proxy = {
        'http': f'{protocol}://{proxy_addr}',
        'https': f'{protocol}://{proxy_addr}'
    }
    try:
        start = time.time()
        r = requests.get(HDREZKA_URL, 
                        proxies=proxy, 
                        timeout=10,
                        headers={'User-Agent': 'Mozilla/5.0'})
        elapsed = time.time() - start
        
        if r.status_code == 200:
            # Check if we got HDRezka content
            content = r.text.lower()
            if 'hdrezka' in content or 'фильм' in content or 'кино' in content:
                return True, elapsed
        return False, elapsed
    except:
        return False, 0

def get_europe_proxies():
    """Get list of Europe/Ukraine proxies."""
    proxies = []
    
    # Try to get from proxy list
    try:
        print("\nFetching proxies from proxyscrape...", flush=True)
        r = requests.get('https://api.proxyscrape.com/v4/free-proxy-recent', 
                        timeout=10)
        data = r.json()
        
        for p in data.get('proxies', []):
            country = p.get('country', '').upper()
            # Filter for Europe (Ukraine, Germany, Netherlands, Poland, etc.)
            if country in ['UA', 'DE', 'NL', 'PL', 'FR', 'CZ', 'RO', 'BG', 'HU']:
                addr = f"{p.get('ip')}:{p.get('port')}"
                proxies.append((addr, country))
        
        print(f"Got {len(proxies)} Europe proxies", flush=True)
    except Exception as e:
        print(f"Error fetching: {e}", flush=True)
    
    # Fallback - known proxy ranges
    if not proxies:
        print("\nUsing fallback proxy list...", flush=True)
        # Some known Europe proxy IPs (these change frequently)
        fallback = [
            ('194.28.225.62:3128', 'UA'),  # Ukraine
            ('194.28.225.63:3128', 'UA'),  # Ukraine
            ('185.129.62.62:80', 'UA'),    # Ukraine
            ('91.218.149.50:8080', 'UA'),  # Ukraine
            ('185.164.191.2:8080', 'UA'),  # Ukraine
            ('5.254.55.154:80', 'UA'),     # Ukraine  
            ('91.194.238.154:80', 'UA'),   # Ukraine
            ('176.119.26.10:8080', 'UA'),  # Ukraine
            ('193.34.243.34:3128', 'DE'),  # Germany
            ('195.201.61.222:8000', 'DE'), # Germany
        ]
        proxies = fallback
    
    return proxies

def main():
    # Get proxies
    proxies = get_europe_proxies()
    
    if not proxies:
        print("\n❌ No proxies found!", flush=True)
        return
    
    print(f"\nTesting {len(proxies)} proxies...", flush=True)
    print("=" * 60, flush=True)
    
    working = []
    
    for i, (proxy_addr, country) in enumerate(proxies, 1):
        print(f"[{i}/{len(proxies)}] Testing {proxy_addr} ({country})...", flush=True)
        success, elapsed = test_proxy(proxy_addr)
        
        if success:
            print(f"  ✅ WORKING! ({elapsed:.1f}s)", flush=True)
            working.append((proxy_addr, country, elapsed))
            # Save it
            with open('working_proxy.json', 'w') as f:
                json.dump({
                    'proxy': proxy_addr,
                    'country': country,
                    'time': elapsed
                }, f, indent=2)
            print(f"  Saved to working_proxy.json", flush=True)
            print("\n" + "=" * 60, flush=True)
            print(f"✅ Found working proxy: {proxy_addr} ({country})", flush=True)
            print("=" * 60, flush=True)
            return
        else:
            print(f"  ❌ Failed", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("❌ No working proxies found in the list.", flush=True)
    print("=" * 60, flush=True)
    print("\nAlternative: Use a paid proxy service like:")
    print("  - BrightData (brightdata.com)")
    print("  - SmartProxy (smartproxy.com)")
    print("  - IPRoyal (iproyal.com)")
    print("\nOr deploy a small proxy server on a VPS in Ukraine/Europe")

if __name__ == '__main__':
    main()
