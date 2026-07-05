"""Tests for the /download endpoint logic, run with: python test_ytdl_app.py

The RapidAPI call is mocked so the tests exercise our parsing and
quality-selection logic without touching the network.
"""
import ytdl_app

MOCK = {
    "status": True,
    "errorId": "Success",
    "title": 'Test: <Video>/"Name"?',
    "videos": {"status": True, "items": [
        {"url": "http://v/144", "quality": "144p", "hasAudio": True},
        {"url": "http://v/360", "quality": "360p", "height": 360, "hasAudio": True},
        {"url": "http://v/720", "quality": "720p", "height": 720, "hasAudio": True},
        {"url": "http://v/1080", "quality": "1080p", "height": 1080, "hasAudio": False},
        {"quality": "4320p", "height": 4320},  # no url -> must be skipped
    ]},
    "audios": {"status": True, "items": [
        {"url": "http://a/small", "size": "1000", "extension": "m4a"},
        {"url": "http://a/big", "size": "5000", "extension": "m4a"},
    ]},
}


def dl(client, fmt):
    return client.post(
        "/download", json={"url": "https://youtu.be/dQw4w9WgXcQ", "format": fmt}
    ).get_json()


def main():
    ytdl_app.RAPIDAPI_KEY = "test-key"
    ytdl_app.fetch_video_details = lambda vid: MOCK
    client = ytdl_app.app.test_client()

    r = dl(client, "720")
    assert r["status"] == "done" and r["url"] == "http://v/720", r
    assert r["filename"].endswith(".mp4") and "<" not in r["filename"], r

    # closest at-or-below the requested quality
    r = dl(client, "480")
    assert r["url"] == "http://v/360", r

    # the 1080 stream is video-only, so the best with-audio stream wins
    r = dl(client, "1080")
    assert r["url"] == "http://v/720", r

    # requested below all available -> lowest available
    r = dl(client, "100")
    assert r["url"] == "http://v/144", r

    # audio: largest stream, correct extension
    r = dl(client, "mp3")
    assert r["url"] == "http://a/big" and r["filename"].endswith(".m4a"), r

    # upstream error is surfaced readably
    ytdl_app.fetch_video_details = lambda vid: {
        "status": False, "errorId": "VideoBlocked", "reason": "Video is blocked"
    }
    r = dl(client, "720")
    assert "blocked" in r["error"].lower(), r

    # tolerate a flat list of streams
    ytdl_app.fetch_video_details = lambda vid: {
        "errorId": "Success", "title": "t",
        "videos": [{"url": "http://v/x", "height": 720}],
    }
    r = dl(client, "720")
    assert r["url"] == "http://v/x", r

    # invalid URL and missing key are rejected cleanly
    r = client.post("/download", json={"url": "not-a-url"}).get_json()
    assert r["error"] == "Invalid YouTube URL", r
    ytdl_app.RAPIDAPI_KEY = ""
    r = dl(client, "720")
    assert "RAPIDAPI_KEY" in r["error"], r

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
