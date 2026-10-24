# Handoff: stutter / lag-spike fix (2026-10-24)

Written by Claude on the notebook. Pick this up from the main PC (i5-13400F, RTX 4060 Ti, 32 GB).

## Problem
About 73 FPS on average, but movement hitches: at first world load and when running into new areas.
The 2026-10-19 spark run showed the server side healthy (median 14 ms per tick), so the hitches are likely frame-time spikes, not one bad mod.

## Ranked suspects (from a read-only audit, unverified until spark confirms)
1. **Live chunk generation**: Tectonic + WWOO + ~20 structure mods run on every new chunk.
   Fix: `/chunky radius 2000` → `/chunky start`, let it finish; always `/chunky pause` before quitting.
2. **Distant Horizons on defaults**: there is no DH config in `config/`.
   Fix: CPU load Balanced (or lower), LOD radius 128–256; ship `config/DistantHorizons.toml`.
3. **Java memory clean-up (GC) pauses**: the Prism Java args on the PC are unknown.
   Fix: add `-XX:+UseZGC -XX:+ZGenerational -XX:+AlwaysPreTouch -XX:+DisableExplicitGC` and keep 12–14 GB.
4. **C2ME alpha (0.120) never passed probation.** Try one session without it.
5. **Shaders (Photon/Bliss)**: try one run with shaders off to see how much they cost.
6. Three particle mods stacked (AsyncParticles, Particle Core, Particle Effects): drop Particle Effects first.
7. Sound Physics 24 rays / 3 bounces → 16 / 2 in `config/sound_physics_aeronautics/soundphysics.properties`.
8. MineColonies `alwaysrendernametag = true` → `false` in `config/minecolonies-server.toml`.
9. LambDynamicLights + Sable Dynamic Lights: keep one, unless Sable's covers only ships.

## Do on the PC, in order
1. Report the current Prism Java args and memory, plus the in-game DH and shader settings.
2. Capture a spike: `/spark profiler start --only-ticks-over 50`, run into new terrain for 2 min, `/spark profiler stop`. Also `/spark gc`. Share both links.
3. Apply fixes 1–3, then play again. Is it smooth now?
4. Only if it isn't: test 4–5 one at a time.

## Rules
- Change pack files on a branch (`perf-stutter`), test on the PC via the branch URL, and merge to `main` only after the user OKs it. See `AGENTS.md`.
- Push the branch so the notebook can pull it. Delete this file when done.
