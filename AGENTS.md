# AGENTS.md — Create Colony Lean (packwiz modpack)

Read this before changing anything in this repo. It is a modpack, not an app. Most failures here
are **runtime** failures (a crash at launch or world join), and no compiler catches them. Treat
every change as a hypothesis until the pack has booted.

## Ground truth
- Minecraft **1.21.1**, NeoForge **21.1.262** (`pack.toml` `[versions]`). Every mod file must be built
  for exactly this loader and version. A Forge or 1.20.1 jar is wrong even if it "looks like" the same mod.
- `mods/*.pw.toml` are packwiz pointers, not jars. Never hand-edit a hash; use `packwiz` commands.
- `index.toml` is generated. After any file change, run `packwiz refresh`.

## How a mod change can break the pack
| Failure | Cause | Where it shows |
|---|---|---|
| Missing dependency | Mod B requires mod A, and A is absent or out of range | `latest.log`: `Missing or unsupported mandatory dependencies` |
| Wrong side | A client-only mod (renderer, HUD, sound, shader, minimap) is marked `side = "both"` | Dedicated server crashes on boot (`Attempted to load class ... for invalid dist DEDICATED_SERVER`) |
| Mixin conflict | Two mods patch the same game code | `crash-reports/`: `Mixin apply failed`, `InvalidInjectionException` |
| Bad id | A KubeJS recipe or quest names an item that does not exist | KubeJS log errors / quest shows a barrier icon |
| Silent version drift | A mod self-updates (Distant Horizons did) | Two jars of one mod in `mods/` |

## Rules for the agent
1. **Never invent an item, block, or mod id.** Ids in `kubejs/` and `config/ftbquests/` must be
   verified against the real jar, using the jar scan the quest generators use or the jar's `assets/<ns>/`.
   Mark anything unverified `(?)`.
2. **Adding a mod:** use `packwiz mr add <slug>` (prefer Modrinth) or `packwiz cf add <slug>`.
   Then read its required dependencies and add them in the same change. Set `side` correctly:
   anything purely visual or audio is `client`.
3. **Removing a mod:** search `kubejs/`, `config/ftbquests/` and `config/` for its namespace first.
   Dead references break recipes and quests.
4. **Config files:** `config/` holds client and common configs that ship to players. A file in `defaultconfigs/`
   is copied into a world's `serverconfig/` only when that file is missing there; an existing file wins.
5. **Quests are generated.** Edit the generator in `../tools/gen_*.py`, not the `.snbt` by hand, unless
   the user edited them in the FTB in-game editor (then those edits are the source; do not regenerate over them).
6. **One change, one test.** Several mods added at once make a crash impossible to bisect.
7. A green CI run is not "it works in-game". Report what CI proved, and list what still needs an in-game check.

## Test ladder (stop at the first failure)
1. `python tools/check.py` — syntax of TOML/JSON/SNBT/KubeJS, plus a stale-index check. Seconds.
2. `node dist/projects/mc-pack/tools/check_deps.js` (run from the vault root) — dependency and version
   ranges, read from the real jars in the Prism instance.
3. `python tools/check_ids.py` — every `ns:path` id in `kubejs/` and quest `item`/`id`/`icon` fields must
   exist in a jar (models, blockstates, block loot tables or `en_us` lang keys) or vanilla. Namespaces with no
   jar assets are listed, not checked. Seconds.
4. `python tools/boot_test.py` — boots a real NeoForge dedicated server from the Prism instance jars
   (client-side mods skipped) with this repo's `config/`, `defaultconfigs/`, `kubejs/`, on a fresh world.
   Fails on a crash (prints the culprit mod from the first mod stack frame) or any KubeJS server error.
   Catches wrong-side mods, server-side crashes and mixin failures. A few minutes; first run downloads NeoForge.
   Not on GitHub: about 19 CurseForge files are excluded from the API and cannot be downloaded by a bot or
   redistributed. GitHub `ci` runs step 1 only.
   - A culprit that is a renderer, HUD, sound or camera mod → set its `side = "client"`, not remove it.
   - The Prism instance must be synced to the branch under test first (launch it once, or `packwiz serve`).
5. Notebook test launch per `../workflows/test-launch.md`, then the in-game checklist the change needs.

## Reading a crash
Open the newest `crash-reports/*.txt`, or `logs/latest.log` when there is no report. Find the first
`Caused by:`, then the first mod package name under it, which names the culprit. Search `Suspected Mods:`
in the report. Quote the line in your report; never guess the culprit from the mod list alone.

## Releases
Tag `vX.Y.Z` and push the tag. The `release` workflow runs `packwiz curseforge export` and attaches the zip
to a GitHub Release. No `.mrpack`: Modrinth export fails on the CurseForge-excluded files.
Bump `version` in `pack.toml` first.
