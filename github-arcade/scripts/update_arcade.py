import json, os, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config.json").read_text())
TOKEN = os.getenv("GITHUB_TOKEN", "")
USER = os.getenv("GITHUB_REPOSITORY_OWNER", CFG["username"])

def api(url):
    headers={"Accept":"application/vnd.github+json","User-Agent":"gustavo-github-arcade"}
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

def arcade_svg(days, score, level, total, st, xp, xp_next, prog, badges):
    t=CFG["theme"]; dots=""
    for i,(_,n) in enumerate(sorted(days.items())[-52:]):
        x=70+i*15; y=215+(i%7)*14
        fill=t["power"] if n>=8 else t["pellet"]
        dots += f'<circle cx="{x}" cy="{y}" r="{2+min(n,8)*.35}" fill="{fill}"/>'
    bar=max(2,int(prog*810))
    badge_row=" ".join(
        f'<rect x="{40+j*107}" y="392" width="97" height="26" rx="13" fill="#141b34" stroke="{t["wall"]}" stroke-width="1.5"/>'
        f'<text x="{88+j*107}" y="408" fill="{t["pellet"]}" font-family="monospace" font-size="12" text-anchor="middle">{b}</text>'
        for j,b in enumerate(badges[:8])
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="430">
<defs>
<linearGradient id="prog" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{t["wall"]}"/>
<stop offset="1" stop-color="{t["power"]}"/>
</linearGradient>
</defs>
<rect width="900" height="430" rx="24" fill="{t["background"]}"/>
<text x="48" y="52" fill="{t["text"]}" font-family="monospace" font-size="26" font-weight="700">GUSTAVO'S GITHUB ARCADE</text>
<text x="640" y="52" fill="{t["pellet"]}" font-family="monospace" font-size="17" font-weight="700">SCORE {score:,}</text>
<text x="640" y="78" fill="{t["power"]}" font-family="monospace" font-size="17" font-weight="700">LEVEL {level} ★</text>
<text x="640" y="104" fill="{t["text"]}" font-family="monospace" font-size="12">COMMITS {total:,} • STREAK {st} 🔥</text>
<text x="48" y="118" fill="{t["muted"]}" font-family="monospace" font-size="12">■ LEVEL PROGRESS • {prog*100:.1f}%</text>
<rect x="40" y="128" width="820" height="17" rx="8" fill="{t["panel"]}" stroke="{t["wall"]}" stroke-width="2"/>
<rect x="44" y="132" width="{bar}" height="9" rx="4" fill="url(#prog)"/>
<rect x="40" y="170" width="820" height="150" rx="12" fill="{t["panel"]}" stroke="{t["wall"]}" stroke-width="5"/>
{dots}
<circle cx="110" cy="240" r="13" fill="{t["pacman"]}"/>
<path d="M110 240 L123 232 A15 15 0 0 1 123 248 Z" fill="{t["background"]}"/>
<text x="48" y="350" fill="{t["text"]}" font-family="monospace" font-size="16" font-weight="700">🏆 CONQUISTAS</text>
{badge_row}
</svg>'''

def stats_block(score, level, total, st, days, xp, xp_next, prog, badges):
    a="<!-- GITHUB_ARCADE_STATS:START -->"
    b="<!-- GITHUB_ARCADE_STATS:END -->"
    block=f'''{a}
<div align="center">

| ⭐ XP | 🎮 Lv | 💻 Commits | 🔥 Streak |
|:---:|:---:|:---:|:---:|
| **{xp:,}** | **{level}** | **{total:,}** | **{st}** |

</div>
{b}'''
    return a, b, block

def main():
    days=get_days()
    total=sum(days.values())
    xp=total*CFG["score_per_commit"]+sum(max(0,n-1)*5 for n in days.values())
    level=max(1,xp//CFG["level_every"]+1)
    xp_threshold=(level-1)*CFG["level_every"]
    xp_in_level=xp-xp_threshold
    xp_next=CFG["level_every"]
    prog=min(1.0,xp_in_level/xp_next)
    st=streak(days)

    badges=[]
    if total>=1: badges.append("🎮 Rookie")
    if total>=50: badges.append("⚡ Coder")
    if total>=150: badges.append("🔥 Grinder")
    if total>=400: badges.append("🚀 Build")
    if total>=1000: badges.append("🏆 Legend")
    if st>=7: badges.append("📅 Week")
    if st>=30: badges.append("📆 Month")
    if len(days)>=150: badges.append("💪 Active")
    if not badges: badges=["🆕 Novo"]

    (ROOT/"arcade.svg").write_text(
        arcade_svg(days,xp//10,level,total,st,xp,xp_next,prog,badges),encoding="utf-8")

    readme=ROOT.parent/"README.md"
    text=readme.read_text(encoding="utf-8")
    a,b,block=stats_block(xp//10,level,total,st,days,xp,xp_next,prog,badges)
    before,rest=text.split(a,1)
    _,after=rest.split(b,1)
    readme.write_text(before+block+after,encoding="utf-8")

if __name__=="__main__":
    main()
