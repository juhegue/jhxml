# -*- coding: utf-8 -*-

import sys, os.path
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class WatchEventHandler(PatternMatchingEventHandler):
    def __init__(self, funcion, patterns):
        super(WatchEventHandler, self).__init__(patterns=patterns)
        self.funcion = funcion

    def on_moved(self, event):
        super(WatchEventHandler, self).on_moved(event)
        self.funcion("El fichero '%s' ha sido modificado por otro proceso." % self.patterns[0])

    def on_created(self, event):
        super(WatchEventHandler, self).on_created(event)
        self.funcion("El fichero '%s' ha sido modificado por otro proceso." % self.patterns[0])

    def on_deleted(self, event):
        super(WatchEventHandler, self).on_deleted(event)
        self.funcion("El fichero '%s' ha sido borrado por otro proceso." % self.patterns[0])

    def on_modified(self, event):
        super(WatchEventHandler, self).on_modified(event)
        self.funcion("El fichero '%s' ha sido modificado por otro proceso." % self.patterns[0])


class WatchFile(object):
    def __init__(self):
        self.observer = None

    def start(self, fichero, funcion):
        self.stop()
        watched_dir = os.path.split(fichero)[0]
        patterns = [fichero]
        event_handler = WatchEventHandler(funcion, patterns=patterns)
        self.observer = Observer()
        self.observer.schedule(event_handler, watched_dir, recursive=False)
        self.observer.start()

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None


if __name__ == "__main__":
    import time

    def fun(txt):
        print txt

    if len(sys.argv) > 1:
        path = sys.argv[1].strip()

        w = WatchFile()
        w.start(path, fun)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            w.stop()
    else:
        sys.exit(1)


