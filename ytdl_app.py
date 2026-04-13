from flask import Flask, request, jsonify, Response, send_file
import yt_dlp
import os
import re
import uuid
import threading
import time

app = Flask(__name__)

DOWNLOAD_DIR = "/tmp/ytdl"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Store job progress
jobs = {}

def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return r

@app.after_request
def after(r): return cors(r)

HTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">\n<meta name="mobile-web-app-capable" content="yes">\n<title>YTSave</title>\n<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">\n<style>\n:root {\n  --bg: #0f0f0f;\n  --surface: #1a1a1a;\n  --card: #222;\n  --border: #333;\n  --red: #ff0000;\n  --red2: #ff4444;\n  --text: #fff;\n  --muted: #888;\n  --glow: rgba(255,0,0,0.3);\n}\n* { margin:0; padding:0; box-sizing:border-box; -webkit-tap-highlight-color:transparent; }\nbody { background:var(--bg); color:var(--text); font-family:\'DM Sans\',sans-serif; min-height:100vh; }\n\nbody::before {\n  content:\'\'; position:fixed; top:0; left:0; right:0; height:400px;\n  background:radial-gradient(ellipse at 50% -20%, rgba(255,0,0,0.08) 0%, transparent 70%);\n  pointer-events:none;\n}\n\n.app { max-width:480px; margin:0 auto; padding:0 0 40px; position:relative; }\n\n/* Header */\n.header { padding:28px 20px 20px; text-align:center; }\n.logo {\n  font-family:\'Oswald\',sans-serif; font-size:38px; font-weight:700;\n  letter-spacing:4px; display:inline-flex; align-items:center; gap:10px;\n}\n.logo-yt { color:var(--red); }\n.logo-save { color:var(--text); }\n.logo-icon {\n  width:36px; height:36px; background:var(--red); border-radius:8px;\n  display:flex; align-items:center; justify-content:center; font-size:16px;\n}\n.tagline { color:var(--muted); font-size:13px; margin-top:6px; letter-spacing:1px; }\n\n/* Input section */\n.input-section { padding:0 16px 20px; }\n.url-box {\n  background:var(--surface); border:1px solid var(--border); border-radius:18px;\n  padding:6px 6px 6px 18px; display:flex; align-items:center; gap:10px;\n  transition:border-color .2s;\n}\n.url-box:focus-within { border-color:var(--red); }\n.url-input {\n  flex:1; background:none; border:none; color:var(--text); font-size:14px;\n  font-family:\'DM Sans\',sans-serif; outline:none; padding:10px 0;\n}\n.url-input::placeholder { color:var(--muted); }\n.btn-fetch {\n  background:var(--red); border:none; border-radius:13px; padding:12px 20px;\n  color:#fff; font-size:14px; font-weight:600; font-family:\'Oswald\',sans-serif;\n  letter-spacing:1px; cursor:pointer; transition:all .2s; white-space:nowrap;\n  display:flex; align-items:center; gap:6px;\n}\n.btn-fetch:active { transform:scale(.95); }\n.btn-fetch:disabled { opacity:.5; cursor:not-allowed; }\n\n/* Video info card */\n.video-card {\n  margin:0 16px 20px; background:var(--surface); border:1px solid var(--border);\n  border-radius:20px; overflow:hidden; display:none;\n}\n.video-card.show { display:block; animation:fadeIn .3s ease; }\n@keyframes fadeIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }\n\n.thumb-wrap { position:relative; }\n.thumb { width:100%; aspect-ratio:16/9; object-fit:cover; display:block; }\n.thumb-overlay {\n  position:absolute; inset:0; background:linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 50%);\n}\n.duration-badge {\n  position:absolute; bottom:10px; right:10px; background:rgba(0,0,0,0.85);\n  color:#fff; font-size:12px; font-weight:600; padding:3px 8px; border-radius:6px;\n}\n\n.video-info { padding:16px; }\n.video-title { font-family:\'Oswald\',sans-serif; font-size:17px; font-weight:500; line-height:1.3; margin-bottom:6px; }\n.video-channel { font-size:12px; color:var(--muted); }\n\n/* Format selector */\n.format-section { padding:14px 16px 0; }\n.format-label { font-size:10px; color:var(--muted); letter-spacing:2px; text-transform:uppercase; margin-bottom:10px; }\n.format-grid { display:flex; flex-wrap:wrap; gap:8px; }\n.fmt-btn {\n  padding:10px 16px; background:var(--card); border:1px solid var(--border);\n  border-radius:12px; color:var(--muted); font-size:13px; font-weight:500;\n  font-family:\'DM Sans\',sans-serif; cursor:pointer; transition:all .2s;\n}\n.fmt-btn.active { background:rgba(255,0,0,0.15); border-color:var(--red); color:var(--red); }\n.fmt-btn:active { transform:scale(.95); }\n\n.btn-download {\n  margin:16px; width:calc(100% - 32px); padding:17px; background:var(--red);\n  border:none; border-radius:16px; color:#fff; font-size:18px; font-weight:600;\n  font-family:\'Oswald\',sans-serif; letter-spacing:2px; cursor:pointer;\n  transition:all .2s; box-shadow:0 4px 30px var(--glow); display:flex;\n  align-items:center; justify-content:center; gap:8px;\n}\n.btn-download:active { transform:scale(.97); }\n.btn-download:disabled { opacity:.5; cursor:not-allowed; }\n\n/* Progress */\n.progress-section {\n  margin:0 16px 20px; background:var(--surface); border:1px solid var(--border);\n  border-radius:20px; padding:20px; display:none;\n}\n.progress-section.show { display:block; }\n.progress-title { font-family:\'Oswald\',sans-serif; font-size:16px; margin-bottom:14px; }\n.progress-bar-wrap { background:var(--card); border-radius:6px; height:8px; overflow:hidden; margin-bottom:10px; }\n.progress-bar { height:100%; background:linear-gradient(90deg,var(--red),var(--red2)); border-radius:6px; transition:width .3s; width:0%; }\n.progress-text { font-size:13px; color:var(--muted); display:flex; justify-content:space-between; }\n\n/* Download ready */\n.ready-section {\n  margin:0 16px 20px; background:var(--surface); border:1px solid #1a4a1a;\n  border-radius:20px; padding:20px; display:none; text-align:center;\n}\n.ready-section.show { display:block; animation:fadeIn .3s ease; }\n.ready-icon { font-size:48px; margin-bottom:10px; }\n.ready-title { font-family:\'Oswald\',sans-serif; font-size:20px; color:#4caf50; margin-bottom:6px; }\n.ready-sub { font-size:13px; color:var(--muted); margin-bottom:16px; }\n.btn-save {\n  display:inline-block; padding:14px 32px; background:#4caf50; border:none;\n  border-radius:14px; color:#fff; font-size:16px; font-weight:600;\n  font-family:\'Oswald\',sans-serif; letter-spacing:1px; cursor:pointer;\n  text-decoration:none; transition:all .2s;\n}\n.btn-save:active { transform:scale(.97); }\n.btn-another { margin-top:10px; background:none; border:none; color:var(--muted); font-size:13px; cursor:pointer; font-family:\'DM Sans\',sans-serif; }\n\n/* Error */\n.error-box {\n  margin:0 16px 20px; background:#1a0a0a; border:1px solid #4a1a1a;\n  border-radius:16px; padding:16px; color:#ff6b6b; font-size:13px;\n  display:none; text-align:center;\n}\n.error-box.show { display:block; }\n\n/* Tips */\n.tips { padding:0 16px; }\n.tip-title { font-size:10px; color:var(--muted); letter-spacing:2px; text-transform:uppercase; margin-bottom:10px; }\n.tip-item {\n  background:var(--surface); border:1px solid var(--border); border-radius:14px;\n  padding:14px; margin-bottom:8px; display:flex; align-items:center; gap:12px;\n}\n.tip-icon { font-size:22px; flex-shrink:0; }\n.tip-text { font-size:13px; color:var(--muted); line-height:1.5; }\n\n.spinner { width:18px; height:18px; border:2px solid rgba(255,255,255,.3); border-top-color:#fff; border-radius:50%; animation:spin .7s linear infinite; }\n@keyframes spin { to{transform:rotate(360deg)} }\n</style>\n</head>\n<body>\n<div class="app">\n  <div class="header">\n    <div class="logo">\n      <div class="logo-icon">▶</div>\n      <span class="logo-yt">YT</span><span class="logo-save">SAVE</span>\n    </div>\n    <div class="tagline">PERSONAL VIDEO DOWNLOADER</div>\n  </div>\n\n  <div class="input-section">\n    <div class="url-box">\n      <input class="url-input" id="urlInput" type="url" placeholder="Paste YouTube URL here...">\n      <button class="btn-fetch" id="fetchBtn" onclick="fetchInfo()">\n        <span id="fetchBtnText">FETCH</span>\n      </button>\n    </div>\n  </div>\n\n  <div class="error-box" id="errorBox"></div>\n\n  <div class="video-card" id="videoCard">\n    <div class="thumb-wrap">\n      <img class="thumb" id="videoThumb" src="" alt="">\n      <div class="thumb-overlay"></div>\n      <div class="duration-badge" id="videoDuration"></div>\n    </div>\n    <div class="video-info">\n      <div class="video-title" id="videoTitle"></div>\n      <div class="video-channel" id="videoChannel"></div>\n    </div>\n    <div class="format-section">\n      <div class="format-label">Select Quality</div>\n      <div class="format-grid" id="formatGrid"></div>\n    </div>\n    <button class="btn-download" id="downloadBtn" onclick="startDownload()">\n      ⬇ DOWNLOAD\n    </button>\n  </div>\n\n  <div class="progress-section" id="progressSection">\n    <div class="progress-title">⏳ Downloading...</div>\n    <div class="progress-bar-wrap">\n      <div class="progress-bar" id="progressBar"></div>\n    </div>\n    <div class="progress-text">\n      <span id="progressPct">0%</span>\n      <span>Please wait...</span>\n    </div>\n  </div>\n\n  <div class="ready-section" id="readySection">\n    <div class="ready-icon">✅</div>\n    <div class="ready-title">READY TO SAVE!</div>\n    <div class="ready-sub" id="readyFilename"></div>\n    <a class="btn-save" id="saveLink" href="#" target="_blank">⬇ SAVE FILE</a>\n    <br>\n    <button class="btn-another" onclick="reset()">← Download another</button>\n  </div>\n\n  <div class="tips" id="tipsSection">\n    <div class="tip-title">HOW TO USE</div>\n    <div class="tip-item">\n      <div class="tip-icon">📋</div>\n      <div class="tip-text">Copy any YouTube video URL and paste it above</div>\n    </div>\n    <div class="tip-item">\n      <div class="tip-icon">🎬</div>\n      <div class="tip-text">Choose your quality — 1080p, 720p, 480p or MP3 audio only</div>\n    </div>\n    <div class="tip-item">\n      <div class="tip-icon">💾</div>\n      <div class="tip-text">Tap Download and save directly to your device</div>\n    </div>\n    <div class="tip-item">\n      <div class="tip-icon">🔒</div>\n      <div class="tip-text">Personal use only — your private downloader</div>\n    </div>\n  </div>\n</div>\n\n<script>\nconst SERVER = window.location.origin;\nlet selectedFormat = null;\nlet currentJobId = null;\nlet pollInterval = null;\n\nasync function fetchInfo() {\n  const url = document.getElementById(\'urlInput\').value.trim();\n  if (!url) { showError(\'Please paste a YouTube URL first\'); return; }\n\n  const btn = document.getElementById(\'fetchBtn\');\n  document.getElementById(\'fetchBtnText\').innerHTML = \'<div class="spinner"></div>\';\n  btn.disabled = true;\n  hideError();\n  hideAll();\n\n  try {\n    const res = await fetch(`${SERVER}/info`, {\n      method: \'POST\',\n      headers: {\'Content-Type\': \'application/json\'},\n      body: JSON.stringify({url})\n    });\n    const data = await res.json();\n\n    if (data.error) { showError(data.error); return; }\n\n    // Show video info\n    document.getElementById(\'videoThumb\').src = data.thumbnail;\n    document.getElementById(\'videoTitle\').textContent = data.title;\n    document.getElementById(\'videoChannel\').textContent = \'📺 \' + data.channel;\n    document.getElementById(\'videoDuration\').textContent = formatDuration(data.duration);\n\n    // Build format buttons\n    const grid = document.getElementById(\'formatGrid\');\n    grid.innerHTML = \'\';\n    data.formats.forEach(f => {\n      const btn = document.createElement(\'button\');\n      btn.className = \'fmt-btn\';\n      btn.textContent = f.label;\n      btn.dataset.id = f.id;\n      btn.dataset.height = f.height;\n      btn.onclick = () => selectFormat(f, btn);\n      grid.appendChild(btn);\n    });\n\n    // Auto select first format\n    if (data.formats.length > 0) {\n      const firstBtn = grid.querySelector(\'.fmt-btn\');\n      selectFormat(data.formats[0], firstBtn);\n    }\n\n    document.getElementById(\'videoCard\').classList.add(\'show\');\n    document.getElementById(\'tipsSection\').style.display = \'none\';\n\n  } catch(e) {\n    showError(\'Failed to fetch video info. Check the URL and try again.\');\n  }\n\n  document.getElementById(\'fetchBtnText\').textContent = \'FETCH\';\n  btn.disabled = false;\n}\n\nfunction selectFormat(fmt, btn) {\n  selectedFormat = fmt;\n  document.querySelectorAll(\'.fmt-btn\').forEach(b => b.classList.remove(\'active\'));\n  btn.classList.add(\'active\');\n}\n\nasync function startDownload() {\n  if (!selectedFormat) { showError(\'Select a quality first\'); return; }\n  const url = document.getElementById(\'urlInput\').value.trim();\n\n  const btn = document.getElementById(\'downloadBtn\');\n  btn.innerHTML = \'<div class="spinner"></div> PROCESSING...\';\n  btn.disabled = true;\n\n  try {\n    const res = await fetch(`${SERVER}/download`, {\n      method: \'POST\',\n      headers: {\'Content-Type\': \'application/json\'},\n      body: JSON.stringify({url, format: selectedFormat.height || \'mp3\'})\n    });\n    const data = await res.json();\n\n    if (data.error) { showError(data.error); btn.innerHTML = \'⬇ DOWNLOAD\'; btn.disabled = false; return; }\n\n    currentJobId = data.job_id;\n    document.getElementById(\'videoCard\').classList.remove(\'show\');\n    document.getElementById(\'progressSection\').classList.add(\'show\');\n    pollProgress();\n\n  } catch(e) {\n    showError(\'Download failed. Try again.\');\n    btn.innerHTML = \'⬇ DOWNLOAD\';\n    btn.disabled = false;\n  }\n}\n\nfunction pollProgress() {\n  pollInterval = setInterval(async () => {\n    try {\n      const res = await fetch(`${SERVER}/progress/${currentJobId}`);\n      const data = await res.json();\n\n      const pct = Math.round(data.progress || 0);\n      document.getElementById(\'progressBar\').style.width = pct + \'%\';\n      document.getElementById(\'progressPct\').textContent = pct + \'%\';\n\n      if (data.status === \'done\') {\n        clearInterval(pollInterval);\n        document.getElementById(\'progressSection\').classList.remove(\'show\');\n        document.getElementById(\'readyFilename\').textContent = data.filename || \'Your file is ready\';\n        document.getElementById(\'saveLink\').href = `${SERVER}/file/${currentJobId}`;\n        document.getElementById(\'readySection\').classList.add(\'show\');\n      } else if (data.status === \'error\') {\n        clearInterval(pollInterval);\n        document.getElementById(\'progressSection\').classList.remove(\'show\');\n        showError(\'Download failed: \' + (data.error || \'Unknown error\'));\n        document.getElementById(\'videoCard\').classList.add(\'show\');\n        document.getElementById(\'downloadBtn\').innerHTML = \'⬇ DOWNLOAD\';\n        document.getElementById(\'downloadBtn\').disabled = false;\n      }\n    } catch(e) {}\n  }, 1000);\n}\n\nfunction reset() {\n  document.getElementById(\'urlInput\').value = \'\';\n  document.getElementById(\'videoCard\').classList.remove(\'show\');\n  document.getElementById(\'progressSection\').classList.remove(\'show\');\n  document.getElementById(\'readySection\').classList.remove(\'show\');\n  document.getElementById(\'tipsSection\').style.display = \'block\';\n  hideError();\n  selectedFormat = null;\n  currentJobId = null;\n  if (pollInterval) clearInterval(pollInterval);\n}\n\nfunction hideAll() {\n  document.getElementById(\'videoCard\').classList.remove(\'show\');\n  document.getElementById(\'progressSection\').classList.remove(\'show\');\n  document.getElementById(\'readySection\').classList.remove(\'show\');\n}\n\nfunction showError(msg) {\n  const el = document.getElementById(\'errorBox\');\n  el.textContent = \'⚠️ \' + msg;\n  el.classList.add(\'show\');\n}\n\nfunction hideError() {\n  document.getElementById(\'errorBox\').classList.remove(\'show\');\n}\n\nfunction formatDuration(secs) {\n  if (!secs) return \'\';\n  const m = Math.floor(secs / 60);\n  const s = secs % 60;\n  return `${m}:${s.toString().padStart(2, \'0\')}`;\n}\n\ndocument.getElementById(\'urlInput\').addEventListener(\'keydown\', e => {\n  if (e.key === \'Enter\') fetchInfo();\n});\n</script>\n</body>\n</html>\n'

@app.route("/")
def index():
    return HTML, 200, {"Content-Type": "text/html"}

@app.route("/info", methods=["POST", "OPTIONS"])
def info():
    if request.method == "OPTIONS": return cors(Response())
    url = request.json.get("url", "")
    try:
        ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen = set()
            for f in info.get("formats", []):
                if f.get("vcodec") != "none" and f.get("acodec") != "none":
                    h = f.get("height")
                    if h and h not in seen:
                        seen.add(h)
                        formats.append({"id": f["format_id"], "label": f"{h}p", "height": h})
            formats = sorted(formats, key=lambda x: x["height"], reverse=True)
            # Add MP3 option
            formats.append({"id": "mp3", "label": "MP3 Audio", "height": 0})
            return jsonify({
                "title": info.get("title", ""),
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration", 0),
                "channel": info.get("uploader", ""),
                "formats": formats
            })
    except Exception as e:
        return jsonify({"error": str(e)})

def do_download(job_id, url, fmt):
    try:
        jobs[job_id] = {"status": "downloading", "progress": 0}
        out_path = os.path.join(DOWNLOAD_DIR, job_id)
        os.makedirs(out_path, exist_ok=True)

        def progress_hook(d):
            if d["status"] == "downloading":
                pct = d.get("_percent_str", "0%").strip().replace("%", "")
                try:
                    jobs[job_id]["progress"] = float(pct)
                except:
                    pass
            elif d["status"] == "finished":
                jobs[job_id]["progress"] = 100

        if fmt == "mp3":
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{out_path}/%(title)s.%(ext)s",
                "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
                "progress_hooks": [progress_hook],
                "quiet": True,
            }
        else:
            ydl_opts = {
                "format": f"bestvideo[height<={fmt}]+bestaudio/best[height<={fmt}]",
                "outtmpl": f"{out_path}/%(title)s.%(ext)s",
                "merge_output_format": "mp4",
                "progress_hooks": [progress_hook],
                "quiet": True,
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find downloaded file
        files = os.listdir(out_path)
        if files:
            jobs[job_id]["status"] = "done"
            jobs[job_id]["file"] = os.path.join(out_path, files[0])
            jobs[job_id]["filename"] = files[0]
        else:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["error"] = "File not found after download"
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

@app.route("/download", methods=["POST", "OPTIONS"])
def download():
    if request.method == "OPTIONS": return cors(Response())
    url = request.json.get("url", "")
    fmt = request.json.get("format", "720")
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "starting", "progress": 0}
    t = threading.Thread(target=do_download, args=(job_id, url, fmt))
    t.daemon = True
    t.start()
    return jsonify({"job_id": job_id})

@app.route("/progress/<job_id>")
def progress(job_id):
    job = jobs.get(job_id, {"status": "not_found"})
    return jsonify(job)

@app.route("/file/<job_id>")
def file(job_id):
    job = jobs.get(job_id)
    if not job or job.get("status") != "done":
        return jsonify({"error": "Not ready"}), 404
    filepath = job.get("file")
    filename = job.get("filename", "download")
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=filename)
    return jsonify({"error": "File not found"}), 404

if __name__ == "__main__":
    import socket
    ip = socket.gethostbyname(socket.gethostname())
    print(f"Server running at http://{ip}:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
