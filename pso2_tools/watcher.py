from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

WATCH_EXTENSIONS = [".py"]


class FileWatcher(FileSystemEventHandler):
    def __init__(self, callback: Callable):
        self._callback = callback
        self._observer = Observer()
        self._callback_running = False

    def start(self):
        self._observer.schedule(self, str(Path(__file__).parent), recursive=True)
        self._observer.start()
        self._callback_running = False

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

    def _handle_event(self, event):
        if self._callback_running:
            return

        if event.is_directory:
            return

        src_ext = Path(event.src_path).suffix
        dest_ext = Path(event.dest_path).suffix

        if src_ext not in WATCH_EXTENSIONS and dest_ext not in WATCH_EXTENSIONS:
            return

        self._callback_running = True
        self._callback()
