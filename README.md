# scraper-studio-claude-code

> Status: every command and number here comes from real runs on 2026-11-20, on Product Hunt's leaderboard for 2026-11-19, with Claude Code 2.1.329 (Claude Opus 5.5) and Bright Data CLI 0.4.1. `check_run.py` runs in CI on those runs. It has not been run on any other site yet.

Give your coding agent one web scraper it calls by ID, then check every run before the agent trusts it.

`check_run.py` reads what a scraper run returned and says whether it's complete: the row count, gaps in a rank or ID sequence, and the type of every field. It exits 1 on a short or broken run, prints what to do next, and with `--heal-prompt` writes the sentence to pass to `bdata scraper heal`. Give it two runs and it keeps the fuller one.

```
python3 check_run.py fixtures/producthunt-2026-11-19/1-first-run.json --expect fixtures/producthunt-2026-11-19/expect.json --heal-prompt
```

```
FAIL  rows           17 of 33 rows. Run it once more; if the count repeats, heal it with a sentence that says how the page loads the rest (scroll, pagination, a 'load more' button).
FAIL  rank-gaps      rank missing: 18 to 33
PASS  rank           rank: int on every row
PASS  product_name   product_name: str on every row
PASS  tagline        tagline: str on every row
PASS  upvote_count   upvote_count: int on every row
PASS  comment_count  comment_count: int on every row
PASS  topics         topics: list on every row
PASS  product_url    product_url: str on every row

INCOMPLETE: 7 of 9 checks pass

heal prompt:
  The scraper returns only 17 of the 33 rows; keep loading the page until the row count stops growing.
```

That's the scraper's real first run: 17 of the 33 products the page shows, because Product Hunt loads the rest as you scroll.

Standard-library Python 3.9+, read-only, no API key.

## The setup, in five commands

```bash
alias bdata="npx -p @brightdata/cli bdata"          # Node 20+, nothing to install
bdata login                                          # opens your browser once
bdata scraper create <url> "<one sentence naming every field>"
bdata scraper run <collector_id> <url> --pretty -o run.json
python3 check_run.py run.json --expect expect.json
```

When a run comes back short, heal it with a sentence, approve, and run again. The ID stays the same:

```bash
bdata scraper heal <collector_id> "$(cat prompts/heal-2.txt)" --url <url>
bdata scraper approve <collector_id> --url <url>
```

The exact sentences used here are in [prompts/](prompts/): `create.txt`, then `heal-1.txt` (it missed), `heal-2.txt` (it worked), `heal-3.txt` (aimed at the flaky runs; it didn't change the rate).

## Pin it so the next session uses it

Put this in your project's CLAUDE.md, with your ID and your `expect.json`:

```markdown
## Web data

- Product Hunt daily leaderboard for a date YYYY/M/D:
  1. `npx -p @brightdata/cli bdata scraper run <collector_id> https://www.producthunt.com/leaderboard/daily/YYYY/M/D -o ph1.json`
  2. the same command again with `-o ph2.json`
  3. `python3 check_run.py ph1.json ph2.json --expect expect.json`
  Answer from the file it KEPT. Never fetch or scrape the page yourself.
```

Two runs, because one run in this test came back short about 3 times in 10. In headless runs on the test machine, Claude Code didn't load a project CLAUDE.md, so the measured sessions passed the same lines with `claude -p --append-system-prompt-file CLAUDE.md`. Ask your agent to quote its project instructions back if it ignores the pin.

## What the runs measured

Fresh Claude Code sessions, each asked for every product on the 2026-11-19 leaderboard. Full tool-call lists in [sessions/](sessions/).

| Session | Time | Steps | Cost | Products |
|---|---|---|---|---|
| [A2](sessions/A2.md): no saved scraper | 19 min | 40 | $1.53 | 33, ranks 18 to 33 copied from a third-party site |
| [B1](sessions/B1.md): a second fresh session, no scraper reached it | 14.5 min | 46 | $1.40 | ranks 30 to 33 missing |
| [B3](sessions/B3.md): pinned scraper, one run | 2 min 26 s | 3 | $0.34 | 17 |
| [B4](sessions/B4.md): pinned scraper, one run | 3 min 17 s | 3 | $0.26 | 17 |
| B5: pinned scraper, two runs plus `check_run.py` | pending | | | |

The scraper itself, every run logged in [runs/](runs/):

| Step | Time | Result |
|---|---|---|
| create | 2 min 7 s | Collector ID `c_mwpbzgtf7zkgs1xfr` |
| first run | 61 s | 17 of 33 |
| heal 1, approve, run | 2 min 14 s to heal | 17 of 33 |
| heal 2, approve, run | 8 min to heal, 80 s to run | 33 of 33 |
| 7 runs after heal 2 (CLI, API and inside sessions) | 6 s to 80 s | 33 in 5, 17 in 2 |
| heal 3, approve, 6 runs | 3 min 17 s to heal | 33 in 4, 17 in 2 |
| API trigger | 25 s | 33 of 33 |

Plain `curl` on the same page: HTTP 403 ([runs/00-plain-fetch.log](runs/00-plain-fetch.log)). The whole test used 8 of the free tier's 5,000 monthly page loads.

## Call it from anything

```bash
curl -X POST "https://api.brightdata.com/dca/trigger?collector=<collector_id>&queue_next=1" \
  -H "Authorization: Bearer $BRIGHTDATA_API_KEY" -H "Content-Type: application/json" \
  -d '[{"url":"https://www.producthunt.com/leaderboard/daily/2026/11/19"}]'
# then poll: https://api.brightdata.com/dca/dataset?id=<collection_id>
```

## Files

- `check_run.py`: the checker. `python3 test_check_run.py` runs its known answers.
- `fixtures/producthunt-2026-11-19/`: four real runs and the `expect.json` they're checked against.
- `prompts/`: the create and heal sentences, verbatim.
- `runs/`: every CLI run, with polling lines removed and local paths replaced by `~`.
- `sessions/`: every Claude Code session, its tool calls and its answer. Tool results are left out.

Companion to the Medium piece [Your Coding Agent Pays for the Same Web Data Every Session](PIECE_URL_PENDING). Bright Data Scraper Studio: [product](https://brightdata.com/products/web-scraper/studio), [free tier](https://docs.brightdata.com/general/account/billing-and-pricing/free-tier), [CLI tutorial](https://docs.brightdata.com/datasets/scraper-studio/build-with-the-cli).

MIT licensed.
