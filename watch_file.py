# -*- coding: utf-8 -*-

import sys, os.path
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import wx


myEVT_WATCH = wx.NewEventType()
EVT_WATCH = wx.PyEventBinder(myEVT_WATCH, 1)


class WatchFileEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self.myVal = None

    def SetMyVal(self, val):
        self.myVal = val

    def GetMyVal(self):
        return self.myVal


class WatchEventHandler(PatternMatchingEventHandler):
    def __init__(self, parent, patterns):
        self.parent = parent
        super(WatchEventHandler, self).__init__(patterns=patterns)

    def _set_even(self, accion):
        event = WatchFileEvent(myEVT_WATCH, self.parent.GetId())
        event.SetMyVal(accion)
        self.parent.GetEventHandler().ProcessEvent(event)

    def on_moved(self, event):
        super(WatchEventHandler, self).on_moved(event)
        self._set_even("movido")

    def on_created(self, event):
        super(WatchEventHandler, self).on_created(event)
        self._set_even("creado")

    def on_deleted(self, event):
        super(WatchEventHandler, self).on_deleted(event)
        self._set_even("borrado")

    def on_modified(self, event):
        super(WatchEventHandler, self).on_modified(event)
        self._set_even("modificado")


class WatchFile(object):
    def __init__(self, parent):
        self.parent = parent
        self.observer = None

    def start(self, fichero):
        self.stop()
        watched_dir = os.path.split(fichero)[0]
        patterns = [fichero]
        event_handler = WatchEventHandler(self.parent, patterns=patterns)
        self.observer = Observer()
        self.observer.schedule(event_handler, watched_dir, recursive=False)
        self.observer.start()

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

