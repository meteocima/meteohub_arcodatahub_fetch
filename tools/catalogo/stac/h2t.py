import sys, html.parser, re
class P(html.parser.HTMLParser):
    def __init__(s): super().__init__(); s.out=[]; s.skip=0
    def handle_starttag(s,t,a):
        if t in('script','style'): s.skip+=1
        if t in('tr','p','div','li','h1','h2','h3','h4','br','dt','dd','pre'): s.out.append('\n')
        if t in('td','th'): s.out.append(' | ')
        if t=='a':
            h=dict(a).get('href'); 
            if h and h.startswith('http'): s.out.append(f'[{h}]')
    def handle_endtag(s,t):
        if t in('script','style'): s.skip-=1
    def handle_data(s,d):
        if not s.skip: s.out.append(d)
p=P(); p.feed(open(sys.argv[1],encoding='utf-8',errors='replace').read())
t=''.join(p.out); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\n\s*\n+','\n',t); print(t)
