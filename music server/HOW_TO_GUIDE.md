# Music Server How-To Guide

This guide explains how to run, use, modify, and connect the music server to a web application.

The server is currently implemented in `proof-of-concpet.py` and uses Python's built-in HTTP server plus SQLite.

## 1. What The Server Does

The server provides:

- A health check endpoint.
- A list of songs.
- Information about one song.
- Live audio streaming with HTTP byte ranges.
- Cacheable audio responses for offline use by a web application.

The server listens on:

```text
http://127.0.0.1:8000
```

The database path is resolved relative to the Python file:

```text
music server/songs.db
```

This means the server can be started from another working directory and still find its database.

## 2. Running The Server

Open PowerShell in the project directory and run:

```powershell
python "music server\proof-of-concpet.py"
```

You should see:

```text
API server running at http://127.0.0.1:8000
```

Check that it is working:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{"status": "ok"}
```

Stop the server with `Ctrl+C`.

## 3. Database Setup

The server expects a SQLite database named `songs.db` in the same directory as the Python file.

A simple file-path-based schema is recommended:

```sql
CREATE TABLE songs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    artist TEXT,
    album TEXT,
    file_path TEXT NOT NULL,
    duration INTEGER
);
```

Example records:

```sql
INSERT INTO songs (title, artist, album, file_path, duration)
VALUES
    ('Example Song', 'Example Artist', 'Example Album', 'audio/example.mp3', 210);
```

Relative audio paths are resolved relative to the `music server` directory. For the example above, the file should be located at:

```text
music server/audio/example.mp3
```

Absolute paths are also accepted:

```sql
INSERT INTO songs (title, artist, file_path)
VALUES ('Another Song', 'Another Artist', 'C:/Music/another-song.mp3');
```

### Supported audio columns

The current code looks for audio data in these columns:

- `audio_data`
- `audio`
- `data`
- `content`
- `file_data`

It looks for file paths in these columns:

- `file_path`
- `path`
- `filename`
- `file`
- `audio_path`

Use one clear audio source column per database design. A file path is recommended for large music libraries.

### Creating the database with Python

```python
import sqlite3

connection = sqlite3.connect("music server/songs.db")
connection.execute("""
    CREATE TABLE IF NOT EXISTS songs (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        artist TEXT,
        album TEXT,
        file_path TEXT NOT NULL,
        duration INTEGER
    )
""")
connection.commit()
connection.close()
```

## 4. API Endpoints

### Health check

```http
GET /health
```

Response:

```json
{"status": "ok"}
```

### List songs

```http
GET /api/songs
```

Example response:

```json
{
  "songs": [
    {
      "id": 1,
      "title": "Example Song",
      "artist": "Example Artist",
      "album": "Example Album",
      "file_path": "audio/example.mp3",
      "duration": 210
    }
  ]
}
```

Binary database fields are represented as metadata instead of being placed directly into JSON:

```json
{
  "audio_data": {
    "binary": true,
    "size": 4829012
  }
}
```

### Get one song

```http
GET /api/song?id=1
```

Possible responses:

- `200`: song found.
- `400`: missing `id`.
- `404`: song not found.
- `500`: database failure.

### Live stream

```http
GET /api/song/stream?id=1
```

This endpoint is intended for an audio player. It supports HTTP byte ranges, which allows a browser to request only the section it needs for playback or seeking.

A range request looks like:

```http
Range: bytes=0-65535
```

The response is:

```http
206 Partial Content
Content-Type: audio/mpeg
Accept-Ranges: bytes
Content-Range: bytes 0-65535/4829012
```

A request without a range returns the complete audio with `200 OK`.

### Cache/download response

```http
GET /api/song/download?id=1
```

This endpoint returns the complete audio without a forced `Content-Disposition: attachment` header. A web application can fetch this response and place it in the browser Cache API for offline playback.

It is not the same as a permanent file download to the user's Downloads folder.

## 5. Integrating With A Web Application

The frontend should use the stream URL for normal online playback:

```html
<audio id="player" controls></audio>

<script>
    const player = document.getElementById("player");
    player.src = "http://127.0.0.1:8000/api/song/stream?id=1";
    player.play();
</script>
```

The browser handles buffering and usually sends range requests automatically.

### Fetch song metadata

```javascript
async function getSongs() {
    const response = await fetch("http://127.0.0.1:8000/api/songs");
    if (!response.ok) {
        throw new Error(`Song request failed: ${response.status}`);
    }
    return response.json();
}
```

### Store a song in the browser Cache API

```javascript
const AUDIO_CACHE = "music-audio-v1";
const SERVER_URL = "http://127.0.0.1:8000";

async function cacheSong(songId) {
    const url = `${SERVER_URL}/api/song/download?id=${encodeURIComponent(songId)}`;
    const cache = await caches.open(AUDIO_CACHE);
    const existing = await cache.match(url);

    if (existing) {
        return existing;
    }

    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`Could not cache song: ${response.status}`);
    }

    await cache.put(url, response.clone());
    return response;
}
```

### Play an offline-cached song

```javascript
async function playCachedSong(songId, audioElement) {
    const url = `${SERVER_URL}/api/song/download?id=${encodeURIComponent(songId)}`;
    const cache = await caches.open(AUDIO_CACHE);
    const response = await cache.match(url);

    if (!response) {
        throw new Error("Song is not cached");
    }

    const blob = await response.blob();
    const objectUrl = URL.createObjectURL(blob);
    audioElement.src = objectUrl;
    await audioElement.play();

    audioElement.addEventListener(
        "ended",
        () => URL.revokeObjectURL(objectUrl),
        { once: true }
    );
}
```

Example:

```javascript
const player = document.getElementById("player");
await cacheSong(1);
await playCachedSong(1, player);
```

The Cache API is browser-managed storage. It can be cleared by the browser or user. It is not the same as saving a visible file to disk.

### Browser security requirements

For reliable `fetch()` and Cache API behavior, serve the web application from `localhost` or HTTPS. Opening an HTML file directly with `file://` can cause origin and CORS problems.

The current server binds to `127.0.0.1`, so it is intended for the same computer. To allow other devices on the network, change `HOST`, but do not expose the server publicly without authentication and access controls.

## 6. Adding A New Endpoint

Add a route inside `ApiHandler._do_get()`:

```python
elif path == "/api/artist":
    artist_name = params.get("name", [None])[0]
    if not artist_name:
        self.send_json({"error": "Missing 'name' parameter"}, status=400)
        return

    # Perform a parameterized database query here.
    self.send_json({"artist": artist_name})
    return
```

Always:

- Use parameterized SQL with `?` placeholders.
- Validate required query parameters.
- Return a useful status code.
- Return JSON errors consistently.
- Close database connections with `finally` or a context manager.

Do not build SQL using string concatenation:

```python
# Incorrect
query = "SELECT * FROM songs WHERE id = " + song_id
```

Use this instead:

```python
# Correct
cursor.execute("SELECT * FROM songs WHERE id = ?", (song_id,))
```

## 7. Modifying The Database Layer

The current database functions are:

- `get_songs()`: returns all rows and column names.
- `get_song_by_id(song_id)`: returns one row and column names.
- `serialize_song(song, columns)`: converts a row into a JSON-safe object.
- `get_audio_source(song, columns)`: finds audio bytes or a file path.
- `get_audio_info(source)`: determines MIME type and size.

When adding a column, update the database schema first. The API automatically includes ordinary columns in song JSON responses because it uses the cursor's column names.

When adding a new audio path column, add its lowercase name to the path list in `get_audio_source()`:

```python
for name in ("file_path", "path", "new_audio_path"):
```

When adding a new BLOB column, add its name to the binary audio list:

```python
for name in ("audio_data", "new_audio_blob"):
```

For large files, prefer storing paths rather than BLOBs. The current implementation can send file-backed audio incrementally, but a normal SQLite `SELECT` loads BLOB audio into memory before sending it.

## 8. Changing Streaming Behavior

`parse_range()` handles headers such as:

```text
bytes=0-65535
bytes=65536-
bytes=-65536
```

`send_audio()` handles:

- `200 OK` for a complete response.
- `206 Partial Content` for a valid range.
- `416 Range Not Satisfiable` for an invalid range.
- `Content-Length`.
- `Content-Range`.
- `Accept-Ranges: bytes`.
- 64 KiB file reads.

If changing this code, preserve the relationship:

```text
Content-Length = number of bytes actually sent
```

A browser media player depends on accurate range and length headers for seeking.

## 9. Common Problems

### `no such table: songs`

The server found `songs.db`, but the database does not contain a `songs` table. Create the table using the schema above.

### `Audio not found`

Check:

1. The song ID exists.
2. The database uses one of the supported audio column names.
3. The file path is correct.
4. Relative paths are relative to the `music server` directory.
5. The server process can read the file.

### Browser cannot fetch the API

Check that:

- The Python server is running.
- The URL uses port `8000`.
- The frontend is served from `localhost` or HTTPS.
- The frontend is not blocked by CORS or browser origin rules.

### Audio will not seek

Check that the client is using `/api/song/stream`, not the metadata endpoint. The stream endpoint must return `Accept-Ranges` and valid `Content-Range` headers.

### The server uses too much memory

Use file paths instead of storing large audio files in SQLite BLOB columns. File-backed streaming reads at most 64 KiB per loop iteration, while a normal SQLite BLOB query materializes the BLOB first.

## 10. Production Considerations

This server is a development proof of concept. Before exposing it beyond the local computer, add:

- Authentication and authorization.
- CORS rules limited to trusted origins.
- Request rate limiting.
- File path validation and access restrictions.
- Structured logging.
- Database connection pooling or a production web framework.
- HTTPS.
- A production WSGI or ASGI server.
- Tests for database queries, ranges, missing files, and response headers.

Do not allow a client to submit arbitrary filesystem paths. Audio paths should come from trusted database records and should be restricted to an approved music directory.
