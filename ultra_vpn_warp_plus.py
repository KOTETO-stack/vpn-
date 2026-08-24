#!/usr/bin/env python3
import requests, re, json, os, time, socket
from datetime import datetime

# 🔑 ВСТАВЬТЕ СЮДА ВАШИ WARP+ КЛЮЧИ
WARP_PLUS_CONFIG = {
    "id": "",                           # ← Ваш UUID
    "license": "",                      # ← Ваш ключ XXXX-XXXX-XXXX
    "private_key": "",                  # ← Ваш приватный ключ
    "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
    "endpoint": "engage.cloudflareclient.com:2408",
    "ipv4": "172.16.0.2",
    "ipv6": "",                         # ← Ваш IPv6
    "reserved": [0, 0, 0],              # ← Ваши 3 числа
    "client_id": "",                    # ← Ваш client_id
}

# 📡 ИСТОЧНИКИ (добавьте ссылки на конфиги)
SOURCES = {
    "public_repos": [
        # ← СЮДА ВСТАВЬТЕ ССЫЛКИ НА КОНФИГИ
        # Пример: "https://raw.githubusercontent.com/.../configs.txt",
    ]
}

MAX_PING = 300
TOP_CONFIGS = 15
OUTPUT_DIR = os.path.expanduser("~/ultra_vpn_configs")

class ConfigBase:
    def __init__(self, url):
        self.original_url = url
        self.protocol = None
        self.address = None
        self.port = None
        self.remark = ""
        self.ping = None
        self.is_working = False
        self.supports_udp = False
        self.is_stealth = False
        self.region = ""

    def detect_region(self):
        addr = self.address.lower() if self.address else ""
        regions = {"germany": "DE", "netherlands": "NL", "finland": "FI", 
                   "turkey": "TR", "singapore": "SG", "hongkong": "HK"}
        for k, v in regions.items():
            if k in addr:
                self.region = v
                return
        self.region = "UN"

class HY2Config(ConfigBase):
    def __init__(self, url):
        super().__init__(url)
        self.protocol = "hysteria2"
        self.supports_udp = True
        m = re.match(r'hysteria2://(?:([^@]+)@)?([^:]+):(\d+)\?([^#]*)#?(.*)', url)
        if m:
            self.address = m.group(2)
            self.port = int(m.group(3))
            self.remark = __import__('urllib.parse').parse.unquote(m.group(5)) if m.group(5) else ""
            self.is_stealth = 'sni' in m.group(4)

class VLESSConfig(ConfigBase):
    def __init__(self, url):
        super().__init__(url)
        self.protocol = "vless"
        m = re.match(r'vless://([^@]+)@([^:]+):(\d+)\?([^#]*)#?(.*)', url)
        if m:
            self.address = m.group(2)
            self.port = int(m.group(3))
            self.remark = __import__('urllib.parse').parse.unquote(m.group(5)) if m.group(5) else ""
            pr = {k: v for k, v in [x.split('=', 1) for x in m.group(4).split('&') if '=' in x]}
            self.supports_udp = pr.get('type') in ['grpc', 'quic']
            self.is_stealth = pr.get('security') in ['reality', 'xtls']

def extract_configs(text):
    configs = []
    for m in re.finditer(r'hysteria2://[^\s<>"\']+', text):
        configs.append(HY2Config(m.group()))
    for m in re.finditer(r'vless://[^\s<>"\']+', text):
        configs.append(VLESSConfig(m.group()))
    return configs

def fetch_url(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        return extract_configs(r.text)
    except:
        return []

def tcp_ping(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except:
        return False

def generate_output(configs, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    configs.sort(key=lambda x: (0 if x.protocol == "hysteria2" else 1, 0 if x.supports_udp else 1))
    
    lines = []
    lines.append("# 🔥 Ultra VPN + WARP+")
    lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # WARP+ шаблон
    wp = WARP_PLUS_CONFIG
    if wp["private_key"]:
        lines.append(f"# WARP+ ACTIVE: {wp['license'][:4]}****")
    else:
        lines.append("# WARP+ NOT CONFIGURED - Add your keys above")
    lines.append("")
    
    for i, c in enumerate(configs[:TOP_CONFIGS]):
        flags = []
        if c.supports_udp: flags.append("📞")
        if c.is_stealth: flags.append("🥷")
        if c.protocol == "hysteria2": flags.append("⚡")
        
        remark = f"[{i+1}] {' '.join(flags)} {c.region} | {c.protocol.upper()} | {c.remark or c.address}"
        url = c.original_url.split('#')[0] + '#' + __import__('urllib.parse').parse.quote(remark)
        lines.append(url)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    print("=" * 50)
    print("🔥 Ultra VPN + WARP+")
    print("=" * 50)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_configs = []
    
    # Загрузка
    print("\nLoading configs...")
    for url in SOURCES["public_repos"]:
        if url:
            configs = fetch_url(url)
            all_configs.extend(configs)
            print(f"  {url.split('/')[-1]}: {len(configs)} configs")
            time.sleep(1)
    
    # Уникальные
    seen = set()
    unique = []
    for c in all_configs:
        key = f"{c.address}:{c.port}"
        if key not in seen and c.address and c.port:
            seen.add(key)
            unique.append(c)
    all_configs = unique
    
    print(f"\nTotal unique: {len(all_configs)}")
    
    if not all_configs:
        print("\n⚠️ No configs found!")
        print("Add sources to SOURCES['public_repos']")
        return
    
    # Проверка
    print("\nTesting...")
    working = [c for c in all_configs if tcp_ping(c.address, c.port)]
    print(f"Working: {len(working)}/{len(all_configs)}")
    
    # Сохранение
    output_file = os.path.join(OUTPUT_DIR, "karing_subscription.txt")
    generate_output(working, output_file)
    
    print(f"\n✅ Done! File saved: {output_file}")
    print(f"Total configs in list: {min(len(working), TOP_CONFIGS)}")

if __name__ == "__main__":
    main()
