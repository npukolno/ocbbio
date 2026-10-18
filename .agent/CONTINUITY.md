# Continuity

## [PLANS]

- 2026-08-30T08:45:00Z [USER] Опубликовать Discord domain verification по пути `/.well-known/discord` для `ocb2016.me`.

- 2026-07-22T00:00:00+03:00 [USER] Restyle the personal static website to a minimal, premium-looking design and remove the cosmic/card/animation-heavy aesthetic.
- 2026-07-22T00:00:00+03:00 [USER] Choose a final signal color from rendered variants before finalizing the palette.
- 2026-07-22T00:00:00+03:00 [USER] Publish the completed site to GitHub Pages.

## [DECISIONS]

- 2026-08-30T08:45:00Z [CODE] Добавлен `.nojekyll`, поскольку GitHub Pages исключает скрытую директорию `.well-known` при Jekyll-сборке; это публикует verification-файл без изменения сайта.

- 2026-07-22T00:00:00+03:00 [ASSUMPTION] Use the Swiss anchor: cold white surface, system sans typography, one red accent, hairline grid rules, and restrained interaction.
- 2026-07-22T00:00:00+03:00 [USER] Supersedes the Swiss direction: the light theme has unreadable SVG icons and the layout lacks character and motion.
- 2026-07-22T00:00:00+03:00 [CODE] Use the Industrial anchor: warm-black surface, JetBrains Mono, acid-lime signal color, flat rules, and restrained reveal/hover motion.

## [PROGRESS]

- 2026-07-22T00:00:00+03:00 [TOOL] Inspected the static site: `index.html`, `style.css`, and `script.js`; no build configuration or package manifest is present.
- 2026-07-22T00:00:00+03:00 [CODE] Rebuilt the visual system with the Swiss anchor and removed particle, constellation, preloader, custom-cursor, audio, shimmer, typewriter, reveal, and tilt code.
- 2026-07-22T00:00:00+03:00 [TOOL] Captured and inspected final Chromium screenshots at 1440x1000 and 390x844.
- 2026-07-22T00:00:00+03:00 [CODE] Reworked the site into the Industrial direction: readable monochrome SVG filters, three-column skills, single-column project records, and intersection-based motion.
- 2026-07-22T00:00:00+03:00 [CODE] Aligned the Discord block to the hero title, increased timeline gutter spacing, made skill icons retain their readable monochrome treatment on hover, renamed visible identity text to `ocb`, and added `img/zayac.png` for the Discord avatar.
- 2026-07-22T00:00:00+03:00 [CODE] Removed destructive brightness/invert filters from skill, timeline, and project SVG icons because their source artwork depends on white shapes with black inner details.
- 2026-07-22T00:00:00+03:00 [CODE] Rebuilt the timeline DOM into explicit year groups at runtime to prevent CSS grid auto-placement from pairing years with unrelated events; simplified the Discord presence into a compact left-rail identity block.
- 2026-07-22T00:00:00+03:00 [USER] Updated Discord display/copy username and Telegram URL to `ocbxvi`; preserved unrelated service URLs and the `ocb` site brand.

## [DISCOVERIES]

- 2026-07-22T00:00:00+03:00 [CODE] The existing presentation includes a particle canvas, constellations, custom cursor, preloader, typewriter, shimmer, hover expansions, and tilt effects.

## [OUTCOMES]

- 2026-07-22T00:00:00+03:00 [CODE] Retained live Discord presence, clipboard copy, scroll-to-top, the GitHub release URL update, and skill-level data; project descriptions are now immediately visible.
- 2026-07-22T00:00:00+03:00 [TOOL] `node --check script.js` and `git diff --check` pass.
- 2026-07-22T00:00:00+03:00 [TOOL] Chromium checks confirm no horizontal overflow at 1440px and 390px viewports; reveal targets appear after scrolling.
- 2026-07-22T00:00:00+03:00 [TOOL] Rendered red, amber, and neutral signal variants at hero and Skills viewports; `node --check script.js` and `git diff --check` pass after the latest changes.
- 2026-07-22T00:00:00+03:00 [USER] Updated the favicon to the existing `icons/ocb_new_logo.svg`; the requested `icons/ocb_icon_new.svg` was not present in the workspace.
- 2026-07-22T00:00:00+03:00 [TOOL] Created local commit `9bf9ce9 Redesign bio site` containing only site files and required assets. Push is blocked because HTTPS has no credentials, `GITHUB_TOKEN`/`GH_TOKEN` are unset, and GitHub SSH authentication fails; `main` is one commit ahead of `origin/main`.
- 2026-07-22T00:00:00+03:00 [USER] Requested a logo-based link preview instead of the Discord avatar. Created `img/og-logo.png` at 1200x630 and updated Open Graph/Twitter metadata to use it.
- 2026-07-22T00:00:00+03:00 [USER] Increased the Rust skill level from 5% to 35%; it will ship with the transparent logo-only social preview.
- 2026-07-22T00:00:00+03:00 [TOOL] Published commits through `3cf2676` to `main`; GitHub Pages reports a successful build for `3cf2676a97d41b2bac1eb8a001f1a36fc8ec8b61`. The final social preview image is an opaque `#0b0c0a` background with the centered OCB logo.

## 2026-10-18 profile refresh

- 2026-10-18T12:00:00Z [USER] Requested identity, contact, role, skill, project-status, timeline, and Ghidra asset updates.
- 2026-10-18T12:00:00Z [CODE] Updated `index.html` and `script.js`: display name `eq`, Discord copy value `emotionalquintessence`, avatar, Telegram `pykuvkrovu`, professional roles, skill levels/categories, H.S.B closed state, and Aug 2026 closure event. Added `img/avatar.jpg` and `icons/ghidra.svg`.
- 2026-10-18T12:00:00Z [TOOL] `node --check script.js` and `git diff --check` pass.
- 2026-10-18T12:05:00Z [USER] Noted that the Aug 2026 H.S.B closure was placed before later 2026 events in the source order.
- 2026-10-18T12:05:00Z [CODE] Moved the `Closed H.S.B` timeline item after `Finished & handed off MIMIC`, preserving chronological order.
- 2026-10-18T12:05:00Z [TOOL] Verified source ordering and `git diff --check`.
- 2026-10-18T12:10:00Z [USER] Requested Swift/Go under Programming, `eq` branding in hero and floating nav, a reliable 100% zoom cube, and cube hero letters changed from OCB to BIO.
- 2026-10-18T12:10:00Z [CODE] Moved Swift and Go into Programming, changed hero/nav labels to `eq`, mapped hero cube faces to BIO, reduced cube footprint and relaxed its desktop gutter threshold to remain visible at normal 100% zoom.
- 2026-10-18T12:10:00Z [TOOL] `node --check cube.js` and `git diff --check` pass.
- 2026-10-18T12:15:00Z [USER] Reported the hero cube visually read BOI and requested swapping I/O.
- 2026-10-18T12:15:00Z [CODE] Swapped hero cube I/O mapping so the visible idle faces read BIO: left B, front O, top I.
- 2026-10-18T12:15:00Z [TOOL] `node --check cube.js` and `git diff --check` pass.
- 2026-10-18T12:25:00Z [USER] Asked to build the proposed redesign as a separate HTML page, reduce red usage, and change page/social preview title to `eq | bio`.
- 2026-10-18T12:25:00Z [CODE] Added `eq.html`, a standalone blue/amber/violet profile design with filtered skill matrix, selected work, and reverse-engineering notes sections. Updated `index.html` title and Open Graph/Twitter titles/alt text to `eq | bio`.
- 2026-10-18T12:25:00Z [TOOL] `git diff --check` passes; metadata and filter markup verified with `rg`.
