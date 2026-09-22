import json
import mimetypes
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import sqlite3


HOST = "127.0.0.1"
PORT = 8000
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "songs.db")


def get_songs():
	"""Return all song rows and their column names."""
	conn = sqlite3.connect(DATABASE_PATH)
	try:
		cursor = conn.execute("SELECT * FROM songs")
		songs = cursor.fetchall()
		columns = [column[0] for column in cursor.description]
		return songs, columns
	finally:
		conn.close()


def get_song_by_id(song_id):
	"""Return one song row and its column names."""
	conn = sqlite3.connect(DATABASE_PATH)
	try:
		cursor = conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
		song = cursor.fetchone()
		columns = [column[0] for column in cursor.description]
		return song, columns
	finally:
		conn.close()


def serialize_song(song, columns):
	"""Convert a database row into a JSON-safe named object."""
	if song is None:
		return None

	serialized = {}
	for name, value in zip(columns, song):
		if isinstance(value, (bytes, bytearray, memoryview)):
			serialized[name] = {"binary": True, "size": len(value)}
		else:
			serialized[name] = value
	return serialized


def get_audio_source(song, columns):
	"""Return audio bytes or a file path from a song row."""
	if not song:
		return None

	values = {name.lower(): value for name, value in zip(columns, song)}
	for name in ("audio_data", "audio", "data", "content", "file_data"):
		if name in values and values[name] is not None:
			return values[name]
	for name in ("file_path", "path", "filename", "file", "audio_path"):
		if name in values and values[name]:
			path = os.fsdecode(os.fspath(values[name]))
			if not os.path.isabs(path):
				path = os.path.join(os.path.dirname(DATABASE_PATH), path)
			return path

	return None


def get_audio_info(source):
	"""Return the source, content type, and byte length."""
	if isinstance(source, (bytes, bytearray, memoryview)):
		return source, "audio/mpeg", len(source)

	if isinstance(source, str):
		return (
			source,
			mimetypes.guess_type(source)[0] or "audio/mpeg",
			os.path.getsize(source),
		)

	return None


def parse_range(range_header, size):
	"""Parse a single HTTP byte range and return inclusive start/end values."""
	if not range_header or not range_header.startswith("bytes="):
		return None, None

	match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header)
	if not match or size == 0:
		raise ValueError
	start_text, end_text = match.groups()
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
	"""Handle the API endpoints."""

	def do_GET(self):
		try:
			self._do_get()
		except sqlite3.Error as error:
			print(f"Database error: {error}")
			self.send_json({"error": "Internal server error"}, status=500)

	def _do_get(self):
		parsed_url = urlparse(self.path)
		path = parsed_url.path

		if path == "/health":
			self.send_json({"status": "ok"})
			return

		elif path == "/api/songs":
			songs, columns = get_songs()
			self.send_json({"songs": [serialize_song(song, columns) for song in songs]})
			return

		elif path == "/api/song":
			params = parse_qs(parsed_url.query)
			song_id = params.get("id", [None])[0]

			if song_id:
				song, columns = get_song_by_id(song_id)
				if song:
					self.send_json({"song": serialize_song(song, columns)})
				else:
					self.send_json({"error": "Song not found"}, status=404)
			else:
				self.send_json({"error": "Missing 'id' parameter"}, status=400)
			return

		elif path in ("/api/song/stream", "/api/song/download"):
			params = parse_qs(parsed_url.query)
			song_id = params.get("id", [None])[0]
			if not song_id:
				self.send_json({"error": "Missing 'id' parameter"}, status=400)
				return

			song, columns = get_song_by_id(song_id)
			source = get_audio_source(song, columns)
			try:
				audio = get_audio_info(source)
			except (OSError, TypeError):
				audio = None
			if not audio:
				self.send_json({"error": "Audio not found"}, status=404)
				return

			audio_source, content_type, audio_size = audio
			if path.endswith("/download"):
				self.send_audio(audio_source, content_type, total=audio_size)
				return

			try:
				start, end = parse_range(self.headers.get("Range"), audio_size)
			except (TypeError, ValueError):
				self.send_response(416)
				self.send_header("Content-Range", f"bytes */{audio_size}")
				self.end_headers()
				return

			if start is None:
				self.send_audio(audio_source, content_type, total=audio_size)
			else:
				self.send_audio(audio_source, content_type, start=start, end=end, total=audio_size)
			return

		else:
			self.send_json({"error": "Not found"}, status=404)
   
	def send_json(self, payload, status=200):
		response = json.dumps(payload).encode("utf-8")

		self.send_response(status)
		self.send_header("Content-Type", "application/json")
		self.send_header("Content-Length", str(len(response)))
		self.end_headers()
		self.wfile.write(response)

	def send_audio(self, source, content_type, start=None, end=None, total=None):
		status = 206 if start is not None else 200
		first_byte = start or 0
		audio_file = None
		if isinstance(source, str):
			try:
				audio_file = open(source, "rb")
			except OSError:
				self.send_json({"error": "Audio not found"}, status=404)
				return
			total = os.fstat(audio_file.fileno()).st_size
		elif total is None:
			total = len(source)

		if start is not None and (total == 0 or first_byte >= total):
			if audio_file:
				audio_file.close()
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

		if audio_file:
			try:
				audio_file.seek(first_byte)
				remaining = content_length
				while remaining:
					chunk = audio_file.read(min(64 * 1024, remaining))
					if not chunk:
						self.log_message("Audio file changed while it was being sent")
						break
					self.wfile.write(chunk)
					remaining -= len(chunk)
			finally:
				audio_file.close()
			return

		body = source
		for offset in range(first_byte, last_byte + 1, 64 * 1024):
			self.wfile.write(body[offset:min(offset + 64 * 1024, last_byte + 1)])

	def log_message(self, format_string, *args):
		print(f"{self.address_string()} - {format_string % args}")


def main():
	server = ThreadingHTTPServer((HOST, PORT), ApiHandler)
	print(f"API server running at http://{HOST}:{PORT}")

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		print("\nStopping API server")
	finally:
		server.server_close()


if __name__ == "__main__":
	main()
