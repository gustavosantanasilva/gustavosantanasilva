import json, os, random, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config.json").read_text())
TOKEN = os.getenv("GITHUB_TOKEN", "")
USER = os.getenv("GITHUB_REPOSITORY_OWNER", CFG["username"])

def api(url):
    headers={"Accept":"application/vnd.github+json","User-Agent":"gustavo-github-profile"}
    if TOKEN: headers["Authorization"]="Bearer "+TOKEN
    req=urllib.request.Request(url,headers=headers)
    with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)

def get_days():
    since=datetime.now(timezone.utc)-timedelta(days=CFG["recent_days"])
    q=urllib.parse.quote(f"author:{USER} committer-date:>={since.date().isoformat()}")
    days={}
    for page in range(1,11):
        try:
            data=api(f"https://api.github.com/search/commits?q={q}&per_page=100&page={page}")
        except Exception: break
        items=data.get("items",[])
        for item in items:
            d=item.get("commit",{}).get("author",{}).get("date","")[:10]
            if d: days[d]=days.get(d,0)+1
        if len(items)<100: break
    return days

def streak(days):
    d=datetime.now(timezone.utc).date()
    if d.isoformat() not in days: d-=timedelta(days=1)
    n=0
    while d.isoformat() in days:
        n+=1; d-=timedelta(days=1)
    return n

# ---- heatmap grid, same layout as GitHub contribution graph ----
CELL=11; GAP=3; PITCH=CELL+GAP
DAYS_LABEL=["Seg","Qua","Sex"]

def build_weeks(days):
    end=datetime.now(timezone.utc).date()
    start=end-timedelta(days=CFG["recent_days"])
    first=start-timedelta(days=start.weekday())
    weeks=[]
    cur=first
    while cur<=end:
        col=[]
        for d in range(7):
            day=cur+timedelta(days=d)
            col.append(days.get(day.isoformat(),0))
        weeks.append(col)
        cur+=timedelta(days=7)
    return weeks

# ---- top languages (aggregated over public repos) ----
LANG_COLORS={
    "Python":"#3776ab","PHP":"#777bb4","JavaScript":"#f1e05a","TypeScript":"#3178c6",
    "HTML":"#e34c26","CSS":"#563d7c","MySQL":"#4479a1","Docker":"#2496ed",
    "Shell":"#89e051","Java":"#b07219","C":"#555555","C++":"#f34b7d",
    "C#":"#178600","Go":"#00adda","Rust":"#dea584","Dart":"#00b4ab",
    "Kotlin":"#b125ea","Ruby":"#cc342d","Swift":"#f05138","Lua":"#000080",
}
FALLBACK_LANG="#7c8cf8"

def get_top_langs():
    langs={}
    page=1
    while page<=10:
        try:
            repos=api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&visibility=public")
        except Exception: break
        if not isinstance(repos,list) or not repos: break
        for repo in repos:
            name=repo.get("name")
            if not name or repo.get("fork"): continue
            try:
                data=api(f"https://api.github.com/repos/{USER}/{name}/languages")
            except Exception: continue
            for k,v in data.items():
                langs[k]=langs.get(k,0)+v
        if len(repos)<100: break
        page+=1
    return langs

def top_langs_svg(langs):
    t=CFG["theme"]
    if not langs:
        langs={"#0 (nenhum repo público)":0}
    top=sorted(langs.items(), key=lambda kv:-kv[1])[:5]
    total=sum(langs.values()) or 1
    W=430; H=250

    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Top Linguagens de Gustavo Santos">']
    s.append('<defs>')
    s.append('<linearGradient id="langBg" x1="0" y1="0" x2="0" y2="1">')
    s.append('<stop offset="0" stop-color="#05070f"/><stop offset="0.5" stop-color="#0b1020"/><stop offset="1" stop-color="#141b3c"/>')
    s.append('</linearGradient>')
    s.append('<radialGradient id="langNeb" cx="0.5" cy="0.5" r="0.5">')
    s.append('<stop offset="0" stop-color="#6366f1" stop-opacity="0.22"/><stop offset="1" stop-color="#6366f1" stop-opacity="0"/>')
    s.append('</radialGradient>')
    s.append('<linearGradient id="langEdge" x1="0" y1="0" x2="1" y2="1">')
    s.append('<stop offset="0" stop-color="#ffffff" stop-opacity="0.28"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.02"/>')
    s.append('</linearGradient>')
    # per-language bar gradients
    for i,(name,_) in enumerate(top):
        c=LANG_COLORS.get(name,FALLBACK_LANG)
        s.append(f'<linearGradient id="barG{i}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c}"/><stop offset="1" stop-color="#ffffff"/></linearGradient>')
    s.append('</defs>')

    s.append(f'<rect width="{W}" height="{H}" rx="22" fill="url(#langBg)"/>')
    s.append(f'<circle cx="{W-40}" cy="30" r="70" fill="url(#langNeb)"/>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="none" stroke="url(#langEdge)" stroke-width="1.4"/>')

    # header (Portuguese)
    s.append('<circle cx="24" cy="30" r="6" fill="#67e8f9" opacity="0.85"><animate attributeName="opacity" values="0.85;0.3;0.85" dur="2.6s" repeatCount="indefinite"/></circle>')
    s.append(f'<text x="40" y="35" fill="{t["text"]}" font-family="sans-serif" font-size="19" font-weight="800">Top Linguagens</text>')
    s.append(f'<text x="40" y="55" fill="{t["muted"]}" font-family="sans-serif" font-size="12">volume de código em repositórios públicos</text>')

    # divider
    s.append(f'<line x1="24" y1="72" x2="{W-24}" y2="72" stroke="#818cf8" stroke-opacity="0.25" stroke-width="1"/>')

    # rows: name | percent | animated bar
    ry=88
    for i,(name,bytes_) in enumerate(top):
        bp=bytes_/total*100
        hx=46
        bw=320
        w=bw*bp/100
        c=LANG_COLORS.get(name,FALLBACK_LANG)
        s.append(f'<circle cx="32" cy="{ry+7}" r="4" fill="{c}"/>')
        s.append(f'<text x="46" y="{ry+11}" fill="#e2e8f0" font-family="monospace" font-size="13" font-weight="600">{name}</text>')
        s.append(f'<text x="406" y="{ry+11}" text-anchor="end" fill="{t["power"]}" font-family="monospace" font-size="12.5" font-weight="700">{bp:.1f}%</text>')
        # track
        s.append(f'<rect x="{hx}" y="{ry+18}" width="{bw}" height="8" rx="4" fill="#1c2546"/>')
        # fill (animates once on load)
        s.append(f'<rect x="{hx}" y="{ry+18}" width="{w:.1f}" height="8" rx="4" fill="url(#barG{i})"><animate attributeName="width" from="0" to="{w:.1f}" dur="1.1s" begin="{i*0.15:.2f}s" fill="freeze"/></rect>')
        ry+=44

    # footer
    s.append(f'<text x="24" y="{H-14}" fill="{t["muted"]}" font-family="sans-serif" font-size="10.5">atualizado automaticamente · via GitHub Actions</text>')

    s.append('</svg>')
    return "".join(s)

def contribution_svg(days, total, st, active_days):
    t=CFG["theme"]; weeks=build_weeks(days)
    ncols=len(weeks)
    W=90+ncols*PITCH+40
    H=330
    top=110

    # star brightness scale (dim indigo -> bright white)
    star_cols=["#7c8cf8","#5eead4","#a5f3fc","#ffffff"]
    empty_col="#1c2546"

    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Gustavo Santos - Constelação de Commits">']
    s.append('<defs>')
    s.append('<linearGradient id="spaceGrad" x1="0" y1="0" x2="0" y2="1">')
    s.append(f'<stop offset="0" stop-color="#05070f"/><stop offset="0.5" stop-color="{t["background"]}"/><stop offset="1" stop-color="#141b3c"/>')
    s.append('</linearGradient>')
    s.append('<radialGradient id="neb1" cx="0.5" cy="0.5" r="0.5">')
    s.append('<stop offset="0" stop-color="#6366f1" stop-opacity="0.28"/><stop offset="1" stop-color="#6366f1" stop-opacity="0"/>')
    s.append('</radialGradient>')
    s.append('<radialGradient id="neb2" cx="0.5" cy="0.5" r="0.5">')
    s.append('<stop offset="0" stop-color="#22d3ee" stop-opacity="0.22"/><stop offset="1" stop-color="#22d3ee" stop-opacity="0"/>')
    s.append('</radialGradient>')
    s.append('<radialGradient id="neb3" cx="0.5" cy="0.5" r="0.5">')
    s.append('<stop offset="0" stop-color="#a855f7" stop-opacity="0.18"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/>')
    s.append('</radialGradient>')
    s.append('<radialGradient id="vignette" cx="0.5" cy="0.5" r="0.75">')
    s.append('<stop offset="0" stop-color="#000000" stop-opacity="0"/><stop offset="1" stop-color="#000000" stop-opacity="0.45"/>')
    s.append('</radialGradient>')
    s.append('<linearGradient id="cometGrad" x1="0" y1="0" x2="1" y2="0">')
    s.append('<stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>')
    s.append('</linearGradient>')
    # comet streak paths (tails already drawn on negative-x, motion auto-rotates)
    s.append(f'<path id="cometPath1" d="M {W+60} 26 L -70 92" fill="none" stroke="none"/>')
    s.append(f'<path id="cometPath2" d="M {W-10} 50 L 60 150" fill="none" stroke="none"/>')
    s.append('</defs>')

    # space background + nebulas + vignette
    s.append(f'<rect width="{W}" height="{H}" rx="24" fill="url(#spaceGrad)"/>')
    s.append(f'<circle cx="{W*0.18}" cy="60" r="150" fill="url(#neb1)"/>')
    s.append(f'<circle cx="{W*0.62}" cy="40" r="130" fill="url(#neb2)"/>')
    s.append(f'<circle cx="{W*0.9}" cy="260" r="170" fill="url(#neb3)"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="24" fill="url(#vignette)"/>')

    # faint scattered deep-sky stars (deterministic, away from the grid)
    rng=random.Random(1000+ncols)
    for _ in range(70):
        yy_pref=rng.random()<0.55
        xs=rng.randint(30,int(W)-30)
        ys=rng.randint(70,100) if yy_pref else rng.randint(top+8*PITCH+6,H-14)
        rad=rng.choice([0.5,0.7,1.0,1.2])
        s.append(f'<circle cx="{xs}" cy="{ys}" r="{rad}" fill="#9aa9ff" opacity="{rng.uniform(0.12,0.35):.2f}"/>')

    # header
    s.append(f'<text x="36" y="44" fill="{t["text"]}" font-family="sans-serif" font-size="22" font-weight="800">Constelação de Commits</text>')
    s.append(f'<text x="36" y="68" fill="{t["muted"]}" font-family="sans-serif" font-size="13">{total:,} commits no último ano · {active_days} dias ativos</text>')

    # right-side stat chips (mini planets)
    s.append(f'<circle cx="{W-168}" cy="40" r="14" fill="{t["pellet"]}" opacity="0.18"/>')
    s.append(f'<circle cx="{W-168}" cy="40" r="14" fill="none" stroke="{t["power"]}" stroke-opacity="0.5" stroke-dasharray="3 3"/>')
    s.append(f'<text x="{W-168}" y="45" text-anchor="middle" fill="{t["power"]}" font-family="monospace" font-size="13" font-weight="700">{st}</text>')
    s.append(f'<text x="{W-146}" y="45" fill="{t["muted"]}" font-family="sans-serif" font-size="13">sequência</text>')
    s.append(f'<circle cx="{W-92}" cy="40" r="14" fill="{t["power"]}" opacity="0.18"/>')
    s.append(f'<circle cx="{W-92}" cy="40" r="14" fill="none" stroke="{t["pellet"]}" stroke-opacity="0.5" stroke-dasharray="3 3"/>')
    s.append(f'<text x="{W-92}" y="45" text-anchor="middle" fill="{t["pellet"]}" font-family="monospace" font-size="13" font-weight="700">{active_days}</text>')
    s.append(f'<text x="{W-70}" y="45" fill="{t["muted"]}" font-family="sans-serif" font-size="13">dias</text>')

    # month labels (português)
    MONTHS_PT=["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    first_week_start=datetime.now(timezone.utc).date()-timedelta(days=CFG["recent_days"])
    first_week_start=first_week_start-timedelta(days=first_week_start.weekday())
    prev=""
    for i in range(ncols):
        d=first_week_start+timedelta(weeks=i)
        mth=MONTHS_PT[d.month-1]
        if mth!=prev:
            s.append(f'<text x="{92+i*PITCH}" y="96" fill="{t["muted"]}" font-family="sans-serif" font-size="11">{mth}</text>')
            prev=mth

    for j,lab in enumerate([0,2,4]):
        s.append(f'<text x="26" y="{top+5+j*PITCH}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">{DAYS_LABEL[j]}</text>')

    # grid -> night sky. empty days = faint dust, commit days = stars.
    maxv=max(1,max((max(col) for col in weeks), default=1))
    active=[]
    phase_groups={p:[] for p in range(6)}
    for i,col in enumerate(weeks):
        for r,v in enumerate(col):
            cx=90+i*PITCH+CELL//2
            cy=top+r*PITCH+CELL//2
            if v==0:
                s.append(f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="{empty_col}" opacity="0.6"/>')
            else:
                lv=min(3,(v-1)*4//maxv)
                phase_groups[(i*7+r)%6].append((cx,cy,star_cols[lv],lv))
                active.append((cx,cy,i,r,lv))

    # constellation lines: link nearest same-row and same-column neighbours
    if active:
        s.append('<g stroke="#6d7cf0" stroke-opacity="0.3" stroke-width="1">')
        for (cx,cy,i,r,lv) in active:
            row_n=[a for a in active if a[3]==r and 0<abs(a[2]-i)<=2]
            col_n=[a for a in active if a[2]==i and 0<abs(a[3]-r)<=2]
            if row_n:
                best=min(row_n,key=lambda a:abs(a[2]-i))
                s.append(f'<line x1="{cx}" y1="{cy}" x2="{best[0]}" y2="{best[1]}"/>')
            if col_n:
                best=min(col_n,key=lambda a:abs(a[3]-r))
                s.append(f'<line x1="{cx}" y1="{cy}" x2="{best[0]}" y2="{best[1]}"/>')
        s.append('</g>')

    # twinkling stars, grouped in 6 phase waves for organic shimmer
    for ph in range(6):
        if not phase_groups[ph]: continue
        gs=[f'<g opacity="0.85">']
        for (cx,cy,colc,lv) in phase_groups[ph]:
            gr=6.0+1.6*lv; go=0.22+0.08*lv
            gs.append(f'<circle cx="{cx}" cy="{cy}" r="{gr:.1f}" fill="{colc}" opacity="{go:.2f}"/>')
            gs.append(f'<circle cx="{cx}" cy="{cy}" r="{2.0+0.5*lv:.1f}" fill="#ffffff" opacity="0.95"/>')
        dur=2.6+0.7*(ph%3)
        gs.append(f'<animate attributeName="opacity" values="0.5;1;0.5" dur="{dur:.2f}s" begin="{-1.3*ph:.2f}s" repeatCount="indefinite"/>')
        gs.append('</g>')
        s.append("".join(gs))

    # comets streaking across the sky
    s.append(f'<g><path d="M0,0 L -48,0" stroke="url(#cometGrad)" stroke-width="2.2" stroke-linecap="round"/><circle r="2.4" fill="#ffffff"/>')
    s.append(f'<animateMotion dur="9s" begin="1.5s" repeatCount="indefinite" rotate="auto"><mpath href="#cometPath1"/></animateMotion>')
    s.append('<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;0.04;0.12;0.88;0.96;1" dur="9s" begin="1.5s" repeatCount="indefinite"/></g>')
    s.append(f'<g><path d="M0,0 L -34,0" stroke="url(#cometGrad)" stroke-width="1.6" stroke-linecap="round"/><circle r="1.7" fill="#ffffff"/>')
    s.append(f'<animateMotion dur="12s" begin="6.5s" repeatCount="indefinite" rotate="auto"><mpath href="#cometPath2"/></animateMotion>')
    s.append('<animate attributeName="opacity" values="0;0;0.8;0.8;0;0" keyTimes="0;0.04;0.12;0.88;0.96;1" dur="12s" begin="6.5s" repeatCount="indefinite"/></g>')

    # footer + legend
    gy=top+7*PITCH+14
    s.append(f'<text x="90" y="{top+7*PITCH+26}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">✧ cada commit brilha como uma estrela na galáxia</text>')
    lx=W-230
    s.append(f'<text x="{lx}" y="{gy+12}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">Menos</text>')
    for k,c in enumerate(star_cols):
        s.append(f'<circle cx="{lx+60+k*(CELL+4)}" cy="{gy+6}" r="4" fill="{c}"/>')
    s.append(f'<text x="{lx+60+4*(CELL+4)}" y="{gy+12}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">Mais</text>')

    s.append('</svg>')
    return "".join(s)

def stats_block(total, st, active_days):
    a="<!-- GITHUB_ARCADE_STATS:START -->"
    b="<!-- GITHUB_ARCADE_STATS:END -->"
    ver=datetime.now(timezone.utc).strftime("%Y%m%d%H")
    block=f'''{a}
<div align="center">

<img src="./github-arcade/contribution-panel.svg?v={ver}" alt="Constelação de Commits" width="900">

</div>
{b}'''
    return a, b, block

def langs_block_text():
    a="<!-- GITHUB_ARCADE_LANGS:START -->"
    b="<!-- GITHUB_ARCADE_LANGS:END -->"
    ver=datetime.now(timezone.utc).strftime("%Y%m%d%H")
    block=f'''{a}
<div align="center">

<img src="./github-arcade/top-langs.svg?v={ver}" alt="Top Linguagens" width="430">

</div>
{b}'''
    return a, b, block

def replace_block(text, a, b, block):
    before,sep,rest=text.partition(a)
    if not sep: return text
    rest=rest.partition(b)[2]
    return before+block+rest

def main():
    days=get_days()
    total=sum(days.values())
    st=streak(days)
    active_days=len(days)

    (ROOT/"contribution-panel.svg").write_text(
        contribution_svg(days,total,st,active_days),encoding="utf-8")

    langs=get_top_langs()
    (ROOT/"top-langs.svg").write_text(top_langs_svg(langs),encoding="utf-8")

    readme=ROOT.parent/"README.md"
    text=readme.read_text(encoding="utf-8")

    a,b,block=stats_block(total,st,active_days)
    text=replace_block(text,a,b,block)

    la,lb,lblock=langs_block_text()
    if "GITHUB_ARCADE_LANGS:START" in text:
        text=replace_block(text,la,lb,lblock)
    else:
        text=text.replace(b, lblock+"\n\n"+b, 1)

    readme.write_text(text,encoding="utf-8")

if __name__=="__main__":
    main()