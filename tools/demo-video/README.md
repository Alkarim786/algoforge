# Demo video

`record.py` records a ~70-second LinkedIn demo of AlgoForge and edits it into `out/algoforge-demo.mp4` (1920×1080,
H.264). It drives the real app in headless Chromium, so re-run it after UI changes to get an up-to-date video.

- Scenes: intro card, landing page, light/dark switch, dashboard, problems page, topic notes, typing and submitting a
  solution (Accepted), the solution guide, the problem list panel, the admin console, a tech-stack card and an outro.
- Effects: an injected cursor with click ripples, animated captions, CSS-animated title cards, and xfade transitions.
- Captured with Chrome's screencast (sharp JPEG frames) and joined with ffmpeg.

It records the development stack (`docker compose up -d`, with content seeded) and needs two short-lived tokens for
throwaway demo accounts: a student with some progress (Two Sum left unsolved) and an admin.

```bash
docker build -t algoforge-demo-recorder tools/demo-video
docker run --rm --network algoforge-dev_default --env-file <tokens.env> \
  -v "$PWD/tools/demo-video:/work" -v "$PWD/tools/demo-video/out:/out" algoforge-demo-recorder python record.py
```

Every scene is saved to `out/clips/`, so a single scene can be fixed without recording everything again:

```bash
... algoforge-demo-recorder python record.py workspace   # re-record one scene (or several), then re-join
... algoforge-demo-recorder python record.py --join      # only re-join the saved clips
```

Scenes: intro, landing, dashboard, problems, topic, workspace, solution, drawer, admin, stack, outro. The run stops
with an error instead of saving a bad clip if the typed code doesn't match or the verdict isn't Accepted.

`<tokens.env>` holds `STUDENT_TOKEN=...` and `ADMIN_TOKEN=...` (make them with `app.security.create_access_token`
inside the api container, and delete the demo accounts afterwards). Don't commit it.
