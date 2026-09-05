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

def fmt(n): return f"{n:,}".replace(",", ".")

def bento_svg(days, xp, level, total, st, prog, daily_max):
    t=CFG["theme"]
    # contribution activity bars (last 52 days, split into 2 rows)
    sorted_days=sorted(days.items())
    weeks=sorted_days[-52:]
    bars1=""; bars2=""
    for i,(d,n) in enumerate(weeks[:26]):
        h=max(4, int(40*(n/max(1,daily_max))))
        x=26+i*14
        bars1+=f'<rect x="{x}" y="{152-h}" width="9" height="{h}" rx="2.5" fill="{t["power"]}"><animate attributeName="opacity" values="0.5;1;0.5" dur="2.5s" repeatCount="indefinite"/></rect>'
    for i,(d,n) in enumerate(weeks[26:]):
        h=max(4, int(40*(n/max(1,daily_max))))
        x=26+i*14
        bars2+=f'<rect x="{x}" y="{158-h}" width="9" height="{h}" rx="2.5" fill="{t["pellet"]}"><animate attributeName="opacity" values="0.5;1;0.5" dur="2.5s" repeatCount="indefinite"/></rect>'

    bar_w=int(prog*200)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="440" viewBox="0 0 900 440">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0b1020"/>
      <stop offset="1" stop-color="#151a33"/>
    </linearGradient>
    <linearGradient id="barGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{t["wall"]}"/>
      <stop offset="1" stop-color="{t["power"]}"/>
    </linearGradient>
    <filter id="g1" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <rect width="900" height="440" rx="26" fill="url(#bg)"/>

  <!-- card grid -->
  <rect x="30" y="24" width="400" height="150" rx="20" fill="#ffffff" fill-opacity="0.05" stroke="#ffffff" stroke-opacity="0.12"/>
  <text x="52" y="60" fill="#64748b" font-family="monospace" font-size="12" font-weight="600" letter-spacing="1">TOTAL XP</text>
  <text x="52" y="112" fill="#ffffff" font-family="sans-serif" font-size="40" font-weight="800">{xp:,}</text>
  <text x="52" y="138" fill="#67e8f9" font-family="sans-serif" font-size="15" font-weight="600">{prog*100:.0f}% to next level</text>
  <rect x="52" y="152" width="200" height="8" rx="4" fill="#1e293b"/>
  <rect x="52" y="152" width="{bar_w}" height="8" rx="4" fill="url(#barGrad)">
    <animate attributeName="opacity" values="1;0.7;1" dur="2s" repeatCount="indefinite"/>
  </rect>

  <rect x="470" y="24" width="180" height="150" rx="20" fill="#ffffff" fill-opacity="0.05" stroke="#818cf8" stroke-opacity="0.35"/>
  <text x="492" y="60" fill="#64748b" font-family="monospace" font-size="12" font-weight="600" letter-spacing="1">LEVEL</text>
  <text x="492" y="118" fill="#a5b4fc" font-family="monospace" font-size="52" font-weight="800">{level}</text>
  <text x="492" y="148" fill="#67e8f9" font-family="monospace" font-size="13">▲ LVL {level+1}</text>

  <rect x="690" y="24" width="180" height="150" rx="20" fill="#ffffff" fill-opacity="0.05" stroke="#22d3ee" stroke-opacity="0.35">
    <animate attributeName="stroke-opacity" values="0.35;0.8;0.35" dur="3s" repeatCount="indefinite"/>
  </rect>
  <text x="712" y="60" fill="#64748b" font-family="monospace" font-size="12" font-weight="600" letter-spacing="1">STREAK</text>
  <text x="712" y="118" fill="#67e8f9" font-family="monospace" font-size="52" font-weight="800">{st}</text>
  <text x="712" y="148" fill="#ffffff" font-family="sans-serif" font-size="13">days on fire 🔥</text>

  <rect x="30" y="194" width="840" height="222" rx="20" fill="#ffffff" fill-opacity="0.03" stroke="#ffffff" stroke-opacity="0.1"/>
  <text x="52" y="232" fill="#64748b" font-family="monospace" font-size="12" font-weight="600" letter-spacing="1">CONTRIBUTION ACTIVITY</text>
  <text x="720" y="232" fill="#94a3b8" font-family="sans-serif" font-size="13" font-weight="600">{total:,} commits</text>
  {bars1}
  <line x1="26" y1="196" x2="390" y2="196" stroke="#ffffff" stroke-opacity="0.06"/>
  {bars2}
  <line x1="26" y1="202" x2="390" y2="202" stroke="#ffffff" stroke-opacity="0.06"/>
  <text x="52" y="404" fill="#475569" font-family="monospace" font-size="11">LAST 52 WEEKS →</text>
  <text x="52" y="384" fill="#475569" font-family="monospace" font-size="11">✎ EVERY COMMIT SHIPS → KEEP SHIPPING</text>
</svg>'''

def stats_block(score, level, total, st, days, xp, xp_next, prog, badges):
    a="<!-- GITHUB_ARCADE_STATS:START -->"
    b="<!-- GITHUB_ARCADE_STATS:END -->"
    block=f'''{a}
<div align="center">

<img src="./github-arcade/bento-stats.svg" alt="Stats" width="900">

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
    daily_max=max(1,max(days.values()) or 1)

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

    (ROOT/"bento-stats.svg").write_text(
        bento_svg(days,xp,level,total,st,prog,daily_max),encoding="utf-8")

    readme=ROOT.parent/"README.md"
    text=readme.read_text(encoding="utf-8")
    a,b,block=stats_block(xp,level,total,st,days,xp,xp_next,prog,badges)
    before,rest=text.split(a,1)
    _,after=rest.split(b,1)
    readme.write_text(before+block+after,encoding="utf-8")

if __name__=="__main__":
    main()
