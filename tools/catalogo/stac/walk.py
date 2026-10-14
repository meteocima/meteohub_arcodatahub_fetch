import json, sys
sys.path.insert(0, sys.argv[2])
from fetch import get
RAW=sys.argv[1]
url='https://stac.arcodatahub.com/collections'; cols=[]
while url:
    c,b=get(url); d=json.loads(b); cols+=d['collections']
    url=next((l['href'] for l in d['links'] if l['rel']=='next'),None)
print(len(cols))
for u in ['https://stac.arcodatahub.com/','https://stac.arcodatahub.com/conformance']: print(get(u)[0],u)
for col in cols:
    cid=col['id']
    for u in [f'https://stac.arcodatahub.com/collections/{cid}', f'https://stac.arcodatahub.com/collections/{cid}/items?limit=100', f'https://stac.arcodatahub.com/collections/{cid}/queryables']:
        c,b=get(u); print(c,len(b),u)
    print(cid, col.get('title'), col['extent']['temporal']['interval'], list(col.get('assets',{})), len(col.get('cube:variables',{})))
json.dump(cols,open(RAW+'/../all_collections.json','w'),indent=1)
