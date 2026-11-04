"""Groq Orpheus test adapter. Requires a free-tier key; no automatic execution."""
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = 'https://api.groq.com/openai/v1/audio/speech'
MODEL = 'canopylabs/orpheus-v1-english'
VOICES = {'autumn', 'diana', 'hannah', 'austin', 'daniel', 'troy'}

def split_text(text, limit=200):
    if not text.strip():
        raise ValueError('Narration cannot be empty')
    words = re.findall(r'\S+', text)
    parts, current = [], ''
    for word in words:
        if len(word) > limit:
            raise ValueError('A word exceeds the API character limit')
        candidate = (current + ' ' + word).strip()
        if len(candidate) > limit:
            parts.append(current)
            current = word
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts

def synthesize(text, output_dir, voice='troy'):
    if voice not in VOICES:
        raise ValueError('Unknown voice')
    key = os.environ.get('GROQ_API_KEY')
    if not key:
        raise RuntimeError('GROQ_API_KEY is not configured')
    parts = split_text(text)
    if len(parts) > 12:
        raise ValueError('Test limited to 12 requests')
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = []
    for index, part in enumerate(parts, start=1):
        payload = json.dumps({'model': MODEL, 'input': part, 'voice': voice, 'response_format': 'wav'}).encode()
        request = urllib.request.Request(ENDPOINT, data=payload, headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                audio = response.read(20_000_000)
        except urllib.error.HTTPError as exc:
            raise RuntimeError('Groq request failed with HTTP ' + str(exc.code)) from None
        if not audio.startswith(b'RIFF') or audio[8:12] != b'WAVE':
            raise RuntimeError('Provider did not return a WAV file')
        path = destination / ('voice_%03d.wav' % index)
        path.write_bytes(audio)
        outputs.append(str(path))
    return outputs
