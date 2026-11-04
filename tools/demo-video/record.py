"""Records a LinkedIn demo of AlgoForge and edits it into one MP4.

Each scene is driven by Playwright in headless Chromium and captured with Chrome's screencast (sharp JPEG frames,
unlike Playwright's low-bitrate recorder). A fake cursor with click ripples and animated captions are injected into
the page, title cards are HTML with CSS animations, and ffmpeg joins everything with transitions.

Run with tools/demo-video/run.sh (see the README in this folder). Needs STUDENT_TOKEN and ADMIN_TOKEN for
throwaway demo accounts, and BASE_URL for the site to record.
"""
import asyncio
import base64
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright

BASE = os.environ.get("BASE_URL", "http://frontend:5173")
STUDENT = os.environ["STUDENT_TOKEN"]
ADMIN = os.environ["ADMIN_TOKEN"]
OUT = Path(os.environ.get("OUT_DIR", "/out"))
CLIPS = OUT / "clips"
W, H, FPS = 1920, 1080, 30
TRANSITION = 0.6

# --- Injected into every page: a visible cursor with click ripples, and animated captions. ---
OVERLAY = r"""
(() => {
  const css = `
    #demo-cursor { position: fixed; left: 0; top: 0; z-index: 2147483647; pointer-events: none;
      width: 26px; height: 26px; margin: -4px 0 0 -4px; transition: transform .08s linear; }
    #demo-cursor svg { filter: drop-shadow(0 3px 6px rgba(20, 10, 50, .45)); }
    .demo-ripple { position: fixed; z-index: 2147483646; pointer-events: none; width: 16px; height: 16px;
      margin: -8px 0 0 -8px; border-radius: 50%; border: 3px solid #8b5cf6; animation: demo-ripple .6s ease-out forwards; }
    @keyframes demo-ripple { from { transform: scale(.4); opacity: 1 } to { transform: scale(3.6); opacity: 0 } }
    #demo-caption { position: fixed; left: 50%; bottom: 46px; z-index: 2147483645; pointer-events: none;
      transform: translate(-50%, 30px); opacity: 0; transition: transform .5s cubic-bezier(.2,.8,.2,1), opacity .5s;
      display: flex; align-items: center; gap: 16px; padding: 16px 28px 16px 18px; border-radius: 999px;
      background: rgba(18, 12, 40, .92); color: #fff; box-shadow: 0 20px 50px -18px rgba(40, 10, 90, .8);
      font: 600 26px/1.25 "Plus Jakarta Sans Variable", system-ui, sans-serif; letter-spacing: -.01em; white-space: nowrap; }
    #demo-caption.show { transform: translate(-50%, 0); opacity: 1; }
    #demo-caption .num { display: inline-grid; place-items: center; width: 40px; height: 40px; border-radius: 50%;
      background: #7c3aed; font-size: 18px; font-weight: 800; }
    #demo-caption .sub { font-weight: 500; opacity: .75; }
  `;
  const ready = () => {
    if (document.getElementById('demo-cursor')) return;
    const style = document.createElement('style'); style.textContent = css; document.documentElement.appendChild(style);
    const cursor = document.createElement('div'); cursor.id = 'demo-cursor';
    cursor.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2l15 9.5-6.7 1.3L16 21l-3 1.4-3.6-8.1L4 19z" fill="#fff" stroke="#1b1533" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    cursor.style.transform = 'translate(-100px, -100px)';
    document.documentElement.appendChild(cursor);
    addEventListener('mousemove', (e) => { cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`; }, true);
    addEventListener('mousedown', (e) => {
      const r = document.createElement('div'); r.className = 'demo-ripple';
      r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
      document.documentElement.appendChild(r); setTimeout(() => r.remove(), 700);
    }, true);
    const caption = document.createElement('div'); caption.id = 'demo-caption'; document.documentElement.appendChild(caption);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ready); else ready();
  window.__caption = (n, text, sub) => {
    const c = document.getElementById('demo-caption'); if (!c) return;
    c.classList.remove('show');
    setTimeout(() => {
      c.innerHTML = `<span class="num">${n}</span><span>${text}</span>` + (sub ? `<span class="sub">${sub}</span>` : '');
      c.classList.add('show');
    }, 120);
  };
  window.__captionHide = () => document.getElementById('demo-caption')?.classList.remove('show');
})();
"""

CARD_CSS = """
  * { box-sizing: border-box; margin: 0; }
  body { width: 1920px; height: 1080px; overflow: hidden; background: #0e0b1c; color: #f0ecff;
    font-family: "Plus Jakarta Sans Variable", system-ui, sans-serif; }
  .stage { position: relative; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 30px; text-align: center; overflow: hidden; }
  .glow { position: absolute; width: 1100px; height: 1100px; border-radius: 50%; left: 50%; top: 50%;
    transform: translate(-50%, -50%); background: radial-gradient(closest-side, rgba(124, 58, 237, .35), transparent);
    animation: breathe 6s ease-in-out infinite; }
  .grid { position: absolute; inset: 0; opacity: .14;
    background-image: linear-gradient(#3d3566 1px, transparent 1px), linear-gradient(90deg, #3d3566 1px, transparent 1px);
    background-size: 64px 64px; mask-image: radial-gradient(closest-side, #000, transparent); }
  @keyframes breathe { 50% { transform: translate(-50%, -50%) scale(1.12); } }
  .mark { width: 132px; height: 132px; border-radius: 36px; display: grid; place-items: center; background: #7c3aed;
    box-shadow: 0 30px 80px -20px rgba(124, 58, 237, .9); animation: pop .9s cubic-bezier(.2, 1.4, .3, 1) both; }
  @keyframes pop { from { transform: scale(0) rotate(-25deg); opacity: 0; } }
  .rise { animation: rise .8s cubic-bezier(.2, .8, .2, 1) both; }
  @keyframes rise { from { transform: translateY(40px); opacity: 0; filter: blur(8px); } }
  h1 { font-size: 132px; font-weight: 800; letter-spacing: -.05em; line-height: 1; }
  h2 { font-size: 76px; font-weight: 800; letter-spacing: -.04em; }
  p.lead { font-size: 36px; color: #c9c2ec; max-width: 1300px; line-height: 1.4; }
  .chips { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; }
  .chip { padding: 14px 26px; border-radius: 999px; background: #1d1838; border: 1px solid #3d3566; font-size: 26px;
    font-weight: 700; color: #ddd6fe; }
  .tiles { display: grid; grid-template-columns: repeat(4, 380px); gap: 22px; }
  .tile { padding: 28px 30px; border-radius: 26px; background: #17132b; border: 1px solid #2c264b; text-align: left;
    box-shadow: 0 24px 60px -30px rgba(0, 0, 0, .9); }
  .tile b { display: block; font-size: 30px; letter-spacing: -.02em; margin-bottom: 8px; color: #fff; }
  .tile span { font-size: 21px; color: #a8a1cc; line-height: 1.35; }
  .tile i { font-style: normal; display: inline-grid; place-items: center; width: 52px; height: 52px; border-radius: 16px;
    background: #2a1f52; color: #c4b5fd; font-size: 24px; font-weight: 800; margin-bottom: 18px; }
  .accent { color: #c4b5fd; }
  .url { font-size: 40px; font-weight: 700; padding: 18px 34px; border-radius: 22px; background: #1d1838;
    border: 1px solid #3d3566; color: #ddd6fe; }
"""
MARK_SVG = ('<svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.6" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 6 3 12l5.5 6M15.5 6 21 12l-5.5 6"/></svg>')


def delay(seconds):
    return f'style="animation-delay:{seconds}s"'


INTRO = f"""
<div class="stage"><div class="grid"></div><div class="glow"></div>
  <div class="mark">{MARK_SVG}</div>
  <h1 class="rise" {delay(.35)}>AlgoForge</h1>
  <p class="lead rise" {delay(.7)}>Learn data structures &amp; algorithms <span class="accent">one topic at a time</span></p>
  <div class="chips">
    <span class="chip rise" {delay(1.1)}>Topic notes</span>
    <span class="chip rise" {delay(1.3)}>Guided solutions</span>
    <span class="chip rise" {delay(1.5)}>Sandboxed judge</span>
    <span class="chip rise" {delay(1.7)}>Progress tracking</span>
  </div>
</div>"""

STACK_TILES = [
    ("API", "FastAPI", "Python REST API with JWT auth and roles"),
    ("DB", "PostgreSQL", "SQLAlchemy 2.0 models, Alembic migrations"),
    ("Q", "Redis + RQ", "Submissions queued and judged by workers"),
    ("⬢", "Docker sandbox", "A fresh locked-down container per test case"),
    ("UI", "React + Monaco", "LeetCode-style editor, light and dark"),
    ("◇", "Mermaid", "Flowcharts for every solution"),
    ("TLS", "Caddy", "HTTPS, compression, security headers"),
    ("✓", "662 tests", "75 problems, 681 test cases, all verified"),
]
STACK = """
<div class="stage"><div class="grid"></div><div class="glow"></div>
  <h2 class="rise">Under the hood</h2>
  <div class="tiles">""" + "".join(
    f'<div class="tile rise" {delay(.3 + i * .12)}><i>{icon}</i><b>{name}</b><span>{body}</span></div>'
    for i, (icon, name, body) in enumerate(STACK_TILES)
) + "</div></div>"

OUTRO = f"""
<div class="stage"><div class="grid"></div><div class="glow"></div>
  <div class="mark">{MARK_SVG}</div>
  <h1 class="rise" {delay(.3)}>AlgoForge</h1>
  <p class="lead rise" {delay(.6)}>75 problems · 10 topics · 150 guided solutions · a real judge</p>
  <span class="url rise" {delay(1.0)}>github.com/Alkarim786/algoforge</span>
  <p class="lead rise" {delay(1.4)} style="font-size:30px">Built by Karim · FastAPI · PostgreSQL · Redis · Docker · React</p>
</div>"""


class Recorder:
    """Collects Chrome screencast frames for one scene, with their timestamps."""

    def __init__(self, page, folder):
        self.page, self.folder, self.frames, self.cdp = page, folder, [], None
        self.squash = []  # (start, end, seconds to keep), wall-clock times
        page.recorder = self
        folder.mkdir(parents=True, exist_ok=True)

    def warp(self, t):
        """Wall-clock time to edited time: each squash window plays in `keep` seconds."""
        shift = 0.0
        for start, end, keep in sorted(self.squash):
            if t <= start:
                break
            span = end - start
            covered = min(t, end) - start
            shift += covered - covered * (keep / span if span > 0 else 1)
        return t - shift

    async def start(self):
        self.cdp = await self.page.context.new_cdp_session(self.page)

        async def on_frame(event):
            stamp = event["metadata"].get("timestamp", time.time())
            path = self.folder / f"{len(self.frames):05d}.jpg"
            path.write_bytes(base64.b64decode(event["data"]))
            self.frames.append((stamp, path))
            try:
                await self.cdp.send("Page.screencastFrameAck", {"sessionId": event["sessionId"]})
            except Exception:
                pass

        self.cdp.on("Page.screencastFrame", lambda event: asyncio.ensure_future(on_frame(event)))
        await self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": W, "maxHeight": H, "everyNthFrame": 1})
        self.started = time.time()

    async def stop(self):
        await asyncio.sleep(0.2)
        await self.cdp.send("Page.stopScreencast")
        self.stopped = time.time()

    def to_clip(self, target):
        """Frames to a constant-rate H.264 clip, each frame held until the next one arrived."""
        frames = sorted(self.frames)
        lines = []
        for index, (stamp, path) in enumerate(frames):
            following = frames[index + 1][0] if index + 1 < len(frames) else self.stopped
            held = self.warp(following) - self.warp(stamp)
            lines += [f"file '{path.as_posix()}'", f"duration {max(held, 1 / (FPS * 4)):.4f}"]
        lines.append(f"file '{frames[-1][1].as_posix()}'")
        listing = self.folder / "frames.txt"
        listing.write_text("\n".join(lines))
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
             "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},format=yuv420p", "-c:v", "libx264", "-preset", "medium",
             "-crf", "16", str(target)],
            check=True,
        )
        return frames[-1][0] - frames[0][0] if len(frames) > 1 else 1


async def fast(page, action, keep=0.35):
    """Runs a slow step (a page load, the judge) and squeezes it to `keep` seconds in the edit."""
    start = time.time()
    await action()
    page.recorder.squash.append((start, time.time(), keep))


async def glide(page, locator, steps=16, click=False, offset=(0.5, 0.5)):
    box = await locator.bounding_box()
    x, y = box["x"] + box["width"] * offset[0], box["y"] + box["height"] * offset[1]
    await page.mouse.move(x, y, steps=steps)
    if click:
        await page.wait_for_timeout(180)
        await page.mouse.down()
        await page.wait_for_timeout(90)
        await page.mouse.up()


async def smooth_scroll(page, y, wait=1200):
    await page.evaluate(f"window.scrollTo({{top: {y}, behavior: 'smooth'}})")
    await page.wait_for_timeout(wait)


async def caption(page, n, text, sub=""):
    await page.evaluate("([n, t, s]) => window.__caption(n, t, s)", [n, text, sub])


async def settle(page, ms=900):
    await page.wait_for_load_state("networkidle")
    await page.wait_for_timeout(ms)


# --- Scenes. Each gets a fresh browser context with its own theme and signed-in user. ---

async def card(page, html, seconds):
    await page.goto(f"{BASE}/__card")
    await settle(page, 600)
    await page.evaluate("([css, html]) => { document.head.innerHTML += `<style>${css}</style>`; document.body.innerHTML = html; }", [CARD_CSS, html])
    return seconds


async def landing(page):
    await page.goto(BASE + "/")
    await settle(page)
    return [
        lambda: caption(page, 1, "A study platform for DSA", "· notes, guided solutions, a real judge"),
        lambda: page.mouse.move(980, 560, steps=16),
        lambda: page.wait_for_timeout(1300),
        lambda: smooth_scroll(page, 760, 1500),
        lambda: smooth_scroll(page, 1500, 1500),
        lambda: smooth_scroll(page, 0, 1100),
        lambda: caption(page, 2, "Light and dark mode", "· remembered for every page"),
        lambda: glide(page, page.get_by_role("button", name="Switch to dark mode"), click=True),
        lambda: page.wait_for_timeout(1500),
    ]


async def dashboard(page):
    await page.goto(BASE + "/")
    await settle(page, 1300)
    return [
        lambda: caption(page, 3, "Your dashboard", "· streaks, progress, strengths & weaknesses"),
        lambda: page.mouse.move(1500, 330, steps=16),
        lambda: page.wait_for_timeout(1500),
        lambda: smooth_scroll(page, 420, 1700),
        lambda: page.mouse.move(700, 600, steps=16),
        lambda: page.wait_for_timeout(1300),
    ]


async def problems(page):
    await page.goto(BASE + "/problems")
    await settle(page, 1200)
    return [
        lambda: caption(page, 4, "75 problems in 10 topics", "· progress ring for every topic"),
        lambda: page.mouse.move(1200, 420, steps=16),
        lambda: page.wait_for_timeout(1000),
        lambda: glide(page, page.get_by_role("button", name="Show all 10").first, click=True),
        lambda: page.wait_for_timeout(1700),
        lambda: smooth_scroll(page, 380, 1400),
    ]


async def topic(page):
    await page.goto(BASE + "/topics/array")
    await settle(page, 1500)
    return [
        lambda: caption(page, 5, "Notes for every topic", "· concepts, built-ins and diagrams"),
        lambda: page.wait_for_timeout(1300),
        lambda: page.evaluate("document.querySelector('.diagram')?.scrollIntoView({behavior: 'smooth', block: 'center'})"),
        lambda: page.wait_for_timeout(2300),
    ]


SOLUTION_BODY = """        seen = {}
        for i, x in enumerate(nums):
            if target - x in seen:
                return [seen[target - x], i]
            seen[x] = i
"""


async def workspace(page):
    await page.goto(BASE + "/problems/two-sum")
    await settle(page, 1500)
    await page.wait_for_function("window.monaco && window.monaco.editor.getEditors().length > 0", timeout=60000)

    async def type_solution():
        # Typed through the editor's API so auto-indent and auto-closing brackets don't double up.
        await page.evaluate("""() => {
            const ed = window.monaco.editor.getEditors()[0], model = ed.getModel();
            const keep = model.getValueInRange({startLineNumber: 1, startColumn: 1, endLineNumber: 2, endColumn: model.getLineMaxColumn(2)});
            model.setValue(keep + "\\n"); ed.setPosition({lineNumber: 3, column: 1}); ed.focus();
        }""")
        # Each line's indentation goes in as one edit and every other character at a steady pace: edits a few
        # milliseconds apart can race the editor's sync with React and drop characters.
        await page.evaluate("""async (text) => {
            const ed = window.monaco.editor.getEditors()[0], model = ed.getModel();
            const pieces = text.match(/\\n| {2,}|[^\\n]/g);
            for (const piece of pieces) {
                const end = model.getFullModelRange().getEndPosition();
                ed.executeEdits('demo', [{range: new window.monaco.Range(end.lineNumber, end.column, end.lineNumber, end.column), text: piece}]);
                const after = model.getFullModelRange().getEndPosition(); ed.setPosition(after);
                await new Promise((r) => setTimeout(r, 34));
            }
        }""", SOLUTION_BODY)
        await page.wait_for_timeout(300)
        typed = await page.evaluate("window.monaco.editor.getEditors()[0].getValue()")
        if not typed.endswith(SOLUTION_BODY):
            raise RuntimeError(f"the editor holds different code than was typed: {typed!r}")

    async def wait_for_verdict():
        await page.wait_for_function("/Accepted|Wrong|Error|TLE/.test(document.querySelector('.result-status')?.textContent || '')", timeout=90000)
        verdict = await page.locator(".result-status").text_content()
        if verdict.strip() != "Accepted":
            raise RuntimeError(f"the demo solution was judged {verdict!r}, not Accepted")

    return [
        lambda: caption(page, 6, "A real code editor", "· write your solution in Python"),
        lambda: glide(page, page.locator(".editor"), offset=(0.45, 0.35)),
        type_solution,
        lambda: page.wait_for_timeout(500),
        lambda: caption(page, 7, "Submit to the judge", "· every test case runs in its own Docker sandbox"),
        lambda: glide(page, page.get_by_role("button", name="Submit"), click=True),
        lambda: fast(page, wait_for_verdict, keep=1.4),
        lambda: caption(page, 8, "Accepted", "· 8 of 8 test cases, hidden ones included"),
        lambda: page.mouse.move(1300, 840, steps=16),
        lambda: page.wait_for_timeout(2300),
    ]


async def solution(page):
    await page.goto(BASE + "/problems/two-sum")
    await settle(page, 1500)

    async def open_optimized():
        await glide(page, page.get_by_role("tab", name="Solution guide"), click=True)
        await fast(page, lambda: page.wait_for_selector(".left-pane .diagram svg", timeout=30000), keep=0.3)
        await page.wait_for_timeout(1100)
        await glide(page, page.get_by_role("tab", name="Optimized"), click=True)
        await fast(page, lambda: page.wait_for_function("document.querySelectorAll('.left-pane .diagram svg').length > 0 && !document.querySelector('.left-pane .diagram.muted')", timeout=30000), keep=0.3)
        await page.wait_for_timeout(1100)

    async def notes_and_flowchart():
        await page.evaluate("document.querySelector('.left-pane .code-with-notes')?.scrollIntoView({behavior: 'smooth', block: 'start'})")
        await page.wait_for_timeout(1300)
        for index in (1, 2, 3):
            await glide(page, page.locator(".line-note").nth(index), steps=10)
            await page.wait_for_timeout(550)
        await page.evaluate("const d = document.querySelectorAll('.left-pane .diagram'); d[d.length - 1]?.scrollIntoView({behavior: 'smooth', block: 'start'})")
        await page.wait_for_timeout(2000)

    return [
        lambda: caption(page, 9, "Guided solutions", "· how to think, brute force → optimized"),
        open_optimized,
        lambda: caption(page, 10, "Line-by-line notes and flowcharts", ""),
        notes_and_flowchart,
    ]


async def drawer(page):
    await page.goto(BASE + "/problems/maximum-subarray")
    await settle(page, 1300)
    return [
        lambda: caption(page, 11, "Move through the study path", "· previous, next, or jump to any topic"),
        lambda: glide(page, page.get_by_role("button", name="Problem list"), click=True),
        lambda: fast(page, lambda: page.wait_for_selector(".drawer", timeout=20000), keep=0.3),
        lambda: page.wait_for_timeout(1100),
        lambda: glide(page, page.locator(".drawer-topic-head").nth(2), click=True),
        lambda: page.wait_for_timeout(1500),
        lambda: page.keyboard.press("Escape"),
        lambda: page.wait_for_timeout(500),
        lambda: glide(page, page.get_by_role("button", name="Next problem", exact=False), click=True),
        lambda: fast(page, lambda: page.wait_for_load_state("networkidle"), keep=0.3),
        lambda: page.wait_for_timeout(1400),
    ]


async def admin(page):
    await page.goto(BASE + "/admin")
    await settle(page, 1400)

    async def editor():
        await glide(page, page.get_by_role("link", name="Problems", exact=True), click=True)
        await fast(page, lambda: page.wait_for_selector("table", timeout=30000))
        await page.wait_for_timeout(1000)
        await glide(page, page.get_by_role("link", name="Two Sum", exact=True), click=True)
        await fast(page, lambda: page.wait_for_selector(".editor-tabs", timeout=30000))
        await page.wait_for_timeout(900)
        await glide(page, page.get_by_role("tab", name="Test cases"), click=True)
        await fast(page, lambda: page.wait_for_selector(".cases-table", timeout=30000))
        await page.wait_for_timeout(1800)

    return [
        lambda: caption(page, 12, "Admin console", "· track every student's progress"),
        lambda: page.mouse.move(900, 520, steps=16),
        lambda: page.wait_for_timeout(1500),
        lambda: caption(page, 13, "Add problems, test cases and solutions", ""),
        editor,
    ]


SCENES = [
    ("intro", None, "dark", None),
    ("landing", landing, "light", None),
    ("dashboard", dashboard, "dark", "student"),
    ("problems", problems, "light", "student"),
    ("topic", topic, "light", "student"),
    ("workspace", workspace, "dark", "student"),
    ("solution", solution, "dark", "student"),
    ("drawer", drawer, "light", "student"),
    ("admin", admin, "light", "admin"),
    ("stack", None, "dark", None),
    ("outro", None, "dark", None),
]
CARDS = {"intro": (INTRO, 4.2), "stack": (STACK, 5.2), "outro": (OUTRO, 4.6)}
TRANSITIONS = ["fade", "smoothleft", "fade", "smoothleft", "smoothup", "fade", "smoothleft", "smoothup", "fade", "fade"]


async def record_all(only):
    work = Path("/tmp/demo-work")  # frames stay inside the container; the host mount is slow on Windows
    shutil.rmtree(work, ignore_errors=True)
    clips = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(args=["--force-color-profile=srgb", "--hide-scrollbars"])
        # Warm the dev server and the editor once, so the recording doesn't wait on first-time compiles.
        warm = await browser.new_context(viewport={"width": W, "height": H})
        warm_page = await warm.new_page()
        for path in ("/", "/problems", "/topics/array", "/problems/two-sum", "/admin"):
            await warm_page.goto(BASE + path)
            await warm_page.wait_for_load_state("networkidle")
        await warm.close()

        for name, run, theme, who in SCENES:
            if only and name not in only:
                continue
            token = {"student": STUDENT, "admin": ADMIN}.get(who)
            context = await browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
            await context.add_init_script(
                f"localStorage.setItem('algoforge-theme', '{theme}');"
                + (f"localStorage.setItem('algoforge-token', '{token}');" if token else "localStorage.removeItem('algoforge-token');")
                + "localStorage.removeItem('algoforge-code:two-sum:python');"
            )
            await context.add_init_script(OVERLAY)
            page = await context.new_page()
            recorder = Recorder(page, work / name)
            if name in CARDS:
                html, seconds = CARDS[name]
                await card(page, "", 0)
                await recorder.start()
                await page.evaluate("([css, html]) => { document.head.innerHTML += `<style>${css}</style>`; document.body.innerHTML = html; }", [CARD_CSS, html])
                await page.wait_for_timeout(seconds * 1000)
            else:
                steps = await run(page)
                await page.mouse.move(W * 0.62, H * 0.45)
                await recorder.start()
                for step in steps:
                    await step()
                await page.wait_for_timeout(500)
            await recorder.stop()
            clip = CLIPS / f"{name}.mp4"  # kept, so a later run can redo one scene and reuse the rest
            recorder.to_clip(clip)
            clips.append(clip)
            print(f"recorded {name}: {len(recorder.frames)} frames", flush=True)
            await context.close()
        await browser.close()
    return clips


def duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def join(clips, target):
    """Chains the clips with xfade transitions into one MP4."""
    inputs, filters = [], []
    for clip in clips:
        inputs += ["-i", str(clip)]
    offset, previous = 0.0, "0:v"
    for index in range(1, len(clips)):
        offset += duration(clips[index - 1]) - TRANSITION
        label = f"v{index}"
        kind = TRANSITIONS[(index - 1) % len(TRANSITIONS)]
        filters.append(f"[{previous}][{index}:v]xfade=transition={kind}:duration={TRANSITION}:offset={offset:.3f}[{label}]")
        previous = label
    total = offset + duration(clips[-1])
    filters.append(f"[{previous}]fade=t=in:st=0:d=0.4,fade=t=out:st={total - 0.6:.3f}:d=0.6,format=yuv420p[out]")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters), "-map", "[out]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-r", str(FPS), "-movflags", "+faststart", str(target)],
        check=True,
    )
    return total


if __name__ == "__main__":
    # python record.py              records every scene
    # python record.py workspace    re-records just that scene (several names are fine) and reuses the saved clips
    # python record.py --join       only re-joins the saved clips
    import sys

    names = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    unknown = set(names) - {scene[0] for scene in SCENES}
    if unknown:
        raise SystemExit(f"unknown scenes {sorted(unknown)}; choose from {[scene[0] for scene in SCENES]}")
    CLIPS.mkdir(parents=True, exist_ok=True)
    if "--join" not in sys.argv:
        asyncio.run(record_all(set(names)))
    clips = [CLIPS / f"{scene[0]}.mp4" for scene in SCENES]
    missing = [clip.name for clip in clips if not clip.exists()]
    if missing:
        raise SystemExit(f"no saved clip for {missing}; record them first")
    target = OUT / "algoforge-demo.mp4"
    seconds = join(clips, target)
    print(f"wrote {target} ({seconds:.1f} s, {target.stat().st_size / 1e6:.1f} MB)")
