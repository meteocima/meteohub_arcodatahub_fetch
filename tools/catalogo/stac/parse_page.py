import sys, json, re, html.parser
class P(html.parser.HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.stack=[]; s.vars=[]; s.cur=None; s.field=None; s.dt=None; s.gattrs=[]; s.in_gattrs=False
        s.tables=[]; s.tab=None; s.row=None; s.cell=None; s.dims={}; s.dimtxt=None; s.skip=0
    def cls(s,a): return (dict(a).get('class') or '').split()
    def handle_starttag(s,t,a):
        c=s.cls(a); s.stack.append((t,c))
        if t in('script','style'): s.skip+=1
        if t=='li' and 'xr-var-item' in c: s.cur={'name':'','dims':'','dtype':'','attrs':{}}; s.vars.append(s.cur)
        if s.cur is not None:
            for k in ('xr-var-name','xr-var-dims','xr-var-dtype'):
                if k in c: s.field=k.split('-')[-1]
        if t=='dl' and 'xr-attrs' in c and s.cur is None: s.in_gattrs=True; s.gattrs=[]
        if t=='dt': s.dt=''; s.field='dt'
        if t=='dd': s.ddv=''; s.field='dd'
        if t=='table': s.tab=[]
        if t=='tr' and s.tab is not None: s.row=[]
        if t in('td','th') and s.row is not None: s.cell=''
        if t=='ul' and 'xr-dim-list' in c: s.dimtxt=''
    def handle_endtag(s,t):
        if t in('script','style'): s.skip-=1
        while s.stack:
            tt,c=s.stack.pop()
            if tt==t: break
        else: c=[]
        if t=='li' and 'xr-var-item' in c: s.cur=None
        if t=='div' and s.field in('name','dims','dtype'): s.field=None
        if t=='dd':
            tgt = s.cur['attrs'] if s.cur is not None else None
            k=(s.dt or '').strip().rstrip(':').strip()
            if tgt is not None: tgt[k]=s.ddv.strip()
            elif s.in_gattrs: s.gattrs.append((k,s.ddv.strip()))
            s.field=None
        if t=='dt': s.field=None
        if t=='dl': s.in_gattrs=False
        if t in('td','th') and s.row is not None and s.cell is not None: s.row.append(s.cell.strip()); s.cell=None
        if t=='tr' and s.tab is not None and s.row is not None: s.tab.append(s.row); s.row=None
        if t=='table' and s.tab is not None: s.tables.append(s.tab); s.tab=None
        if t=='ul' and s.dimtxt is not None: s.dims_raw=s.dimtxt; s.dimtxt=None
    def handle_data(s,d):
        if s.skip: return
        if s.dimtxt is not None: s.dimtxt+=d+' '
        if s.cell is not None: s.cell+=d
        if s.field in('name','dims','dtype') and s.cur is not None: s.cur[s.field]+=d
        elif s.field=='dt': s.dt+=d
        elif s.field=='dd': s.ddv+=d
def text(path):
    import subprocess
class T(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.o=[]; s.skip=0
    def handle_starttag(s,t,a):
        if t in('script','style'): s.skip+=1
        if t in('tr','p','div','li','h1','h2','h3','h4','br','dt','dd','pre'): s.o.append('\n')
    def handle_endtag(s,t):
        if t in('script','style'): s.skip-=1
    def handle_data(s,d):
        if not s.skip: s.o.append(d)
out={}
for path in sys.argv[2:]:
    h=open(path,encoding='utf-8').read()
    store=re.search(r'datasets_datasets_(.+?)\.zarr_\.html',path).group(1)
    p=P(); p.feed(h)
    t=T(); t.feed(h); lines=[l.strip() for l in ''.join(t.o).split('\n') if l.strip()]
    meta={}
    labels=['Collection','License','Attribution','Temporal coverage','Last update','Spatial extent (W / S / E / N)','Resolution','Grid CRS','Virtual size (uncompressed)','Size on disk (full download)']
    for i,l in enumerate(lines[:200]):
        if l in labels and l not in meta: meta[l]=lines[i+1]
    try:
        i=lines.index('Notebook'); j=next(k for k in range(i,len(lines)) if lines[k].startswith('In [1]'))
        intro=' '.join(lines[i+1:j])
    except Exception: intro=''
    vt=[]
    for tab in p.tables:
        if tab and tab[0][:4]==['Name','Description','Units','Dimensions']: vt=[dict(zip(tab[0],r)) for r in tab[1:]]
    for v in p.vars:
        for k in ('name','dims','dtype'): v[k]=re.sub(r'\s+',' ',v[k]).strip()
    out[store]={'page_meta':meta,'notebook_intro':intro,'var_table':vt,'xr_vars':p.vars,'xr_global_attrs':dict(p.gattrs),'xr_dims':re.sub(r'\s+',' ',getattr(p,'dims_raw','')).strip()}
json.dump(out,open(sys.argv[1],'w'),indent=1,ensure_ascii=False)
