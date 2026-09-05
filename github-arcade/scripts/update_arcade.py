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
DAYS_LABEL=["Mon","Wed","Fri"]

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

# ------------------------------------------------------------------
# SNAKE GAME AI: classic snake on a toroidal board (wrap-around edges)
# Straight-line, cell-by-cell moves; greedy pick of nearest "food".
# ------------------------------------------------------------------
def wrap_dist2(a, b, ncols, nrows):
    dc=min((a[0]-b[0])%ncols, (b[0]-a[0])%ncols)
    dr=min((a[1]-b[1])%nrows, (b[1]-a[1])%nrows)
    return dc+dr

def short_delta(d, n):
    if d>0 and d>n//2: return d-n
    if d<0 and -d>n//2: return d+n
    return d

def ai_snake_cells(weeks):
    """Returns a list of canonical (col,row) cells the snake visits,
    moving one cell at a time, wrapping at edges."""
    ncols=len(weeks); nrows=7
    rng=random.Random(int(datetime.now(timezone.utc).strftime("%Y%m%d")) ^ ncols)
    pellets=[(c,r) for c,col in enumerate(weeks) for r,v in enumerate(col) if v>0]
    if not pellets:
        pellets=[(c,r) for c in range(ncols) for r in range(nrows)]
    start=(rng.randrange(0,min(3,ncols)), rng.randrange(0,nrows))
    pos=start
    path=[pos]
    remaining=list(pellets)
    while remaining:
        target=min(remaining, key=lambda p:(wrap_dist2(pos,p,ncols,nrows), p[0], p[1]))
        remaining.remove(target)
        dc=short_delta(target[0]-pos[0], ncols)
        step=1 if dc>=0 else -1
        for _ in range(abs(dc)):
            pos=((pos[0]+step)%ncols, pos[1])
            path.append(pos)
        dr=short_delta(target[1]-pos[1], nrows)
        step=1 if dr>=0 else -1
        for _ in range(abs(dr)):
            pos=(pos[0], (pos[1]+step)%nrows)
            path.append(pos)
    return path

def _corners_next(x, y, ncols, nrows, left, top, step_right):
    """Emit an off-viewBox detour so the snake exits one side and
    re-enters from the opposite side (true wrap teleport)."""
    xr=left+ncols*PITCH+40
    xl=left-40
    yt=top-34
    return [(xr, y), (xr, yt), (xl, yt), (xl, y)]

def ai_snake_path(weeks, left, top):
    """Convert snake cells to SVG polyline points with wrap detours."""
    cells=ai_snake_cells(weeks)
    ncols=len(weeks); nrows=7
    pts=[]
    for i,(c,r) in enumerate(cells):
        pts.append((left+c*PITCH+CELL//2, top+r*PITCH+CELL//2))
    out=[pts[0]]
    for k in range(1, len(pts)):
        px,py=pts[k-1]; cx,cy=pts[k]
        # horizontal seam wrap: ncols-1 -> 0 going right, or 0 -> ncols-1 going left
        prev_c,cur_c=cells[k-1][0], cells[k][0]
        prev_r,cur_r=cells[k-1][1], cells[k][1]
        if prev_c==ncols-1 and cur_c==0:
            out.extend(_corners_next(cx,cy,ncols,nrows,left,top,1))
        elif prev_c==0 and cur_c==ncols-1:
            out.extend(_corners_next(cx,cy,ncols,nrows,left,top,-1))
        elif prev_r==nrows-1 and cur_r==0:
            # vertical wrap: detour below/above through off-viewBox
            xr=left+ncols*PITCH+40; xl=left-40
            out.extend([(cx, top+nrows*PITCH+34), (xr, top+nrows*PITCH+40), (xl, -40), (cx, top-34)])
        elif prev_r==0 and cur_r==nrows-1:
            xr=left+ncols*PITCH+40; xl=left-40
            out.extend([(cx, top-34), (xr, -40), (xl, top+nrows*PITCH+40), (cx, top+nrows*PITCH+34)])
        out.append((cx,cy))
    # drop reactive duplicates
    final=[out[0]]
    for p in out[1:]:
        if p!=final[-1]: final.append(p)
    return final

def contribution_svg(days, total, st, active_days):
    t=CFG["theme"]; weeks=build_weeks(days)
    ncols=len(weeks)
    W=90+ncols*PITCH+40
    H=330
    top=110

    c0="#171c2e"
    c1="#3b4fd8"; c2="#5b6cf0"; c3="#8ea0ff"; c4="#a5f3fc"
    colors=[c1,c2,c3,c4]

    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Gustavo Santos - AI Snake eats commits">']
    s.append('<defs>')
    s.append('<linearGradient id="snakeGrad" x1="0" y1="0" x2="1" y2="1">')
    s.append(f'<stop offset="0" stop-color="{t["ghost1"]}"/><stop offset="1" stop-color="{t["ghost2"]}"/></linearGradient>')
    s.append(f'<linearGradient id="headGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd21f"/><stop offset="1" stop-color="#ff9d4d"/></linearGradient>')
    s.append('</defs>')

    s.append(f'<rect width="{W}" height="{H}" rx="24" fill="{t["background"]}"/>')

    # header
    s.append(f'<text x="36" y="44" fill="{t["text"]}" font-family="sans-serif" font-size="22" font-weight="800">Contribution Graph</text>')
    s.append(f'<text x="36" y="68" fill="{t["muted"]}" font-family="sans-serif" font-size="13">{total:,} commits in the last year</text>')

    # right stats
    s.append(f'<circle cx="{W-168}" cy="40" r="14" fill="{t["pellet"]}" opacity="0.2"/>')
    s.append(f'<text x="{W-168}" y="45" text-anchor="middle" fill="{t["power"]}" font-family="monospace" font-size="13" font-weight="700">{st}</text>')
    s.append(f'<text x="{W-146}" y="45" fill="{t["muted"]}" font-family="sans-serif" font-size="13">streak</text>')
    s.append(f'<circle cx="{W-92}" cy="40" r="14" fill="{t["power"]}" opacity="0.2"/>')
    s.append(f'<text x="{W-92}" y="45" text-anchor="middle" fill="{t["pellet"]}" font-family="monospace" font-size="13" font-weight="700">{active_days}</text>')
    s.append(f'<text x="{W-70}" y="45" fill="{t["muted"]}" font-family="sans-serif" font-size="13">days</text>')
    s.append(f'<text x="{W-262}" y="45" fill="{t["muted"]}" font-family="sans-serif" font-size="11">🤖 AI snake · wrap mode</text>')

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

    for j,lab in enumerate([0,2,4]):
        s.append(f'<text x="26" y="{top+5+j*PITCH}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">{DAYS_LABEL[j]}</text>')

    # grid cells: "food pellets" are the days with commits
    maxv=max(1,max((max(col) for col in weeks), default=1))
    pellets=[]
    for i,col in enumerate(weeks):
        for r,v in enumerate(col):
            cx=90+i*PITCH+CELL//2
            cy=top+r*PITCH+CELL//2
            if v==0:
                s.append(f'<rect x="{cx-CELL//2}" y="{cy-CELL//2}" width="{CELL}" height="{CELL}" rx="3" fill="{c0}"/>')
            else:
                idx=min(3,(v-1)*4//maxv)
                s.append(f'<rect x="{cx-CELL//2}" y="{cy-CELL//2}" width="{CELL}" height="{CELL}" rx="3" fill="{colors[idx]}"/>')
                pellets.append((cx,cy))
                s.append(f'<circle cx="{cx}" cy="{cy}" r="2" fill="#ffffff" opacity="{0.35+0.15*idx}"/>')

    # footer
    gy=top+7*PITCH+14
    s.append(f'<text x="90" y="{top+7*PITCH+26}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">🐍 the AI snake eats one commit at a time · straight lines · wraps edges</text>')
    lx=W-230
    s.append(f'<text x="{lx}" y="{gy+12}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">Less</text>')
    for k,c in enumerate([c0]+colors):
        s.append(f'<rect x="{lx+42+k*(CELL+3)}" y="{gy+2}" width="{CELL}" height="{CELL}" rx="3" fill="{c}"/>')
    s.append(f'<text x="{lx+42+5*(CELL+3)}" y="{gy+12}" fill="{t["muted"]}" font-family="sans-serif" font-size="11">More</text>')

    # ---- AI snake path (cell-by-cell, straight lines, wrap) ----
    path=ai_snake_path(weeks, 90, top)
    px=[p[0] for p in path]
    py=[p[1] for p in path]
    dstr="M "+" L ".join(f"{px[i]} {py[i]}" for i in range(len(px)))
    s.append(f'<path id="snakepath" d="{dstr}" fill="none" stroke="none"/>')

    steps=len(path)
    per=0.055                     # seconds per cell
    dur=max(8, steps*per)
    head_begin=-dur*0.5
    body=4
    for k in range(1,body+1):
        begin=head_begin + k*per*9
        r=12.5-2.2*(k-1)
        op=0.9-0.16*(k-1)
        s.append(f'<circle r="{r:.1f}" fill="url(#snakeGrad)" opacity="{op:.2f}"><animateMotion dur="{dur:.2f}s" repeatCount="indefinite" begin="{begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')
    # head (Pac-Man-ish yellow, chewing)
    s.append(f'<circle r="15" fill="url(#headGrad)"><animateMotion dur="{dur:.2f}s" repeatCount="indefinite" begin="{head_begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')
    s.append(f'<circle r="6" fill="#ffffff"><animateMotion dur="{dur:.2f}s" repeatCount="indefinite" begin="{head_begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')
    s.append(f'<circle r="2.6" fill="#111111"><animateMotion dur="{dur:.2f}s" repeatCount="indefinite" begin="{head_begin:.3f}s"><mpath href="#snakepath"/></animateMotion></circle>')

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