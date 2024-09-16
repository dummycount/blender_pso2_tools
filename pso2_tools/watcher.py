import hashlib
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_EXTENSIONS = [".py"]

ROOT_PATH = Path(__file__).parent


class FileWatcher(FileSystemEventHandler):
    _hashes: dict[str, str] = {}

    def __init__(self, callback: Callable, path=ROOT_PATH):
        self._callback = callback
        self._path = path
        self._observer = Observer()
        self._callback_running = False

    def start(self):
        self._observer.schedule(self, str(self._path), recursive=True)
        self._observer.start()
        self._callback_running = False

        self._init_hashes()

    def stop(self):
        self._observer.stop()
        self._observer.join()

    def reset(self):
        self._callback_running = False

    def on_moved(self, event):
        self._handle_event(event)

    def on_created(self, event):
        self._handle_event(event)

    def on_deleted(self, event):
        self._handle_event(event)

    def on_modified(self, event):
        self._handle_event(event)

    def _hash_file(self, path: Path):
        with path.open("rb") as f:
            return (
                str(path.relative_to(self._path)),
                hashlib.file_digest(f, "md5").hexdigest(),
            )

    def _init_hashes(self):
        for ext in WATCH_EXTENSIONS:
            for path in self._path.rglob(f"*{ext}"):
                key, digest = self._hash_file(path)
                self._hashes[key] = digest

    def _handle_event(self, event):
        if self._callback_running:
            return

        if event.is_directory:
            return

        path = Path(event.dest_path or event.src_path)

        if path.suffix not in WATCH_EXTENSIONS:
            return

        key, digest = self._hash_file(path)

        if prev_digest := self._hashes.get(key):
            if digest == prev_digest:
                return

        self._hashes[key] = digest

        self._callback_running = True
        self._callback()
