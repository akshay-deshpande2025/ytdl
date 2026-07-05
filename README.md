# YTSave (ytdl)

A small personal Flask app for downloading YouTube videos/audio via the
[youtube-media-downloader](https://rapidapi.com/) RapidAPI service.

## Setup

```bash
pip install -r requirements.txt
export RAPIDAPI_KEY=your-rapidapi-key   # required — the app refuses downloads without it
python ytdl_app.py                       # serves on http://0.0.0.0:5000
```

For production, use gunicorn:

```bash
RAPIDAPI_KEY=your-rapidapi-key gunicorn -b 0.0.0.0:5000 ytdl_app:app
```

## Notes

- The API key must never be committed to the repo — it is read from the
  `RAPIDAPI_KEY` environment variable.
- Download availability depends entirely on the upstream RapidAPI service;
  YouTube actively blocks downloader backends, so outages are expected from
  time to time.
- Personal use only.
