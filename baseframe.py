# -*- coding: utf-8 -*-

import wx
import util


class BaseFrame(wx.Frame):
    def __init__(self, *args, **kargs):
        wx.Frame.__init__(self, *args, **kargs)
        self.Bind(wx.EVT_SIZE, self._on_size)

    def _on_size(self, event):
        valor = self.GetSizeTuple()
        if valor[0] < 200 or valor[1] < 200:
            return

        self._set_propi_size()
        event.Skip(True)

    def _set_propi_size(self):
        if not self.IsMaximized():
            propi = self.GetTitle()
            valor = self.GetSizeTuple()
            if util.is_windows:
                wx.GetApp().set_propiedad(propi, valor)
            else:
                # TODO:: error en ubuntu 15.10 wx 3.0.0.1
                d1 = valor[0]
                d2 = valor[1] - 28
                wx.GetApp().set_propiedad(propi, (d1, d2))

    def set_size(self, defecto=(800, 600)):
        propi = self.GetTitle()
        valor = wx.GetApp().get_propiedad(propi)
        if valor:
            self.SetSize(valor)
        else:
            self.SetSize(defecto)
