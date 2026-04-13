from flask import Flask, request, jsonify, Response
import requests
import re

app = Flask(__name__)

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<meta name="mobile-web-app-capable" content="yes">
<title>YTSave</title>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0f0f0f; --surface: #1a1a1a; --card: #222; --border: #333;
  --red: #ff0000; --red2: #ff4444; --text: #fff; --muted: #888;
  --glow: rgba(255,0,0,0.3);
}
* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
body { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; min-height:100vh; }
body::before { content:''; position:fixed; top:0; left:0; right:0; height:400px; background:radial-gradient(ellipse at 50% -20%, rgba(255,0,0,0.08) 0%, transparent 70%); pointer-events:none; }
.app { max-width:480px; margin:0 auto; padding:0 0 40px; position:relative; }
.header { padding:28px 20px 20px; text-align:center; }
.logo { font-family:'Oswald',sans-serif; font-size:38px; font-weight:700; letter-spacing:4px; display:inline-flex; align-items:center; gap:10px; }
.logo-icon { width:36px; height:36px; background:var(--red); border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px; }
.logo-yt { color:var(--red); } .logo-save { color:var(--text); }
.tagline { color:var(--muted); font-size:13px; margin-top:6px; letter-spacing:1px; }
.input-section { padding:0 16px 20px; }
.url-box { background:var(--surface); border:1px solid var(--border); border-radius:18px; padding:6px 6px 6px 18px; display:flex; align-items:center; gap:10px; transition:border-color .2s; }
.url-box:focus-within { border-color:var(--red); }
.url-input { flex:1; background:none; border:none; color:var(--text); font-size:14px; font-family:'DM Sans',sans-serif; outline:none; padding:10px 0; }
.url-input::placeholder { color:var(--muted); }
.btn-fetch { background:var(--red); border:none; border-radius:13px; padding:12px 20px; color:#fff; font-size:14px; font-weight:600; font-family:'Oswald',sans-serif; letter-spacing:1px; cursor:pointer; transition:all .2s; white-space:nowrap; display:flex; align-items:center; gap:6px; }
.btn-fetch:active { transform:scale(.95); } .btn-fetch:disabled { opacity:.5; cursor:not-allowed; }
.video-card { margin:0 16px 20px; background:var(--surface); border:1px solid var(--border); border-radius:20px; overflow:hidden; display:none; }
.video-card.show { display:block; animation:fadeIn .3s ease; }
@keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
.thumb-wrap { position:relative; }
.thumb { width:100%; aspect-ratio:16/9; object-fit:cover; display:block; }
.thumb-overlay { position:absolute; inset:0; background:linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 50%); }
.video-info { padding:16px; }
.video-title { font-family:'Oswald',sans-serif; font-size:17px; font-weight:500; line-height:1.3; margin-bottom:6px; }
.video-channel { font-size:12px; color:var(--muted); }
.format-section { padding:14px 16px 0; }
.format-label { font-size:10px; color:var(--muted); letter-spacing:2px; text-transform:uppercase; margin-bottom:10px; }
.format-grid { display:flex; flex-wrap:wrap; gap:8px; }
.fmt-btn { padding:10px 16px; background:var(--card); border:1px solid var(--border); border-radius:12px; color:var(--muted); font-size:13px; font-weight:500; font-family:'DM Sans',sans-serif; cursor:pointer; transition:all .2s; }
.fmt-btn.active { background:rgba(255,0,0,0.15); border-color:var(--red); color:var(--red); }
.fmt-btn:active { transform:scale(.95); }
.btn-download { margin:16px; width:calc(100% - 32px); padding:17px; background:var(--red); border:none; border-radius:16px; color:#fff; font-size:18px; font-weight:600; font-family:'Oswald',sans-serif; letter-spacing:2px; cursor:pointer; transition:all .2s; box-shadow:0 4px 30px var(--glow); display:flex; align-items:center; justify-content:center; gap:8px; }
.btn-download:active { transform:scale(.97); } .btn-download:disabled { opacity:.5; cursor:not-allowed; }
.ready-section { margin:0 16px 20px; background:var(--surface); border:1px solid #1a4a1a; border-radius:20px; padding:20px; display:none; text-align:center; }
.ready-section.show { display:block; animation:fadeIn .3s ease; }
.ready-icon { font-size:48px; margin-bottom:10px; }
.ready-title { font-family:'Oswald',sans-serif; font-size:20px; color:#4caf50; margin-bottom:6px; }
.ready-sub { font-size:13px; color:var(--muted); margin-bottom:16px; }
.btn-save { display:inline-block; padding:14px 32px; background:#4caf50; border:none; border-radius:14px; color:#fff; font-size:16px; font-weight:600; font-family:'Oswald',sans-serif; letter-spacing:1px; cursor:pointer; text-decoration:none; transition:all .2s; }
.btn-save:active { transform:scale(.97); }
.btn-another { margin-top:10px; background:none; border:none; color:var(--muted); font-size:13px; cursor:pointer; font-family:'DM Sans',sans-serif; }
.error-box { margin:0 16px 20px; background:#1a0a0a; border:1px solid #4a1a1a; border-radius:16px; padding:16px; color:#ff6b6b; font-size:13px; display:none; text-align:center; }
.error-box.show { display:block; }
.tips { padding:0 16px; }
.tip-title { font-size:10px; color:var(--muted); letter-spacing:2px; text-transform:uppercase; margin-bottom:10px; }
.tip-item { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:14px; margin-bottom:8px; display:flex; align-items:center; gap:12px; }
.tip-icon { font-size:22px; flex-shrink:0; }
.tip-text { font-size:13px; color:var(--muted); line-height:1.5; }
.spinner { width:18px; height:18px; border:2px solid rgba(255,255,255,.3); border-top-color:#fff; border-radius:50%; animation:spin .7s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }
.loading-section { margin:0 16px 20px; background:var(--surface); border:1px solid var(--border); border-radius:20px; padding:24px; display:none; text-align:center; }
.loading-section.show { display:block; }
.loading-big { width:48px; height:48px; border:3px solid rgba(255,0,0,.2); border-top-color:var(--red); border-radius:50%; animation:spin .8s linear infinite; margin:0 auto 16px; }
.loading-text { font-family:'Oswald',sans-serif; font-size:18px; color:var(--muted); }
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <div class="logo">
      <div class="logo-icon">▶</div>
      <span class="logo-yt">YT</span><span class="logo-save">SAVE</span>
    </div>
    <div class="tagline">PERSONAL VIDEO DOWNLOADER</div>
  </div>

  <div class="input-section">
    <div class="url-box">
      <input class="url-input" id="urlInput" type="url" placeholder="Paste YouTube URL here...">
      <button class="btn-fetch" id="fetchBtn" onclick="fetchInfo()">
        <span id="fetchBtnText">FETCH</span>
      </button>
    </div>
  </div>

  <div class="error-box" id="errorBox"></div>

  <div class="video-card" id="videoCard">
    <div class="thumb-wrap">
      <img class="thumb" id="videoThumb" src="" alt="">
      <div class="thumb-overlay"></div>
    </div>
    <div class="video-info">
      <div class="video-title" id="videoTitle"></div>
      <div class="video-channel" id="videoChannel"></div>
    </div>
    <div class="format-section">
      <div class="format-label">Select Quality</div>
      <div class="format-grid" id="formatGrid"></div>
    </div>
    <button class="btn-download" id="downloadBtn" onclick="startDownload()">⬇ DOWNLOAD</button>
  </div>

  <div class="loading-section" id="loadingSection">
    <div class="loading-big"></div>
    <div class="loading-text">Processing...</div>
  </div>

  <div class="ready-section" id="readySection">
    <div class="ready-icon">✅</div>
    <div class="ready-title">READY TO SAVE!</div>
    <div class="ready-sub" id="readyFilename"></div>
    <a class="btn-save" id="saveLink" href="#" target="_blank">⬇ SAVE FILE</a>
    <br>
    <button class="btn-another" onclick="reset()">← Download another</button>
  </div>

  <div class="tips" id="tipsSection">
    <div class="tip-title">HOW TO USE</div>
    <div class="tip-item"><div class="tip-icon">📋</div><div class="tip-text">Copy any YouTube video URL and paste it above</div></div>
    <div class="tip-item"><div class="tip-icon">🎬</div><div class="tip-text">Choose your quality — 1080p, 720p, 480p or MP3 audio only</div></div>
    <div class="tip-item"><div class="tip-icon">💾</div><div class="tip-text">Tap Download and save directly to your device</div></div>
    <div class="tip-item"><div class="tip-icon">🔒</div><div class="tip-text">Personal use only — your private downloader</div></div>
  </div>
</div>

<script>
const SERVER = window.location.origin;
let selectedFormat = null;

async function fetchInfo() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { showError('Please paste a YouTube URL first'); return; }
  const btn = document.getElementById('fetchBtn');
  document.getElementById('fetchBtnText').innerHTML = '<div class="spinner"></div>';
  btn.disabled = true;
  hideError(); hideAll();
  try {
    const res = await fetch(`${SERVER}/info`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url})
    });
    const data = await res.json();
    if (data.error) { showError(data.error); return; }
    document.getElementById('videoThumb').src = data.thumbnail;
    document.getElementById('videoTitle').textContent = data.title;
    document.getElementById('videoChannel').textContent = '📺 ' + data.channel;
    const grid = document.getElementById('formatGrid');
    grid.innerHTML = '';
    data.formats.forEach(f => {
      const b = document.createElement('button');
      b.className = 'fmt-btn'; b.textContent = f.label;
      b.onclick = () => selectFormat(f, b);
      grid.appendChild(b);
    });
    if (data.formats.length > 0) selectFormat(data.formats[0], grid.querySelector('.fmt-btn'));
    document.getElementById('videoCard').classList.add('show');
    document.getElementById('tipsSection').style.display = 'none';
  } catch(e) { showError('Failed to fetch. Check the URL and try again.'); }
  document.getElementById('fetchBtnText').textContent = 'FETCH';
  btn.disabled = false;
}

function selectFormat(fmt, btn) {
  selectedFormat = fmt;
  document.querySelectorAll('.fmt-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

async function startDownload() {
  if (!selectedFormat) { showError('Select a quality first'); return; }
  const url = document.getElementById('urlInput').value.trim();
  const btn = document.getElementById('downloadBtn');
  btn.innerHTML = '<div class="spinner"></div> PROCESSING...';
  btn.disabled = true;
  document.getElementById('videoCard').classList.remove('show');
  document.getElementById('loadingSection').classList.add('show');
  try {
    const res = await fetch(`${SERVER}/download`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({url, format: selectedFormat.height || 'mp3'})
    });
    const data = await res.json();
    document.getElementById('loadingSection').classList.remove('show');
    if (data.error) {
      showError(data.error);
      document.getElementById('videoCard').classList.add('show');
      btn.innerHTML = '⬇ DOWNLOAD'; btn.disabled = false;
      return;
    }
    if (data.status === 'done' && data.url) {
      document.getElementById('readyFilename').textContent = data.filename || 'Your file is ready';
      document.getElementById('saveLink').href = data.url;
      document.getElementById('readySection').classList.add('show');
    }
  } catch(e) {
    document.getElementById('loadingSection').classList.remove('show');
    showError('Download failed. Try again.');
    document.getElementById('videoCard').classList.add('show');
    btn.innerHTML = '⬇ DOWNLOAD'; btn.disabled = false;
  }
}

function reset() {
  document.getElementById('urlInput').value = '';
  hideAll();
  document.getElementById('tipsSection').style.display = 'block';
  hideError(); selectedFormat = null;
}
function hideAll() {
  ['videoCard','loadingSection','readySection'].forEach(id => document.getElementById(id).classList.remove('show'));
}
function showError(msg) { const el = document.getElementById('errorBox'); el.textContent = '⚠️ ' + msg; el.classList.add('show'); }
function hideError() { document.getElementById('errorBox').classList.remove('show'); }
document.getElementById('urlInput').addEventListener('keydown', e => { if(e.key === 'Enter') fetchInfo(); });
</script>
</body>
</html>'''


def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r

@app.after_request
def after(r): return cors(r)

@app.route("/")
def index():
    return HTML, 200, {"Content-Type": "text/html"}

@app.route("/info", methods=["POST", "OPTIONS"])
def info():
    if request.method == "OPTIONS": return cors(Response())
    url = request.json.get("url", "")
    try:
        oembed = requests.get(
            f"https://www.youtube.com/oembed?url={url}&format=json",
            timeout=10
        ).json()
        vid_match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
        vid_id = vid_match.group(1) if vid_match else ""
        thumbnail = f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg" if vid_id else ""
        formats = [
            {"id": "1080", "label": "1080p", "height": 1080},
            {"id": "720", "label": "720p", "height": 720},
            {"id": "480", "label": "480p", "height": 480},
            {"id": "360", "label": "360p", "height": 360},
            {"id": "mp3", "label": "MP3 Audio", "height": 0},
        ]
        return jsonify({
            "title": oembed.get("title", ""),
            "thumbnail": thumbnail,
            "channel": oembed.get("author_name", ""),
            "duration": 0,
            "formats": formats
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/download", methods=["POST", "OPTIONS"])
def download():
    if request.method == "OPTIONS": return cors(Response())
    url = request.json.get("url", "")
    fmt = str(request.json.get("format", "720"))
    try:
        if fmt == "0" or fmt == "mp3":
            payload = {"url": url, "downloadMode": "audio", "audioFormat": "mp3"}
        else:
            quality = fmt if fmt in ["144","240","360","480","720","1080","1440","2160"] else "720"
            payload = {"url": url, "downloadMode": "auto", "videoQuality": quality}

        res = requests.post(
            "https://api.cobalt.tools/",
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=30
        )
        data = res.json()

        if data.get("status") in ["redirect", "tunnel"]:
            return jsonify({"status": "done", "url": data.get("url"), "filename": data.get("filename", "download")})
        elif data.get("status") == "picker":
            items = data.get("picker", [])
            if items:
                return jsonify({"status": "done", "url": items[0].get("url"), "filename": "download.mp4"})

        error_code = data.get("error", {}).get("code", "Download failed")
        return jsonify({"error": error_code})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
