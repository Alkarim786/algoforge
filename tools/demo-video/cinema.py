"""The cinematic cut: app footage in floating 3D browser windows on an animated stage, with camera moves, kinetic
titles, flash and light-sweep transitions, and an original soundtrack (music.py) cut to the same beat.

Every frame is rendered deterministically: the stage page exposes renderAt(t), which poses everything and seeks the
footage to the right moment, then Playwright screenshots it. Nothing depends on real-time playback, so the motion is
smooth no matter how fast the machine is.

Uses the clips that record.py saved in out/clips (record them with NO_CAPTIONS=1). Run with:
    python cinema.py        (in the recorder image, with the dev frontend reachable for the fonts)
"""
import asyncio
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

import music

OUT = Path(os.environ.get("OUT_DIR", "/out"))
CLIPS = OUT / "clips"
FONT_HOST = os.environ.get("BASE_URL", "http://frontend:5173")
STAGE = Path("/tmp/cinema")
W, H, FPS = 1920, 1080, 30
BAR = music.BAR  # 2.4 s: every cut lands on a bar line

# Shots: (name, start, end). Everything is a multiple of a bar so the edit sits on the music.
SHOTS = [
    ("intro", 0.0, 4.8),
    ("slam", 4.8, 9.6),
    ("landing", 9.6, 16.8),
    ("dashboard", 16.8, 24.0),
    ("problems", 24.0, 31.2),
    ("workspace", 31.2, 43.2),
    ("solution", 43.2, 50.4),
    ("admin", 50.4, 55.2),
    ("stack", 55.2, 60.0),
    ("outro", 60.0, 67.2),
]
TOTAL = SHOTS[-1][2]

# Which part of each recording plays during its shot: (clip, seconds trimmed from the start, from the end).
FOOTAGE = {
    "landing": ("landing", 0.5, None, 9.5),
    "dashboard": ("dashboard", 0.3, 0.3, None),
    "problems": ("problems", 0.3, 0.3, None),
    "workspace": ("workspace", 0.6, 0.4, None),
    "solution": ("solution", 3.5, 0.3, None),
    "admin": ("admin", 0.3, None, 7.5),
}

# Text for the side panels: (eyebrow, headline, sub, side of the screen).
COPY = {
    "landing": ("01 · Learn", "Notes, guides and a clear study path", "10 topics, each with concepts, built-ins and diagrams", "left"),
    "dashboard": ("02 · Track", "Your progress, at a glance", "Streaks, strengths, weaknesses and what to solve next", "right"),
    "problems": ("03 · Practice", "75 problems in 10 topics", "A progress ring for every topic", "left"),
    "solution": ("04 · Understand", "From brute force to optimized", "Line-by-line notes and a flowchart for every solution", "right"),
    "admin": ("05 · Teach", "An admin console that sees everything", "Problems, test cases, solutions and every student's progress", "left"),
}


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def prepare_footage():
    """VP9 copies of the clips (Chromium can't play H.264) and each shot's in/out points."""
    footage = {}
    (STAGE / "clips").mkdir(parents=True, exist_ok=True)
    for shot, (clip, trim_in, trim_out, until) in FOOTAGE.items():
        source = CLIPS / f"{clip}.mp4"
        length = probe(source)
        start, end = trim_in, (until if until else length - (trim_out or 0))
        end = min(end, length - 0.05)
        target = STAGE / "clips" / f"{clip}.webm"
        if not target.exists():
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(source), "-c:v", "libvpx-vp9", "-b:v", "0",
                            "-crf", "26", "-g", "8", "-deadline", "realtime", "-cpu-used", "8", "-row-mt", "1", "-an",
                            str(target)], check=True)
        footage[shot] = {"src": f"clips/{clip}.webm", "in": start, "out": end, "length": length}
    return footage


def fetch_fonts():
    for name, path in (
        ("jakarta.woff2", "/node_modules/@fontsource-variable/plus-jakarta-sans/files/plus-jakarta-sans-latin-wght-normal.woff2"),
        ("mono.woff2", "/node_modules/@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2"),
    ):
        target = STAGE / name
        if not target.exists():
            target.write_bytes(urllib.request.urlopen(FONT_HOST + path, timeout=60).read())


STAGE_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8"><style>
@font-face { font-family: Jakarta; src: url(jakarta.woff2) format("woff2"); font-weight: 200 800; }
@font-face { font-family: Mono; src: url(mono.woff2) format("woff2"); font-weight: 100 800; }
* { box-sizing: border-box; margin: 0; }
html, body { width: 1920px; height: 1080px; overflow: hidden; background: #050913; }
body { font-family: Jakarta, system-ui, sans-serif; color: #eef3ff; -webkit-font-smoothing: antialiased; }
#bg { position: absolute; inset: 0; background: radial-gradient(1200px 800px at 50% 40%, #0c1a3a 0%, #070d1d 55%, #04070f 100%); }
.orb { position: absolute; width: 1100px; height: 1100px; border-radius: 50%; left: 0; top: 0; }
#orbA { background: radial-gradient(closest-side, rgba(37, 99, 235, .42), rgba(37, 99, 235, 0)); }
#orbB { background: radial-gradient(closest-side, rgba(34, 211, 238, .24), rgba(34, 211, 238, 0)); }
#floor { position: absolute; left: -50%; right: -50%; bottom: -10%; height: 70%; transform-origin: 50% 0;
  transform: perspective(900px) rotateX(68deg);
  background-image: linear-gradient(rgba(96, 165, 250, .22) 1.5px, transparent 1.5px), linear-gradient(90deg, rgba(96, 165, 250, .22) 1.5px, transparent 1.5px);
  background-size: 90px 90px; -webkit-mask-image: linear-gradient(to bottom, transparent, #000 30%, #000 60%, transparent); }
.dot { position: absolute; width: 4px; height: 4px; border-radius: 50%; background: #93c5fd; }
#world { position: absolute; inset: 0; perspective: 2200px; perspective-origin: 50% 45%; }
.frame { position: absolute; left: 240px; top: 115px; width: 1440px; height: 850px; border-radius: 22px; overflow: hidden;
  background: #0b1222; border: 1px solid rgba(147, 197, 253, .28);
  box-shadow: 0 60px 140px -40px rgba(0, 0, 0, .9), 0 0 0 1px rgba(255, 255, 255, .04), 0 0 120px -30px rgba(37, 99, 235, .55);
  transform-style: preserve-3d; opacity: 0; }
.bar { height: 40px; display: flex; align-items: center; gap: 9px; padding: 0 18px; background: #0f1a31; border-bottom: 1px solid rgba(147, 197, 253, .15); }
.bar i { width: 12px; height: 12px; border-radius: 50%; display: block; }
.bar span { margin-left: 18px; padding: 5px 16px; border-radius: 999px; background: #0a1326; color: #9fb3d9; font-size: 15px; font-weight: 600; }
.view { position: relative; width: 1440px; height: 810px; overflow: hidden; }
.zoom { position: absolute; inset: 0; transform-origin: 50% 50%; }
.zoom video { width: 1440px; height: 810px; display: block; object-fit: cover; }
.panel { position: absolute; top: 0; bottom: 0; width: 560px; display: flex; flex-direction: column; justify-content: center; gap: 22px; opacity: 0; }
.panel.left { left: 110px; } .panel.right { right: 100px; }
.eyebrow { font-size: 22px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: #60a5fa; }
.headline { font-size: 66px; font-weight: 800; letter-spacing: -.035em; line-height: 1.04; }
.sub { font-size: 26px; line-height: 1.45; color: #a9bad9; font-weight: 500; }
.word { display: inline-block; white-space: pre; }
.center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 26px; }
.mark { width: 170px; height: 170px; border-radius: 46px; display: grid; place-items: center; background: linear-gradient(145deg, #3b82f6, #1d4ed8);
  box-shadow: 0 40px 100px -20px rgba(37, 99, 235, .9), inset 0 1px 0 rgba(255, 255, 255, .35); }
.title { font-size: 168px; font-weight: 800; letter-spacing: -.055em; line-height: 1; }
.tagline { font-size: 40px; color: #b6c6e6; font-weight: 500; }
.accent { color: #60a5fa; }
.slam { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; }
.slam div { font-size: 150px; font-weight: 800; letter-spacing: -.05em; line-height: 1.02; opacity: 0; }
.lower { position: absolute; left: 140px; bottom: 120px; display: flex; flex-direction: column; gap: 14px; opacity: 0; }
.pill { align-self: flex-start; display: inline-flex; align-items: center; gap: 14px; padding: 16px 30px 16px 18px; border-radius: 999px;
  background: rgba(8, 14, 30, .88); border: 1px solid rgba(147, 197, 253, .3); box-shadow: 0 30px 70px -20px rgba(0, 0, 0, .9);
  font-size: 40px; font-weight: 800; letter-spacing: -.02em; }
.pill b { display: inline-grid; place-items: center; width: 54px; height: 54px; border-radius: 50%; background: #2563eb; font-size: 28px; }
.pill.ok b { background: #16a34a; }
.pill.ok { border-color: rgba(74, 222, 128, .55); box-shadow: 0 0 80px -10px rgba(34, 197, 94, .7), 0 30px 70px -20px rgba(0, 0, 0, .9); }
.lower .sub { padding-left: 24px; font-size: 28px; }
.tiles { display: grid; grid-template-columns: repeat(4, 360px); gap: 24px; perspective: 1600px; }
.tile { padding: 30px 30px 32px; border-radius: 26px; background: rgba(13, 22, 42, .92); border: 1px solid rgba(147, 197, 253, .22);
  text-align: left; opacity: 0; box-shadow: 0 30px 70px -30px rgba(0, 0, 0, .9); }
.tile i { font-style: normal; display: inline-grid; place-items: center; width: 56px; height: 56px; border-radius: 16px; background: #13284f;
  color: #93c5fd; font: 800 22px Mono, monospace; margin-bottom: 18px; }
.tile b { display: block; font-size: 32px; letter-spacing: -.02em; margin-bottom: 8px; }
.tile span { font-size: 21px; color: #a3b4d4; line-height: 1.4; }
.url { font: 700 38px Mono, monospace; padding: 18px 34px; border-radius: 20px; background: rgba(12, 20, 38, .9); border: 1px solid rgba(147, 197, 253, .3); color: #dbe7ff; }
#flash { position: absolute; inset: 0; background: #dbeafe; opacity: 0; pointer-events: none; }
#sweep { position: absolute; top: -40%; bottom: -40%; width: 380px; left: 0;
  background: linear-gradient(90deg, transparent, rgba(147, 197, 253, .0), rgba(191, 219, 254, .55), rgba(147, 197, 253, 0), transparent);
  transform: rotate(18deg); opacity: 0; mix-blend-mode: screen; }
#vignette { position: absolute; inset: 0; background: radial-gradient(ellipse at center, transparent 55%, rgba(0, 0, 0, .55) 100%); pointer-events: none; }
#black { position: absolute; inset: 0; background: #000; opacity: 0; }
</style></head><body>
<div id="bg"><div class="orb" id="orbA"></div><div class="orb" id="orbB"></div><div id="floor"></div><div id="dots"></div></div>
<div id="world"></div>
<div id="flash"></div><div id="sweep"></div><div id="vignette"></div><div id="black"></div>
<script>
const CONFIG = __CONFIG__;
const $ = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstChild; };
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, k) => a + (b - a) * k;
const ease = {
  out: (k) => 1 - Math.pow(1 - k, 3),
  inOut: (k) => (k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2),
  back: (k) => { const c = 1.7, d = c + 1; return 1 + d * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); },
};
const prog = (t, a, b, fn = ease.out) => fn(clamp((t - a) / (b - a)));
const MARK = '<svg width="92" height="92" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 6 3 12l5.5 6M15.5 6 21 12l-5.5 6"/></svg>';
const world = document.getElementById('world');
const words = (text, cls = '') => text.split(' ').map((w) => `<span class="word ${cls}">${w} </span>`).join('');

// Background particles.
const dots = document.getElementById('dots');
const DOTS = Array.from({ length: 70 }, (_, i) => ({ x: (i * 977) % 1920, y: (i * 613) % 1080, s: .4 + ((i * 37) % 10) / 10, v: 8 + (i % 7) * 4 }));
DOTS.forEach(() => dots.appendChild($('<div class="dot"></div>')));

// Shots.
const shots = {};
for (const shot of CONFIG.shots) {
  const s = { ...shot, el: null, video: null };
  if (shot.footage) {
    const f = $(`<div class="frame"><div class="bar"><i style="background:#f87171"></i><i style="background:#fbbf24"></i><i style="background:#4ade80"></i><span>AlgoForge · ${shot.tab}</span></div>
      <div class="view"><div class="zoom"><video muted preload="auto" src="${shot.footage.src}"></video></div></div></div>`);
    world.appendChild(f);
    s.frame = f; s.video = f.querySelector('video'); s.zoom = f.querySelector('.zoom');
  }
  if (shot.copy) {
    const [eyebrow, headline, sub, side] = shot.copy;
    const p = $(`<div class="panel ${side}"><div class="eyebrow">${eyebrow}</div><div class="headline">${words(headline)}</div><div class="sub">${sub}</div></div>`);
    world.appendChild(p); s.panel = p;
  }
  shots[shot.name] = s;
}
const intro = $(`<div class="center"><div class="mark">${MARK}</div><div class="title">${'AlgoForge'.split('').map((c) => `<span class="word">${c}</span>`).join('')}</div>
  <div class="tagline">Learn data structures &amp; algorithms <span class="accent">one topic at a time</span></div></div>`);
world.appendChild(intro);
const slam = $(`<div class="slam"><div>Learn <span class="accent">it.</span></div><div>Understand <span class="accent">it.</span></div><div>Prove <span class="accent">it.</span></div></div>`);
world.appendChild(slam);
const lower = $(`<div class="lower"><div class="pill" id="lowerPill"><b>✎</b><span id="lowerText">Write your solution</span></div><div class="sub" id="lowerSub">A real code editor, right in the browser</div></div>`);
world.appendChild(lower);
const stack = $(`<div class="center" style="gap:46px"><div class="title" style="font-size:96px">Under the hood</div><div class="tiles">${CONFIG.tiles.map(([i, b, s]) => `<div class="tile"><i>${i}</i><b>${b}</b><span>${s}</span></div>`).join('')}</div></div>`);
world.appendChild(stack);
const outro = $(`<div class="center"><div class="mark">${MARK}</div><div class="title" style="font-size:140px">AlgoForge</div>
  <div class="tagline">75 problems · 10 topics · 150 guided solutions · a real judge</div><div class="url">github.com/Alkarim786/algoforge</div>
  <div class="tagline" style="font-size:30px;color:#8ea3c9">Built by Karim · FastAPI · PostgreSQL · Redis · Docker · React</div></div>`);
world.appendChild(outro);

function poseFrame(s, t) {
  const { start, end } = s;
  const d = end - start, k = (t - start) / d;
  const side = s.copy ? s.copy[3] : 'center';
  const baseX = side === 'left' ? 230 : side === 'right' ? -230 : 0;
  const baseS = side === 'center' ? .96 : .76;
  const enter = prog(t, start, start + .9, ease.out), leave = prog(t, end - .45, end, ease.inOut);
  const dir = side === 'right' ? -1 : 1;
  const x = baseX + (1 - enter) * 260 * dir - leave * 200 * dir;
  const y = (1 - enter) * 120 - leave * 40 + Math.sin(t * .8) * 6;
  const ry = lerp(-18 * dir, -6 * dir, ease.inOut(clamp(k))) * (side === 'center' ? .4 : 1) + leave * 14 * dir;
  const rx = lerp(14, 4, enter) + leave * 6;
  const sc = baseS * lerp(.88, 1, enter) * lerp(1, 1.04, clamp(k)) * lerp(1, .94, leave);
  s.frame.style.opacity = Math.min(enter * 1.4, 1 - leave);
  s.frame.style.transform = `translate(${x}px, ${y}px) rotateX(${rx}deg) rotateY(${ry}deg) scale(${sc})`;
  // Zoom moves inside the window ("camera into the UI").
  let z = 1, ox = 50, oy = 50;
  for (const [a, b, c, zz, zx, zy] of s.zooms || []) {
    const kin = prog(t, a, a + .8, ease.inOut), kout = prog(t, c - .8, c, ease.inOut);
    const amount = kin * (1 - kout);
    if (amount > 0) { z = lerp(1, zz, amount); ox = zx; oy = zy; }
  }
  s.zoom.style.transformOrigin = `${ox}% ${oy}%`;
  s.zoom.style.transform = `scale(${z})`;
}

function posePanel(s, t) {
  const p = s.panel, { start, end } = s;
  const show = prog(t, start + .3, start + 1.1), hide = prog(t, end - .5, end - .1);
  p.style.opacity = show * (1 - hide);
  p.style.transform = `translateY(${(1 - show) * 30 - hide * 20}px)`;
  p.querySelectorAll('.headline .word').forEach((w, i) => {
    const k = prog(t, start + .45 + i * .07, start + 1.05 + i * .07);
    w.style.opacity = k; w.style.transform = `translateY(${(1 - k) * 40}px)`; w.style.filter = `blur(${(1 - k) * 8}px)`;
  });
  const eyebrow = p.querySelector('.eyebrow'); const ke = prog(t, start + .3, start + .8);
  eyebrow.style.letterSpacing = `${lerp(.4, .14, ke)}em`; eyebrow.style.opacity = ke;
  const sub = p.querySelector('.sub'); const ks = prog(t, start + 1.0, start + 1.6);
  sub.style.opacity = ks; sub.style.transform = `translateY(${(1 - ks) * 16}px)`;
}

async function seek(video, time) {
  time = Math.max(0, Math.min(time, video.duration - .04));
  if (Math.abs(video.currentTime - time) < .001 && video.readyState >= 2) return;
  await new Promise((resolve) => { video.addEventListener('seeked', resolve, { once: true }); video.currentTime = time; });
}

window.ready = () => Promise.all(Object.values(shots).filter((s) => s.video).map((s) => new Promise((resolve) => {
  if (s.video.readyState >= 2) resolve(); else s.video.addEventListener('loadeddata', resolve, { once: true });
}))).then(() => document.fonts.ready);

window.renderAt = async (t) => {
  // Background drift.
  document.getElementById('orbA').style.transform = `translate(${-150 + Math.sin(t * .23) * 220}px, ${-300 + Math.cos(t * .19) * 120}px)`;
  document.getElementById('orbB').style.transform = `translate(${1050 + Math.cos(t * .17) * 240}px, ${100 + Math.sin(t * .21) * 160}px)`;
  document.getElementById('floor').style.backgroundPosition = `0 ${t * 45}px`;
  dots.childNodes.forEach((el, i) => {
    const d = DOTS[i]; const y = (d.y - t * d.v + 1080 * 4) % 1080;
    el.style.transform = `translate(${d.x + Math.sin(t * .5 + i) * 14}px, ${y}px) scale(${d.s})`; el.style.opacity = .15 + .35 * d.s;
  });

  // Intro.
  const [is, ie] = CONFIG.times.intro;
  const iOut = prog(t, ie - .5, ie, ease.inOut);
  intro.style.opacity = 1 - iOut; intro.style.transform = `scale(${lerp(1, 1.06, clamp(t / ie)) + iOut * .25})`;
  intro.style.filter = `blur(${iOut * 14}px)`;
  const mk = prog(t, .25, 1.1, ease.back);
  intro.querySelector('.mark').style.transform = `scale(${mk}) rotate(${(1 - mk) * -30}deg)`;
  intro.querySelectorAll('.title .word').forEach((w, i) => {
    const k = prog(t, .7 + i * .06, 1.3 + i * .06); w.style.opacity = k; w.style.transform = `translateY(${(1 - k) * 70}px)`; w.style.filter = `blur(${(1 - k) * 10}px)`;
  });
  const tk = prog(t, 1.7, 2.4); const tag = intro.querySelector('.tagline'); tag.style.opacity = tk; tag.style.transform = `translateY(${(1 - tk) * 24}px)`;

  // Slam: one line per beat.
  const [ss, se] = CONFIG.times.slam;
  slam.style.display = t >= ss - .1 && t <= se ? 'flex' : 'none';
  [...slam.children].forEach((line, i) => {
    const at = ss + i * CONFIG.beat * 2;
    const k = prog(t, at, at + .35, ease.back), out = prog(t, se - .55, se - .1, ease.inOut);
    line.style.opacity = clamp(k * 1.2) * (1 - out);
    line.style.transform = `scale(${lerp(1.6, 1, clamp(k))}) translateY(${-out * 60}px)`;
    line.style.filter = `blur(${(1 - clamp(k)) * 16 + out * 10}px)`;
  });

  // App shots.
  const seeks = [];
  for (const s of Object.values(shots)) {
    if (!s.frame) continue;
    const active = t >= s.start - .05 && t <= s.end + .05;
    s.frame.style.display = active ? 'block' : 'none';
    if (s.panel) s.panel.style.display = active ? 'flex' : 'none';
    if (!active) continue;
    poseFrame(s, t);
    if (s.panel) posePanel(s, t);
    const f = s.footage, k = clamp((t - s.start) / (s.end - s.start));
    seeks.push(seek(s.video, lerp(f.in, f.out, k)));
  }

  // Workspace lower third: "Write your solution", then "Accepted".
  const ws = shots.workspace;
  const wActive = t >= ws.start && t <= ws.end;
  lower.style.display = wActive ? 'flex' : 'none';
  if (wActive) {
    const acc = CONFIG.acceptedAt;
    const accepted = t >= acc;
    const pill = document.getElementById('lowerPill');
    pill.classList.toggle('ok', accepted);
    pill.querySelector('b').textContent = accepted ? '✓' : '✎';
    document.getElementById('lowerText').textContent = accepted ? 'Accepted' : 'Write your solution';
    document.getElementById('lowerSub').textContent = accepted ? '8 / 8 test cases · each one in its own Docker sandbox' : 'A real code editor, right in the browser';
    const show = prog(t, ws.start + .8, ws.start + 1.4), hide = prog(t, ws.end - .5, ws.end - .1);
    const pop = accepted ? ease.back(clamp((t - acc) / .45)) : 1;
    lower.style.opacity = show * (1 - hide) * (accepted ? clamp((t - acc) / .2) : (t > acc - .5 ? clamp((acc - t) / .3) : 1));
    lower.style.transform = `scale(${accepted ? lerp(.7, 1, pop) : 1})`; lower.style.transformOrigin = '0% 100%';
  }

  // Stack tiles.
  const [ks0, ke0] = CONFIG.times.stack;
  stack.style.display = t >= ks0 - .1 && t <= ke0 + .1 ? 'flex' : 'none';
  const kOut = prog(t, ke0 - .5, ke0, ease.inOut);
  stack.style.opacity = 1 - kOut;
  const st = stack.querySelector('.title'); const kt = prog(t, ks0 + .1, ks0 + .7);
  st.style.opacity = kt; st.style.transform = `translateY(${(1 - kt) * 40}px)`;
  stack.querySelectorAll('.tile').forEach((tile, i) => {
    const k = prog(t, ks0 + .35 + i * .09, ks0 + 1.05 + i * .09, ease.out);
    tile.style.opacity = k; tile.style.transform = `translateZ(${(1 - k) * -500}px) rotateX(${(1 - k) * 35}deg) translateY(${(1 - k) * 60 - kOut * 40}px)`;
  });

  // Outro.
  const [os, oe] = CONFIG.times.outro;
  outro.style.display = t >= os - .1 ? 'flex' : 'none';
  const om = prog(t, os + .2, os + 1.0, ease.back);
  outro.querySelector('.mark').style.transform = `scale(${om})`;
  [...outro.children].slice(1).forEach((el, i) => {
    const k = prog(t, os + .5 + i * .35, os + 1.1 + i * .35); el.style.opacity = k; el.style.transform = `translateY(${(1 - k) * 30}px)`; el.style.filter = `blur(${(1 - k) * 8}px)`;
  });
  document.getElementById('black').style.opacity = prog(t, oe - 1.4, oe, ease.inOut);

  // Transitions on every cut: a quick flash and a light sweep.
  let flash = 0, sweepK = -1;
  for (const cut of CONFIG.cuts) {
    flash = Math.max(flash, Math.exp(-Math.pow((t - cut) / .07, 2)) * .28);
    if (t > cut - .35 && t < cut + .35) sweepK = (t - (cut - .35)) / .7;
  }
  const acc = CONFIG.acceptedAt;
  flash = Math.max(flash, Math.exp(-Math.pow((t - acc) / .09, 2)) * .22);
  document.getElementById('flash').style.opacity = flash;
  const sweep = document.getElementById('sweep');
  sweep.style.opacity = sweepK >= 0 ? Math.sin(sweepK * Math.PI) * .9 : 0;
  sweep.style.transform = `translateX(${lerp(-500, 2300, clamp(sweepK))}px) rotate(18deg)`;

  await Promise.all(seeks);
};
</script></body></html>"""

TILES = [
    ("API", "FastAPI", "Python REST API, JWT auth, student and admin roles"),
    ("DB", "PostgreSQL", "SQLAlchemy 2.0 models and Alembic migrations"),
    ("Q", "Redis + RQ", "Submissions queued and judged by workers"),
    ("[ ]", "Docker sandbox", "A fresh locked-down container per test case"),
    ("UI", "React + Monaco", "LeetCode-style editor, light and dark mode"),
    ("◇", "Mermaid", "A flowchart for every solution"),
    ("TLS", "Caddy", "HTTPS, compression and security headers"),
    ("✓", "662 tests", "75 problems and 681 test cases, all verified"),
]
TABS = {"landing": "Home", "dashboard": "Dashboard", "problems": "Problems", "workspace": "Two Sum",
        "solution": "Two Sum · Solution guide", "admin": "Admin console"}


def build_config(footage):
    times = {name: (start, end) for name, start, end in SHOTS}
    shots = []
    for name, start, end in SHOTS:
        if name not in footage:
            continue
        shot = {"name": name, "start": start, "end": end, "footage": footage[name], "tab": TABS[name],
                "copy": list(COPY[name]) if name in COPY else None, "zooms": []}
        shots.append(shot)
    work = next(s for s in shots if s["name"] == "workspace")
    f = work["footage"]
    rate = (f["out"] - f["in"]) / (work["end"] - work["start"])
    # The verdict appears about 2.9 s before the recording ends (record.py waits there).
    accepted = work["start"] + (f["length"] - 2.9 - f["in"]) / rate
    accepted = min(max(accepted, work["start"] + 4), work["end"] - 1.5)
    typing = (work["start"] + 1.2, accepted - 2.6)
    # Camera: push into the editor while typing, then punch in on the verdict.
    work["zooms"] = [[typing[0], typing[0] + .1, typing[1] + .4, 1.45, 76, 22], [accepted - .1, accepted, work["end"] - .3, 1.75, 76, 74]]
    for shot in shots:
        if shot["name"] == "dashboard":
            shot["zooms"] = [[shot["start"] + 2.6, 0, shot["end"] - .6, 1.3, 50, 26]]
        if shot["name"] == "solution":
            shot["zooms"] = [[shot["start"] + 2.4, 0, shot["end"] - .6, 1.25, 26, 60]]
    cuts = [start for _, start, _ in SHOTS[1:]]
    return {
        "shots": shots, "times": times, "tiles": TILES, "cuts": cuts, "beat": music.BEAT, "acceptedAt": accepted,
    }, accepted, typing, cuts


async def render(config):
    frames = STAGE / "frames"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True)
    (STAGE / "stage.html").write_text(STAGE_HTML.replace("__CONFIG__", json.dumps(config)), encoding="utf-8")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(args=["--autoplay-policy=no-user-gesture-required", "--force-color-profile=srgb"])
        page = await browser.new_page(viewport={"width": W, "height": H})
        await page.goto((STAGE / "stage.html").as_uri())
        await page.evaluate("window.ready()")
        count = int(round(TOTAL * FPS))
        for i in range(count):
            await page.evaluate("(t) => window.renderAt(t)", i / FPS)
            await page.screenshot(path=str(frames / f"{i:05d}.jpg"), type="jpeg", quality=92)
            if i % 150 == 0:
                print(f"frame {i}/{count}", flush=True)
        await browser.close()
    return frames


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    fetch_fonts()
    footage = prepare_footage()
    config, accepted, typing, cuts = build_config(footage)
    print(f"accepted at {accepted:.2f}s, typing {typing[0]:.2f}-{typing[1]:.2f}s", flush=True)

    score = music.compose(
        TOTAL + 0.5, cuts=cuts, impacts=[SHOTS[2][1], accepted, SHOTS[-1][1]], typing=[typing], accepted=accepted,
        beat_start=SHOTS[2][1], beat_end=SHOTS[-2][2], arp_start=SHOTS[5][1], arp_end=SHOTS[-2][2],
    )
    audio = STAGE / "music.wav"
    music.write_wav(audio, score)
    print("music done", flush=True)

    frames = asyncio.run(render(config))
    target = OUT / "algoforge-cinematic.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "%05d.jpg"), "-i", str(audio),
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-profile:v", "high",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(target)],
        check=True,
    )
    shutil.copy(audio, OUT / "algoforge-soundtrack.wav")
    print(f"wrote {target} ({TOTAL:.1f} s, {target.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
