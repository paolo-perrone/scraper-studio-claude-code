import json, re, sys
from datetime import datetime, timezone, timedelta

html = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
st = json.loads(m.group(1))["props"]["pageProps"]["initialStats"]
ts = sorted(st["postStatsByProductId"], key=int)
PT = timezone(timedelta(hours=-8))
fmt = lambda t: datetime.fromtimestamp(int(t) / 1000, PT).strftime("%Y-%m-%d %H:%M PT")
print("stat snapshots:", len(ts), "first:", fmt(ts[0]), "last:", fmt(ts[-1]))
last = st["postStatsByProductId"][ts[-1]]
print("posts in last snapshot:", len(last))
for pid, name in [("1314645", "TestSprite 4.0"), ("1320414", "Verse Engine")]:
    print(name, "last:", last.get(pid), "| first:", st["postStatsByProductId"][ts[0]].get(pid))
print("todayTopTenStats:", json.dumps(st.get("todayTopTenStats"))[:400])
