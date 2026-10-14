import json, sys, os, re, urllib.request, urllib.error, hashlib
RAW = sys.argv[1]
def fname(url):
    s = re.sub(r'^https?://', '', url); s = re.sub(r'[^A-Za-z0-9._-]+', '_', s)
    return s[:180]
def get(url, ext='.json'):
    p = os.path.join(RAW, fname(url) + ext)
    if os.path.exists(p):
        b = open(p,'rb').read(); return 200, b
    req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 catalog'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read(); code = r.status
    except urllib.error.HTTPError as e:
        b = e.read(); code = e.code
    except Exception as e:
        return None, str(e).encode()
    open(p if code==200 else p+f'.HTTP{code}', 'wb').write(b)
    return code, b
if __name__ == '__main__':
    for u in sys.argv[2:]:
        c, b = get(u, '.html' if 'arcodatahub.com/datasets' in u else '.json')
        print(c, len(b), u)
