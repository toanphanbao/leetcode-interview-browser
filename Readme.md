## Leetcode Company wise Problems Lists

- Curated lists of Leetcode questions group by companies, updated as of 1 June 2025.
- Each company folder consists of questions from the past 30, 60, 90 days and all time questions wherever available.

- System Design Notes: https://github.com/liquidslr/system-design-notes

---

## Local Interview Browser

A local website to browse, filter, and sort questions by company, difficulty, topic, frequency, and time period.

### Requirements

- Python 3.7+

### Setup (one-time)

```bash
cd leetcode-browser
python import_data.py
```

This reads all CSV files from the `data/` folder and builds a `leetcode.db` SQLite database (~5 seconds).

### Run

```bash
cd leetcode-browser
python app.py
```

Then open **http://localhost:8000** in your browser.

### Options

| Flag | Default | Description |
|---|---|---|
| `--port` | `8000` | Port to listen on |
| `--host` | `127.0.0.1` | Host to bind to (`0.0.0.0` to expose to the network) |
| `--db-path` | `./leetcode.db` | Path to the SQLite database |
| `--data-dir` | `../data` | Path to company CSV folders (import only) |

---

## Podman (Container)

No Python installation needed — the database is baked into the image at build time.

### Build

```bash
podman build -t leetcode-browser .
```

> The build imports all 470 companies into SQLite automatically (~30 seconds on first build).

### Run

```bash
podman run -p 8000:8000 leetcode-browser
```

Then open **http://localhost:8000** in your browser.

### Custom port

```bash
podman run -p 9090:9090 leetcode-browser python app.py --host 0.0.0.0 --port 9090 --db-path /app/leetcode.db
```

### Stop

```bash
podman ps                         # find CONTAINER ID
podman stop <CONTAINER ID>
```

---

## Project Structure

```
interview-company-wise-problems-main/
  data/                  ← 470 company folders (CSV files)
  leetcode-browser/
    import_data.py       ← run once to build the database (Python)
    app.py               ← web server (self-contained, no dependencies)
  Containerfile          ← Podman/Docker build definition
  .containerignore       ← files excluded from the container image
  Run-LeetcodeBrowser.ps1 ← Windows PowerShell launcher script
  .gitignore
  Readme.md
```

