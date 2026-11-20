"""Write sessions/<id>.md from a Claude Code stream-json file: prompt, time, steps, cost, every tool call, the answer.
Local paths are replaced with ~ and the contents of tool results are left out."""
import json, re, sys

def clean(s):
    s = re.sub(r"/Users/[^\s\"']*", "~", s)
    s = re.sub(r"/private/tmp/[^\s\"']*", "~", s)
    return s

def main(stream, prompt, meta, out, title):
    calls, result = [], {}
    for line in open(stream, encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") == "assistant":
            for c in d["message"]["content"]:
                if c.get("type") == "tool_use":
                    i = c["input"]
                    arg = i.get("command") or i.get("url") or i.get("query") or i.get("file_path") or i.get("description") or ""
                    if c["name"] == "Read" and "/memory/" in str(arg):
                        arg = "a local note"
                    calls.append(f"{len(calls)+1}. {c['name']}: `{clean(str(arg))[:140]}`")
        if d.get("type") == "result":
            result = d
    m = open(meta).read().split()
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"# {title}\n\n**Prompt:** {open(prompt).read().strip()}\n\n")
        fh.write(f"**Started** {m[1]}, **ended** {m[3]}, **{result.get('duration_ms',0)/1000:.0f} s**, "
                 f"**{result.get('num_turns')} turns**, **${result.get('total_cost_usd',0):.2f}** (Claude Code's own count).\n\n")
        fh.write("## Tool calls\n\n" + "\n".join(calls) + "\n\n## Answer\n\n" + clean(result.get("result", "")) + "\n")

if __name__ == "__main__":
    main(*sys.argv[1:6])
