"""Controlled narrated rendering test. No scheduler, upload or network listener."""
import json
import subprocess
from pathlib import Path
from providers.groq_voice import split_text, synthesize


FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def run(text, directory):
    """Generate narration and combine it with a minimal animated test scene."""
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    if len(split_text(text)) != 1:
        raise ValueError('This test accepts a single voice segment of up to 200 characters')
    pieces = synthesize(text, root)
    audio = pieces[0]
    duration = float(json.loads(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', audio],
        capture_output=True, text=True, check=True, timeout=30).stdout)['format']['duration'])
    if not 0 < duration <= 60:
        raise ValueError('Unexpected audio duration')
    target = root / 'narrated_test.mp4'
    effect = ("drawbox=x='80+120*sin(t)':y=510:w=160:h=160:color=0x1663a6:t=fill,"
              "drawtext=fontfile=" + FONT + ":text='PizarrIA':fontcolor=black:fontsize=58:x=(w-text_w)/2:y=200")
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y',
        '-f','lavfi','-i',f'color=c=white:s=720x1280:r=24:d={duration:.3f}',
        '-i',audio,'-vf',effect,'-c:v','libx264','-threads','1','-preset','ultrafast',
        '-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-shortest','-movflags','+faststart',
        str(target)], check=True, timeout=600)
    probe = subprocess.run(['ffprobe','-v','error','-show_entries',
        'format=duration,size:stream=codec_name,codec_type,width,height','-of','json',str(target)],
        capture_output=True, text=True, check=True, timeout=30)
    return {'path': str(target), 'audio_seconds': duration, 'probe': json.loads(probe.stdout)}

