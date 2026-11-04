"""One-time cloud benchmark, not a production application."""
import json, os, subprocess, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

root = Path('/tmp/autofactory-benchmark')
root.mkdir(exist_ok=True)
video = root / 'test.mp4'
state = {'status': 'starting', 'resolution': '720x1280', 'seconds': 35}

def render():
    start = time.monotonic()
    state['status'] = 'rendering'
    vf = "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='■':fontcolor=0x1976d2:fontsize=120:x='50+14*t':y=425,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='AUTOFACTORY':fontcolor=black:fontsize=46:x=(w-text_w)/2:y=230,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='Cloud render test':fontcolor=black:fontsize=28:x=(w-text_w)/2:y=305"
    cmd = ['ffmpeg','-hide_banner','-y','-f','lavfi','-i','color=c=white:s=720x1280:r=24:d=35','-f','lavfi','-i','sine=frequency=440:sample_rate=44100:duration=35','-vf',vf,'-c:v','libx264','-threads','1','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-b:a','96k','-shortest','-movflags','+faststart',str(video)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=True)
        probe = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration,size:stream=codec_name,codec_type,width,height','-of','json',str(video)],capture_output=True,text=True,timeout=30,check=True)
        state.update(status='complete', render_seconds=round(time.monotonic()-start,2), probe=json.loads(probe.stdout))
    except Exception as exc:
        state.update(status='failed', error=str(exc), render_seconds=round(time.monotonic()-start,2))

class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        path = self.path.split('?',1)[0]
        if path == '/video.mp4' and state['status'] == 'complete':
            data = video.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','video/mp4')
            self.send_header('Content-Length',str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path in ('/','/status'):
            body = json.dumps(state).encode()
            self.send_response(200)
            self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

threading.Thread(target=render, daemon=True).start()
ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','10000'))),Handler).serve_forever()
