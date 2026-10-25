import math
import random
import struct
import wave
from pathlib import Path

from config import SOUNDS_DIR

SAMPLE_RATE = 22050
DEFAULT_DURATION = 12.0
CROSSFADE_SECONDS = 0.35
TAU = math.tau

SOUND_PROFILES = [
    {
        'slug': 'calm-tide',
        'title': 'Calm tide',
        'category': 'Calm',
        'icon': '🌊',
        'description': 'A slow, warm pad for loosening your shoulders.',
        'kind': 'pad',
        'duration': 12.0,
        'frequencies': [130.8125, 164.8125, 196.0, 261.625],
        'volume': 0.55,
        'drift': 0.22,
    },
    {
        'slug': 'deep-focus',
        'title': 'Deep focus',
        'category': 'Focus',
        'icon': '🎯',
        'description': 'A steady, low pulse for one task at a time.',
        'kind': 'pulse',
        'duration': 12.0,
        'frequencies': [110.0, 220.0, 330.0],
        'volume': 0.46,
        'drift': 0.08,
        'beat': 0.5,
    },
    {
        'slug': 'sleep-drift',
        'title': 'Sleep drift',
        'category': 'Sleep',
        'icon': '🌙',
        'description': 'A very low, slow pad for winding down at night.',
        'kind': 'pad',
        'duration': 20.0,
        'frequencies': [65.4, 98.0, 130.8, 196.0],
        'volume': 0.5,
        'drift': 0.12,
    },
    {
        'slug': 'four-six-breath',
        'title': 'Four-six breathing',
        'category': 'Breathe',
        'icon': '🌬️',
        'description': 'A soft swell that guides a slower out-breath.',
        'kind': 'swell',
        'duration': 20.0,
        'frequencies': [130.8, 196.0, 261.6],
        'volume': 0.44,
        'drift': 0.06,
        'breath_cycles': 2,
        'noise': 0.04,
    },
    {
        'slug': 'grounding-hum',
        'title': 'Grounding hum',
        'category': 'Ground',
        'icon': '🌳',
        'description': 'A low, even hum to anchor a spiralling moment.',
        'kind': 'pad',
        'duration': 16.0,
        'frequencies': [55.0, 82.5, 110.0, 164.8],
        'volume': 0.56,
        'drift': 0.08,
    },
    {
        'slug': 'rain-on-leaves',
        'title': 'Rain on leaves',
        'category': 'Nature',
        'icon': '🌧️',
        'description': 'Soft rain texture with a warm pad underneath.',
        'kind': 'rain',
        'duration': 16.0,
        'frequencies': [196.0, 261.6],
        'volume': 0.48,
        'drift': 0.1,
        'noise': 0.55,
        'noise_mode': 'brown',
        'noise_tone': 196.0,
    },
    {
        'slug': 'ocean-breath',
        'title': 'Ocean breath',
        'category': 'Nature',
        'icon': '🌊',
        'description': 'Slow wave swells with a low, rounded tone.',
        'kind': 'ocean',
        'duration': 20.0,
        'frequencies': [65.4, 98.0, 130.8],
        'volume': 0.5,
        'drift': 0.12,
        'noise': 0.5,
        'noise_mode': 'brown',
        'noise_tone': 98.0,
    },
    {
        'slug': 'brown-noise',
        'title': 'Brown noise',
        'category': 'Noise',
        'icon': '🟤',
        'description': 'A warm, low hiss that masks background sound.',
        'kind': 'noise',
        'duration': 16.0,
        'frequencies': [65.4, 98.0],
        'volume': 0.46,
        'drift': 0.05,
        'noise': 0.55,
        'noise_mode': 'brown',
        'noise_tone': 65.4,
    },
    {
        'slug': 'pink-noise',
        'title': 'Pink noise',
        'category': 'Noise',
        'icon': '🌸',
        'description': 'A softer, balanced hiss for busy rooms.',
        'kind': 'noise',
        'duration': 16.0,
        'frequencies': [82.5, 130.8],
        'volume': 0.42,
        'drift': 0.04,
        'noise': 0.5,
        'noise_mode': 'pink',
        'noise_tone': 82.5,
    },
]


def _quantize(frequency, duration):
    return max(1, round(frequency * duration)) / duration


def _weights(count):
    if count == 1:
        return [1.0]
    return [1.0 - 0.55 * (index / (count - 1)) for index in range(count)]


def _breath_envelope(t, duration, cycles):
    phase = (t * cycles / duration) % 1.0
    if phase < 0.4:
        shaped = 0.5 - 0.5 * math.cos(math.pi * phase / 0.4)
    else:
        shaped = 0.5 + 0.5 * math.cos(math.pi * (phase - 0.4) / 0.6)
    return max(0.0, min(1.0, shaped))


def _noise_sample(mode, white, state):
    if mode == 'brown':
        state[0] = state[0] * 0.995 + white * 0.05
        return state[0] * 4.0
    if mode == 'pink':
        state[0] += 0.10 * (white - state[0])
        state[1] += 0.025 * (white - state[1])
        state[2] += 0.006 * (white - state[2])
        return (state[0] + state[1] + state[2]) * 1.6
    state[0] += 0.18 * (white - state[0])
    return state[0] * 1.5


def _render(profile):
    duration = float(profile.get('duration', DEFAULT_DURATION))
    kind = profile.get('kind', 'pad')
    volume = float(profile.get('volume', 0.5))
    drift = float(profile.get('drift', 0.12))
    frequencies = [_quantize(float(f), duration) for f in profile.get('frequencies', [])]
    weights = profile.get('weights') or _weights(len(frequencies))
    normalizer = sum(weights) or 1.0
    rng = random.Random(profile.get('slug', 'sound'))
    crossfade = int(CROSSFADE_SECONDS * SAMPLE_RATE)
    frames_count = int(duration * SAMPLE_RATE)
    total_count = frames_count + crossfade
    noise_state = [0.0, 0.0, 0.0]
    drift_cycles = max(1, round(duration / 7.0))
    beat = float(profile.get('beat', 0.5))
    noise_level = float(profile.get('noise', 0.0))
    noise_mode = profile.get('noise_mode', 'brown')
    noise_freq = _quantize(float(profile.get('noise_tone', frequencies[0] if frequencies else 110.0)), duration)
    chime_times = [float(item) for item in profile.get('chimes', [])]
    chime_freqs = [_quantize(float(item), duration) for item in profile.get('chime_frequencies', frequencies)]
    frames = [0.0] * total_count

    for index in range(total_count):
        t = index / SAMPLE_RATE
        pad = 0.0
        for freq, weight in zip(frequencies, weights):
            pad += math.sin(TAU * freq * t) * weight
        pad = pad / normalizer
        modulation = 1.0 - drift + drift * (0.5 + 0.5 * math.sin(TAU * drift_cycles * t / duration))

        sample = pad * modulation

        if kind == 'pulse':
            phase = (t * beat) % 1.0
            pluck = math.sin(TAU * (frequencies[0] if frequencies else 110.0) * t)
            envelope = math.exp(-7.0 * phase) * min(1.0, phase / 0.03)
            sample += pluck * envelope * 0.34

        elif kind == 'swell':
            cycles = float(profile.get('breath_cycles', 2))
            sample *= 0.15 + 0.85 * _breath_envelope(t, duration, cycles)

        elif kind in ('noise', 'rain', 'ocean'):
            white = rng.uniform(-1.0, 1.0)
            noise = _noise_sample(noise_mode, white, noise_state)
            if kind == 'rain':
                wave_shape = 0.55 + 0.45 * math.sin(TAU * 2 * t / duration)
                noise *= wave_shape
                sample = pad * 0.16 + noise * 0.52
            elif kind == 'ocean':
                swell = 0.18 + 0.82 * (0.5 + 0.5 * math.sin(TAU * 3 * t / duration - math.pi / 2))
                noise *= swell
                sample = pad * 0.28 + noise * 0.5
            else:
                sample = pad * 0.18 + noise * max(noise_level, 0.45)
            sample += math.sin(TAU * noise_freq * t) * 0.035

        elif kind == 'chime':
            sample = pad * 0.5
            for chime_index, start in enumerate(chime_times):
                if t < start:
                    continue
                elapsed = t - start
                chime_freq = chime_freqs[chime_index % len(chime_freqs)]
                bell = math.sin(TAU * chime_freq * elapsed) + 0.35 * math.sin(TAU * chime_freq * 2.01 * elapsed)
                sample += bell * math.exp(-1.8 * elapsed) * 0.16

        frames[index] = math.tanh(sample * volume * 1.6)

    for index in range(crossfade):
        mix = index / max(1, crossfade - 1)
        frames[index] = frames[index] * mix + frames[frames_count + index] * (1.0 - mix)

    return frames[:frames_count]


def write_sound(profile, directory=None):
    target_dir = Path(directory) if directory is not None else SOUNDS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{profile['slug']}.wav"
    frames = _render(profile)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        payload = bytearray()
        for sample in frames:
            payload.extend(struct.pack('<h', int(max(-1.0, min(1.0, sample)) * 32767)))
        handle.writeframes(bytes(payload))
    return path


def ensure_builtin_sounds(directory=None, profiles=None):
    target_dir = Path(directory) if directory is not None else SOUNDS_DIR
    selected = profiles or SOUND_PROFILES
    written = []
    for profile in selected:
        path = target_dir / f"{profile['slug']}.wav"
        if not path.exists():
            path = write_sound(profile, target_dir)
            written.append(path)
    return written


def sound_cards():
    return [
        {
            **profile,
            'url': f"/static/sounds/{profile['slug']}.wav",
        }
        for profile in SOUND_PROFILES
    ]
