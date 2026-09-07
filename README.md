# Roblox AI Agent

Give it a prompt like `"a simple obby with 10 levels and a leaderboard"` and
it will plan the game, generate the parts and scripts, and publish it
straight to a Roblox place — no Studio required.

## How it works

1. **`ai_planner.py`** — calls Claude to break your prompt into a task list,
   then generates the concrete data for each task (parts to build, or Lua
   script source).
2. **`rbxlx_builder.py`** — assembles that data into a real Roblox place
   file (`.rbxlx`).
3. **`roblox_publisher.py`** — uploads the place file to your Roblox game
   using Roblox's Open Cloud API.
4. **`main.py`** — runs the whole pipeline end to end.
5. **`.github/workflows/build_game.yml`** — lets you run all of this in the
   cloud via GitHub Actions, either manually (enter a prompt in the Actions
   tab) or on a schedule.

## One-time setup

### 1. Create an empty Roblox place (only manual Studio step, ever)
- Open Roblox Studio, create a new blank place, publish it once.
- Note its **Universe ID** and **Place ID** (visible in the game's Creator
  Dashboard page URL, or under Game Settings > Basic Info).

### 2. Get a Roblox Open Cloud API key
- Go to the [Creator Dashboard](https://create.roblox.com/dashboard/credentials)
- Create an API key with `universe-places:write` permission, scoped to your
  universe.

### 3. Get an Anthropic API key
- From [console.anthropic.com](https://console.anthropic.com) if you don't
  already have one.

### 4. Add secrets to your GitHub repo
Go to your repo's **Settings > Secrets and variables > Actions** and add:
- `ANTHROPIC_API_KEY`
- `ROBLOX_API_KEY`
- `ROBLOX_UNIVERSE_ID`
- `ROBLOX_PLACE_ID`

### 5. Push this code to that repo
Commit all these files (including the `.github/workflows` folder) and push.

## Running it

**From GitHub (cloud, no computer needed):**
Go to the repo's **Actions** tab → select "Build and Publish Roblox Game" →
"Run workflow" → type your game idea → Run.

**Locally (for testing/debugging):**
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
export ROBLOX_API_KEY=...
export ROBLOX_UNIVERSE_ID=...
export ROBLOX_PLACE_ID=...
python main.py "a simple obby with 10 levels and a leaderboard"
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
- **Every run replaces the published place with a fresh build** — it
  doesn't currently merge with what's already there. Fine for testing
  standalone generated games; something to change if you want it to build
  incrementally on a previous version.
