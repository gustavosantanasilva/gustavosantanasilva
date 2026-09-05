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
    "HTML":"#e34c26","CSS":"#663399","MySQL":"#4479a1","Docker":"#2496ed",
    "Shell":"#4eaa25","Java":"#e76f00","C":"#555555","C++":"#00599c",
    "C#":"#178600","Go":"#00adda","Rust":"#dea584","Dart":"#00b4ab",
    "Kotlin":"#a97bff","Ruby":"#cc342d","Swift":"#f05138","Lua":"#000080",
}
FALLBACK_LANG="#7c8cf8"

# real logos (Simple Icons 24x24 paths), monochrome per brand color
LANG_ICONS={
"Python":"M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33.08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z",
"PHP":"M7.01 10.207h-.944l-.515 2.648h.838c.556 0 .97-.105 1.242-.314.272-.21.455-.559.55-1.049.092-.47.05-.802-.124-.995-.175-.193-.523-.29-1.047-.29zM12 5.688C5.373 5.688 0 8.514 0 12s5.373 6.313 12 6.313S24 15.486 24 12c0-3.486-5.373-6.312-12-6.312zm-3.26 7.451c-.261.25-.575.438-.917.551-.336.108-.765.164-1.285.164H5.357l-.327 1.681H3.652l1.23-6.326h2.65c.797 0 1.378.209 1.744.628.366.418.476 1.002.33 1.752a2.836 2.836 0 0 1-.305.847c-.143.255-.33.49-.561.703zm4.024.715l.543-2.799c.063-.318.039-.536-.068-.651-.107-.116-.336-.174-.687-.174H11.46l-.704 3.625H9.388l1.23-6.327h1.367l-.327 1.682h1.218c.767 0 1.295.134 1.586.401s.378.7.263 1.299l-.572 2.944h-1.389zm7.597-2.265a2.782 2.782 0 0 1-.305.847c-.143.255-.33.49-.561.703a2.44 2.44 0 0 1-.917.551c-.336.108-.765.164-1.286.164h-1.18l-.327 1.682h-1.378l1.23-6.326h2.649c.797 0 1.378.209 1.744.628.366.417.477 1.001.331 1.751zM17.766 10.207h-.943l-.516 2.648h.838c.557 0 .971-.105 1.242-.314.272-.21.455-.559.551-1.049.092-.47.049-.802-.125-.995s-.524-.29-1.047-.29z",
"JavaScript":"M0 0h24v24H0V0zm22.034 18.276c-.175-1.095-.888-2.015-3.003-2.873-.736-.345-1.554-.585-1.797-1.14-.091-.33-.105-.51-.046-.705.15-.646.915-.84 1.515-.66.39.12.75.42.976.9 1.034-.676 1.034-.676 1.755-1.125-.27-.42-.404-.601-.586-.78-.63-.705-1.469-1.065-2.834-1.034l-.705.089c-.676.165-1.32.525-1.71 1.005-1.14 1.291-.811 3.541.569 4.471 1.365 1.02 3.361 1.244 3.616 2.205.24 1.17-.87 1.545-1.966 1.41-.811-.18-1.26-.586-1.755-1.336l-1.83 1.051c.21.48.45.689.81 1.109 1.74 1.756 6.09 1.666 6.871-1.004.029-.09.24-.705.074-1.65l.046.067zm-8.983-7.245h-2.248c0 1.938-.009 3.864-.009 5.805 0 1.232.063 2.363-.138 2.711-.33.689-1.18.601-1.566.48-.396-.196-.597-.466-.83-.855-.063-.105-.11-.196-.127-.196l-1.825 1.125c.305.63.75 1.172 1.324 1.517.855.51 2.004.675 3.207.405.783-.226 1.458-.691 1.811-1.411.51-.93.402-2.07.397-3.346.012-2.054 0-4.109 0-6.179l.004-.056z",
"HTML":"M1.5 0h21l-1.91 21.563L11.977 24l-8.564-2.438L1.5 0zm7.031 9.75l-.232-2.718 10.059.003.23-2.622L5.412 4.41l.698 8.01h9.126l-.326 3.426-2.91.804-2.955-.81-.188-2.11H6.248l.33 4.171L12 19.351l5.379-1.443.744-8.157H8.531z",
"CSS":"M0 0v20.16A3.84 3.84 0 0 0 3.84 24h16.32A3.84 3.84 0 0 0 24 20.16V3.84A3.84 3.84 0 0 0 20.16 0Zm14.256 13.08c1.56 0 2.28 1.08 2.304 2.64h-1.608c.024-.288-.048-.6-.144-.84-.096-.192-.288-.264-.552-.264-.456 0-.696.264-.696.84-.024.576.288.888.768 1.08.72.288 1.608.744 1.92 1.296q.432.648.432 1.656c0 1.608-.912 2.592-2.496 2.592-1.656 0-2.4-1.032-2.424-2.688h1.68c0 .792.264 1.176.792 1.176.264 0 .456-.072.552-.24.192-.312.24-1.176-.048-1.512-.312-.408-.912-.6-1.32-.816q-.828-.396-1.224-.936c-.24-.36-.36-.888-.36-1.536 0-1.44.936-2.472 2.424-2.448m5.4 0c1.584 0 2.304 1.08 2.328 2.64h-1.608c0-.288-.048-.6-.168-.84-.096-.192-.264-.264-.528-.264-.48 0-.72.264-.72.84s.288.888.792 1.08c.696.288 1.608.744 1.92 1.296.264.432.408.984.408 1.656.024 1.608-.888 2.592-2.472 2.592-1.68 0-2.424-1.056-2.448-2.688h1.68c0 .744.264 1.176.792 1.176.264 0 .456-.072.552-.24.216-.312.264-1.176-.048-1.512-.288-.408-.888-.6-1.32-.816-.552-.264-.96-.576-1.2-.936s-.36-.888-.36-1.536c-.024-1.44.912-2.472 2.4-2.448m-11.031.018c.711-.006 1.419.198 1.839.63.432.432.672 1.128.648 1.992H9.336c.024-.456-.096-.792-.432-.96-.312-.144-.768-.048-.888.24-.12.264-.192.576-.168.864v3.504c0 .744.264 1.128.768 1.128a.65.65 0 0 0 .552-.264c.168-.24.192-.552.168-.84h1.776c.096 1.632-.984 2.712-2.568 2.688-1.536 0-2.496-.864-2.472-2.472v-4.032c0-.816.24-1.44.696-1.848.432-.408 1.146-.624 1.857-.63",
"MySQL":"M16.405 5.501c-.115 0-.193.014-.274.033v.013h.014c.054.104.146.18.214.273.054.107.1.214.154.32l.014-.015c.094-.066.14-.172.14-.333-.04-.047-.046-.094-.08-.14-.04-.067-.126-.1-.18-.153zM5.77 18.695h-.927a50.854 50.854 0 00-.27-4.41h-.008l-1.41 4.41H2.45l-1.4-4.41h-.01a72.892 72.892 0 00-.195 4.41H0c.055-1.966.192-3.81.41-5.53h1.15l1.335 4.064h.008l1.347-4.064h1.095c.242 2.015.384 3.86.428 5.53zm4.017-4.08c-.378 2.045-.876 3.533-1.492 4.46-.482.716-1.01 1.073-1.583 1.073-.153 0-.34-.046-.566-.138v-.494c.11.017.24.026.386.026.268 0 .483-.075.647-.222.197-.18.295-.382.295-.605 0-.155-.077-.47-.23-.944L6.23 14.615h.91l.727 2.36c.164.536.233.91.205 1.123.4-1.064.678-2.227.835-3.483zm12.325 4.08h-2.63v-5.53h.885v4.85h1.745zm-3.32.135l-1.016-.5c.09-.076.177-.158.255-.25.433-.506.648-1.258.648-2.253 0-1.83-.718-2.746-2.155-2.746-.704 0-1.254.232-1.65.697-.43.508-.646 1.256-.646 2.245 0 .972.19 1.686.574 2.14.35.41.877.615 1.583.615.264 0 .506-.033.725-.098l1.325.772.36-.622zM15.5 17.588c-.225-.36-.337-.94-.337-1.736 0-1.393.424-2.09 1.27-2.09.443 0 .77.167.977.5.224.362.336.936.336 1.723 0 1.404-.424 2.108-1.27 2.108-.445 0-.77-.167-.978-.5zm-1.658-.425c0 .47-.172.856-.516 1.156-.344.3-.803.45-1.384.45-.543 0-1.064-.172-1.573-.515l.237-.476c.438.22.833.328 1.19.328.332 0 .593-.073.783-.22a.754.754 0 00.3-.615c0-.33-.23-.61-.648-.845-.388-.213-1.163-.657-1.163-.657-.422-.307-.632-.636-.632-1.177 0-.45.157-.81.47-1.085.315-.278.72-.415 1.22-.415.512 0 .98.136 1.4.41l-.213.476a2.726 2.726 0 00-1.064-.23c-.283 0-.502.068-.654.206a.685.685 0 00-.248.524c0 .328.234.61.666.85.393.215 1.187.67 1.187.67.433.305.648.63.648 1.168zm9.382-5.852c-.535-.014-.95.04-1.297.188-.1.04-.26.04-.274.167.055.053.063.14.11.214.08.134.218.313.346.407.14.11.28.216.427.31.26.16.555.255.81.416.145.094.293.213.44.313.073.05.12.14.214.172v-.02c-.046-.06-.06-.147-.105-.214-.067-.067-.134-.127-.2-.193a3.223 3.223 0 00-.695-.675c-.214-.146-.682-.35-.77-.595l-.013-.014c.146-.013.32-.066.46-.106.227-.06.435-.047.67-.106.106-.027.213-.06.32-.094v-.06c-.12-.12-.21-.283-.334-.395a8.867 8.867 0 00-1.104-.823c-.21-.134-.476-.22-.697-.334-.08-.04-.214-.06-.26-.127-.12-.146-.19-.34-.275-.514a17.69 17.69 0 01-.547-1.163c-.12-.262-.193-.523-.34-.763-.69-1.137-1.437-1.826-2.586-2.5-.247-.14-.543-.2-.856-.274-.167-.008-.334-.02-.5-.027-.11-.047-.216-.174-.31-.235-.38-.24-1.364-.76-1.644-.072-.18.434.267.862.422 1.082.115.153.26.328.34.5.047.116.06.235.107.356.106.294.207.622.347.897.073.14.153.287.247.413.054.073.146.107.167.227-.094.136-.1.334-.154.5-.24.757-.146 1.693.194 2.25.107.166.362.534.703.393.3-.12.234-.5.32-.835.02-.08.007-.133.048-.187v.015c.094.188.188.367.274.555.206.328.566.668.867.895.16.12.287.328.487.402v-.02h-.015c-.043-.058-.1-.086-.154-.133a3.445 3.445 0 01-.35-.4 8.76 8.76 0 01-.747-1.218c-.11-.21-.202-.436-.29-.643-.04-.08-.04-.2-.107-.24-.1.146-.247.273-.32.453-.127.288-.14.642-.188 1.01-.027.007-.014 0-.027.014-.214-.052-.287-.274-.367-.46-.2-.475-.233-1.238-.06-1.785.047-.14.247-.582.167-.716-.042-.127-.174-.2-.247-.303a2.478 2.478 0 01-.24-.427c-.16-.374-.24-.788-.414-1.162-.08-.173-.22-.354-.334-.513-.127-.18-.267-.307-.368-.52-.033-.073-.08-.194-.027-.274.014-.054.042-.075.094-.09.088-.072.335.022.422.062.247.1.455.194.662.334.094.066.195.193.315.226h.14c.214.047.455.014.655.073.355.114.675.28.962.46a5.953 5.953 0 012.085 2.286c.08.154.115.295.188.455.14.33.313.663.455.982.14.315.275.636.476.897.1.14.502.213.682.286.133.06.34.115.46.188.23.14.454.3.67.454.11.076.443.243.463.378z",
"TypeScript":"M1.125 0C.502 0 0 .502 0 1.125v21.75C0 23.498.502 24 1.125 24h21.75c.623 0 1.125-.502 1.125-1.125V1.125C24 .502 23.498 0 22.875 0zm17.363 9.75c.612 0 1.154.037 1.627.111a6.38 6.38 0 0 1 1.306.34v2.458a3.95 3.95 0 0 0-.643-.361 5.093 5.093 0 0 0-.717-.26 5.453 5.453 0 0 0-1.426-.2c-.3 0-.573.028-.819.086a2.1 2.1 0 0 0-.623.242c-.17.104-.3.229-.393.374a.888.888 0 0 0-.14.49c0 .196.053.373.156.529.104.156.252.304.443.444s.423.276.696.41c.273.135.582.274.926.416.47.197.892.407 1.266.628.374.222.695.473.963.753.268.279.472.598.614.957.142.359.214.776.214 1.253 0 .657-.125 1.21-.373 1.656a3.033 3.033 0 0 1-1.012 1.085 4.38 4.38 0 0 1-1.487.596c-.566.12-1.163.18-1.79.18a9.916 9.916 0 0 1-1.84-.164 5.544 5.544 0 0 1-1.512-.493v-2.63a5.033 5.033 0 0 0 3.237 1.2c.333 0 .624-.03.872-.09.249-.06.456-.144.623-.25.166-.108.29-.234.373-.38a1.023 1.023 0 0 0-.074-1.089 2.12 2.12 0 0 0-.537-.5 5.597 5.597 0 0 0-.807-.444 27.72 27.72 0 0 0-1.007-.436c-.918-.383-1.602-.852-2.053-1.405-.45-.553-.676-1.222-.676-2.005 0-.614.123-1.141.369-1.582.246-.441.58-.804 1.004-1.089a4.494 4.494 0 0 1 1.47-.629 7.536 7.536 0 0 1 1.77-.201zm-15.113.188h9.563v2.166H9.506v9.646H6.789v-9.646H3.375z",
"Docker":"M13.983 11.078h2.119a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.119a.185.185 0 00-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 00.186-.186V3.574a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m0 2.716h2.118a.187.187 0 00.186-.186V6.29a.186.186 0 00-.186-.185h-2.118a.185.185 0 00-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 00.184-.186V6.29a.185.185 0 00-.185-.185H8.1a.185.185 0 00-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 00.185-.186V6.29a.185.185 0 00-.185-.185H5.136a.186.186 0 00-.186.185v1.887c0 .102.084.185.186.185m5.893 2.715h2.118a.186.186 0 00.186-.185V9.006a.186.186 0 00-.186-.186h-2.118a.185.185 0 00-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 00.185-.185V9.006a.185.185 0 00-.184-.186h-2.12a.186.186 0 00-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 00.184-.185V9.006a.185.185 0 00-.184-.186h-2.12a.185.185 0 00-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 00-.75.748 11.376 11.376 0 00.692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 003.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z",
"Java":"M11.915 0 11.7.215C9.515 2.4 7.47 6.39 6.046 10.483c-1.064 1.024-3.633 2.81-3.711 3.551-.093.87 1.746 2.611 1.55 3.235-.198.625-1.304 1.408-1.014 1.939.1.188.823.011 1.277-.491a13.389 13.389 0 0 0-.017 2.14c.076.906.27 1.668.643 2.232.372.563.956.911 1.667.911.397 0 .727-.114 1.024-.264.298-.149.571-.33.91-.5.68-.34 1.634-.666 3.53-.604 1.903.062 2.872.39 3.559.704.687.314 1.15.664 1.925.664.767 0 1.395-.336 1.807-.9.412-.563.631-1.33.72-2.24.06-.623.055-1.32 0-2.066.454.45 1.117.604 1.213.424.29-.53-.816-1.314-1.013-1.937-.198-.624 1.642-2.366 1.549-3.236-.08-.748-2.707-2.568-3.748-3.586C16.428 6.374 14.308 2.394 12.13.215zm.175 6.038a2.95 2.95 0 0 1 2.943 2.942 2.95 2.95 0 0 1-2.943 2.943A2.95 2.95 0 0 1 9.148 8.98a2.95 2.95 0 0 1 2.942-2.942zM8.685 7.983a3.515 3.515 0 0 0-.145.997c0 1.951 1.6 3.55 3.55 3.55 1.95 0 3.55-1.598 3.55-3.55 0-.329-.046-.648-.132-.951.334.095.64.208.915.336a42.699 42.699 0 0 1 2.042 5.829c.678 2.545 1.01 4.92.846 6.607-.082.844-.29 1.51-.606 1.94-.315.431-.713.651-1.315.651-.593 0-.932-.27-1.673-.61-.741-.338-1.825-.694-3.792-.758-1.974-.064-3.073.293-3.821.669-.375.188-.659.373-.911.5s-.466.2-.752.2c-.53 0-.876-.209-1.16-.64-.285-.43-.474-1.101-.545-1.948-.141-1.693.176-4.069.823-6.614a43.155 43.155 0 0 1 1.934-5.783c.348-.167.749-.31 1.192-.425zm-3.382 4.362a.216.216 0 0 1 .13.031c-.166.56-.323 1.116-.463 1.665a33.849 33.849 0 0 0-.547 2.555 3.9 3.9 0 0 0-.2-.39c-.58-1.012-.914-1.642-1.16-2.08.315-.24 1.679-1.755 2.24-1.781zm13.394.01c.562.027 1.926 1.543 2.24 1.783-.246.438-.58 1.068-1.16 2.08a4.428 4.428 0 0 0-.163.309 32.354 32.354 0 0 0-.562-2.49 40.579 40.579 0 0 0-.482-1.652.216.216 0 0 1 .127-.03z",
"C++":"M22.394 6c-.167-.29-.398-.543-.652-.69L12.926.22c-.509-.294-1.34-.294-1.848 0L2.26 5.31c-.508.293-.923 1.013-.923 1.6v10.18c0 .294.104.62.271.91.167.29.398.543.652.69l8.816 5.09c.508.293 1.34.293 1.848 0l8.816-5.09c.254-.147.485-.4.652-.69.167-.29.27-.616.27-.91V6.91c.003-.294-.1-.62-.268-.91zM12 19.11c-3.92 0-7.109-3.19-7.109-7.11 0-3.92 3.19-7.11 7.11-7.11a7.133 7.133 0 016.156 3.553l-3.076 1.78a3.567 3.567 0 00-3.08-1.78A3.56 3.56 0 008.444 12 3.56 3.56 0 0012 15.555a3.57 3.57 0 003.08-1.778l3.078 1.78A7.135 7.135 0 0112 19.11zm7.11-6.715h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79zm2.962 0h-.79v.79h-.79v-.79h-.79v-.79h.79v-.79h.79v.79h.79z",
"Shell":"M21.038,4.9l-7.577-4.498C13.009,0.134,12.505,0,12,0c-0.505,0-1.009,0.134-1.462,0.403L2.961,4.9 C2.057,5.437,1.5,6.429,1.5,7.503v8.995c0,1.073,0.557,2.066,1.462,2.603l7.577,4.497C10.991,23.866,11.495,24,12,24 c0.505,0,1.009-0.134,1.461-0.402l7.577-4.497c0.904-0.537,1.462-1.529,1.462-2.603V7.503C22.5,6.429,21.943,5.437,21.038,4.9z M15.17,18.946l0.013,0.646c0.001,0.078-0.05,0.167-0.111,0.198l-0.383,0.22c-0.061,0.031-0.111-0.007-0.112-0.085L14.57,19.29 c-0.328,0.136-0.66,0.169-0.872,0.084c-0.04-0.016-0.057-0.075-0.041-0.142l0.139-0.584c0.011-0.046,0.036-0.092,0.069-0.121 c0.012-0.011,0.024-0.02,0.036-0.026c0.022-0.011,0.043-0.014,0.062-0.006c0.229,0.077,0.521,0.041,0.802-0.101 c0.357-0.181,0.596-0.545,0.592-0.907c-0.003-0.328-0.181-0.465-0.613-0.468c-0.55,0.001-1.064-0.107-1.072-0.917 c-0.007-0.667,0.34-1.361,0.889-1.8l-0.007-0.652c-0.001-0.08,0.048-0.168,0.111-0.2l0.37-0.236 c0.061-0.031,0.111,0.007,0.112,0.087l0.006,0.653c0.273-0.109,0.511-0.138,0.726-0.088c0.047,0.012,0.067,0.076,0.048,0.151 l-0.144,0.578c-0.011,0.044-0.036,0.088-0.065,0.116c-0.012,0.012-0.025,0.021-0.038,0.028c-0.019,0.01-0.038,0.013-0.057,0.009 c-0.098-0.022-0.332-0.073-0.699,0.113c-0.385,0.195-0.52,0.53-0.517,0.778c0.003,0.297,0.155,0.387,0.681,0.396 c0.7,0.012,1.003,0.318,1.01,1.023C16.105,17.747,15.736,18.491,15.17,18.946z M19.143,17.859c0,0.06-0.008,0.116-0.058,0.145 l-1.916,1.164c-0.05,0.029-0.09,0.004-0.09-0.056v-0.494c0-0.06,0.037-0.093,0.087-0.122l1.887-1.129 c0.05-0.029,0.09-0.004,0.09,0.056V17.859z M20.459,6.797l-7.168,4.427c-0.894,0.523-1.553,1.109-1.553,2.187v8.833 c0,0.645,0.26,1.063,0.66,1.184c-0.131,0.023-0.264,0.039-0.398,0.039c-0.42,0-0.833-0.114-1.197-0.33L3.226,18.64 c-0.741-0.44-1.201-1.261-1.201-2.142V7.503c0-0.881,0.46-1.702,1.201-2.142l7.577-4.498c0.363-0.216,0.777-0.33,1.197-0.33 c0.419,0,0.833,0.114,1.197,0.33l7.577,4.498c0.624,0.371,1.046,1.013,1.164,1.732C21.686,6.557,21.12,6.411,20.459,6.797z",
"Go":"M1.811 10.231c-.047 0-.058-.023-.035-.059l.246-.315c.023-.035.081-.058.128-.058h4.172c.046 0 .058.035.035.07l-.199.303c-.023.036-.082.07-.117.07zM.047 11.306c-.047 0-.059-.023-.035-.058l.245-.316c.023-.035.082-.058.129-.058h5.328c.047 0 .07.035.058.07l-.093.28c-.012.047-.058.07-.105.07zm2.828 1.075c-.047 0-.059-.035-.035-.07l.163-.292c.023-.035.07-.07.117-.07h2.337c.047 0 .07.035.07.082l-.023.28c0 .047-.047.082-.082.082zm12.129-2.36c-.736.187-1.239.327-1.963.514-.176.046-.187.058-.34-.117-.174-.199-.303-.327-.548-.444-.737-.362-1.45-.257-2.115.175-.795.514-1.204 1.274-1.192 2.22.011.935.654 1.706 1.577 1.835.795.105 1.46-.175 1.987-.77.105-.13.198-.27.315-.434H10.47c-.245 0-.304-.152-.222-.35.152-.362.432-.97.596-1.274a.315.315 0 01.292-.187h4.253c-.023.316-.023.631-.07.947a4.983 4.983 0 01-.958 2.29c-.841 1.11-1.94 1.8-3.33 1.986-1.145.152-2.209-.07-3.143-.77-.865-.655-1.356-1.52-1.484-2.595-.152-1.274.222-2.419.993-3.424.83-1.086 1.928-1.776 3.272-2.02 1.098-.2 2.15-.07 3.096.571.62.41 1.063.97 1.356 1.648.07.105.023.164-.117.2m3.868 6.461c-1.064-.024-2.034-.328-2.852-1.029a3.665 3.665 0 01-1.262-2.255c-.21-1.32.152-2.489.947-3.529.853-1.122 1.881-1.706 3.272-1.95 1.192-.21 2.314-.095 3.33.595.923.63 1.496 1.484 1.648 2.605.198 1.578-.257 2.863-1.344 3.962-.771.783-1.718 1.273-2.805 1.495-.315.06-.63.07-.934.106zm2.78-4.72c-.011-.153-.011-.27-.034-.387-.21-1.157-1.274-1.81-2.384-1.554-1.087.245-1.788.935-2.045 2.033-.21.912.234 1.835 1.075 2.21.643.28 1.285.244 1.905-.07.923-.48 1.425-1.228 1.484-2.233z",
"Rust":"M23.8346 11.7033l-1.0073-.6236a13.7268 13.7268 0 00-.0283-.2936l.8656-.8069a.3483.3483 0 00-.1154-.578l-1.1066-.414a8.4958 8.4958 0 00-.087-.2856l.6904-.9587a.3462.3462 0 00-.2257-.5446l-1.1663-.1894a9.3574 9.3574 0 00-.1407-.2622l.49-1.0761a.3437.3437 0 00-.0274-.3361.3486.3486 0 00-.3006-.154l-1.1845.0416a6.7444 6.7444 0 00-.1873-.2268l.2723-1.153a.3472.3472 0 00-.417-.4172l-1.1532.2724a14.0183 14.0183 0 00-.2278-.1873l.0415-1.1845a.3442.3442 0 00-.49-.328l-1.076.491c-.0872-.0476-.1742-.0952-.2623-.1407l-.1903-1.1673A.3483.3483 0 0016.256.955l-.9597.6905a8.4867 8.4867 0 00-.2855-.086l-.414-1.1066a.3483.3483 0 00-.5781-.1154l-.8069.8666a9.2936 9.2936 0 00-.2936-.0284L12.2946.1683a.3462.3462 0 00-.5892 0l-.6236 1.0073a13.7383 13.7383 0 00-.2936.0284L9.9803.3374a.3462.3462 0 00-.578.1154l-.4141 1.1065c-.0962.0274-.1903.0567-.2855.086L7.744.955a.3483.3483 0 00-.5447.2258L7.009 2.348a9.3574 9.3574 0 00-.2622.1407l-1.0762-.491a.3462.3462 0 00-.49.328l.0416 1.1845a7.9826 7.9826 0 00-.2278.1873L3.8413 3.425a.3472.3472 0 00-.4171.4171l.2713 1.1531c-.0628.075-.1255.1509-.1863.2268l-1.1845-.0415a.3462.3462 0 00-.328.49l.491 1.0761a9.167 9.167 0 00-.1407.2622l-1.1662.1894a.3483.3483 0 00-.2258.5446l.6904.9587a13.303 13.303 0 00-.087.2855l-1.1065.414a.3483.3483 0 00-.1155.5781l.8656.807a9.2936 9.2936 0 00-.0283.2935l-1.0073.6236a.3442.3442 0 000 .5892l1.0073.6236c.008.0982.0182.1964.0283.2936l-.8656.8079a.3462.3462 0 00.1155.578l1.1065.4141c.0273.0962.0567.1914.087.2855l-.6904.9587a.3452.3452 0 00.2268.5447l1.1662.1893c.0456.088.0922.1751.1408.2622l-.491 1.0762a.3462.3462 0 00.328.49l1.1834-.0415c.0618.0769.1235.1528.1873.2277l-.2713 1.1541a.3462.3462 0 00.4171.4161l1.153-.2713c.075.0638.151.1255.2279.1863l-.0415 1.1845a.3442.3442 0 00.49.327l1.0761-.49c.087.0486.1741.0951.2622.1407l.1903 1.1662a.3483.3483 0 00.5447.2268l.9587-.6904a9.299 9.299 0 00.2855.087l.414 1.1066a.3452.3452 0 00.5781.1154l.8079-.8656c.0972.0111.1954.0203.2936.0294l.6236 1.0073a.3472.3472 0 00.5892 0l.6236-1.0073c.0982-.0091.1964-.0183.2936-.0294l.8069.8656a.3483.3483 0 00.578-.1154l.4141-1.1066a8.4626 8.4626 0 00.2855-.087l.9587.6904a.3452.3452 0 00.5447-.2268l.1903-1.1662c.088-.0456.1751-.0931.2622-.1407l1.0762.49a.3472.3472 0 00.49-.327l-.0415-1.1845a6.7267 6.7267 0 00.2267-.1863l1.1531.2713a.3472.3472 0 00.4171-.416l-.2713-1.1542c.0628-.0749.1255-.1508.1863-.2278l1.1845.0415a.3442.3442 0 00.328-.49l-.49-1.076c.0475-.0872.0951-.1742.1407-.2623l1.1662-.1893a.3483.3483 0 00.2258-.5447l-.6904-.9587.087-.2855 1.1066-.414a.3462.3462 0 00.1154-.5781l-.8656-.8079c.0101-.0972.0202-.1954.0283-.2936l1.0073-.6236a.3442.3442 0 000-.5892zm-6.7413 8.3551a.7138.7138 0 01.2986-1.396.714.714 0 11-.2997 1.396zm-.3422-2.3142a.649.649 0 00-.7715.5l-.3573 1.6685c-1.1035.501-2.3285.7795-3.6193.7795a8.7368 8.7368 0 01-3.6951-.814l-.3574-1.6684a.648.648 0 00-.7714-.499l-1.473.3158a8.7216 8.7216 0 01-.7613-.898h7.1676c.081 0 .1356-.0141.1356-.088v-2.536c0-.074-.0536-.0881-.1356-.0881h-2.0966v-1.6077h2.2677c.2065 0 1.1065.0587 1.394 1.2088.0901.3533.2875 1.5044.4232 1.8729.1346.413.6833 1.2381 1.2685 1.2381h3.5716a.7492.7492 0 00.1296-.0131 8.7874 8.7874 0 01-.8119.9526zM6.8369 20.024a.714.714 0 11-.2997-1.396.714.714 0 01.2997 1.396zM4.1177 8.9972a.7137.7137 0 11-1.304.5791.7137.7137 0 011.304-.579zm-.8352 1.9813l1.5347-.6824a.65.65 0 00.33-.8585l-.3158-.7147h1.2432v5.6025H3.5669a8.7753 8.7753 0 01-.2834-3.348zm6.7343-.5437V8.7836h2.9601c.153 0 1.0792.1772 1.0792.8697 0 .575-.7107.7815-1.2948.7815zm10.7574 1.4862c0 .2187-.008.4363-.0243.651h-.9c-.09 0-.1265.0586-.1265.1477v.413c0 .973-.5487 1.1846-1.0296 1.2382-.4576.0517-.9648-.1913-1.0275-.4717-.2704-1.5186-.7198-1.8436-1.4305-2.4034.8817-.5599 1.799-1.386 1.799-2.4915 0-1.1936-.819-1.9458-1.3769-2.3153-.7825-.5163-1.6491-.6195-1.883-.6195H5.4682a8.7651 8.7651 0 014.907-2.7699l1.0974 1.151a.648.648 0 00.9182.0213l1.227-1.1743a8.7753 8.7753 0 016.0044 4.2762l-.8403 1.8982a.652.652 0 00.33.8585l1.6178.7188c.0283.2875.0425.577.0425.8717zm-9.3006-9.5993a.7128.7128 0 11.984 1.0316.7137.7137 0 01-.984-1.0316zm8.3389 6.71a.7107.7107 0 01.9395-.3625.7137.7137 0 11-.9405.3635z",
}
LANG_ICONS["bash"]=LANG_ICONS["Shell"]

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

def _lang_icon(x, y, name):
    """Render a real language logo (simple-icons path) centered at (x,y)."""
    path=LANG_ICONS.get(name)
    if not path:
        return f'<text x="{x}" y="{y+6}" text-anchor="middle" font-family="monospace" font-size="13" font-weight="700" fill="#94a3b8">&lt;/&gt;</text>'
    c=LANG_COLORS.get(name,FALLBACK_LANG)
    return f'<g transform="translate({x-10},{y-10}) scale(0.82)"><path d="{path}" fill="{c}"/></g>'

def _size(vb):
    if vb>=1024*1024: return f"{vb/1024/1024:.1f} MB"
    if vb>=1024: return f"{vb/1024:.1f} KB"
    return f"{vb:.0f} B"

def top_langs_svg(langs):
    t=CFG["theme"]
    total=sum(langs.values()) or 1
    n=len(langs)
    top=sorted(langs.items(), key=lambda kv:-kv[1])[:6]
    W=430
    H=96+len(top)*42+18

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
    # per-language brand gradients for the bars
    for i,(name,_) in enumerate(top):
        c=LANG_COLORS.get(name,FALLBACK_LANG)
        s.append(f'<linearGradient id="barG{i}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c}"/><stop offset="0.85" stop-color="{c}"/><stop offset="1" stop-color="#ffffff"/></linearGradient>')
    s.append('</defs>')

    s.append(f'<rect width="{W}" height="{H}" rx="22" fill="url(#langBg)"/>')
    s.append(f'<circle cx="{W-40}" cy="30" r="70" fill="url(#langNeb)"/>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="22" fill="none" stroke="url(#langEdge)" stroke-width="1.4"/>')

    # header
    s.append('<circle cx="24" cy="26" r="6" fill="#67e8f9" opacity="0.85"><animate attributeName="opacity" values="0.85;0.3;0.85" dur="2.6s" repeatCount="indefinite"/></circle>')
    s.append(f'<text x="40" y="31" fill="{t["text"]}" font-family="sans-serif" font-size="19" font-weight="800">Top Linguagens</text>')
    if n:
        s.append(f'<text x="40" y="52" fill="{t["muted"]}" font-family="sans-serif" font-size="12">{n} linguagens · {_size(sum(langs.values()))} de código público</text>')
    else:
        s.append(f'<text x="40" y="52" fill="{t["muted"]}" font-family="sans-serif" font-size="12">aguardando dados dos repositórios públicos...</text>')

    # divider
    s.append(f'<line x1="24" y1="68" x2="{W-24}" y2="68" stroke="#818cf8" stroke-opacity="0.25" stroke-width="1"/>')

    # rows: [icon] name ......... %  (aligned columns)
    #          [bar ---- brand] {track}
    ry=86
    for i,(name,bytes_) in enumerate(top):
        bp=bytes_/total*100
        bx=48; bw=360
        w=bw*bp/100
        c=LANG_COLORS.get(name,FALLBACK_LANG)

        # icon chip
        s.append(f'<rect x="20" y="{ry}" width="32" height="32" rx="9" fill="#ffffff" fill-opacity="0.05" stroke="{c}" stroke-opacity="0.35" stroke-width="1"/>')
        s.append(f'<clipPath id="chip{i}"><rect x="20" y="{ry}" width="32" height="32" rx="9"/></clipPath>')
        s.append(f'<g clip-path="url(#chip{i})">{_lang_icon(36, ry+16, name)}</g>')
        # name (left column, fixed x)
        s.append(f'<text x="66" y="{ry+14}" fill="#e2e8f0" font-family="monospace" font-size="14" font-weight="600">{name}</text>')
        # percent (right column, aligned)
        s.append(f'<text x="{W-24}" y="{ry+14}" text-anchor="end" fill="{c}" font-family="monospace" font-size="14" font-weight="700">{bp:.1f}%</text>')
        # track + brand fill (aligned under the name, full width)
        s.append(f'<rect x="{bx}" y="{ry+20}" width="{bw}" height="8" rx="4" fill="#1c2546"/>')
        s.append(f'<rect x="{bx}" y="{ry+20}" width="{w:.1f}" height="8" rx="4" fill="url(#barG{i})"><animate attributeName="width" from="0" to="{w:.1f}" dur="1.1s" begin="{i*0.15:.2f}s" fill="freeze"/></rect>')
        ry+=42

    # footer
    s.append(f'<text x="24" y="{H-13}" fill="{t["muted"]}" font-family="sans-serif" font-size="10.5">atualizado automaticamente · via GitHub Actions</text>')

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