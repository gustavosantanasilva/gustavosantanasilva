from pathlib import Path
import json, math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/"config.json").read_text())
T=C["theme"]
W,H=900,430

def F(n,b=False):
    p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if b else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p,n)

frames=[]
for k in range(C["frames"]):
    im=Image.new("RGB",(W,H),T["background"])
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((25,20,875,410),22,fill=T["panel"],outline=T["wall"],width=3)
    d.text((48,43),"GUSTAVO'S GITHUB ARCADE",fill=T["text"],font=F(25,True))
    d.text((48,76),"YOUR COMMITS • YOUR MAP • YOUR SCORE",fill=T["muted"],font=F(13))
    d.text((650,43),"SCORE LIVE",fill=T["pellet"],font=F(16,True))
    d.text((650,70),"LEVEL UP",fill=T["power"],font=F(16,True))
    d.rounded_rectangle((45,150,855,320),12,outline=T["wall"],width=5)

    for i in range(42):
        x=70+i*18
        y=185+((i*31)%105)
        d.ellipse((x-3,y-3,x+3,y+3),fill=T["pellet"])

    progress=k/max(1,C["frames"]-1)
    px=70+progress*740
    py=235+math.sin(k/3)*25
    mouth=.35+.25*abs(math.sin(k/2))
    d.pieslice((px-16,py-16,px+16,py+16),
               start=int(mouth*45),end=int(360-mouth*45),fill=T["pacman"])
    d.ellipse((px+2,py-9,px+6,py-5),fill="#111111")

    for i,col in enumerate([T["ghost1"],T["ghost2"],T["ghost3"],T["ghost4"]]):
        gx=180+((k*9+i*145)%620)
        gy=220+math.sin(k/3+i)*22
        d.rounded_rectangle((gx,gy,gx+30,gy+28),12,fill=col)
        d.rectangle((gx,gy+14,gx+30,gy+25),fill=col)
        d.ellipse((gx+7,gy+8,gx+12,gy+13),fill="white")
        d.ellipse((gx+19,gy+8,gx+24,gy+13),fill="white")

    d.text((48,355),"COMMITS → SCORE → LEVEL → STREAK",fill=T["muted"],font=F(13))
    d.text((48,385),"KEEP CODING • KEEP BUILDING • KEEP LEVELING UP",fill=T["text"],font=F(16,True))
    frames.append(im)

frames[0].save(ROOT/"arcade.gif",save_all=True,append_images=frames[1:],duration=100,loop=0)
