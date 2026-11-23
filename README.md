# NTorrent

A zero-ad, dark-mode BitTorrent client for Windows. PyQt6 UI, libtorrent engine.

![platform](https://img.shields.io/badge/platform-Windows-0a0a0a?style=flat-square)
![python](https://img.shields.io/badge/python-3.10%7C3.11%7C3.12-00E5C9?style=flat-square)
![license](https://img.shields.io/badge/license-MIT-2ECC71?style=flat-square)

## Features

- **libtorrent engine** — DHT, Peer Exchange, Local Service Discovery, UPnP/NAT-PMP
  all on by default for maximum peer reach and throughput.
- **Magnet links & .torrent files** — add either, with a confirm dialog showing
  name/size and a per-download output-folder override.
- **Private-tracker safe** — the `private` flag is honored automatically; DHT/PeX/LSD
  never activate for a private torrent, so no passkey or peer ever leaks outside the
  tracker's swarm.
- **Persistent sessions** — active and paused torrents survive a restart via
  `.fastresume` data, no re-checking from scratch.
- **Per-torrent & global controls** — pause/resume/remove (with optional delete from
  disk), global up/down speed caps, max connections, listen port — all live-applied.
- **Dark, modern UI** — flat charcoal theme, real progress-bar cells, status filters
  (All / Downloading / Seeding / Completed / Paused), right-click context menu with
  **Open Output Folder** straight into Explorer.
- **Live speed graph** — 60-second rolling download/upload chart via `pyqtgraph`,
  plus a status bar with DHT node count and session totals.

## Project layout

```
ntorrent/
├── main.py                 entry point
├── engine.py                libtorrent session wrapper
├── models.py                table model + formatting helpers
├── requirements.txt
├── installer/
│   └── ntorrent.iss          Inno Setup script for the Windows installer
└── ui/
    ├── theme.py              dark QSS stylesheet + palette
    ├── delegates.py          progress-bar cell renderer
    ├── icons.py              inline SVG → QIcon helper, dev-credit icons
    ├── add_dialogs.py        add-by-file / add-by-magnet dialogs
    ├── settings_dialog.py    default folder, speed limits, connections, port
    ├── speed_graph.py        pyqtgraph 60s rolling speed graph
    └── main_window.py        toolbar, sidebar, table, status bar, QTimer polling
```

## Running from source

Python 3.10–3.12 on Windows.

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

If `pip install python-libtorrent` can't find a wheel for your exact Python
version, use conda instead:

```bat
conda install -c conda-forge libtorrent
pip install PyQt6 PyQt6-SVG pyqtgraph
```

Config and session state live in `%USERPROFILE%\.ntorrent\` — `config.json` for
settings, `resume\*.fastresume` for the data that reloads your active torrents on
next launch. Nothing is written next to the app itself.

## Building a standalone .exe

```bat
pip install pyinstaller
pyinstaller --noconsole --onefile --name NTorrent --collect-all libtorrent main.py
```

`--collect-all libtorrent` is required — libtorrent ships a native `.pyd` and
supporting DLLs PyInstaller's import scan won't catch on its own. Output lands at
`dist\NTorrent.exe`, fully self-contained.

## Building a Windows installer

The .exe above is a single portable binary, not an installer — no Start Menu
entry, no uninstaller, no file association. To get a real installer, wrap it with
**Inno Setup** (free, the standard tool for this):

1. Build the exe first (previous step) — Inno Setup packages `dist\NTorrent.exe`.
2. Install [Inno Setup](https://jrsoftware.org/isinfo.php).
3. Open `installer\ntorrent.iss` (included in this repo) in the Inno Setup
   Compiler, or run it from the command line:
   ```bat
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\ntorrent.iss
   ```
4. The compiled installer appears at `installer\Output\NTorrent-Setup.exe`.

The included script adds a Start Menu shortcut, an optional desktop shortcut, a
proper uninstaller entry in Windows "Apps & features", and registers a `.torrent`
file association so double-clicking a torrent file opens it in NTorrent.

If you'd rather use **NSIS** instead of Inno Setup, the same two inputs apply —
point its `File` directive at `dist\NTorrent.exe` and its `CreateShortcut` at the
Start Menu / Desktop; the logic is equivalent, just different script syntax.

## Tech stack

PyQt6 · libtorrent · pyqtgraph · PyInstaller · Inno Setup

## License

MIT — see `LICENSE`.

## Credits

Built by **NengzXGODZ**
[![GitHub](https://img.shields.io/badge/GitHub-NengzXGODZ-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/NengzXGODZ)
[![Telegram](https://img.shields.io/badge/Telegram-@nengzx__fernandez-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://t.me/nengzx_fernandez)
