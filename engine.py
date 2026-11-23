"""
NTorrent engine: wraps a libtorrent session with high-performance settings,
torrent add/remove/pause/resume, persistent state save/restore, and a
polling snapshot API consumed by the UI via QTimer.
"""
from __future__ import annotations

import os
import time
import json
import dataclasses
from dataclasses import dataclass, field
from typing import Optional

import libtorrent as lt

APP_DIR = os.path.join(os.path.expanduser("~"), ".ntorrent")
STATE_FILE = os.path.join(APP_DIR, "session_state.dat")
RESUME_DIR = os.path.join(APP_DIR, "resume")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")

DEFAULT_CONFIG = {
    "download_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
    "download_limit_kibs": 0,   # 0 = unlimited
    "upload_limit_kibs": 0,
    "max_connections": 400,
    "listen_port": 6881,
}

STATUS_NAMES = {
    lt.torrent_status.states.checking_files: "Checking",
    lt.torrent_status.states.downloading_metadata: "Fetching metadata",
    lt.torrent_status.states.downloading: "Downloading",
    lt.torrent_status.states.finished: "Finished",
    lt.torrent_status.states.seeding: "Seeding",
    lt.torrent_status.states.checking_resume_data: "Checking resume data",
}


def ensure_dirs() -> None:
    os.makedirs(APP_DIR, exist_ok=True)
    os.makedirs(RESUME_DIR, exist_ok=True)


def load_config() -> dict:
    ensure_dirs()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    ensure_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


@dataclass
class TorrentSnapshot:
    info_hash: str
    name: str
    size: int
    progress: float          # 0.0 - 1.0
    status: str
    download_rate: float     # bytes/sec
    upload_rate: float
    num_seeds: int
    num_peers: int
    eta_seconds: Optional[int]
    save_path: str
    is_paused: bool
    is_finished: bool
    total_downloaded: int
    total_uploaded: int


@dataclass
class SessionSnapshot:
    torrents: list = field(default_factory=list)
    dht_nodes: int = 0
    download_rate: float = 0.0
    upload_rate: float = 0.0
    total_download: int = 0
    total_upload: int = 0
    num_peers: int = 0
    listening: bool = True


class TorrentEngine:
    """Thin, UI-agnostic wrapper around a libtorrent.session."""

    def __init__(self, config: dict):
        self.config = config
        self._handles: dict[str, lt.torrent_handle] = {}
        self._custom_save: dict[str, str] = {}  # info_hash -> save path override memory
        self._session = self._build_session()
        self._load_persisted_torrents()

    # ---------------------------------------------------------------- setup
    def _build_session(self) -> lt.session:
        settings = {
            "user_agent": "NTorrent/1.0",
            "listen_interfaces": f"0.0.0.0:{self.config['listen_port']}",
            "enable_dht": True,
            "enable_lsd": True,
            "enable_upnp": True,
            "enable_natpmp": True,
            "alert_mask": lt.alert.category_t.status_notification
            | lt.alert.category_t.error_notification
            | lt.alert.category_t.storage_notification,
            "connections_limit": self.config["max_connections"],
            "active_downloads": -1,
            "active_seeds": -1,
            "active_limit": -1,
            # Performance-leaning defaults for high throughput.
            "cache_size": 4096,
            "aio_threads": 8,
            "checking_mem_usage": 2048,
            "send_buffer_watermark": 3 * 1024 * 1024,
            "mixed_mode_algorithm": lt.bandwidth_mixed_algo_t.prefer_tcp,
        }
        ses = lt.session(settings)
        self._apply_rate_limits(ses)

        # Peer exchange (PeX) is enabled by default via the ut_pex extension.
        ses.add_extension(lt.create_ut_pex_plugin)
        ses.add_extension(lt.create_ut_metadata_plugin)
        ses.add_extension(lt.create_smart_ban_plugin)

        ses.start_dht()
        ses.start_lsd()
        ses.start_upnp()
        ses.start_natpmp()
        return ses

    def _apply_rate_limits(self, ses: lt.session) -> None:
        down = self.config["download_limit_kibs"]
        up = self.config["upload_limit_kibs"]
        ses.apply_settings({
            "download_rate_limit": int(down * 1024) if down > 0 else 0,
            "upload_rate_limit": int(up * 1024) if up > 0 else 0,
            "connections_limit": self.config["max_connections"],
        })

    def apply_settings(self, new_config: dict) -> None:
        """Live-apply settings changes (speed limits, connections, port)."""
        restart_needed = new_config["listen_port"] != self.config["listen_port"]
        self.config.update(new_config)
        save_config(self.config)
        self._apply_rate_limits(self._session)
        if restart_needed:
            self._session.apply_settings({
                "listen_interfaces": f"0.0.0.0:{self.config['listen_port']}"
            })

    # ------------------------------------------------------------- adding
    def add_torrent_file(self, file_path: str, save_path: str) -> str:
        info = lt.torrent_info(file_path)
        return self._add(info=info, save_path=save_path)

    def add_magnet(self, magnet_uri: str, save_path: str) -> str:
        params = lt.parse_magnet_uri(magnet_uri)
        params.save_path = save_path
        params.storage_mode = lt.storage_mode_t.storage_mode_sparse
        self._ensure_resume_flags(params)
        handle = self._session.add_torrent(params)
        info_hash = str(handle.info_hash())
        self._handles[info_hash] = handle
        self._custom_save[info_hash] = save_path
        return info_hash

    def _add(self, info: lt.torrent_info, save_path: str) -> str:
        params = {
            "ti": info,
            "save_path": save_path,
            "storage_mode": lt.storage_mode_t.storage_mode_sparse,
        }
        handle = self._session.add_torrent(params)
        info_hash = str(handle.info_hash())
        self._handles[info_hash] = handle
        self._custom_save[info_hash] = save_path
        return info_hash

    @staticmethod
    def _ensure_resume_flags(params: lt.add_torrent_params) -> None:
        # Respect the private flag: private torrents must not use DHT/PeX/LSD,
        # to avoid leaking peers (and, by extension, tracker passkeys) outside
        # the tracker's swarm. libtorrent already disables these per-torrent
        # when torrent_info.priv() is true; nothing further to set here for
        # add-by-magnet (metadata isn't known yet, enforced once fetched).
        return

    def peek_torrent_file_info(self, file_path: str) -> tuple[str, int]:
        """Return (name, total_size) without adding the torrent."""
        info = lt.torrent_info(file_path)
        return info.name(), info.total_size()

    # ------------------------------------------------------------ control
    def pause(self, info_hash: str) -> None:
        h = self._handles.get(info_hash)
        if h:
            h.pause()

    def resume(self, info_hash: str) -> None:
        h = self._handles.get(info_hash)
        if h:
            h.resume()

    def remove(self, info_hash: str, delete_files: bool) -> None:
        h = self._handles.get(info_hash)
        if not h:
            return
        flags = lt.session.delete_files if delete_files else 0
        self._session.remove_torrent(h, flags)
        self._handles.pop(info_hash, None)
        self._custom_save.pop(info_hash, None)
        resume_path = os.path.join(RESUME_DIR, f"{info_hash}.fastresume")
        if os.path.exists(resume_path):
            os.remove(resume_path)

    def get_save_path(self, info_hash: str) -> str:
        h = self._handles.get(info_hash)
        if h:
            return h.status().save_path
        return self._custom_save.get(info_hash, "")

    # ------------------------------------------------------------- polling
    def poll(self) -> SessionSnapshot:
        snap = SessionSnapshot()
        self._session.post_dht_stats()
        session_status = self._session.status()
        snap.dht_nodes = getattr(session_status, "dht_nodes", 0)
        snap.download_rate = session_status.download_rate
        snap.upload_rate = session_status.upload_rate
        snap.total_download = session_status.total_download
        snap.total_upload = session_status.total_upload
        snap.num_peers = session_status.num_peers
        snap.listening = not self._session.is_listening() is False

        for info_hash, handle in list(self._handles.items()):
            if not handle.is_valid():
                continue
            st = handle.status()
            name = st.name or os.path.basename(st.save_path)
            eta = self._estimate_eta(st)
            is_paused = bool(st.flags & lt.torrent_flags.paused) if hasattr(st, "flags") else st.paused
            status_label = "Paused" if is_paused else STATUS_NAMES.get(st.state, str(st.state))
            snap.torrents.append(TorrentSnapshot(
                info_hash=info_hash,
                name=name,
                size=st.total_wanted,
                progress=st.progress,
                status=status_label,
                download_rate=st.download_rate,
                upload_rate=st.upload_rate,
                num_seeds=st.num_seeds,
                num_peers=st.num_peers,
                eta_seconds=eta,
                save_path=st.save_path,
                is_paused=is_paused,
                is_finished=st.is_finished,
                total_downloaded=st.total_done,
                total_uploaded=st.total_upload,
            ))
        return snap

    @staticmethod
    def _estimate_eta(st) -> Optional[int]:
        if st.download_rate <= 0 or st.is_finished:
            return None
        remaining = st.total_wanted - st.total_wanted_done
        if remaining <= 0:
            return None
        return int(remaining / st.download_rate)

    # --------------------------------------------------------- persistence
    def _load_persisted_torrents(self) -> None:
        ensure_dirs()
        if not os.path.isdir(RESUME_DIR):
            return
        for fname in os.listdir(RESUME_DIR):
            if not fname.endswith(".fastresume"):
                continue
            path = os.path.join(RESUME_DIR, fname)
            try:
                with open(path, "rb") as f:
                    data = f.read()
                params = lt.read_resume_data(data)
                handle = self._session.add_torrent(params)
                info_hash = str(handle.info_hash())
                self._handles[info_hash] = handle
                self._custom_save[info_hash] = params.save_path
            except Exception:
                # Corrupt or incompatible resume entry; skip it rather than crash startup.
                continue

    def save_all_resume_data(self) -> None:
        """Ask libtorrent for fresh resume data for every torrent and write it out.
        Call on a timer and on shutdown so active torrents reload on restart."""
        ensure_dirs()
        pending = 0
        for handle in self._handles.values():
            if handle.is_valid() and handle.status().has_metadata:
                handle.save_resume_data()
                pending += 1
        if pending == 0:
            return
        deadline = time.time() + 5.0
        collected = 0
        while collected < pending and time.time() < deadline:
            if not self._session.wait_for_alert(200):
                continue
            for alert in self._session.pop_alerts():
                if isinstance(alert, lt.save_resume_data_alert):
                    info_hash = str(alert.handle.info_hash())
                    out_path = os.path.join(RESUME_DIR, f"{info_hash}.fastresume")
                    with open(out_path, "wb") as f:
                        f.write(lt.write_resume_data_buf(alert.params))
                    collected += 1
                elif isinstance(alert, lt.save_resume_data_failed_alert):
                    collected += 1

    def shutdown(self) -> None:
        self.save_all_resume_data()
        self._session.pause()
