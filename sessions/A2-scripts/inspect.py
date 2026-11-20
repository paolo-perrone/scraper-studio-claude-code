import json, re, sys

html = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
data = json.loads(m.group(1))


def walk(o, path="$", depth=0):
    if depth > 6:
        return
    if isinstance(o, dict):
        keys = list(o.keys())
        print(f"{path}: dict keys={keys[:25]}")
        for k in keys:
            walk(o[k], f"{path}.{k}", depth + 1)
    elif isinstance(o, list):
        print(f"{path}: list len={len(o)}")
        if o:
            walk(o[0], f"{path}[0]", depth + 1)


walk(data)
