# -*- coding: utf-8 -*-

import platform
import struct
import wx

is_windows = any(platform.win32_ver())
bits = struct.calcsize("P") * 8


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


def get_frame_title(self):
    frame = wx.GetTopLevelParent(self)
    titulo = frame.GetTitle().split(" ")
    return titulo[0]


def tree_get_item_text(tree, text, text_padre=None):
    def recorre(tree, text, root):
        item, cookie = tree.GetFirstChild(root)
        while item.IsOk():
            if tree.GetItemText(item) == text:
                return item
            if tree.ItemHasChildren(item):
                item1 = recorre(tree, text, item)
                if item1:
                    return item1

            item, cookie = tree.GetNextChild(root, cookie)
        return None

    root = tree.GetRootItem()
    if root and text_padre:
        padre = recorre(tree, text_padre, root)
        if padre:
            root = padre

    if root:
        return recorre(tree, text, root)
    else:
        return None


def tree_get_item_data(tree, data, data_padre=None):
    def recorre(tree, data, root):
        item, cookie = tree.GetFirstChild(root)
        while item.IsOk():
            if tree.GetPyData(item) == data:
                return item
            if tree.ItemHasChildren(item):
                item1 = recorre(tree, data, item)
                if item1:
                    return item1

            item, cookie = tree.GetNextChild(root, cookie)
        return None

    root = tree.GetRootItem()
    if root and data_padre:
        padre = recorre(tree, data_padre, root)
        if padre:
            root = padre

    if root:
        return recorre(tree, data, root)
    else:
        return None


def tree_collapse(tree, branch):
    item, cookie = tree.GetFirstChild(branch)
    while item.IsOk():
        tree.Collapse(item)
        if tree.ItemHasChildren(item):
            tree_collapse(tree, item)
        item, cookie = tree.GetNextChild(branch, cookie)


def tree_get_item_path(tree, path):
    def recorre(tree, path, root):
        item, cookie = tree.GetFirstChild(root)
        while item.IsOk():
            if tree.GetPyData(item)[0] == path:
                return item
            if tree.ItemHasChildren(item):
                item1 = recorre(tree, path, item)
                if item1:
                    return item1

            item, cookie = tree.GetNextChild(root, cookie)
        return None

    root = tree.GetRootItem()
    if root:
        return recorre(tree, path, root)
    else:
        return None


def txt_2_list_str(txt):
    if not txt:
        return None

    try:
        tmp = txt.strip()
        # quito los [] si los tienen
        if txt.startswith("[") and txt.endswith("]"):
            tmp = tmp[1:]
            tmp = tmp[:-1]

        # reemplaza las ' y " por nada
        tmp = tmp.replace("'", "")
        tmp = tmp.replace('"', '"')

        # y hace una lista de los terminos separados por ,
        tmp1 = tmp.split(",")
        tmp2 = list()
        for t in tmp1:
            t = str(t.strip())  # de unicode a str
            tmp2.append(t)
        return tmp2

    except:
        pass