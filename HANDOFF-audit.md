# Handoff: pre-survival audit checks (2026-10-30)

Written by Claude on the notebook. Claude on the PC: do each step in order. For every step,
**check first** whether it is already done on the PC. If done, report "already done" with the
evidence. If not, do it as written. Report each step's result to the user before moving on.

Rules: pack changes go on a branch, are tested via the branch URL, and merge to `main` only after
the user says OK (see `AGENTS.md`). Before removing any mod, grep `kubejs/`, `config/ftbquests/`
and `config/` for its namespace (AGENTS.md rule 3). Ask the user before any delete. Delete this file when all steps are done.

## Step 0: sync
- Check: `git log -1 --oneline` on the PC pack matches GitHub `main` (or newer).
- If not: `git pull`. Confirm Prism points at `/main/pack.toml` and launch once so the PC `mods/` updates.

## Step 1: world backup (proven risk, high priority)
Why: the pack has 10+ alpha/beta jars (C2ME, Connector, Iris, Steam 'n' Rails, Vein Mining, mcfd-compat).
- Check: does a backup of each world in `saves/` exist from today?
- If not: copy `saves/` to a dated folder outside the instance, or use Prism's backup. Report the path.

## Step 2: decide the final mod list (proven, must do before the real world)
Why: `.packwizignore` currently disables 9 mods (Sable, Create Aeronautics and add-ons, Linear Bearing,
Create Tracks) for the stutter test. Removing a mod later deletes its blocks from the world.
- Check: read `.packwizignore`; are those 9 lines still there?
- If yes: **ask the user** "Keep Create Aeronautics in the survival world, yes or no?"
  - Yes → on a branch, delete the 9 mod lines + `config/sound_physics_aeronautics/`, `packwiz refresh`, test, merge on OK.
  - No → leave them disabled; note the decision in the report.
- Do not start the real survival world until this is answered.

## Step 3: remove Reactive Music (proven)
Why: still in `mods/` though the user decided to remove it on 2026-10-24 (it replaces the vanilla soundtrack);
the notebook log shows it adds about 2.5 s to load.
- Check: does `mods/reactive-music.pw.toml` exist?
- If yes: on the branch, `packwiz remove reactive-music`. Keep YACL.

## Step 4: C2ME evidence test (partly proven, medium)
Evidence so far: the log shows C2ME turning off 4 ModernFix fixes incl. `chunk_deadlock`; the jar is alpha.
No crash or corruption has been seen.
- Check the PC `logs/latest.log` and `crash-reports/` for any line naming `c2me` with ERROR or a crash. Report what you find.
- Run `/spark profiler start --only-ticks-over 50`, fly into new terrain 2 min, `/spark profiler stop`. Share the link.
- Repeat with C2ME removed (branch only). Keep it only if the run without it is clearly worse.

## Step 5: Connector / Axiom check (partly proven, medium)
Evidence: Moonlight logs an ERROR "Fabric API detected … proceed at your own risk"; Connector broke world join on 2026-10-16.
Connector + Forgified Fabric API are only in the pack for Axiom.
- Check: grep the PC `logs/latest.log` for `Fabric API detected` and any `connector` ERROR.
- **Ask the user** "Will you use Axiom in survival?" No → on the branch, remove `axiom`, `sinytra-connector`, `forgified-fabric-api`.

## Not needed (no evidence of harm, leave as is)
- Sable Dynamic Lights: Sable is optional in its jar; it is a LambDynamicLights add-on, not a duplicate.
- Particle mods (AsyncParticles, Particle Core, Particle Effects, Particle Rain, FootprintParticle): only
  touch them if the Step 4 spark run points at particles.
- DH `maxGenerationRequestDistance = 4096`, Dynamic FPS / Eating Animation 1.21.0 builds, two tooltip mods.

## Report back
One line per step: done / already done / skipped (why), plus the spark links and the branch name.
