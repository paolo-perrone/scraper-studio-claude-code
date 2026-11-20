"""Known answers from the real Product Hunt runs of 2026-11-19. Run: python3 test_check_run.py"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "fixtures", "producthunt-2026-11-19")
EXPECT = os.path.join(FIX, "expect.json")


def run(*files, extra=()):
    p = subprocess.run([sys.executable, os.path.join(HERE, "check_run.py"), *[os.path.join(FIX, f) for f in files],
                        "--expect", EXPECT, *extra], capture_output=True, text=True)
    return p.returncode, p.stdout


def main():
    bad = []
    code, out = run("1-first-run.json", extra=("--heal-prompt",))
    if code != 1 or "17 of 33 rows" not in out or "rank missing: 18 to 33" not in out:
        bad.append("the first run (17 of 33) must fail rows and rank gaps")
    if "The scraper returns only 17 of the 33 rows" not in out:
        bad.append("--heal-prompt must name the shortfall")
    code, out = run("3-after-heal-2.json")
    if code != 0 or "COMPLETE: 9 of 9" not in out:
        bad.append("the full run (33 of 33) must pass every check")
    code, out = run("4-after-heal-3-short-run.json", "3-after-heal-2.json")
    if code != 0 or "KEPT" not in out or "3-after-heal-2.json: 33 rows" not in out:
        bad.append("given a short and a full run, it must keep the full one")
    rows = json.load(open(os.path.join(FIX, "3-after-heal-2.json")))
    rows[0]["upvote_count"] = str(rows[0]["upvote_count"])
    tmp = os.path.join(HERE, "_typed.json")
    json.dump(rows, open(tmp, "w"))
    p = subprocess.run([sys.executable, os.path.join(HERE, "check_run.py"), tmp, "--expect", EXPECT],
                       capture_output=True, text=True)
    os.remove(tmp)
    if p.returncode != 1 or "upvote_count is str in 1 of 33 rows" not in p.stdout:
        bad.append("a number stored as text must fail its field")
    if bad:
        print("FAIL: " + "; ".join(bad)); sys.exit(1)
    print("PASS: 5 known answers")


if __name__ == "__main__":
    main()
