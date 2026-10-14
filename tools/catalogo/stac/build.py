import json, csv, re, sys
D=sys.argv[1]
cols=json.load(open(f'{D}/all_collections.json'))
pages=json.load(open(f'{D}/pages.json'))
nbs=json.load(open(f'{D}/notebook_md.json'))
STAC='https://stac.arcodatahub.com/collections/'
PAGE='https://arcodatahub.com/datasets/datasets/{}.zarr/'
NB='https://arcodatahub.com/datasets/notebooks/{}/download/'
PL_LEVELS='1000, 925, 850, 700, 500, 250 hPa'
def cat(cid):
    if 'radar' in cid or 'opera' in cid: return 'radar'
    if 'icon' in cid: return 'model'
    if cid=='mswx': return 'other'
    return 'other'
def crs_desc(c):
    dims=c.get('cube:dimensions',{})
    rs=(dims.get('x') or dims.get('longitude') or {}).get('reference_system')
    if isinstance(rs,dict):
        p={q['name']:q['value'] for q in rs['conversion']['parameters']}
        return f"Transverse Mercator lat_0={p['Latitude of natural origin']} lon_0={p['Longitude of natural origin']} k=1 x_0=0 y_0=0, WGS84 ellipsoid (+proj=tmerc +lat_0=42 +lon_0=12.5 +k=1 +x_0=0 +y_0=0 +ellps=WGS84)"
    if rs==4326: return 'EPSG:4326 (regular lat/lon; zarr spatial_ref: sphere R=6371229 m from GRIB)' if 'icon' in c['id'] else 'EPSG:4326'
    if rs==3035: return 'EPSG:3035 (ETRS89 / LAEA Europe)'
    return str(rs)
def grid(c, pg):
    dims=c['cube:dimensions']; xs=pg['xr_dims']
    n=dict(re.findall(r'(\w+) : (\d+)',xs))
    if 'x' in dims:
        return f"{n.get('x','?')} x {n.get('y','?')} (x,y)", f"{dims['x']['step']:g} m x {dims['y']['step']:g} m"
    return f"{n.get('longitude','?')} x {n.get('latitude','?')} (lon,lat)", f"{dims['longitude']['step']} deg lon x {dims['latitude']['step']} deg lat (~2.2 km)"
NOTES={
 'italian-radar-dpc-sri':'Time axis irregular: 15-min steps at 2010 start (per time coordinate), 10-min until July 2018, 5-min after; axis pre-allocated to 2049-12-31, valid data up to attr last_valid.',
 'italian-radar-dpc-srt1-adj':'Time axis irregular: hourly until 2020-07-01T08:00, every 5 min from 2020-07-01T08:55; 1-h accumulation ending at timestamp; pre-allocated to 2050, valid to last_valid.',
 'opera-plus-it-vmi':'Notebook text says "2 km / 5 min" but STAC cube:dimensions step and page say 1 km (3819x4411 grid).',
 'icon-2i':'DEPRECATED: retired 21 Oct 2026, replaced by icon-2i-forecast-3-day. Rolling window of recent runs (6 runs in notebook render). t2m in K, tp accumulated since run start (mm), from notebook text only (no units in metadata).',
 'icon-2i-forecast-3-day':'66 surface/single-level vars at store root + 7 vars in zarr group pressure_level at 1000,925,850,700,500,250 hPa (STAC pressure_level step=150 hPa is wrong). Runs kept (store grows). Temps in degC; fluxes/precip are hourly mean rates (NaN at lead 0). STAC init_time cube extent is stale (ends 2026-10-07T00).',
 'mswx':'Sample of MSWX over Italy/Europe-box; no license, attribution, units or long_names in public metadata; STAC providers lists host only (no producer). Category set to other: site collection Climate, described as sample of the MSWX bias-corrected meteorological dataset (not a reanalysis per se).',
 'italian-radar-dpc-vil':'Units: metadata says mm, notebook text says kg/m2. Data caveat 2019-08-01 06:50 -> 2025-10-08 09:30 on 0.5-unit quantisation (notebook).',
 'italian-radar-dpc-etm':'No-echo-top encoded -9998 throughout.',
}
crow=[]; vrows=[]
for c in cols:
    cid=c['id']; pg=pages[cid]; pm=pg['page_meta']; ga=pg['xr_global_attrs']; nb=nbs.get(cid,{})
    z=c['assets']['zarr-https']; dims=c['cube:dimensions']
    tdim=dims.get('time') or dims.get('init_time')
    gsize,gres=grid(c,pg)
    providers='; '.join(f"{p['name']} [{','.join(p['roles'])}]" for p in c['providers'])
    producer='; '.join(p['name'] for p in c['providers'] if 'producer' in p['roles'])
    tc=pm.get('Temporal coverage','').split(' → ')
    ism=cat(cid)=='model'
    step = ('1 h lead step; runs every 12 h (PT12H)' if ism else
            (pm.get('Resolution','').split(' / ')[0] + (f" (STAC step {tdim.get('step')})" if tdim.get('step') else ' (STAC step null = irregular)')))
    datavars=[k for k,v in c['cube:variables'].items() if k!='valid_time']
    upd = {'model':'new run every 12 h (00/12 UTC), live from MeteoHub','radar':'live, ~5 min (LIVE badge)'}.get(cat(cid),'static sample (no LIVE badge)')
    crow.append({
     'id':cid,'title':c.get('title'),'site_collection':pm.get('Collection',''),
     'product_name':ga.get('product_name') or ga.get('name') or ga.get('title',''),
     'description':c.get('description',''),
     'store':cid+'.zarr','zarr_url':z['href'],
     'providers':providers,'producer':producer,
     'license':c.get('license',''),'license_page':pm.get('License',''),
     'attribution':pm.get('Attribution') or ga.get('attribution_description') or ga.get('Attribution',''),
     'category':cat(cid),
     'bbox_w_s_e_n':' '.join(f'{x:.4f}' for x in c['extent']['spatial']['bbox'][0]),
     'crs':crs_desc(c),'grid_size':gsize,'resolution':gres,
     'temporal_start':c['extent']['temporal']['interval'][0][0],
     'temporal_end_stac':c['extent']['temporal']['interval'][0][1],
     'temporal_end_page':tc[1] if len(tc)>1 else '','last_update_page':pm.get('Last update',''),
     'time_step':step,
     'forecast_range':'0-72 h hourly (73 lead times)' if ism else '',
     'forecast_runs':('00 and 12 UTC; ' + ('rolling window, old runs dropped' if cid=='icon-2i' else 'all runs kept, store grows')) if ism else '',
     'n_variables':len(datavars),
     'update_frequency':upd,
     'size_on_disk_bytes':z.get('file:size',''),'virtual_size_page':pm.get('Virtual size (uncompressed)',''),
     'access_url':z['href'],
     'auth_required':'y (zarr: HTTP 401 without username:api-key; STAC, dataset page and notebook are public)',
     'notes':NOTES.get(cid,''),
     'source_urls':' '.join([STAC+cid, PAGE.format(cid), NB.format(cid)]),
    })
    # variables
    xr={v['name']:v for v in pg['xr_vars']}
    vt={r['Name']:r for r in pg['var_table']}
    for name,sv in c['cube:variables'].items():
        a=xr.get(name.split('/')[-1] if not name.startswith('pressure_level/') else '__none__',{}).get('attrs',{})
        t=vt.get(name,{})
        units=sv.get('unit') or a.get('units') or t.get('Units','')
        desc=sv.get('description') or t.get('Description','')
        lvl=''; acc=a.get('step_type','')
        cm=a.get('cell_methods','')
        n=name
        if name.startswith('pressure_level/'): lvl='isobaric: '+PL_LEVELS+' (zarr group pressure_level)'
        elif cid.startswith('icon'):
            if n.endswith('_2m') or n=='t2m': lvl='height above ground 2 m'
            elif n.endswith('_10m'): lvl='height above ground 10 m'
            elif m:=re.match(r'soil_moisture_(\d+)_(\d+)cm',n): lvl=f'soil layer {m[1]}-{m[2]} cm'
            elif m:=re.match(r'soil_temperature_(\w+)cm',n): lvl=f"soil depth {m[1].replace('p','.')} cm"
            elif n.startswith('cloud_cover_'): lvl='cloud layer '+a.get('comment','').replace('Cloud cover ','').strip('.')
            elif n=='pressure_reduced_to_mean_sea_level': lvl='mean sea level'
            elif n.endswith('_mixed_layer'): lvl='mixed layer (lowest 50 hPa)' if '50' in a.get('short_name','') else 'mixed layer'
            elif n=='height_0c_isotherm': lvl='0 degC isotherm'
            elif n=='height_snowfall_limit': lvl='snowfall limit'
            elif n.startswith('maximum_updraft_helicity'): lvl='layer 2000-8000 m'
            elif 'shear_0_6000m' in n: lvl='layer 0-6000 m above ground'
            elif n.endswith('_atmosphere'): lvl='entire atmosphere (column)'
            elif n=='runoff_subsurface': lvl='subsurface (below 10 cm)'
            elif n=='valid_time': lvl='n/a (coordinate-like)'
            else: lvl='surface'
        elif 'cappi' in cid:
            h=re.search(r'cappi(\d)',cid)[1]; lvl=f'constant altitude {h}000 m'
        elif cid.endswith('vmi'): lvl='column maximum (vertical max of reflectivity)'
        elif cid.endswith('etm'): lvl='echo top (height of highest echo)'
        elif cid.endswith('vil'): lvl='vertical column integral'
        elif cid.endswith(('sri','srt1-adj')): lvl='surface'
        elif cid=='mswx': lvl='surface/near-surface (not stated)'
        if cid=='icon-2i':
            units={'t2m':'K (notebook text)','tp':'mm (notebook text)'}.get(name,units)
            desc={'t2m':'2 m temperature','tp':'total precipitation accumulated since the forecast start','valid_time':'init_time + lead_time'}.get(name,desc)
            acc={'t2m':'instant (implied)','tp':'accumulated since run start'}.get(name,'')
            lvl={'t2m':'height above ground 2 m','tp':'surface','valid_time':'n/a'}[name]
        if cid=='italian-radar-dpc-srt1-adj': acc='accumulated 1 h ending at timestamp ('+cm+')'
        if cid=='italian-radar-dpc-sri': acc='instantaneous rate'
        if cid.split('-')[-1] in ('vmi','etm','vil') or 'cappi' in cid: acc='instantaneous (radar scan)'
        if name.startswith('pressure_level/'): acc='not stated (instant presumably)'
        dims=', '.join(sv.get('dimensions',[]))
        if name.startswith('pressure_level/') and 'pressure_level' not in dims: dims=t.get('Dimensions','')
        vrows.append({'collection_id':cid,'variable':name,
          'long_name':a.get('long_name') or desc,'standard_name':a.get('standard_name',''),'short_name':a.get('short_name',''),
          'units':units,'dimensions':dims or t.get('Dimensions',''),'level':lvl,'accumulation':acc,
          'description':(a.get('comment') or ('' if desc==(a.get('long_name') or desc) and not cid=='icon-2i' else desc)),
          'source_url':' '.join([STAC+cid, PAGE.format(cid)])})
    if cid=='icon-2i-forecast-3-day':
        assert sum(1 for r in vrows if r['collection_id']==cid)==73
def w(path,rows):
    with open(path,'w',newline='') as f:
        wr=csv.DictWriter(f,fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
w(f'{D}/collections.csv',crow); w(f'{D}/variables.csv',vrows)
print(len(crow),len(vrows))
