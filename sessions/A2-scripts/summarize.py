import json, re, sys
from collections import Counter
from datetime import datetime, timezone, timedelta

html = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
data = json.loads(m.group(1))
pp = data["props"]["pageProps"]
st = pp["initialStats"]
print("todayDateString:", pp.get("todayDateString"))
for k in ["postRowsCount", "unfeaturedPostRowsCount", "range", "mostPopularTopic"]:
    print(k, "=", json.dumps(st.get(k))[:300])
print("query:", data.get("query"), "page:", data.get("page"))

posts = st["posts"]
print("posts:", len(posts))
print("unique ids:", len({p["id"] for p in posts}))
PT = timezone(timedelta(hours=-8))


def ptday(s):
    if not s:
        return None
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d.astimezone(PT).date().isoformat()


print("createdAt PT day:", Counter(ptday(p["createdAt"]) for p in posts).most_common(10))
print("featuredAt PT day:", Counter(ptday(p["featuredAt"]) for p in posts).most_common(10))
print("featured flag:", Counter(p["featured"] for p in posts))
print("order sample:", [p["order"] for p in posts[:40]])
for p in posts[:3]:
    q = dict(p)
    q.pop("thumbnail", None)
    print(json.dumps(q)[:600])
