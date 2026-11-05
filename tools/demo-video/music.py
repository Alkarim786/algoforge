"""An original soundtrack for the cinematic cut, synthesized with numpy (no samples, so no licensing questions).

A minor at 100 BPM (one bar = 2.4 s), chords Am - F - C - G. The structure follows cinema.py's timeline: a soft pad
and a riser for the intro, drums and bass when the app appears, an arpeggio for the editor scene, impacts on the big
moments, whooshes on every cut, typing ticks and a chime when the solution is Accepted, then a calm outro.
"""
import wave

import numpy as np

SR = 44100
BPM = 100
BEAT = 60 / BPM
BAR = BEAT * 4
CHORDS = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am, F, C, G (MIDI)
BASS = [33, 29, 36, 31]
rng = np.random.default_rng(7)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def lowpass(x, cutoff, order=2):
    spectrum = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    spectrum *= 1 / np.sqrt(1 + (freqs / cutoff) ** (2 * order))
    return np.fft.irfft(spectrum, len(x))


def highpass(x, cutoff):
    spectrum = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    spectrum *= 1 - 1 / np.sqrt(1 + (freqs / cutoff) ** 4)
    return np.fft.irfft(spectrum, len(x))


def reverb(x, seconds=2.2, decay=0.45, mix=0.35):
    length = int(seconds * SR)
    impulse = rng.standard_normal(length) * np.exp(-np.arange(length) / (decay * SR))
    impulse = lowpass(impulse, 6000)
    impulse /= np.sqrt(np.sum(impulse ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + length)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(impulse, size), size)[: len(x)]
    return (1 - mix) * x + mix * wet


def env(n, attack, release, sustain_level=1.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.clip((n / SR - t) / max(release, 1e-4), 0, 1)
    return a * r * sustain_level


def place(track, start, sound):
    i = int(start * SR)
    if i >= len(track):
        return
    j = min(len(track), i + len(sound))
    track[i:j] += sound[: j - i]


def saw(freq, n, detune=0.0, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * freq * (1 + detune) + phase) % 1) - 1


def compose(total, cuts, impacts, typing, accepted, beat_start, beat_end, arp_start, arp_end):
    n = int(total * SR)
    pad, bass, drums, arp, fx = (np.zeros(n) for _ in range(5))

    # Pads: three detuned saws per note, filtered warm, one chord per bar.
    bars = int(np.ceil(total / BAR))
    for bar in range(bars):
        start, length = bar * BAR, int(BAR * SR) + int(0.4 * SR)
        chord = CHORDS[bar % 4]
        voice = np.zeros(length)
        for note in chord + [chord[0] + 12]:
            for detune in (-0.004, 0.0, 0.005):
                voice += saw(hz(note), length, detune, rng.random())
        voice *= env(length, 0.6, 0.8) / 12
        place(pad, start, voice)
    pad = lowpass(pad, 1400)

    # Bass: eighth-note pluck on the chord root, from the drop.
    eighth = BEAT / 2
    t = beat_start
    while t < beat_end:
        bar = int(t / BAR)
        length = int(eighth * SR)
        tone = np.sin(2 * np.pi * hz(BASS[bar % 4]) * np.arange(length) / SR)
        tone += 0.35 * saw(hz(BASS[bar % 4]), length)
        place(bass, t, tone * np.exp(-np.arange(length) / (0.16 * SR)) * 0.55)
        t += eighth
    bass = lowpass(bass, 500)

    # Drums: kick on every beat, hats on the off-beats, a clap on 2 and 4.
    kick_len = int(0.45 * SR)
    k = np.arange(kick_len) / SR
    kick = np.sin(2 * np.pi * (45 * k + (110 / 18) * (1 - np.exp(-18 * k)))) * np.exp(-k / 0.18)
    hat = highpass(rng.standard_normal(int(0.05 * SR)), 7000) * np.exp(-np.arange(int(0.05 * SR)) / (0.012 * SR))
    clap = highpass(rng.standard_normal(int(0.2 * SR)), 1200) * np.exp(-np.arange(int(0.2 * SR)) / (0.05 * SR))
    beat_index = 0
    t = beat_start
    while t < beat_end - 1e-6:
        place(drums, t, kick * 0.9)
        place(drums, t + BEAT / 2, hat * 0.22)
        if beat_index % 2 == 1:
            place(drums, t, clap * 0.32)
        t += BEAT
        beat_index += 1

    # Arpeggio: chord tones in sixteenths, for the editor scene.
    sixteenth = BEAT / 4
    t, step = arp_start, 0
    while t < arp_end:
        chord = CHORDS[int(t / BAR) % 4]
        note = (chord + [chord[0] + 12])[[0, 1, 2, 3, 2, 1][step % 6]] + 12
        length = int(0.22 * SR)
        tone = np.sin(2 * np.pi * hz(note) * np.arange(length) / SR) + 0.3 * saw(hz(note), length)
        place(arp, t, tone * np.exp(-np.arange(length) / (0.07 * SR)) * 0.22)
        t += sixteenth
        step += 1
    arp = reverb(lowpass(arp, 3200), mix=0.3)

    # Effects: whoosh into every cut, impacts, riser, typing ticks, the Accepted chime.
    for cut in cuts:
        length = int(0.7 * SR)
        noise = rng.standard_normal(length)
        sweep = lowpass(noise, 2500) * np.sin(np.linspace(0, np.pi, length)) ** 2
        place(fx, cut - 0.55, sweep * 0.16)
    for hit in impacts:
        length = int(1.6 * SR)
        h = np.arange(length) / SR
        boom = np.sin(2 * np.pi * (32 * h + 40 * (1 - np.exp(-6 * h)) / 6)) * np.exp(-h / 0.5)
        crack = lowpass(rng.standard_normal(length), 3000) * np.exp(-h / 0.12)
        place(fx, hit, boom * 0.8 + crack * 0.25)
    rise_len = int(2.4 * SR)
    riser = rng.standard_normal(rise_len)
    riser = lowpass(riser, 4000) * np.linspace(0, 1, rise_len) ** 2.2
    place(fx, beat_start - 2.4, riser * 0.22)
    for start, end in typing:
        t = start
        while t < end:
            tick = highpass(rng.standard_normal(int(0.012 * SR)), 3000) * np.exp(-np.arange(int(0.012 * SR)) / (0.003 * SR))
            place(fx, t, tick * 0.12)
            t += 0.05 + rng.random() * 0.06
    if accepted is not None:
        length = int(2.4 * SR)
        c = np.arange(length) / SR
        chime = sum(np.sin(2 * np.pi * f * c) * amp for f, amp in ((880, 0.5), (1318.5, 0.35), (1760, 0.2)))
        place(fx, accepted, chime * np.exp(-c / 0.6) * 0.35)

    pad, fx = reverb(pad, mix=0.4), reverb(fx, mix=0.25)
    # Duck the pad a little under each kick, for movement.
    duck = np.ones(n)
    t = beat_start
    while t < beat_end:
        i = int(t * SR)
        length = min(int(BEAT * SR), n - i)
        duck[i : i + length] = 1 - 0.35 * np.exp(-np.arange(length) / (0.12 * SR))
        t += BEAT

    mix = pad * duck * 0.5 + bass * 0.7 + drums * 0.55 + arp * 0.8 + fx
    fade = np.ones(n)
    fade[: int(1.0 * SR)] = np.linspace(0, 1, int(1.0 * SR))
    tail = int(3.0 * SR)
    fade[-tail:] = np.linspace(1, 0, tail) ** 1.5
    mix *= fade
    # A little stereo width: the right channel is a few milliseconds behind on the pad and arpeggio.
    wide = np.roll(pad * duck * 0.5 + arp * 0.8, int(0.012 * SR))
    left = mix
    right = mix - (pad * duck * 0.5 + arp * 0.8) * 0.5 + wide * 0.5
    stereo = np.stack([left, right], axis=1)
    stereo = np.tanh(stereo / np.max(np.abs(stereo)) * 1.3)
    return stereo / np.max(np.abs(stereo)) * 0.95


def write_wav(path, stereo):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(SR)
        file.writeframes(data.tobytes())
