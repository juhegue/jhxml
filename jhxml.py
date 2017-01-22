# -*- coding: utf-8 -*-

import sys
import os
import pickle
import datetime
import json
# import xml.etree.cElementTree as ET -> quita el CDATA
import lxml.etree as ET
import wx
import wx.lib.buttons as buttons
import wx.lib.agw.infobar as IB
import watch_file
import imagenes.imagenes as imagenes
import baseframe
import basespliter
import baselistctrl
import util
import template_jrxml
from constantes import *


CREA_COPIA_JRXML = True     # Crea una copia cada vez que seguarda
CREA_COPIA_XML = True       # ""


def dialogo_abrir_fic(win, wildcard, fichero=""):
    paths = []
    dlg = wx.FileDialog(win, message="Elija un fichero", defaultFile=fichero, wildcard=wildcard, style=wx.OPEN | wx.CHANGE_DIR)
    if dlg.ShowModal() == wx.ID_OK:
        paths = dlg.GetPaths()

    return paths


def dialogo_grabar_fic(win, extension_defecto, wildcard, fichero=""):
    resul = None
    dlg = wx.FileDialog(win, message="Grabar fichero como...", defaultFile=fichero, wildcard=wildcard, style=wx.SAVE)#defaultDir=os.getcwd(),
    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()

        if '__WXMSW__' not in wx.Platform:  # windows retorna la extensión si no se indica en el dialogo
            nom, ext = os.path.splitext(path)
            if len(ext) == 0 or ext == ".":
                path = "%s.%s" % (nom, extension_defecto)
            else:
                path = nom + ext

        if os.path.exists(path):
            txt = 'Ya existe el archivo ' + path + u'.\n¿Desea Reemplazarlo?'
            dlg1 = wx.MessageDialog(win, txt, 'Grabar fichero', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            if dlg1.ShowModal() == wx.ID_YES:
                resul = path
            dlg1.Destroy()
        else:
            resul = path

    dlg.Destroy()
    return resul


class Cursor:
    def __init__(self):
        self.pila = []
        self.busy = None

    def pon_reloj(self, texto=None):
        if texto and self.busy is None:
            self.busy = wx.BusyInfo(texto, self)

        self.Enable(False)
        c = self.GetCursor()
        self.pila.append(c)
        self.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
        wx.Yield()

    def quita_reloj(self):
        if self.busy:
            del self.busy
            self.busy = None

        self.Enable(True)
        c = self.pila.pop()
        self.SetCursor(c)
        self.Refresh()


class MainFrame(baseframe.BaseFrame, Cursor):
    namespace = "http://jasperreports.sourceforge.net/jasperreports"

    def __init__(self, app):
        baseframe.BaseFrame.__init__(self, None, wx.ID_ANY, app.GetAppName(), size=(600, 400))
        Cursor.__init__(self)

        self.app = app
        self.contador_campos = 0
        self.root_lxml = None
        self.xml_str = None
        self.jrxml_str = template_jrxml.template
        self.tree_item_xml = None
        self.campos = dict()
        self.relacion = ""
        self.busca_xml = ""
        self.busca_jrxml = ""
        self.sw_orden_xml = None
        self.sw_orden_jrxml = True
        self.copia_campos = None
        self.controls_habilita = list()
        self.watch = watch_file.WatchFile()

        self.SetIcon(imagenes.xml.GetIcon())

        self.imglst = wx.ImageList(16, 16, True)
        self.img_err = self.imglst.Add(wx.ArtProvider_GetBitmap(wx.ART_DELETE, wx.ART_OTHER, (16, 16)))
        self.img_propi = self.imglst.Add(wx.ArtProvider_GetBitmap(wx.ART_LIST_VIEW, wx.ART_OTHER, (16, 16)))
        self.img_libroa = self.imglst.Add(imagenes.libroa.GetBitmap())
        self.img_libro = self.imglst.Add(imagenes.libro.GetBitmap())
        self.img_marca = self.imglst.Add(imagenes.marca.GetBitmap())
        self.img_marca = self.imglst.Add(imagenes.marca.GetBitmap())
        self.img_cuadrog = self.imglst.Add(imagenes.cuadrog.GetBitmap())
        self.img_refrescar = self.imglst.Add(imagenes.refrescar.GetBitmap())

        self.infobar = IB.InfoBar(self)

        # box = wx.BoxSizer()
        # notebook = wx.Notebook(self, wx.ID_ANY, style=wx.NB_TOP)
        # box.Add(notebook, 1, wx.EXPAND)
        # p1 = wx.Panel(notebook, wx.ID_ANY)
        # notebook.AddPage(p1, u"Campos iReport", True)
        box = wx.BoxSizer(wx.VERTICAL)
        p1 = wx.Panel(self, wx.ID_ANY)
        box.Add(self.infobar, 0, wx.EXPAND)
        box.Add(p1, 1, wx.EXPAND)
        #

        self.pagina1(p1)
        self.SetSizer(box)
        self.CreateStatusBar(1, wx.ST_SIZEGRIP)
        self.set_size()

        wx.CallAfter(self.on_load)

    def pagina1(self, win):
        panel = wx.Panel(win, wx.ID_ANY)

        bmp = wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16))
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_xml_abrir = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_xml_abrir.SetToolTipString("Abrir fichero xml")

        st1 = wx.StaticText(panel, wx.ID_ANY, "xml:")
        self.fic_xml = wx.TextCtrl(panel, wx.ID_ANY)

        bmp = imagenes.refrescar.GetBitmap()
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_xml_refrescar = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_xml_refrescar.SetToolTipString("Refrescar xml")

        bmp = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, (16, 16))
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_xml_grabar = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_xml_grabar.SetToolTipString("Grabar fichero xml")

        btn_xml_grabar_nuevo = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_xml_grabar_nuevo.SetToolTipString("Grabar fichero xml 'bonito'")

        bmp = wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16))
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_jrxml_abrir = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_jrxml_abrir.SetToolTipString("Abrir fichero jrxml")

        st2 = wx.StaticText(panel, wx.ID_ANY, "jrxml:")
        self.fic_jrxml = wx.TextCtrl(panel, wx.ID_ANY)

        bmp = imagenes.refrescar.GetBitmap()
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_jrxml_refrescar = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_jrxml_refrescar.SetToolTipString("Refrescar jrxml")

        bmp = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE, wx.ART_OTHER, (16, 16))
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_jrxml_grabar = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_jrxml_grabar.SetToolTipString("Grabar fichero jrxml")

        bmp = wx.ArtProvider_GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_OTHER, (16, 16))
        mask = wx.Mask(bmp, wx.WHITE)
        bmp.SetMask(mask)
        btn_jrxml_grabar_nuevo = wx.BitmapButton(panel, -1, bmp, (15, 25), (bmp.GetWidth()+15, bmp.GetHeight()+15))
        btn_jrxml_grabar_nuevo.SetToolTipString("Grabar nuevo fichero jrxml")

        gbs = wx.GridBagSizer(5, 5)
        gbs.Add((2, 2), (0, 0), border=2, span=(1, 3))
        gbs.Add(btn_xml_abrir, (1, 0), border=2)
        gbs.Add(st1, (1, 1), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(self.fic_xml, (1, 2), flag=wx.EXPAND, border=2)
        gbs.Add(btn_xml_refrescar, (1, 3), border=2)
        gbs.Add(btn_xml_grabar, (1, 4), border=2)
        gbs.Add(btn_xml_grabar_nuevo, (1, 5), border=2)
        gbs.Add(btn_jrxml_abrir, (2, 0), border=2)
        gbs.Add(st2, (2, 1), flag=wx.ALIGN_CENTER | wx.ALL, border=2)
        gbs.Add(self.fic_jrxml, (2, 2), flag=wx.EXPAND, border=2)
        gbs.Add(btn_jrxml_refrescar, (2, 3), border=2)
        gbs.Add(btn_jrxml_grabar, (2, 4), border=2)
        gbs.Add(btn_jrxml_grabar_nuevo, (2, 5), border=2)
        gbs.Add((2, 2), (3, 0), border=2, span=(1, 3))
        gbs.AddGrowableCol(2)

        boxH = wx.BoxSizer(wx.HORIZONTAL)
        boxH.AddSpacer((2, 2))
        boxH.Add(gbs, 1, wx.EXPAND)
        boxH.AddSpacer((2, 2))
        panel.SetSizer(boxH)

        splitter = basespliter.BaseSplitter(win, "spliter")

        p1 = wx.Panel(splitter, style=wx.BORDER_THEME)

        bmp = wx.ArtProvider_GetBitmap(wx.ART_HELP_SETTINGS, wx.ART_OTHER, (16, 16))
        btn0 = buttons.GenBitmapButton(p1, wx.ID_ANY, bmp, size=(26, 26))
        self.cb_tagx = wx.CheckBox(p1, wx.ID_ANY, "Nombre", style=wx.CHK_3STATE | wx.CHK_ALLOW_3RD_STATE_FOR_USER)
        boxc = wx.BoxSizer(wx.HORIZONTAL)
        boxc.Add(btn0, 0, wx.ALL, border=2)
        boxc.Add(self.cb_tagx, 0, wx.ALL, border=2)

        self.tree_xml = wx.TreeCtrl(p1, style=wx.TR_HAS_BUTTONS)
        self.tree_xml.SetImageList(self.imglst)
        self.filtro_xml = wx.SearchCtrl(p1, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.filtro_xml.ShowCancelButton(True)

        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(boxc, 0, wx.ALL)
        box1.Add(self.tree_xml, 1, wx.EXPAND)
        box1.Add(self.filtro_xml, 0, wx.EXPAND)
        p1.SetSizer(box1)

        p2 = wx.Panel(splitter, style=wx.BORDER_THEME)

        bmp = imagenes.flechaup.GetBitmap()
        btn1 = buttons.GenBitmapButton(p2, wx.ID_ANY, bmp, size=(26, 26))
        bmp = imagenes.flechadown.GetBitmap()
        btn2 = buttons.GenBitmapButton(p2, wx.ID_ANY, bmp, size=(26, 26))
        bmp = wx.ArtProvider_GetBitmap(wx.ART_HELP_SETTINGS, wx.ART_OTHER, (16, 16))
        btn3 = buttons.GenBitmapButton(p2, wx.ID_ANY, bmp, size=(26, 26))
        self.cb_tagj = wx.CheckBox(p2, wx.ID_ANY, "Nombre", style=wx.CHK_3STATE | wx.CHK_ALLOW_3RD_STATE_FOR_USER)

        boxb = wx.BoxSizer(wx.HORIZONTAL)
        boxb.Add(btn1, 0, wx.ALL)
        boxb.Add(btn2, 0, wx.ALL)
        boxb.Add((10, 10), 0, wx.ALL)
        boxb.Add(btn3, 0, wx.ALL)
        boxb.Add((10, 10), 0, wx.ALL)
        boxb.Add(self.cb_tagj, 0, wx.ALL | wx.ALIGN_CENTER)

        self.list = baselistctrl.BaseListCtrl(p2, wx.ID_ANY, style=wx.LC_REPORT | wx.BORDER_NONE)# | wx.LC_SORT_ASCENDING)

        st3 = wx.StaticText(p2, wx.ID_ANY, "OPENERP_RELATIONS: ")
        st4 = wx.StaticText(p2, wx.ID_ANY, "sortField: ")
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(st3, 0, wx.ALL, border=5)
        box1.Add(st4, 0, wx.ALL, border=5)

        self.txt_relacion = wx.TextCtrl(p2, wx.ID_ANY)
        self.txt_campo_orden = wx.TextCtrl(p2, wx.ID_ANY)
        box2 = wx.BoxSizer(wx.VERTICAL)
        box2.Add(self.txt_relacion, 1, wx.EXPAND, border=5)
        box2.Add(self.txt_campo_orden, 1, wx.EXPAND, border=5)

        boxr = wx.BoxSizer(wx.HORIZONTAL)
        boxr.Add(box1, 0, wx.EXPAND)
        boxr.Add(box2, 1, wx.EXPAND)

        self.filtro_jrxml = wx.SearchCtrl(p2, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.filtro_jrxml.ShowCancelButton(True)

        box2 = wx.BoxSizer(wx.VERTICAL)
        box2.Add(boxb, 0, wx.ALL)
        box2.Add(boxr, 0, wx.EXPAND)
        box2.Add(self.list, 1, wx.EXPAND)
        box2.Add(self.filtro_jrxml, 0, wx.EXPAND)
        p2.SetSizer(box2)

        splitter.SetMinimumPaneSize(50)
        splitter.SplitVertically(p1, p2, splitter.get_size())

        boxV = wx.BoxSizer(wx.VERTICAL)
        boxV.Add(panel, 0, wx.EXPAND)
        boxV.Add(splitter, 1, wx.EXPAND)

        win.SetSizer(boxV)

        self.controls_habilita = [btn1, btn2, btn_jrxml_grabar, btn_jrxml_grabar_nuevo]

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.cb_tagx.Bind(wx.EVT_CHECKBOX, self.on_nombres_xlx)
        self.cb_tagj.Bind(wx.EVT_CHECKBOX, self.on_nombres_jrxlx)
        btn_xml_abrir.Bind(wx.EVT_BUTTON, self.on_abrir_xml)
        btn_xml_grabar.Bind(wx.EVT_BUTTON, self.on_grabar_xml)
        btn_xml_grabar_nuevo.Bind(wx.EVT_BUTTON, self.on_grabar_nuevo_xml)
        btn_jrxml_abrir.Bind(wx.EVT_BUTTON, self.on_abrir_jrxml)
        btn_jrxml_grabar.Bind(wx.EVT_BUTTON, self.on_grabar_jrxml)
        btn_jrxml_grabar_nuevo.Bind(wx.EVT_BUTTON, self.on_grabar_nuevo_jrxml)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_sel_tree_changed_xml, self.tree_xml)
        self.tree_xml.Bind(wx.EVT_RIGHT_DOWN, self.on_right_tree_xml)
        self.tree_xml.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.on_collapsed_tree_xml)
        self.tree_xml.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.on_expanding_tree_xml)
        self.tree_xml.Bind(wx.EVT_LEFT_DCLICK, self.on_dclick_tree_xml)
        self.tree_xml.Bind(wx.EVT_KEY_DOWN, self.on_tree_keydown)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down_list)
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.on_right_click_list)    # wxMSW
        self.list.Bind(wx.EVT_RIGHT_UP, self.on_right_click_list)               # wxGTK
        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_select_list)
        self.list.Bind(wx.EVT_KEY_DOWN, self.on_list_keydown)
        btn0.Bind(wx.EVT_BUTTON, self.on_tree_ordena)
        btn1.Bind(wx.EVT_BUTTON, self.on_list_arriba)
        btn2.Bind(wx.EVT_BUTTON, self.on_list_abajo)
        btn3.Bind(wx.EVT_BUTTON, self.on_list_ordena)
        self.filtro_xml.Bind(wx.EVT_TEXT_ENTER, self.on_filtro_xml)
        self.filtro_xml.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.on_filtro_cancel_xml)
        self.filtro_jrxml.Bind(wx.EVT_TEXT_ENTER, self.on_filtro_jrxml)
        self.filtro_jrxml.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.on_filtro_cancel_jrxml)
        btn_xml_refrescar.Bind(wx.EVT_BUTTON, self.on_tree_xml_refresca)
        btn_jrxml_refrescar.Bind(wx.EVT_BUTTON, self.on_list_jrxml_refresca)
        self.list.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.on_end_edit)

    @property
    def contador(self):
        self.contador_campos += 1
        return self.contador_campos

    def on_load(self):
        tag1 = self.app.get_propiedad("tag1") or 0
        tag2 = self.app.get_propiedad("tag2") or 0
        xml = self.app.get_propiedad("xml") or ""
        jrxml = self.app.get_propiedad("jrxml") or ""

        self.cb_tagx.Set3StateValue(tag1)
        self.cb_tagj.Set3StateValue(tag2)
        self.abrir_xml(xml)
        self.abrir_jrxml(jrxml)

    def abrir_xml(self, fichero):
        if fichero:
            try:
                self.fic_xml.Value = fichero
                with open(fichero, 'r') as f:
                    self.xml_str = f.read()

                self.sw_orden_xml = None
                self.carga_xml(self.orden_xml())

            except IOError, e:
                wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def abrir_jrxml(self, fichero):
        if fichero:
            self.fic_jrxml.Value = fichero
            self.infobar.Dismiss()
            self.watch.stop()
            try:
                with open(fichero, 'r') as f:
                    self.jrxml_str = f.read()

                self.watch.start(fichero, self.jrxml_modificado)
                self.parse_jrxml()
                self.carga_jrxml()

            except IOError, e:
                pass

            self.habilita(True)

    def on_salir(self, evt):
        self.Destroy()

    def on_abrir_xml(self, evt):
        fichero = dialogo_abrir_fic(self, "Archivos xml (*.xml)|*.xml|Todos los archivos (*.*)|*")
        if fichero:
            self.abrir_xml(fichero[0])

    def on_grabar_xml(self, evt):
        def conta(fic):
            f = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            return fic + f

        xml_str = self.orden_xml(False)
        try:
            fic = dialogo_grabar_fic(self, "xml", "Archivos xml (*.xml)|*.xml|Todos los archivos (*.*)|*", self.fic_xml.Value)
            if fic:
                if CREA_COPIA_XML:
                    self.graba_copia(fic)

                with open(fic, 'w') as f:
                    f.write(xml_str)
                self.fic_xml.Value = fic
                self.info("Fichero xml grabado satisfactoriamente.")
        except Exception, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def on_abrir_jrxml(self, evt):
        fichero = dialogo_abrir_fic(self, "Archivos jrxml (*.jrxml)|*.jrxml|Todos los archivos (*.*)|*")
        if fichero:
            self.abrir_jrxml(fichero[0])

    def on_grabar_jrxml(self, evt):
        if self.modifica_jrxml():
            try:
                fic = dialogo_grabar_fic(self, "jxml", "Archivos jrxml (*.jrxml)|*.jrxml|Todos los archivos (*.*)|*", self.fic_jrxml.Value)
                if fic:
                    if CREA_COPIA_JRXML:
                        self.graba_copia(fic)

                    self.watch.stop()
                    self.infobar.Dismiss()

                    with open(fic, 'w') as f:
                        f.write(self.jrxml_str)

                    self.watch.start(fic, self.jrxml_modificado)
                    self.fic_jrxml.Value = fic
                    self.info("Fichero jrxml grabado satisfactoriamente.")

            except Exception, e:
                wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def on_grabar_nuevo_xml(self, evt):
        xml_str = self.orden_xml(False, pretty_print=True)
        try:
            fic = dialogo_grabar_fic(self, "xml", "Archivos xml (*.xml)|*.xml|Todos los archivos (*.*)|*", self.fic_xml.Value)
            if fic:
                if CREA_COPIA_XML:
                    self.graba_copia(fic)

                with open(fic, 'w') as f:
                    f.write(xml_str)
                self.fic_xml.Value = fic
                self.info("Fichero xml grabado satisfactoriamente.")
        except Exception, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def on_grabar_nuevo_jrxml(self, evt):
        self.jrxml_str = template_jrxml.template
        if self.modifica_jrxml():
            try:
                fic = dialogo_grabar_fic(self, "jrxml", "Archivos jrxml (*.jrxml)|*.jrxml|Todos los archivos (*.*)|*", self.fic_jrxml.Value)
                if fic:
                    if CREA_COPIA_JRXML:
                        self.graba_copia(fic)

                    self.watch.stop()
                    self.infobar.Dismiss()

                    with open(fic, 'w') as f:
                        f.write(self.jrxml_str)

                    self.watch.start(fic, self.jrxml_modificado)
                    self.fic_jrxml.Value = fic
                    self.info("Fichero jrxml grabado satisfactoriamente.")

            except Exception, e:
                wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def on_tree_ordena(self, evt):
        if self.sw_orden_xml is None:
            self.sw_orden_xml = True
        else:
            self.sw_orden_xml = not self.sw_orden_xml

        index = self.tree_xml.GetSelection()
        data = self.tree_xml.GetPyData(index) if index.IsOk() else None
        self.carga_xml(self.orden_xml())
        if data:
            self.expand_tree(data[0])
            # index = util.tree_get_item_data(self.tree_xml, data)
            # if index:
            #     self.tree_xml.SelectItem(index)
            #     self.tree_xml.EnsureVisible(index)

    def on_nombres_xlx(self, evt):
        index = self.tree_xml.GetSelection()
        data = self.tree_xml.GetPyData(index) if index.IsOk() else None
        self.carga_xml(self.orden_xml())
        if data:
            self.expand_tree(data[0])
            # index = util.tree_get_item_data(self.tree_xml, data)
            # if index:
            #     self.tree_xml.SelectItem(index)
            #     self.tree_xml.EnsureVisible(index)

    def on_nombres_jrxlx(self, evt):
        index = self.list.GetFirstSelected()
        self.carga_jrxml()
        if index >= 0:
            self.list.Select(0, 0)
            self.list.Select(index)
            self.list.EnsureVisible(index)

    def on_sel_tree_changed_xml(self, evt):
        index = evt.GetItem()
        self.tree_item_xml = evt.GetItem()

        valor = self.tree_xml.GetPyData(index)
        self.info(valor)

    def on_right_tree_xml(self, evt):
        if not hasattr(self, "IDX1"):
            self.IDX1 = wx.NewId()
            self.IDX2 = wx.NewId()
            self.IDX3 = wx.NewId()
            self.IDX4 = wx.NewId()
            self.IDX5 = wx.NewId()
            self.IDX6 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_add_campo, id=self.IDX1)
            self.Bind(wx.EVT_MENU, self.on_add_relacion, id=self.IDX2)
            self.Bind(wx.EVT_MENU, self.on_clipboar_tree, id=self.IDX3)
            self.Bind(wx.EVT_MENU, self.on_copia_nodo, id=self.IDX4)
            self.Bind(wx.EVT_MENU, self.on_borra_nodo, id=self.IDX5)
            self.Bind(wx.EVT_MENU, self.on_pega_nodo, id=self.IDX6)

        menu = wx.Menu()
        item1 = wx.MenuItem(menu, self.IDX1, "Añadir campo")
        item2 = wx.MenuItem(menu, self.IDX2, u"Añadir relación")
        item3 = wx.MenuItem(menu, self.IDX3, u"Copiar 'Ctrl+C'")
        item4 = wx.MenuItem(menu, self.IDX4, "Copiar nodo")
        item5 = wx.MenuItem(menu, self.IDX5, "Borrar nodo")
        item6 = wx.MenuItem(menu, self.IDX6, "Pegar nodo")
        menu.AppendItem(item1)
        menu.AppendSeparator()
        menu.AppendItem(item2)
        menu.AppendSeparator()
        menu.AppendItem(item3)
        menu.AppendSeparator()
        menu.AppendItem(item4)
        menu.AppendItem(item5)
        menu.AppendItem(item6)

        root = self.tree_xml.GetRootItem()
        parent = None
        if self.tree_item_xml and self.tree_item_xml != root:
            parent = self.tree_xml.GetItemParent(self.tree_item_xml)

        if self.tree_item_xml and self.tree_item_xml != root and parent != root:
            if self.has_children(self.tree_item_xml):
                item1.Enable(False)
            else:
                item2.Enable(False)
        else:
            item1.Enable(False)
            item2.Enable(False)
            item3.Enable(False)

        if not evt.ControlDown():
            item4.Enable(False)
            item5.Enable(False)
            item6.Enable(False)

        self.info("Pulsando 'Ctrl' activa las opciones de nodo. Doble-Click Añade campo")
        self.PopupMenu(menu)
        menu.Destroy()
        self.info("")

    def on_add_campo(self, evt):
        if self.tree_item_xml:
            if not self.has_children(self.tree_item_xml):
                self.append_campo(self.tree_item_xml)

    def on_add_relacion(self, evt):
        if self.tree_item_xml:
            if self.has_children(self.tree_item_xml):
                self.append_relacion(self.tree_item_xml)

    def on_clipboar_tree(self, evt):
        self.tree_copiar()

    def on_clipboar_list(self, evt):
        self.list_copiar()

    def on_marca_tree(self, evt):
        root = self.tree_xml.GetRootItem()
        if root.IsOk():
            util.tree_collapse(self.tree_xml, root)
        index = self.list.GetFirstSelected()
        data = self.list.GetItemData(index)
        self.expand_tree(self.campos[data][0])
        self.list.SetFocus()

    def on_add_campo_ord(self, evt):
        txt = util.txt_2_list_str(self.txt_campo_orden.Value)
        if txt is None:
            txt = list()

        index = self.list.GetFirstSelected()

        data = self.list.GetItemData(index)
        campo = self.campos[data][1]
        campo = str(campo)

        txt.append(campo)
        self.txt_campo_orden.Value = str(txt)

    def on_set_string(self, evt):
        index = self.list.GetFirstSelected()
        while index >= 0:
            self.list.SetStringItem(index, 1, "java.lang.String")
            data = self.list.GetItemData(index)
            self.campos[data][2] = "java.lang.String"
            index = self.list.GetNextSelected(index)

    def on_set_double(self, evt):
        index = self.list.GetFirstSelected()
        while index >= 0:
            self.list.SetStringItem(index, 1, "java.lang.Double")
            data = self.list.GetItemData(index)
            self.campos[data][2] = "java.lang.Double"
            index = self.list.GetNextSelected(index)

    def on_set_date(self, evt):
        index = self.list.GetFirstSelected()
        while index >= 0:
            self.list.SetStringItem(index, 1, "java.util.Date")
            data = self.list.GetItemData(index)
            self.campos[data][2] = "java.util.Date"
            index = self.list.GetNextSelected(index)

    def on_right_down_list(self, evt):
        x = evt.GetX()
        y = evt.GetY()
        index, flags = self.list.HitTest((x, y))

        if index != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(index)

        evt.Skip()

    def on_right_click_list(self, evt):
        if not hasattr(self, "IDJ1"):
            self.IDJ1 = wx.NewId()
            self.IDJ2 = wx.NewId()
            self.IDJ3 = wx.NewId()
            self.IDJ4 = wx.NewId()
            self.IDJ5 = wx.NewId()
            self.IDJ6 = wx.NewId()
            self.IDJ7 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.on_set_string, id=self.IDJ1)
            self.Bind(wx.EVT_MENU, self.on_set_double, id=self.IDJ2)
            self.Bind(wx.EVT_MENU, self.on_set_date, id=self.IDJ3)
            self.Bind(wx.EVT_MENU, self.on_del_campo, id=self.IDJ4)
            self.Bind(wx.EVT_MENU, self.on_clipboar_list, id=self.IDJ5)
            self.Bind(wx.EVT_MENU, self.on_marca_tree, id=self.IDJ6)
            self.Bind(wx.EVT_MENU, self.on_add_campo_ord, id=self.IDJ7)

        menu = wx.Menu()
        item1 = wx.MenuItem(menu, self.IDJ1, "Asignar String")
        item2 = wx.MenuItem(menu, self.IDJ2, "Asignar Double")
        item3 = wx.MenuItem(menu, self.IDJ3, "Asignar Date")
        if self.list.GetSelectedItemCount() == 1:
            item4 = wx.MenuItem(menu, self.IDJ4, "Borrar campo")
        else:
            item4 = wx.MenuItem(menu, self.IDJ4, "Borrar campos")
        item5 = wx.MenuItem(menu, self.IDJ5, "Copiar 'Ctrl+C'")
        item6 = wx.MenuItem(menu, self.IDJ6, "Marcar 'Enter'")
        item7 = wx.MenuItem(menu, self.IDJ7, u"Añadir campo orden")

        menu.AppendItem(item1)
        menu.AppendItem(item2)
        menu.AppendItem(item3)
        menu.AppendSeparator()
        menu.AppendItem(item7)
        menu.AppendSeparator()
        menu.AppendItem(item4)
        menu.AppendSeparator()
        menu.AppendItem(item5)
        menu.AppendItem(item6)

        self.info("Doble-Click modifica el nombre del campo.")
        self.PopupMenu(menu)
        menu.Destroy()

    def on_item_select_list(self, evt):
        index = evt.m_itemIndex
        data = self.list.GetItemData(index)
        self.info(self.campos[data])
        evt.Skip()

    def on_collapsed_tree_xml(self, evt):
        self.pon_reloj()
        index = evt.GetItem()
        util.tree_collapse(self.tree_xml, index)
        self.quita_reloj()

    def on_expanding_tree_xml(self, evt):
        parent = evt.GetItem()
        index, cookie = self.tree_xml.GetFirstChild(parent)
        text = self.tree_xml.GetItemText(index)
        if text == "|HIJO":
            elem, tree_lxml = self.tree_xml.GetPyData(index)
            self.tree_xml.Delete(index)
            nombres = self.cb_tagx.Get3StateValue()

            def add(parent, elem, nivel):
                for e in elem:
                    if nivel >= 1:
                        index = self.tree_xml.AppendItem(parent, "|HIJO", data=None)
                        self.tree_xml.SetPyData(index, (elem, tree_lxml))
                        break

                    nom = e.tag
                    if nombres == 1:
                        nom = nom.split("-")[0]
                    if nombres == 2:
                        nom = nom.split("-")
                        nom = nom[1] if len(nom) == 2 else nom[0]

                    index = self.tree_xml.AppendItem(parent, nom, data=None)
                    xpath = tree_lxml.getpath(e)
                    data = (xpath, e.text)
                    self.tree_xml.SetPyData(index, data)
                    if len(e):
                        self.tree_xml.SetItemImage(index, self.img_libro, wx.TreeItemIcon_Expanded)
                        self.tree_xml.SetItemImage(index, self.img_libroa, wx.TreeItemIcon_Normal)
                    else:
                        self.tree_xml.SetItemImage(index, self.img_cuadrog, wx.TreeItemIcon_Normal)
                    add(index, e, nivel + 1)
            add(parent, elem, 0)

    def on_del_campo(self, evt):
        tmp = list()
        index = self.list.GetFirstSelected()
        while index >= 0:
            tmp.append(index)
            index = self.list.GetNextSelected(index)

        tmp.reverse()
        for index in tmp:
            key = self.list.GetItemData(index)
            del self.campos[key]
            self.list.DeleteItem(index)

        n = self.list.GetItemCount()
        if index < n:
            self.list.Select(index)
        elif n >= 0:
            self.list.Select(n - 1)

    def on_dclick_tree_xml(self, evt):
        pt = evt.GetPosition()
        index, flags = self.tree_xml.HitTest(pt)
        if not index.IsOk():
            return

        if not index or self.has_children(index):
            return
        
        self.append_campo(index)

    def on_tree_keydown(self, evt):
        key = evt.KeyCode
        if evt.ControlDown() and key in (ord('C'), ord('C')):
            self.tree_copiar()
        else:
            evt.Skip()
            
    def on_list_keydown(self, evt):
        key = evt.KeyCode
        if evt.ControlDown() and key in (ord('C'), ord('C')):
            self.list_copiar()
        elif key == wx.WXK_DELETE:
            self.on_del_campo(evt)
        elif key == wx.WXK_RETURN:
            self.on_marca_tree(evt)
        else:
            evt.Skip()

    def on_list_arriba(self, evt):
        index = self.list.GetFirstSelected()
        if index > 0:
            [self.list.Select(i, 0) for i in range(0, self.list.GetItemCount())]

            nombres = self.cb_tagj.Get3StateValue()

            data0 = self.list.GetItemData(index -1)
            des0, nom0, tipo0 = self.campos[data0]
            des0 = self.nombre_campo(des0, nombres)
            nom0 = self.nombre_campo(nom0, nombres)

            data1 = self.list.GetItemData(index)
            des1, nom1, tipo1 = self.campos[data1]
            des1 = self.nombre_campo(des1, nombres)
            nom1 = self.nombre_campo(nom1, nombres)

            self.list.SetItemText(index - 1, nom1)
            self.list.SetStringItem(index - 1, 1, tipo1)
            self.list.SetStringItem(index - 1, 2, des1)

            self.list.SetItemText(index, nom0)
            self.list.SetStringItem(index, 1, tipo0)
            self.list.SetStringItem(index, 2, des0)

            campo = self.campos[data0]
            self.campos[data0] = self.campos[data1]
            self.campos[data1] = campo

            self.list.Select(index - 1)
            self.list.EnsureVisible(index - 1)

    def on_list_abajo(self, evt):
        index = self.list.GetFirstSelected()
        if index < self.list.GetItemCount() - 1:
            [self.list.Select(i, 0) for i in range(0, self.list.GetItemCount())]

            nombres = self.cb_tagj.Get3StateValue()

            data0 = self.list.GetItemData(index)
            des0, nom0, tipo0 = self.campos[data0]
            des0 = self.nombre_campo(des0, nombres)
            nom0 = self.nombre_campo(nom0, nombres)

            data1 = self.list.GetItemData(index + 1)
            des1, nom1, tipo1 = self.campos[data1]
            des1 = self.nombre_campo(des1, nombres)
            nom1 = self.nombre_campo(nom1, nombres)

            self.list.SetItemText(index, nom1)
            self.list.SetStringItem(index, 1, tipo1)
            self.list.SetStringItem(index, 2, des1)

            self.list.SetItemText(index + 1, nom0)
            self.list.SetStringItem(index + 1, 1, tipo0)
            self.list.SetStringItem(index + 1, 2, des0)

            campo = self.campos[data0]
            self.campos[data0] = self.campos[data1]
            self.campos[data1] = campo

            self.list.Select(index + 1)
            self.list.EnsureVisible(index + 1)

    def on_list_ordena(self, evt):
        index = self.list.GetFirstSelected()
        data = self.list.GetItemData(index)
        self.carga_jrxml(ordena_alfa=True)
        if index >= 0:
            self.list.Select(0, 0)
            for i in range(0, self.list.GetItemCount()):
                if data == self.list.GetItemData(i):
                    self.list.Select(i)
                    self.list.EnsureVisible(i)

        self.sw_orden_jrxml = not self.sw_orden_jrxml

    def on_filtro_xml(self, evt):
        self.busca_xml = self.filtro_xml.GetValue().strip()
        if not self.busca_xml:
            self.on_filtro_cancel_xml(evt)
            return

        if len(self.busca_xml) < 2:
            wx.MessageBox("Debe de indicar al menos 2 letras", APLICACION, wx.ICON_WARNING)
        else:
            self.carga_xml(self.orden_xml())
            self.tree_xml.ExpandAll()
            # root = self.tree_xml.GetRootItem()
            # if root:
            #    self.tree_xml.SelectItem(root)
            #    self.tree_xml.EnsureVisible(root)

    def on_filtro_cancel_xml(self, evt):
        self.filtro_xml.SetValue("")
        self.busca_xml = ""
        self.carga_xml(self.orden_xml())

    def on_filtro_jrxml(self, evt):
        self.busca_jrxml = self.filtro_jrxml.GetValue().strip().lower()
        if not self.busca_jrxml:
            self.habilita(True)
        else:
            self.habilita(False)

        self.carga_jrxml()

    def on_filtro_cancel_jrxml(self, evt):
        self.habilita(True)

        self.filtro_jrxml.SetValue("")
        self.busca_jrxml = ""
        self.carga_jrxml()

    def on_tree_xml_refresca(self, evt):
        self.abrir_xml(self.fic_xml.Value)

    def on_list_jrxml_refresca(self, evt):
        self.abrir_jrxml(self.fic_jrxml.Value)

    def on_end_edit(self, evt):
        index = evt.m_item
        key = index.Data
        data = self.campos[key]
        self.campos[key][1] = index.Text

    def info(self, data):
        self.SetStatusText(str(data), 0)

    def orden_xml(self, con_busca=True, pretty_print=False):
        nombres = self.cb_tagx.Get3StateValue()
        primero_padres = True

        def ordena_tag(a, b):
            ha = a.getchildren()
            hb = b.getchildren()
            if (ha and hb) or (not ha and not hb):
                a = a.tag
                b = b.tag
                # if nombres == 1:
                #     a = a.split("-")[0]
                #     b = b.split("-")[0]
                #
                if nombres == 2:
                    a = a.split("-")
                    b = b.split("-")
                    a = a[1] if len(a) == 2 else a[0]
                    b = b[1] if len(b) == 2 else b[0]

                if self.sw_orden_xml:
                    return cmp(a.upper(), b.upper())
                else:
                    return cmp(b.upper(), a.upper())
            else:
                if primero_padres:
                    return -1 if ha else 1
                else:
                    return 1 if ha else -1

        @util.static_vars(conta=0)
        def ordena_elemen(nuevo, elem):
            if ordena_elemen.conta % 5000 == 0: wx.Yield()
            ordena_elemen.conta += 1
            tmp = list()
            [tmp.append(e) for e in elem]
            for e in sorted(tmp, cmp=ordena_tag):
                hijo = ET.SubElement(nuevo, e.tag)
                hijo.text = e.text
                ordena_elemen(hijo, e)

        if self.busca_xml and con_busca:
            root_xml = ET.fromstring(self.get_busca_xml(self.busca_xml))
        else:
            self.root_lxml = root_xml = ET.fromstring(self.xml_str)

        if self.sw_orden_xml is None:
            nuevo = root_xml
        else:
            self.pon_reloj("Ordenando...")
            nuevo = ET.Element(root_xml.tag)
            ordena_elemen(nuevo, root_xml)
            self.quita_reloj()

        return ET.tostring(nuevo, pretty_print=pretty_print)

    def carga_xml(self, xml_str, max_nivel=1):
        if not xml_str:
            return

        self.pon_reloj("Cargando xml...")
        self.tree_xml.Freeze()
        try:
            self.tree_xml.DeleteAllItems()

            nombres = self.cb_tagx.Get3StateValue()
            root_xml = ET.fromstring(xml_str)
            tree_lxml = ET.ElementTree(root_xml)

            font = self.tree_xml.GetFont()
            if not util.is_windows or util.bits == 64:
                font.SetWeight(wx.BOLD)

            root_tree = self.tree_xml.AddRoot(root_xml.tag)
            self.tree_xml.SetItemFont(root_tree, font)
            self.tree_xml.SetItemImage(root_tree, self.img_libro, wx.TreeItemIcon_Expanded)
            self.tree_xml.SetItemImage(root_tree, self.img_libroa, wx.TreeItemIcon_Normal)

            def add(parent, elem, nivel):
                for e in elem:
                    if nivel > max_nivel:
                        index = self.tree_xml.AppendItem(parent, "|HIJO", data=None)
                        self.tree_xml.SetPyData(index, (elem, tree_lxml))
                        break

                    nom = e.tag
                    if nombres == 1:
                        nom = nom.split("-")[0]
                    if nombres == 2:
                        nom = nom.split("-")
                        nom = nom[1] if len(nom) == 2 else nom[0]

                    index = self.tree_xml.AppendItem(parent, nom, data=None)
                    data = (tree_lxml.getpath(e), e.text)
                    self.tree_xml.SetPyData(index, data)
                    if len(e):
                        self.tree_xml.SetItemImage(index, self.img_libro, wx.TreeItemIcon_Expanded)
                        self.tree_xml.SetItemImage(index, self.img_libroa, wx.TreeItemIcon_Normal)
                    else:
                        self.tree_xml.SetItemImage(index, self.img_cuadrog, wx.TreeItemIcon_Normal)
                    add(index, e, nivel + 1)

            add(root_tree, root_xml, 0)

            self.tree_xml.Expand(root_tree)
            index, cookie = self.tree_xml.GetFirstChild(root_tree)
            if index.IsOk():
                self.tree_xml.Expand(index)
            self.tree_xml.SelectItem(root_tree)

        except ET.XMLSyntaxError, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

        finally:
            self.tree_xml.Thaw()
            self.quita_reloj()

    def parse_jrxml(self):
        if not self.jrxml_str:
            return

        self.pon_reloj()
        try:
            root_jrxml = ET.fromstring(self.jrxml_str)
            self.campos = dict()
            self.relacion = ""

            propertys = root_jrxml.xpath("//nm:property", namespaces={"nm": self.namespace})
            for property in propertys:
                name = property.attrib["name"]
                value = property.attrib["value"]
                if name == "OPENERP_RELATIONS":
                    self.relacion = value

            campos = dict()
            fields = root_jrxml.xpath("//nm:field", namespaces={"nm": self.namespace})
            for n, field in enumerate(fields):
                name = field.attrib["name"]
                for e in field:
                    value = e.text
                    campos[name] = (n, value, "java.lang.String")

            campos_orden = list()
            fields = root_jrxml.xpath("//nm:sortField", namespaces={"nm": self.namespace})
            for field in fields:
                name = field.attrib["name"]
                campos_orden.append(name)

            fields = root_jrxml.xpath("//nm:variable", namespaces={"nm": self.namespace})
            for field in fields:
                name = field.attrib["name"]
                for e in field:
                    if name in campos:
                        n, value, clase = campos[name]
                        clase = field.attrib["class"]
                        if clase == "java.lang.String" and e.text.find("SimpleDateFormat") > 0:
                            clase = "java.util.Date"
                        if clase != "java.lang.String":
                            campos[name] = (n, value, clase)

            def ordena_campo(a, b):
                return cmp(a[0], b[0])

            for k, v in sorted(campos.iteritems(), cmp=ordena_campo):
                self.campos[self.contador] = [v[1], k, v[2]]

            if campos_orden:
                self.txt_campo_orden.Value = str(campos_orden)
            else:
                self.txt_campo_orden.Value = ""

        except ET.XMLSyntaxError, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)
        finally:
            self.quita_reloj()

    def carga_jrxml(self, ordena_alfa=False):
        self.pon_reloj("Cargando jrxml...")
        self.list.Freeze()
        self.list.DeleteAllItems()

        nombres = self.cb_tagj.Get3StateValue()

        def ordena_campo(a, b):
            a = a[1][0]
            b = b[1][0]
            if self.sw_orden_jrxml:
                return cmp(self.nombre_campo(a, nombres).upper(), self.nombre_campo(b, nombres).upper())
            else:
                return cmp(self.nombre_campo(b, nombres).upper(), self.nombre_campo(a, nombres).upper())

        def existe_tag(tag):
            if self.root_lxml is not None:
                index = self.root_lxml.xpath(tag)
                return index

        # pasa los campos a una lista
        campos = list()
        for k, v in sorted(self.campos.iteritems()):
            campos.append((k, v))

        self.campos = dict()

        if ordena_alfa:
            tmp = list()
            for k, v in (sorted(campos, cmp=ordena_campo)):
                tmp.append((k, v))
            campos = tmp

        for nn, c in enumerate(campos):
            n, (k, v, t) = c
            if self.busca_jrxml:
                if k.lower().find(self.busca_jrxml) < 0 and v.lower().find(self.busca_jrxml) < 0:
                    continue

            des = self.nombre_campo(k, nombres)
            campo = self.nombre_campo(v, nombres)
            index = self.list.InsertStringItem(sys.maxint, campo)
            self.list.SetStringItem(index, 1, t)
            self.list.SetStringItem(index, 2, des)
            self.list.SetItemData(index, nn + 1)
            if not existe_tag(k):
                item = self.list.GetItem(index)
                item.SetTextColour(wx.RED)
                self.list.SetItem(item)

            self.campos[nn + 1] = [k, v, t]

        if self.list.GetItemCount() > 0:
            self.list.Select(0)

        self.txt_relacion.Value = self.relacion

        self.list.Thaw()
        self.quita_reloj()

    def append_campo(self, index):
        data = self.get_name_xpath(index)
        if data:
            nom, des = data
            nom = self.name_no_duplicado(nom)
            conta = self.contador

            self.campos[conta] = [des, nom, "java.lang.String"]

            nombres = self.cb_tagj.Get3StateValue()
            des = self.nombre_campo(des, nombres)
            nom = self.nombre_campo(nom, nombres)

            index = self.list.InsertStringItem(sys.maxint, nom)
            self.list.SetStringItem(index, 1, "java.lang.String")
            self.list.SetStringItem(index, 2, des)
            self.list.SetItemData(index, conta)
            [self.list.Select(i, 0) for i in range(0, self.list.GetItemCount())]
            self.list.Select(index)
            self.list.EnsureVisible(index)

    def name_no_duplicado(self, name):
        """Si existe el nombre le concatena un contador, imita al ireport"""
        for c, n, t in self.campos.itervalues():
            if n == name:
                conta = 0
                lname = len(name)
                for c, n, t in self.campos.itervalues():
                    if n[:lname] == name:
                        if n == name:
                            conta = 2
                        else:
                            try:
                                tmp = int(n[lname:])
                                if tmp >= conta:
                                    conta = tmp + 1
                            except:
                                pass
                name = "%s%s" % (name, conta)
                break
        return name

    @staticmethod
    def nombre_campo(path, tipo):
        nuevo = list()
        for campo in path.split("/"):
            if tipo == 1:
                nom = campo.split("-")
                campo = nom[0]
            if tipo == 2:
                nom = campo.split("-")
                if len(nom) == 1:
                    nom = nom[0]
                else:
                    nom = nom[1]
                campo = nom
            nuevo.append(campo)
        return "/".join(nuevo)

    def append_relacion(self, index):
        data = self.tree_xml.GetPyData(index)
        if data:
            tmp = data[0].split("/")
            del tmp[0]
            del tmp[0]
            del tmp[0]
            nom = list()
            for t in tmp:
                t = t.split("-")
                nom.append(t[len(t) - 1])
            name = "['%s']" % "/".join(nom)
            self.relacion = name
            self.txt_relacion.Value = name

    def modifica_jrxml(self):
        self.pon_reloj()

        parser = ET.XMLParser(strip_cdata=False, remove_blank_text=True)
        root_jrxml = ET.fromstring(self.jrxml_str, parser)

        queryString = root_jrxml.xpath("//x:queryString", namespaces={"x": self.namespace})
        if not queryString:
            self.quita_reloj()
            wx.MessageBox("Tag no encontrado 'queryString'\n(Debe definir language='xPath')", APLICACION, wx.ICON_ERROR)
            return False

        queryString_parent = queryString[0].getparent()

        # Busca la property con name OPENERP_RELATIONS y la borra
        propertys = root_jrxml.xpath("//nm:property", namespaces={"nm": self.namespace})
        for property in propertys:
            data = property.attrib
            if data["name"] == "OPENERP_RELATIONS":
                property.getparent().remove(property)

        # Busca todos los fields y los borra
        nom_fields = list()
        fields = root_jrxml.xpath("//nm:field", namespaces={"nm": self.namespace})
        for field in fields:
            nom = field.attrib["name"]
            nom_fields.append(nom)
            field.getparent().remove(field)

        # Busca todos los sortField y los borra
        fields = root_jrxml.xpath("//nm:sortField", namespaces={"nm": self.namespace})
        for field in fields:
            nom = field.attrib["name"]
            field.getparent().remove(field)

        # Busca las variables con el nombre=field y las borra
        variables = root_jrxml.xpath("//nm:variable", namespaces={"nm": self.namespace})
        for variable in variables:
            nom = variable.attrib["name"]
            if nom in nom_fields:
                variable.getparent().remove(variable)

        # Añade la relacion al inicio (el parent de queryString)
        if self.relacion:
            nuevo = ET.Element("{%s}property" % self.namespace, name="OPENERP_RELATIONS")
            nuevo.set("value", self.relacion)
            queryString_parent.insert(0, nuevo)

        # Añade los fields despues de queryString
        tmp = list()
        for k, (des, name, tipo) in sorted(self.campos.iteritems()):
            nuevo = ET.Element("{%s}field" % self.namespace, name=name)
            nuevo.set("class", "java.lang.String")
            body = ET.SubElement(nuevo, "{%s}fieldDescription" % self.namespace)
            body.text = ET.CDATA(des)
            tmp.append(nuevo)

        # Añade los sortField despues de los fields
        campos_orden = util.txt_2_list_str(self.txt_campo_orden.Value)
        if campos_orden:
            for name in campos_orden:
                nuevo = ET.Element("{%s}sortField" % self.namespace, name=name)
                tmp.append(nuevo)

        # Y las variables date y double
        for k, (des, name, tipo) in sorted(self.campos.iteritems()):
            if tipo == "java.lang.Double":
                nuevo = ET.Element("{%s}variable" % self.namespace, name=name)
                nuevo.set("class", "java.lang.Double")
                body = ET.SubElement(nuevo, "{%s}variableExpression" % self.namespace)
                body.text = ET.CDATA(template_jrxml.double % (name, name, name, name, name, name, name, name, name))
                tmp.append(nuevo)
            if tipo == "java.util.Date":
                nuevo = ET.Element("{%s}variable" % self.namespace, name=name)
                nuevo.set("class", "java.lang.String")
                body = ET.SubElement(nuevo, "{%s}variableExpression" % self.namespace)
                body.text = ET.CDATA(template_jrxml.date % (name, name, name))
                tmp.append(nuevo)

        for e in reversed(tmp):
            queryString_parent.insert(queryString_parent.index(queryString[0])+1, e)

        self.jrxml_str = ET.tostring(root_jrxml, encoding="UTF-8", xml_declaration=True, pretty_print=True)

        self.quita_reloj()
        return True

    def get_busca_xml(self, busca):
        self.pon_reloj("Buscando...")

        # busca = "//*[starts-with(local-name(), '%s')]" % busca
        busca = "//*[contains(local-name(), '%s')]" % busca

        encontrados = list()
        elems = self.root_lxml.xpath(busca)
        for e in elems:
            def recorre(e, l):
                l.insert(0, e)
                p = e.getparent()
                if p is not None:
                    recorre(p, l)
            lista = list()
            recorre(e, lista)
            encontrados.append(lista)

        nuevo = ET.fromstring("<data><record></record></data>")
        for e in encontrados:
            xpath = ""
            for t in e:
                xpath += "/" + t.tag
                index = nuevo.xpath(xpath)
                if index:
                    parent = index[0]
                else:
                    parent = ET.SubElement(parent, t.tag, t.attrib)
                    parent.text = t.text

        resul = ET.tostring(nuevo)

        self.quita_reloj()
        return resul

    def get_name_xpath(self, index):
        data = self.tree_xml.GetPyData(index)
        if data:
            xpath = data[0]
            nom = xpath.split("/")
            nom = nom[len(nom) - 1]
            return nom, xpath

    def has_children(self, index):
        data = self.get_name_xpath(index)
        if data:
            name, xpath = data
            index = self.root_lxml.xpath(xpath)
            if index and len(index[0]):
                return True

    def habilita(self, estado):
        if estado:
            self.filtro_jrxml.SetValue("")
            self.busca_jrxml = ""
            if self.copia_campos:
                self.campos = self.copia_campos
                self.copia_campos = None
        else:
            if self.copia_campos is None:
                self.copia_campos = self.campos.copy()
            else:
                self.campos = self.copia_campos.copy()

        for c in self.controls_habilita:
            c.Enable(estado)

    @staticmethod
    def pega_clipboard(data):
        try:
            clipdata = wx.TextDataObject()
            clipdata.SetText(data)
            wx.TheClipboard.Open()
            wx.TheClipboard.SetData(clipdata)
            wx.TheClipboard.Close()
        except:
            pass

    @staticmethod
    def copia_clipboard():
        try:
            if not wx.TheClipboard.IsOpened():
                do = wx.TextDataObject()
                wx.TheClipboard.Open()
                ok = wx.TheClipboard.GetData(do)
                wx.TheClipboard.Close()
                if ok:
                    return do.GetText()
        except:
            pass

    def tree_copiar(self):
        index = self.tree_xml.GetSelection()
        if index.IsOk():
            data = self.get_name_xpath(index)
            if data:
                des = data[1].split("/")
                nom = des[len(des) - 1]

                root = self.tree_xml.GetRootItem()
                parent = None
                if self.tree_item_xml and self.tree_item_xml != root:
                    parent = self.tree_xml.GetItemParent(self.tree_item_xml)

                if self.tree_item_xml and self.tree_item_xml != root and parent != root:
                    if self.has_children(self.tree_item_xml):
                        txt = template_jrxml.propiedad % (data[1])
                        self.pega_clipboard(txt)
                    else:
                        txt = template_jrxml.field % (nom, data[1])
                        self.pega_clipboard(txt)

    def list_copiar(self):
        index = self.list.GetFirstSelected()
        txt = ""
        while index >= 0:
            data = self.list.GetItemData(index)
            data = self.campos[data]
            des = data[0]
            nom = data[1]
            txt += template_jrxml.field % (nom, des)
            index = self.list.GetNextSelected(index)
        self.pega_clipboard(txt)

    def on_copia_nodo(self, evt):
        try:
            index = self.tree_xml.GetSelection()
            if index.IsOk():
                data = self.get_name_xpath(index)
                if data:
                    name, xpath = data
                    elems = self.root_lxml.xpath(xpath)
                    if elems:
                        txt = ET.tostring(elems[0])
                        self.pega_clipboard(txt)
        except Exception, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def on_borra_nodo(self, evt):
        try:
            index = self.tree_xml.GetSelection()
            data = self.get_name_xpath(index)
            if data:
                name, xpath = data
                elems = self.root_lxml.xpath(xpath)
                for e in elems:
                    e.getparent().remove(e)
                    self.xml_str = ET.tostring(self.root_lxml)
                    self.tree_xml.Delete(index)
        except Exception, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def on_pega_nodo(self, evt):
        try:
            index = self.tree_xml.GetSelection()
            data = self.get_name_xpath(index)
            if data:
                name, xpath = data
                elems = self.root_lxml.xpath(xpath)
                if elems:
                    txt = self.copia_clipboard()
                    if type(txt) is unicode or type(txt) is str:
                        nuevo = ET.fromstring(txt)
                        parent = elems[0].getparent()
                        ind = parent.index(elems[0])
                        parent.insert(ind + 0, nuevo)

                        self.xml_str = ET.tostring(self.root_lxml)
                        self.carga_xml(self.orden_xml())
                        self.expand_tree(xpath)
        except Exception, e:
            wx.MessageBox(str(e), APLICACION, wx.ICON_ERROR)

    def expand_tree(self, path):
        lpath = path.split("/")
        del lpath[0]
        del lpath[0]
        lon = len(lpath) - 1
        path = "/data"
        item = None
        for n, p in enumerate(lpath):
            path += "/" + p
            item = util.tree_get_item_path(self.tree_xml, path)
            if item and n != lon:
                self.tree_xml.Expand(item)

        if item:
            self.tree_xml.SelectItem(item)
            self.tree_xml.EnsureVisible(item)

    @staticmethod
    def graba_copia(fic):
        def conta(nom):
            return nom + datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        try:
            with open(fic, 'r') as f:
                tmp = f.read()
                with open(conta(fic), 'w') as f:
                    f.write(tmp)
        except:
            pass

    def OnClose(self, evt):
        self.Hide()     # de esta forma parece que el frame se cierra rápidamente
        wx.Yield()

        xml = self.fic_xml.Value
        jrxml = self.fic_jrxml.Value
        tag1 = self.cb_tagx.Get3StateValue()
        tag2 = self.cb_tagj.Get3StateValue()

        self.app.set_propiedad("tag1", tag1)
        self.app.set_propiedad("tag2", tag2)
        self.app.set_propiedad("xml", xml)
        self.app.set_propiedad("jrxml", jrxml)

        self.watch.stop()
        self.Destroy()

    def jrxml_modificado(self, txt):
        self.infobar.Dismiss()
        self.infobar.ShowMessage(txt, wx.ICON_WARNING)


class MySplashScreen(wx.SplashScreen):
    def __init__(self, parent=None):
        self.parent = parent
        aBitmap = imagenes.splash.GetBitmap()
        # aBitmap = wx.Image(name="splash.jpg").ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT
        splashDuration = 1000
        wx.SplashScreen.__init__(self, aBitmap, splashStyle, splashDuration, None)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        wx.Yield()

    def OnExit(self, evt):
        self.Hide()
        frame = MainFrame(self.parent)
        app.SetTopWindow(frame)
        frame.Center()
        frame.Show()
        evt.Skip()


class MyApp(wx.App):
    propidades = dict()
    config = None
    fic_config = ""

    def __init__(self, redirect=False):
        wx.App.__init__(self, redirect)

    def OnInit(self):
        wx.SetDefaultPyEncoding("utf-8")
        self.locale = wx.Locale(wx.LANGUAGE_SPANISH)

        self.config = self.get_config()
        propi = self.config.Read("propiedades")
        ver = self.config.Read("version")
        try:
            if propi and ver == self.get_version:
                self.propidades = pickle.loads(propi.decode("hex").decode("zlib"))
        except:
            pass

        self.SetAppName(APLICACION)

        #
        MySplash = MySplashScreen(self)
        MySplash.Show()
        # frame = MainFrame(self)
        # frame.Center()
        # frame.Show()
        return True

    def OnExit(self):
        propi = pickle.dumps(self.propidades).encode("zlib").encode('hex')
        self.config.Write("version", self.get_version)
        self.config.Write("propiedades", propi)
        self.config.Flush()
        self.Exit()

    @property
    def get_version(self):
        return NVERSION

    @property
    def get_data_dir(self):
        sp = wx.StandardPaths.Get()
        return sp.GetUserDataDir()

    def get_config(self):
        if not os.path.exists(self.get_data_dir):
            os.makedirs(self.get_data_dir)
        self.fic_config = os.path.join(self.get_data_dir, "propiedades")
        config = wx.FileConfig(localFilename=self.fic_config)
        return config

    def get_propiedad(self, propi):
        if propi in self.propidades:
            return self.propidades[propi]
        return None

    def set_propiedad(self, propi, valor):
        self.propidades[propi] = valor


if __name__=='__main__':
    app = MyApp()
    app.MainLoop()
