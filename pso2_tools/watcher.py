from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileWatcher(FileSystemEventHandler):
    def __init__(self, callback: callable):
        self._callback = callback
        self._observer = Observer()

    def start(self):
        self._observer.schedule(self, str(Path(__file__).parent), recursive=True)
        self._observer.start()

    def stop(self):
        self._observer.stop()
        self._observer.join()

    def on_moved(self, event):
        print(event)
        self._reload()

    def on_created(self, event):
        print(event)
        self._reload()

    def on_deleted(self, event):
        print(event)
        self._reload()

    def on_modified(self, event):
        print(event)
        self._reload()

    def _reload(self):
        self._callback()
