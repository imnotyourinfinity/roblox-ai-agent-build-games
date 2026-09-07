# Roblox AI Agent

Give it a prompt like `"a simple obby with 10 levels and a leaderboard"`, or
leave it blank and let the AI invent its own game concept, and it will plan
the game, generate the parts and scripts, and publish it to a fresh Roblox
place from your pool — no Studio required per run.

## How it works

0. **`idea_generator.py`** — if you don't give a prompt, this invents a game
   concept itself (mixing genres freely) and keeps a running history
   (`idea_history.json`) so it doesn't repeat past ideas.
1. **`ai_planner.py`** — calls Gemini (free tier) to break the prompt into a task list,
   then generates the concrete data for each task (parts to build, or Lua
   script source).
2. **`rbxlx_builder.py`** — assembles that data into a real Roblox place
   file (`.rbxlx`).
3. **`pool_manager.py`** — picks the next unused empty place from your
   pre-created pool (`places_pool.json`) and marks it used, so each run
   publishes into a *different* game instead of overwriting the same one.
4. **`roblox_publisher.py`** — uploads the place file to that place using
   Roblox's Open Cloud API.
5. **`main.py`** — runs the whole pipeline end to end.
6. **`.github/workflows/build_game.yml`** — lets you run all of this in the
   cloud via GitHub Actions, either manually (enter a prompt, or leave it
   blank, in the Actions tab) or on a schedule.

## One-time setup

### 1. Batch-create a pool of empty Roblox places
Since Roblox's API can't create brand-new experiences on its own (see note
below), create a batch of empty places up front so the agent has a supply
to draw from without you touching Studio each run:

- In Roblox Studio, create a new blank place, then **File > Publish As...**
  and choose your **CryptoCore Labs** group as the owner. Repeat this
  20-50 times (or however many games you want ready) - it's quick since
  each one starts blank.
- For each one, note its **Universe ID** and **Place ID** (visible in the
  game's Creator Dashboard page URL, or under Game Settings > Basic Info).
- Fill these into `places_pool.json` in this format:
  ```json
  [
    {"label": "game-1", "universe_id": "111111", "place_id": "222222", "used": false},
    {"label": "game-2", "universe_id": "333333", "place_id": "444444", "used": false}
  ]
  ```
- Commit this file to your repo. Each run marks one slot `used: true` and
  commits that change back automatically, so you always know what's left.
- **When the pool runs low:** repeat this batch-create step for another
  round. This is the only recurring manual step - everything else runs
  itself.

> **Why this exists:** Open Cloud currently has no way to create brand new
> experiences/universes via API - only to publish updates into a place
> that already exists. A bot that clicked through Roblox's website to
> "create new experience" automatically would risk your account/group
> getting flagged, so that's not something to automate. Batch-creating
> places yourself up front is the safe way to get the same hands-off
> result.

### 2. Get a Roblox Open Cloud API key
- Go to the [Creator Dashboard](https://create.roblox.com/dashboard/credentials)
- Create an API key with `universe-places:write` permission. Choose your
  **CryptoCore Labs** group as the owner context, and grant it access to
  all the universes in your pool (or your whole group's experiences, if
  that option is available) so one key can publish to any of them.

### 3. Get a Gemini API key (free tier, used while testing)
- Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey),
  sign in, and click "Create API key". Free tier limits apply - fine for
  testing at low volume. See [ai.google.dev/pricing](https://ai.google.dev/pricing)
  for current limits.
- Once the pipeline is reliable and you care more about output quality than
  cost, you can swap in a different provider (e.g. Claude) - only
  `ai_planner.py` needs to change.

### 4. Add secrets to your GitHub repo
Go to your repo's **Settings > Secrets and variables > Actions** and add:
- `GEMINI_API_KEY`
- `ROBLOX_API_KEY`

(Universe/Place IDs are no longer secrets - they live in `places_pool.json`
since they aren't sensitive on their own, just the API key is.)

### 5. Push this code to that repo
Commit all these files (including `places_pool.json` and the
`.github/workflows` folder) and push.

## Running it

**From GitHub (cloud, no computer needed):**
Go to the repo's **Actions** tab → select "Build and Publish Roblox Game" →
"Run workflow" → type a game idea, or leave the field blank to let the AI
invent its own → Run. It'll publish into the next unused place in your pool.

**Locally (for testing/debugging):**
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...
export ROBLOX_API_KEY=...
python main.py "a simple obby with 10 levels and a leaderboard"
# or, to let the AI pick its own idea:
python main.py
```

## Known limitations (read before relying on this)

- **The XML place format is minimal.** It covers basic Parts and Scripts,
  which is enough for simple games, but Roblox's real format has many more
  optional properties. If something doesn't look right when you open the
  published place in Studio, compare it against a file Studio itself saves
  and adjust `rbxlx_builder.py`.
- **No real self-testing yet.** The agent doesn't run the game to catch
  errors — `ai_planner.fix_script()` exists for future use (feed it a Lua
  error message and it'll return a fix) but nothing currently calls it
  automatically. This is the natural next upgrade once the basics are solid.
- **The pool is finite.** Once every slot is used, runs will fail with a
  clear error telling you to top it up - by design, since fully automated
  place creation isn't something Roblox's API (safely) supports.

