# -*- coding: utf-8 -*-

import wx
import util


class BaseSplitter(wx.SplitterWindow):
    def __init__(self, parent, nombre, size_defecto=200):
        wx.SplitterWindow.__init__(self, parent, wx.ID_ANY, style=wx.SP_LIVE_UPDATE)
        self.nombre = nombre
        self.size_defecto = size_defecto

        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self._on_sash_changed)

    def _on_sash_changed(self, event):
        valor = int(event.GetSashPosition())
        propi = util.get_frame_title(self)
        propi += self.nombre
        wx.GetApp().set_propiedad(propi, valor)

    def get_size(self):
        propi = util.get_frame_title(self)
        propi += self.nombre
        valor = wx.GetApp().get_propiedad(propi)

        return valor if valor else self.size_defecto
