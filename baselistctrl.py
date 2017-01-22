# -*- coding: utf-8 -*-

from bisect import bisect
import wx
import wx.lib.mixins.listctrl  as  listmix


class BaseListCtrl(wx.ListCtrl,
                   listmix.ListCtrlAutoWidthMixin,
                   listmix.TextEditMixin):

    non_propi = "listctrl"

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        self.InsertColumn(0, "Nombre")
        self.InsertColumn(1, "Tipo")
        self.InsertColumn(2, u"Descripción")
        self.SetColumnWidth(0, 300)
        self.SetColumnWidth(1, 50)
        listmix.TextEditMixin.__init__(self)
        self.currentItem = 0

        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.on_edit)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.set_propi_columns)
        self.set_size_columns()

    def on_edit(self, evt):
        if evt.m_col == 0:
            evt.Skip()
        else:
            evt.Veto()

    def set_propi_columns(self, evt):
        """ Guarda el ancho de las columnas
        """
        propi = self.non_propi
        valor = dict()
        for i in range(0, self.GetColumnCount()):
            nom = self.GetColumn(i).GetText()
            val = self.GetColumnWidth(i)
            valor[nom] = val
        wx.GetApp().set_propiedad(propi, valor)

    def set_size_columns(self):
        """ Restaura el ancho de las columnas
        """
        propi = self.non_propi
        valor = wx.GetApp().get_propiedad(propi)
        if valor:
            # menos la última columna, ya que tiene autosize con ListCtrlAutoWidthMixin
            for i in range(0, self.GetColumnCount()-1):
                nom = self.GetColumn(i).GetText()
                if nom in valor:
                    self.SetColumnWidth(i, valor[nom])
