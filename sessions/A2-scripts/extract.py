"""Build the Nov 19 2026 Product Hunt list from hunted.space page data,
overriding votes/comments with the figures Product Hunt's own leaderboard printed."""
import csv, json, re, sys

src, out_csv = sys.argv[1], sys.argv[2]
html = open(src, encoding="utf-8").read()
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
posts = json.loads(m.group(1))["props"]["pageProps"]["initialStats"]["posts"]

# Read from producthunt.com/leaderboard/daily/2026/11/19/all on 2026-11-20: name -> (PH rank, upvotes, comments)
PH = {
    "TestSprite 4.0": (1, 363, 55), "Verse Engine by Ctruh": (2, 321, 60),
    "Netlify Server": (3, 289, 20), "Stripo Email Widgets": (4, 254, 149),
    "Adside": (5, 230, 51), "Spellar for Chrome": (6, 198, 41), "Manufact": (7, 205, 59),
    "Tabstack by Mozilla": (8, 193, 18), "Teaflask": (9, 178, 15), "Gemini 4 Neon": (10, 147, 4),
    "Wispr Flow Notetaker for iPhone": (11, 132, 8), "Impractical": (14, 98, 6),
    "ToolJet": (15, 98, 2), "Meilisearch Searchandising": (17, 97, 12),
    "Mesh API": (34, 143, 10), "Oodle AI": (36, 34, 34), "Localist": (40, 17, 10),
}

feat = sorted([p for p in posts if p["featured"] == 1], key=lambda p: p["order"])
unf = sorted([p for p in posts if p["featured"] != 1], key=lambda p: (-p["votesCount"], -p["commentsCount"]))

rows = []
for i, p in enumerate(feat, 1):
    ph = PH.get(p["name"])
    if ph and ph[0] != i:
        print(f"RANK MISMATCH {p['name']}: tracker {i} vs PH {ph[0]}", file=sys.stderr)
    rows.append(dict(rank=i, name=p["name"], featured="yes",
                     upvotes=ph[1] if ph else p["votesCount"], comments=ph[2] if ph else p["commentsCount"],
                     source="producthunt.com" if ph else "hunted.space",
                     tracker_upvotes=p["votesCount"], tracker_comments=p["commentsCount"],
                     tagline=p["tagline"], url=p["url"]))
for p in unf:
    ph = PH.get(p["name"])
    rows.append(dict(rank=ph[0] if ph else "", name=p["name"], featured="no",
                     upvotes=ph[1] if ph else p["votesCount"], comments=ph[2] if ph else p["commentsCount"],
                     source="producthunt.com" if ph else "hunted.space",
                     tracker_upvotes=p["votesCount"], tracker_comments=p["commentsCount"],
                     tagline=p["tagline"], url=p["url"]))

missing = [n for n in PH if n not in {r["name"] for r in rows}]
print("PH names not found in tracker:", missing, file=sys.stderr)
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

print(f"featured={len(feat)} unfeatured={len(unf)} total={len(rows)}")
print("--- featured ---")
for r in rows[: len(feat)]:
    mark = "" if r["source"] == "producthunt.com" else " *"
    print(f"{r['rank']} | {r['name']} | {r['upvotes']} | {r['comments']}{mark} | tracker {r['tracker_upvotes']}/{r['tracker_comments']}")
print("--- unfeatured, top 25 by votes ---")
for r in rows[len(feat): len(feat) + 25]:
    print(f"{r['rank'] or '-'} | {r['name']} | {r['upvotes']} | {r['comments']} | {r['source']}")
votes = [r["tracker_upvotes"] for r in rows[len(feat):]]
print("unfeatured with >=10 votes:", sum(v >= 10 for v in votes), "| <=3 votes:", sum(v <= 3 for v in votes))
