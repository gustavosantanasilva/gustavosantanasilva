import json, os, urllib.request, urllib.parse
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
DAYS_LABEL=["Mon","Wed","Fri"]

def build_weeks(days):
    # anchor: sunday that starts the earliest needed week
    end=datetime.now(timezone.utc).date()
    start=end-timedelta(days=CFG["recent_days"])
    # row for 'Mon' (0=Mon ... 6=Sun)
    weeks=[]
    # first monday <= start
    first=start-timedelta(days=start.weekday())
    cur=first
    while cur<=end:
        col=[]
        for d in range(7):
            day=cur+timedelta(days=d)
            col.append(days.get(day.isoformat(),0))
        weeks.append(col)
        cur+=timedelta(days=7)
    return weeks

def contribution_svg(days, total, st, active_days):
    t=CFG["theme"]; weeks=build_weeks(days)
    ncols=len(weeks)
    W=90+ncols*PITCH+20
    H=330

    # intensity colors
    c0="#171c2e"
    c1="#3b4fd8"; c2="#5b6cf0"; c3="#8ea0ff"; c4="#a5f3fc"
    colors=[c1,c2,c3,c4]

    # header
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Gustavo Santos contribution graph">']
    s.append('<defs>')
    s.append('<linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">')
    s.append(f'<stop offset="0" stop-color="{t["wall"]}"/><stop offset="1" stop-color="{t["power"]}"/></linearGradient>')
    s.append('<linearGradient id="snakeGrad" x1="0" y1="0" x2="1" y2="1">')
    s.append(f'<stop offset="0" stop-color="{t["ghost1"]}"/><stop offset="1" stop-color="{t["ghost2"]}"/></linearGradient>')
    s.append('</defs>')

    s.append(f'<rect width="{W}" height="{H}" rx="24" fill="{t["background"]}"/>')

    # title
    s.append(f'<text x="36" y="44" fill="{t["text"]}" font-family="sans-serif" font-size="22" font-weight="800">Contribution Graph</text>')
    s.append(f'<text x="36" y="68" fill="{t["muted"]}" font-family="sans-serif" font-size="13">{total:,} commits in the last year</text>')

    # right stats
    s.append(f'<circle cx="{W-168}" cy="40" r="14" fill="{t["pellet"]}" opacity="0.2"/>')
    s.append(f'<text x="{W-168}" y="45" text-anchor="middle" fill="{t["power"]}" font-family="monospace" font-size="13" font-weight="700">{st}</text>')
    s.append(f'<text x="{W-146}" y="45" fill="{t["muted"]}" font-family="sans-serif" font-size="13">streak</text>')
    s.append(f'<circle cx="{W-92}" cy="40" r="14" fill="{t["power"]}" opacity="0.2"/>')
    s.append(f'<text x="{W-92}" y="45" text-anchor="middle" fill="{t["pellet"]}" font-family="monospace" font-size="13" font-weight="700">{active_days}</text>')
    s.append(f'<text x="{W-70}" y="45" fill="{t["muted"]}" font-family="sans-serif" font-size="13">days</text>')

    # month labels
    first_week_start=datetime.now(timezone.utc).date()-timedelta(days=CFG["recent_days"])
    first_week_start=first_week_start-timedelta(days=first_week_start.weekday())
    prev=""
    for i in range(ncols):
        d=first_week_start+timedelta(weeks=i)
        mth=d.strftime("%b")
        if mth!=prev:
            s.append(f'<text x="{92+i*PITCH}" y="96" fill="{t["muted"]}" font-family="sans-serif" font-size="11">{mth}</text>')
            prev=mth

    # vertical day labels
    for j,lab in enumerate([0,2,4]):
        s.append(f'<text x="26" y="{126+j*(PITCH)}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">{DAYS_LABEL[j]}</text>')

    # grid
    top=110
    maxv=max(1,max((max(col) for col in weeks), default=1))
    for i,col in enumerate(weeks):
        for r,v in enumerate(col):
            x=90+i*PITCH
            y=top+r*PITCH
            if v==0: fill=c0
            else:
                idx=min(3,(v-1)*4//maxv)
                fill=colors[idx]
            s.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{fill}"/>')

    # footer
    gy=top+7*PITCH+14
    s.append(f'<text x="90" y="{top+7*PITCH+26}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">shipped with 💜 in Brazil</text>')
    lx=W-230
    s.append(f'<text x="{lx}" y="{gy+12}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">Less</text>')
    for k,c in enumerate([c0]+colors):
        s.append(f'<rect x="{lx+42+k*(CELL+3)}" y="{gy+2}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>')
    s.append(f'<text x="{lx+42+5*(CELL+3)}" y="{gy+12}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">More</text>')

    # ---- build snake zig-zag path across ALL cells ----
    cells=[]
    for i in range(ncols):
        col=[(90+i*PITCH+CELL//2, top+r*PITCH+CELL//2) for r in range(7)]
        cells.append(col)
    path_pts=[]
    for i in range(0,ncols,2):
        path_pts+=cells[i]
        if i+1<ncols:
            path_pts+=list(reversed(cells[i+1]))
    dstr="M "+" L ".join(f"{p[0]} {p[1]}" for p in path_pts)
    s.append(f'<path id="snakepath" d="{dstr}" fill="none" stroke="none"/>')

    # snake body: several segments following path with offsets behind the head
    dur=18+ ncols*0.35
    head_begin=-(dur*0.5)
    body=4
    for k in range(1,body+1):          # k=1 closest to head, k=body farthest (tail)
        begin=head_begin + k*(dur*0.035)
        r=14-2.4*(k-1)                 # biggest near head, thins toward tail
        op=0.95-0.18*(k-1)
        s.append(f'<circle r="{r:.1f}" fill="url(#snakeGrad)" opacity="{op:.2f}"><animateMotion dur="{dur}s" repeatCount="indefinite" begin="{begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')
    # head
    s.append(f'<circle r="16" fill="url(#snakeGrad)"><animateMotion dur="{dur}s" repeatCount="indefinite" begin="{head_begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')
    s.append(f'<circle r="6.5" fill="#ffffff"><animateMotion dur="{dur}s" repeatCount="indefinite" begin="{head_begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')
    s.append(f'<circle r="2.8" fill="#111111"><animateMotion dur="{dur}s" repeatCount="indefinite" begin="{head_begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')

    s.append('</svg>')
    return "".join(s)

def stats_block(total, st, active_days):
    a="<!-- GITHUB_ARCADE_STATS:START -->"
    b="<!-- GITHUB_ARCADE_STATS:END -->"
    block=f'''{a}
<div align="center">

<img src="./github-arcade/contribution-panel.svg" alt="Contribution Graph" width="900">

</div>
{b}'''
    return a, b, block

def main():
    days=get_days()
    total=sum(days.values())
    st=streak(days)
    active_days=len(days)

    (ROOT/"contribution-panel.svg").write_text(
        contribution_svg(days,total,st,active_days),encoding="utf-8")

    readme=ROOT.parent/"README.md"
    text=readme.read_text(encoding="utf-8")
    a,b,block=stats_block(total,st,active_days)
    before,rest=text.split(a,1)
    _,after=rest.split(b,1)
    readme.write_text(before+block+after,encoding="utf-8")

if __name__=="__main__":
    main()