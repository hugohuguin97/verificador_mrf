"""Subclass of MainF, which is generated by wxFormBuilder."""

import wx
import src.main_app as main_app

import os
import wx.xrc as xrc
import wx.adv as adv
import wx.richtext as rt
import  wx.html
from os import path
import logging
import wx.lib.scrolledpanel
import wx.lib.agw.aui as aui
from glob import glob

from threading import Thread
import subprocess

from src.val_MAGE import MAGE_panel
from src.val_XML import XML_panel
from src.val_RAW import RAW_panel

ruta_base = path.dirname(path.abspath(__file__))
ruta_xrc = path.join(ruta_base,"main_app.xrc")
log = logging.getLogger("validaciones_uso")
log.setLevel(logging.INFO)

# Implementing MainF
class MainFrameMainF( main_app.MainF ):
    def __init__( self, parent ):
        main_app.MainF.__init__( self, parent )
        self.worker = None
        
        self.estado_ayuda = 0
        self.ruta_base = ruta_base
        self.Bind(wx.EVT_MENU, lambda event: self.abrir_ayuda(event, "instrucciones.html"), self.introduccion)
        self.Bind(wx.EVT_MENU, lambda event: self.abrir_ayuda(event, "queries.html"), self.queries)

        self.mage_panel = MAGE_panel(self, self)
        self.xml_panel = XML_panel(self, self)
        self.raw_panel = RAW_panel(self, self)
        
        # self.archivos_requeridos = set()

    def abrir_ayuda(self, event, archivo):
        """Abre un archivo html de ayuda en una nueva ventana.

        Para que la funcion fuese generica y evitar la repetición del codigo, en
        la llamda se aplicó una función lambda para poder añadir un parámetro
        adicional, en este caso es el nombre del archivo html que se desea
        desplegar.

        Parameters
        ----------
        archivo: str
            Nombre del archivo html que se desea abrir en la ventana
        """
        if self.estado_ayuda == 0:
            frame = AyudaFrame(wx.GetTopLevelParent(self), u"Ayuda", archivo, self)
        else:
            self.SetStatusText(u'Ya hay una ventana de ayuda abierta')

    def inicializar_thread(self, event, thread, comentario):
        """Inicializa un thread"""
        if self.worker is None:
            self.SetStatusText(comentario)
            self.worker = thread()
            self.worker.start()
        else:
            self.SetStatusText('Proceso ocupado, espere a finalizar el anterior.')

    # def OnOpen(self, event):

    #     if self._estadoOtherFrame == 0:
    #         frame = OtherFrame(u"Recuperar casos históricos",
    #             wx.GetTopLevelParent(self), self)
    #     else:
    #         self.SetStatusText(u'La ventana de recuperación de casos históricos'
    #             u' ya está abierta')
            
            
class AyudaFrame(wx.Frame):
    """Clase que permite abrir una ventana de ayuda desde la ventana principal"""
    def __init__(self, parent, title, archivo, main_frame):
        wx.Frame.__init__(self, parent,-1, title, size = (600,400))
        # Use current window as container of the Html Frame
        self.mf = main_frame
        self.mf.estado_ayuda = 1
        self.html = wx.html.HtmlWindow(self)
        self.html.LoadPage(path.join(self.mf.ruta_base, "ayuda", archivo))
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()
        self.Maximize()

    def on_close(self, event):
        """Metodo de destruccion de la ayuda"""

        self.mf.estado_ayuda = 0
        self.Destroy()
    
class App(wx.App):
    def OnInit(self):
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)
        frame = MainFrameMainF(None)
        frame.Show(True)
        frame.Maximize(True)
        return True
    
if __name__ == '__main__':
    # main()
    app = App()
    # frame = MainWindow(None)
    app.MainLoop()