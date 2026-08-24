#!/usr/bin/env python3
import requests, re, json, os, time, socket
from datetime import datetime

SOURCES = {"public_repos": []}
MAX_PING, TOP = 300, 15
OUT = os.path.expanduser("~/vpn_configs")

class C:
    def __init__(self, url):
        self.url = url
        self.p = None
        self.a = None
        self.pt = None
        self.r = ""
        self.ok = False
        self.udp = False

def ext(t):
    r = []
    for m in re.finditer(r'hysteria2://[^\s<>"\']+', t):
        r.append(("hysteria2", m.group()))
    for m in re.finditer(r'vless://[^\s<>"\']+', t):
        r.append(("vless", m.group()))
    for m in re.finditer(r'vmess://[^\s<>"\']+', t):
        r.append(("vmess", m.group()))
    return r

def fetch(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        return ext(r.text)
    except:
        return []

def ping(h, p):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        ok = s.connect_ex((h, p)) == 0
        s.close()
        return ok
    except:
        return False

def parse(url):
    if url.startswith("hysteria2://"):
        m = re.match(r'hysteria2://(?:([^@]+)@)?([^:]+):(\d+)', url)
        if m:
            return C(url)
    elif url.startswith("vless://"):
        m = re.match(r'vless://([^@]+)@([^:]+):(\d+)', url)
        if m:
            return C(url)
    elif url.startswith("vmess://"):
        return C(url)
    return None

def main():
    print("VPN Collector")
    os.makedirs(OUT, exist_ok=True)
    
    all = []
    for url in SOURCES["public_repos"]:
        if url and url.strip():
            all.extend(fetch(url))
            time.sleep(1)
    
    # Parse
    configs = []
    for p, url in all:
        c = parse(url)
        if c:
            c.p = p
            configs.append(c)
    
    # Unique
    seen = set()
    unique = []
    for c in configs:
        if c.a and f"{c.a}:{c.pt}" not in seen:
            seen.add(f"{c.a}:{c.pt}")
            unique.append(c)
    configs = unique
    
    print(f"Found: {len(configs)}")
    
    # Test
    working = []
    for c in configs:
        if ping(c.a, c.pt):
            c.ok = True
            working.append(c)
    
    print(f"Working: {len(working)}")
    
    # Save
    lines = ["# VPN Configs", f"# {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    for i, c in enumerate(working[:TOP]):
        f = "⚡" if c.p == "hysteria2" else ""
        n = f"[{i+1}] {f} {c.p.upper()} | {c.r or 'server'}"
        lines.append(c.url.split('#')[0] + '#' + __import__('urllib.parse').parse.quote(n))
    
    out = os.path.join(OUT, "karing.txt")
    with open(out, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Saved: {out}")

if __name__ == "__main__":
    main()
