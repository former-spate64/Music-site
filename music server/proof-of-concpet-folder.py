import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


HOST = "127.0.0.1"
PORT = 8000
SONGS_FOLDER = os.environ.get(
    "SONGS_FOLDER",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "songs"),
)
SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".opus"}


def get_songs():
    """Return the audio files in the songs folder as API-ready objects."""
    songs = []
    root = os.path.abspath(SONGS_FOLDER)

    if not os.path.isdir(root):
        return songs

    for current_root, _, filenames in os.walk(root):
        for filename in filenames:
            path = os.path.join(current_root, filename)
            if os.path.splitext(filename)[1].lower() not in SUPPORTED_EXTENSIONS:
                continue
            songs.append(path)

    songs.sort(key=lambda path: os.path.relpath(path, root).casefold())
    return [serialize_song(song_id, path, root) for song_id, path in enumerate(songs, 1)]


def get_song_by_id(song_id):
    """Find one song by its deterministic ID."""
    try:
        requested_id = int(song_id)
    except (TypeError, ValueError):
        return None

    for song in get_songs():
        if song["id"] == requested_id:
            return song
    return None


def serialize_song(song_id, path, root):
    """Convert a file path into the metadata returned by the API."""
    relative_path = os.path.relpath(path, root)
    title = os.path.splitext(os.path.basename(path))[0]
    return {
        "id": song_id,
        "title": title,
        "artist": None,
        "album": None,
        "file_path": relative_path,
        "content_type": mimetypes.guess_type(path)[0] or "audio/mpeg",
        "size": os.path.getsize(path),
    }


def parse_range(range_header, size):
    """Parse a single HTTP byte range and return inclusive start/end values."""
    if not range_header or not range_header.startswith("bytes="):
        return None, None

    value = range_header.removeprefix("bytes=")
    if "," in value or "-" not in value:
        raise ValueError

    start_text, end_text = value.split("-", 1)
    if size == 0:
        raise ValueError

    if not start_text:
        length = int(end_text)
        if length <= 0:
            raise ValueError
        return max(size - length, 0), size - 1

    start = int(start_text)
    end = int(end_text) if end_text else size - 1
    if start >= size or start > end:
        raise ValueError
    return start, min(end, size - 1)


class ApiHandler(BaseHTTPRequestHandler):
    """Handle the folder-backed song API."""

    def do_GET(self):
        self._do_get()

    def _do_get(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/health":
            self.send_json({"status": "ok"})
            return

        if path == "/api/songs":
            self.send_json({"songs": get_songs()})
            return

        if path == "/api/song":
            song_id = parse_qs(parsed_url.query).get("id", [None])[0]
            song = get_song_by_id(song_id)
            if song:
                self.send_json({"song": song})
            elif song_id:
                self.send_json({"error": "Song not found"}, status=404)
            else:
                self.send_json({"error": "Missing 'id' parameter"}, status=400)
            return

        if path in ("/api/song/stream", "/api/song/download"):
            song_id = parse_qs(parsed_url.query).get("id", [None])[0]
            if not song_id:
                self.send_json({"error": "Missing 'id' parameter"}, status=400)
                return

            song = get_song_by_id(song_id)
            audio_path = (
                os.path.join(os.path.abspath(SONGS_FOLDER), song["file_path"])
                if song
                else None
            )
            if not audio_path or not os.path.isfile(audio_path):
                self.send_json({"error": "Audio not found"}, status=404)
                return

            if path.endswith("/download"):
                self.send_audio(audio_path, song["content_type"], total=song["size"])
                return

            try:
                start, end = parse_range(self.headers.get("Range"), song["size"])
            except (TypeError, ValueError):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{song['size']}")
                self.end_headers()
                return

            self.send_audio(
                audio_path,
                song["content_type"],
                start=start,
                end=end,
                total=song["size"],
            )
            return

        self.send_json({"error": "Not found"}, status=404)

    def send_json(self, payload, status=200):
        response = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def send_audio(self, path, content_type, start=None, end=None, total=None):
        status = 206 if start is not None else 200
        first_byte = start or 0

        try:
            audio_file = open(path, "rb")
        except OSError:
            self.send_json({"error": "Audio not found"}, status=404)
            return

        try:
            total = os.fstat(audio_file.fileno()).st_size
            if start is not None and (total == 0 or first_byte >= total):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{total}")
                self.end_headers()
                return

            last_byte = end if end is not None else total - 1
            last_byte = min(last_byte, total - 1)
            content_length = last_byte - first_byte + 1

            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(content_length))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "private, max-age=3600")
            if start is not None:
                self.send_header("Content-Range", f"bytes {first_byte}-{last_byte}/{total}")
            self.end_headers()

            audio_file.seek(first_byte)
            remaining = content_length
            while remaining:
                chunk = audio_file.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
        finally:
            audio_file.close()

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def main():
    server = ThreadingHTTPServer((HOST, PORT), ApiHandler)
    print(f"Folder-backed API server running at http://{HOST}:{PORT}")
    print(f"Serving songs from: {os.path.abspath(SONGS_FOLDER)}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping API server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
