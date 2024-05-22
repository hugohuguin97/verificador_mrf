import wx
import os
import wx.xrc as xrc
import wx.adv as adv
import wx.dataview as dv
import wx.stc as stc
from os import path
import logging
import wx.lib.scrolledpanel
import wx.lib.agw.aui as aui
import xml.etree.ElementTree as ET
import re
import wx.grid as gridlib
from glob import glob
from os.path import join, basename, getmtime
from datetime import datetime, timedelta, date
from threading import Thread
from collections import defaultdict
from pyraw import RAWFile
from usolibpy.rawfile import RAWFile2

import matplotlib
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar2Wx
from matplotlib.patches import Rectangle, Ellipse, Circle, Polygon
from matplotlib.text import Text


from matplotlib.figure import Figure
import matplotlib.pyplot as plt

RAW_REGEX = re.compile(r'.*\d{2}\w{3}\d{4}_(\d{2}).r?R?a?A?w?W?')
EVT_RESULT_ID = wx.NewId()
WX_ROJO = wx.Colour(238,46,46)
WX_VERDE = wx.Colour(86,219,65)
WX_NEGRO = wx.Colour(0, 0, 0)
WX_BLANCO = wx.Colour(255,255,255)
delimitador = '\t'

ruta_base = path.abspath(path.join(__file__, "../.."))
ruta_resultados = path.join(ruta_base,"resultados")
ruta_data = path.join(ruta_base,"data")
log = logging.getLogger("verificador_imm_raw")
log.setLevel(logging.INFO)
# Formatea la fecha y hora
name_archivo = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

# Guardar el archivo con el nombre basado en la fecha
archivo_xlsx = f"ValidacionesXML{name_archivo}.xlsx"
path_exp = path.join(ruta_resultados, archivo_xlsx)

#Manejador del logger para el verificador
class CustomConsoleLogHandler(logging.StreamHandler):
    """Clase para redireccionar el flujo de logs hacia un text control en el
    verificador."""

    def __init__(self, textctrl):
        logging.StreamHandler.__init__(self)
        self.textctrl = textctrl

    def emit(self, record):
        """Constructor"""

        msg = self.format(record)
        self.textctrl.SetInsertionPointEnd()
        self.textctrl.WriteText(msg + "\n")
        self.flush()
        
class RAW_panel(wx.Panel):
    def __init__(self, parent, main_frame):
        # wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        super().__init__(parent)
        # wx.Panel.__init__(self, parent)
        self.mf = main_frame
        self.parent = parent
        
        self.log = log
        self.raw_log_textCtrl = self.mf.raw_log_textCtrl
        txt_handler = CustomConsoleLogHandler(self.raw_log_textCtrl)
        txt_handler.setFormatter(
            logging.Formatter('%(name)-12s %(levelname)9s: %(message)s'))
        txt_handler.setLevel(logging.INFO)
        self.log.addHandler(txt_handler)
        # logging.getLogger("arbol_mage").addHandler(txt_handler)
        
        self.nb = nb = self.mf.RAW_nb
        
        self.mf.RAWselected_path_1 = ''
        self.mf.RAWselected_path_2 = ''
        self.ruta_base = ruta_base
        self.lista_ok = []
        self.index_start = 0
        self.word_aux = ''
        self.cont = 0
        self.start_date_aux = 0
        self.end_date_aux = 0
        # Diccionario para almacenar los estilos aplicados a cada palabra
        self.word_styles = {}
        # self.mf.RAWParameters_Panel = 
        # self.mf.RAWParameters_Panel = RAWParameters_Panel(nb, self.mf)
        
        # Definir los paneles para la impresion de la SE
        self.raw1_panel = self.mf.RAW1_panel
        self.raw2_panel = self.mf.RAW2_panel
        # Panel del comparativo
        self.mf.RAWParameters_Panel = RAWParam_Panel(nb, self.mf)
        self.mf.RAWDiag_Panel = RAWDiag_Panel(nb, self.mf)
        self.mf.RAWDiagram1_Panel = RAWDiag1_Panel(self.raw1_panel, self.raw1_panel)
        self.mf.RAWDiagram2_Panel = RAWDiag1_Panel(self.raw2_panel, self.raw2_panel)
        
        
        pass
    
    
class RAWParam_Panel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, main_frame, tipos = None, etiquetas = None, data = None):
        super().__init__(parent)
        # wx.Panel.__init__(self, parent)
        self.mf = main_frame
        self.val_raw = parent
        # Directorio XML
        path_raw1 = r'Z:\RAWS_RED_COMPLETA\SP7\SIN\03May2024_ABB_CS.raw'
        path_raw2 = r'Z:\RAWS_RED_COMPLETA\ABB\29Abr2024_CS_v2.raw'
        self.RAWselected_path_1 = path_raw1
        self.RAWselected_path_2 = path_raw2
        self.mf._archivos_raw = []
        self.sistema = 0
        # self.RAWParameters_Panel = RAWParameters_Panel(self.mf, self.mf)
        
        self._sistema = self.mf._sistema
        self._sistema.SetCheckedItems([0])
        self._sistema.Bind(wx.EVT_CHECKLISTBOX, self.on_check)
        self.mf._sistema = self._sistema.GetCheckedItems()[0]
        print("El sistema", self.sistema)
        
        # Obtener la XML path data
        self.RAW_pathSel1 = self.mf.RAW_pathSel1
        self.RAW_pathSel2 = self.mf.RAW_pathSel2
        self.RAW_pathSel1.SetPath(path_raw1)
        self.RAW_pathSel1.Bind(wx.EVT_DIRPICKER_CHANGED, self.RAWpath_select1)
        self.RAW_pathSel2.SetPath(path_raw2)
        self.RAW_pathSel2.Bind(wx.EVT_DIRPICKER_CHANGED, self.RAWpath_select2)
        # Hace la lista de archivos RAW
        self.mf._archivos_raw.append(self.RAW_pathSel1.GetPath())
        self.mf._archivos_raw.append(self.RAW_pathSel2.GetPath())
        print("Consulta 1",self.mf._archivos_raw)
        # Lee los RAW
        self.bto_leer_RAWs = self.mf.bto_leer_RAWs
        # self._sistema = self.mf.sistema
        self.bto_leer_RAWs.Bind(wx.EVT_BUTTON, self._recargar)
        
    def on_check(self, event):
        checked_item = event.GetSelection()
        num_items = self._sistema.GetCount()
        for i in range(num_items):
            if i != checked_item:
                self._sistema.Check(i, False)
        self.sistema = checked_item

    def RAWpath_select1(self, event):
        self.RAWselected_path_1 = self.RAW_pathSel1.GetPath()
        print("El RAW 1 es",self.mf.RAWselected_path_1)
    def RAWpath_select2(self, event):
        self.RAWselected_path_2 = self.RAW_pathSel2.GetPath()
        print("El RAW 2 es",self.mf.RAWselected_path_2)

    def _recargar(self, event):

        # print(self.mf._archivos_raw)
        # self.sistema = self._sistema.GetSelection()
        print("El sistema seleccionado es:", self.sistema)
        if self.mf.worker is None:
            self._ramasEnTabla = []
            self._busesEnTabla = []
            self.mf.SetStatusText(
                u'Iniciando el analisis de estatus de lineas')
            self.mf.worker = LectorRamas(self.mf, self.mf._archivos_raw,
                                          self.sistema)
            
            self.mf.rawfile1 = RAWFile(self.mf._archivos_raw[0], self.sistema, "")
            self.mf.rawfile2 = RAWFile(self.mf._archivos_raw[1], self.sistema, "")
            
            self.mf.worker.start()
        else:
            self.mf.SetStatusText(
                'Proceso ocupado, espere a finalizar el anterior.')


class RAWDiag_Panel(wx.lib.scrolledpanel.ScrolledPanel):
    
    def __init__(self, parent, main_frame, tipos = None, etiquetas = None, data = None):
        super().__init__(parent)
        # wx.Panel.__init__(self, parent)
        self.mf = main_frame
        self.val_raw = parent
        self._statusRamas = []
        self._statusBuses = []
        self.equipos_graficar_1 = {}
        self.equipos_graficar_2 = {}
        
        self.elm_grid_panel = self.mf.elm_panel
        # print("panel para la lista",self.elm_grid_panel)
        # self.grid_panel = wx.Panel(self.elm_grid_panel)
        # self.elm_grid_panel.AddPage(self.grid_panel, "Lista de busqueda")
        
        self._elm_grid = Grid2(self.elm_grid_panel, pegar = 0, filtrar = 1)
        self._elm_grid.CreateGrid(10,7)
        self._elm_grid.SetColSize(0,200)
        self._elm_grid.SetRowLabelSize(20)
        
        # self._elm_grid.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK,
        #     self._elm_grid.OnLabelRclick)
        # self._elm_grid.Bind(wx.EVT_CHAR, self._elm_grid.OnCTRL)

        self._elm_grid.Bind(gridlib.EVT_GRID_CELL_LEFT_DCLICK,
            self.OnDLClickLinea)

        # self._elm_grid.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK,
        #     self._elm_grid.OnCellRclick)

        self._elm_grid.SetColLabelValue(0, u"CLAVE DE RAMA")
        self._elm_grid.SetColLabelValue(1, u"NODO FROM")
        self._elm_grid.SetColLabelValue(2, u"NODO TO")
        self._elm_grid.SetColLabelValue(3, u"ID")
        self._elm_grid.SetColLabelValue(4, u"TIPO")
        self._elm_grid.SetColLabelValue(5, u"RAW 1")
        self._elm_grid.SetColLabelValue(6, u"RAW 2")

        sizer_grid = wx.BoxSizer(wx.VERTICAL)
        sizer_grid.Add(self._elm_grid, 1, wx.EXPAND)
        
        self.elm_grid_panel.SetSizer(sizer_grid)
        
        self._rowBorrar = None
        self._rowCambiar = None
        self._colCambiar = None
        self._ramasEnTabla = []
        
        # Ejecutar la busqueda 
        self.RAW_searchCtrl = self.mf.RAW_searchCtrl
        # print(self.RAW_searchCtrl)
        self.mf.RAW_searchCtrl.Bind( wx.EVT_TEXT, self.buscar )
        # Declara la etiqueta de la ramma
        self.rama_Stext = self.mf.rama_Stext
        self.subRama_Stext = self.mf.subRama_Stext
        # Declara las listas de las ramas
        self.RAW1_listCtrl = self.mf.RAW1_listCtrl
        self.RAW1_listCtrl.InsertColumn(0, 'RAMA', width=200)
        self.RAW1_listCtrl.InsertColumn(1, 'NODO TO')#, width=50)
        self.RAW1_listCtrl.InsertColumn(2, 'ST')#, width=20)
        self.RAW1_listCtrl.InsertColumn(3, 'TIPO')#, width=20)
        self.RAW2_listCtrl = self.mf.RAW2_listCtrl
        self.RAW2_listCtrl.InsertColumn(0, 'RAMA', width=200)
        self.RAW2_listCtrl.InsertColumn(1, 'NODO TO')#, width=50)
        self.RAW2_listCtrl.InsertColumn(2, 'ST')#, width=20)
        self.RAW2_listCtrl.InsertColumn(3, 'TIPO')#, width=20)
        
        # Enlazar el evento de doble clic al ListCtrl
        self.RAW1_listCtrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDLClickBus)
        self.RAW2_listCtrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnDLClickBus)
        
    def limpiar(self):
        # print(self._elm_grid)
        self._elm_grid.clear()
        self._elm_grid.clear()
        self._elm_grid.clear()
        
    def buscar(self, event, regex = None):

        listaBusesFiltrados = []
        listaRamasFiltradas = []
        bandera = 0
        
        regex = self.RAW_searchCtrl.GetValue()
        
        if regex is not None:
            regex = self.RAW_searchCtrl.GetValue()
            bandera = 1
        if not regex:
            self._elm_grid.clear()
            return 1

        regex = ((r'.*' + regex + r'.*').replace(" ", ".*")).upper()
        REGEX = re.compile(regex)

        for ele in self._statusRamas:
            # print(ele)
            
            find = REGEX.search(ele)
            if find:
                listaBusesFiltrados.append(self._statusRamas[ele])
                datos = self._statusRamas[ele]['datos']
                raws = self._statusRamas[ele]['raw']
                # print(self._statusRamas[ele])
                if len(datos) != 0:
                    n_from = datos[0]
                    n_to = datos[1]
                    ckt = datos[2]
                    rama = datos[3]
                    if 0 in raws and 1 in raws:
                        raw1 = 'True'
                        raw2 = 'True'
                    elif 0 in raws and 1 not in raws:
                        raw1 = 'True'
                        raw2 = 'False'
                    elif 1 in raws and 0 not in raws:
                        raw1 = 'False'
                        raw2 = 'True'
                    elif 1 not in raws and 0 not in raws:
                        raw1 = 'False'
                        raw2 = 'False'
                        
                listaRamasFiltradas.append((ele, n_from, n_to, ckt, rama, raw1, raw2))
        
        # print(listaRamasFiltradas)
        # print(listaBusesFiltrados)

        if bandera:
            self._elm_grid.clear()
            numRows = self._elm_grid.GetNumberRows()
            if numRows != 0:
                self._elm_grid.DeleteRows(numRows = numRows)

            self._elm_grid.data = [[x] for x in listaRamasFiltradas]
            self._elm_grid.row_labels = map(str, range(len(listaRamasFiltradas)))
            self._elm_grid.InsertRows(0,len(listaRamasFiltradas))
            for i,ele in enumerate(listaRamasFiltradas):
                # print(ele)
                self._elm_grid.SetRowLabelValue(i,str(i))
                self._elm_grid.SetCellValue(i,0,ele[0])
                self._elm_grid.SetCellValue(i,1,str(ele[1]))
                self._elm_grid.SetCellValue(i,2,str(ele[2]))
                self._elm_grid.SetCellValue(i,3,str(ele[3]))
                self._elm_grid.SetCellValue(i,4,str(ele[4]))
                self._elm_grid.SetCellValue(i,5,ele[5])
                self._elm_grid.SetCellValue(i,6,ele[6])
                self._elm_grid.SetReadOnly(i,0,True)
                self._elm_grid.SetReadOnly(i,1,True)
                self._elm_grid.SetReadOnly(i,2,True)
                self._elm_grid.SetReadOnly(i,3,True)
                self._elm_grid.SetReadOnly(i,4,True)
                self._elm_grid.SetReadOnly(i,5,True)
                self._elm_grid.SetReadOnly(i,6,True)

            self._elm_grid.ForceRefresh()
            self.mf.worker = None
        else:
            # print("no entra en bandera")
            return listaRamasFiltradas

    def _buscarBuses(self, event):

        listaBusesFiltradas = []
        regex = self._regexBuscarEnBuses.GetValue()
        if not regex:
            return 1

        regex = ((r'.*' + regex + r'.*').replace(" ", ".*")).upper()
        REGEX = re.compile(regex)

        for ele in self._statusBuses.values():
            find = REGEX.search(ele["datos"][1])
            if find:
                listaBusesFiltradas.append(ele["datos"][0])

        self._elm_grid.clear()
        numRows = self._elm_grid.GetNumberRows()
        if numRows != 0:
            self._elm_grid.DeleteRows(numRows = numRows)

        self._elm_grid.data = [[x, str(self._statusBuses[x]["datos"][0])] for x in listaBusesFiltradas]
        self._elm_grid.row_labels = map(str, range(len(listaBusesFiltradas)))
        self._elm_grid.InsertRows(0,len(listaBusesFiltradas))
        for i,ele in enumerate(listaBusesFiltradas):
            self._elm_grid.SetRowLabelValue(i,str(i))
            self._elm_grid.SetCellValue(i,0,str(self._statusBuses[ele]["datos"][0]))
            self._elm_grid.SetCellValue(i,1,str(self._statusBuses[ele]["datos"][1]))
            self._elm_grid.SetReadOnly(i,0,True)
            self._elm_grid.SetReadOnly(i,1,True)

        self._elm_grid.ForceRefresh()

    def OnRclickStatusBus(self,event):
        """
        Despliega el menu contextual para eliminar ramas de la seccion status
        """
        if self.mf.worker is None:
            self._rowBorrar = event.GetRow()
            self._rowCambiar = event.GetRow()
            self._colCambiar = event.GetCol()
            menu = wx.Menu()
            menu.Append(self._popupIdEliminarBus, 'Eliminar')
            menu.Append(self._popupIdCambiarStatusBus, 'Cambiar estatus')
            menu.Append(self._popupIdGraficarBus, 'Graficar bus')
            self.PopupMenu(menu)
            menu.Destroy()


    def OnRclickStatus(self,event):
        """
        Despliega el menu contextual para eliminar ramas de la seccion status
        """
        if self.mf.worker is None:
            self._rowBorrar = event.GetRow()
            self._rowCambiar = event.GetRow()
            self._colCambiar = event.GetCol()
            menu = wx.Menu()
            menu.Append(self._popupIdEliminar, 'Eliminar')
            menu.Append(self._popupIdCambiarStatus, 'Cambiar estatus')
            self.PopupMenu(menu)
            menu.Destroy()

    def OnBorrarEstatus(self,event):
        if self._rowBorrar is not None:

            try:
                top_left =  self._status_grid.GetSelectionBlockTopLeft()[0]
                bottom_right = self._status_grid.GetSelectionBlockBottomRight()[0]
                self._status_grid.ClearSelection()
            except IndexError:
                top_left = [0,0]
                top_left[0] = self._rowBorrar
                top_left[1] = 0
                bottom_right = top_left

            for i in range(bottom_right[0],top_left[0]-1,-1):
                rama = self._status_grid.GetCellValue(i,0)
                idx = self._ramasEnTabla.index(rama)
                self._ramasEnTabla.pop(idx)
                self._status_grid.DeleteRows(i, 1)

        self._status_grid.ForceRefresh()

    def OnBorrarEstatusBus(self,event):
        if self._rowBorrar is not None:

            try:
                top_left =  self._status_elm_grid.GetSelectionBlockTopLeft()[0]
                bottom_right = self._status_elm_grid.GetSelectionBlockBottomRight()[0]
                self._status_elm_grid.ClearSelection()
            except IndexError:
                top_left = [0,0]
                top_left[0] = self._rowBorrar
                top_left[1] = 0
                bottom_right = top_left

            for i in range(bottom_right[0],top_left[0]-1,-1):
                bus = self._status_elm_grid.GetCellValue(i,0)
                idx = self._busesEnTabla.index(bus)
                self._busesEnTabla.pop(idx)
                self._status_elm_grid.DeleteRows(i, 1)

        self._status_elm_grid.ForceRefresh()

    def OnDLClickLinea(self, event):
        """"
        Selecciona el elemento que se desea revisar        
        """
        # print("Entra al DClick")
        self._rowCambiar = event.GetRow()
        self._colCambiar = event.GetCol()
        
        if self.mf.worker is None and len(self._statusRamas) != 0:
            # print("Entra al IF")
            row = event.Row
            # print(row)
            rama = self._elm_grid.GetCellValue(row,0)
            sel_n_from = self._elm_grid.GetCellValue(row,1)
            sel_n_to = self._elm_grid.GetCellValue(row,2)
            
            self.OnGraficarBus(event, 0)
            
        event.Skip()
        
    def OnDLClickBus(self, event):
        """"
        Selecciona el elemento que se desea revisar        
        """
        
        listCtrl = event.GetEventObject()
        
        if self.mf.worker is None and listCtrl.GetItemCount() != 0:
            # Obtener el índice de la fila seleccionada
            index = listCtrl.GetFirstSelected()

            if index != -1:  # Verificar si se seleccionó alguna fila
                # Obtener el valor de la columna 2 de la fila seleccionada
                value = listCtrl.GetItem(index, 1).GetText()
                # print("Entra al DClick")
                self._rowCambiar = value
                self._colCambiar = 1#event.GetCol()
                # print("Valor de la columna 2:", value)
            
            self.OnGraficarBus(event, 1, listCtrl)
            
        event.Skip()
        
    def OnGraficarBus(self, event, modo=0, listCtrl = None):
        
        # print("Row de la rama",self._rowCambiar is not None)
        # print("Col de la rama",self._colCambiar is not None)
        # print(self._colCambiar)
        if self._rowCambiar is not None and self._colCambiar is not None:# and \
            # self.mf.worker is None:
            if modo == 0:
                rama = str(self._elm_grid.GetCellValue(self._rowCambiar, 0))
                if self._colCambiar == 2:
                    numero_bus = int(self._elm_grid.GetCellValue(self._rowCambiar, 2).split("(")[0])
                    self.rama_Stext.SetLabel(f"Rama: {rama}   Bus: {numero_bus}")
                    
                else:
                    numero_bus = int(self._elm_grid.GetCellValue(self._rowCambiar, 1).split("(")[0])
                    self.rama_Stext.SetLabel(f"Rama: {rama}   Bus: {numero_bus}")
            elif modo == 1 and listCtrl != None:
                # Obtener el índice de la fila seleccionada
                index = listCtrl.GetFirstSelected()
                # Obtener el valor de la columna 2 de la fila seleccionada
                rama = str(listCtrl.GetItem(index, 0).GetText())
                numero_bus = listCtrl.GetItem(index, 1).GetText()
                self.subRama_Stext.SetLabel(f"Rama: {rama}   Bus: {numero_bus}")
                print("Valor de la columna 2:", numero_bus)
                if numero_bus == "None":
                    return 1
                else:
                    numero_bus = int(numero_bus)
            
                
            
            self.mf.SetStatusText(u'Graficando bus %d.'% (numero_bus))

            self.mf.RAWDiagram1_Panel.limpiar()
            self.mf.RAWDiagram2_Panel.limpiar()
            self.mf.RAWDiagram1_Panel.limpiar()
            self.mf.RAWDiagram2_Panel.limpiar()
            
            self.RAW1_listCtrl.DeleteAllItems()
            self.RAW2_listCtrl.DeleteAllItems()

            sistema = self.mf._sistema#.GetSelection()
            
            rawfile1 = self.mf.rawfile1 #RAWFile(self.mf._archivos_raw[0], sistema, "")
            dicc_equipos1 = get_dicc_equipos(rawfile1)
            # print(dicc_equipos1)
            dicc_buses1 = make_dicc_buses_numero(rawfile1)
            # print(dicc_buses1)
            
            rawfile2 = self.mf.rawfile2 #RAWFile(self.mf._archivos_raw[1], sistema, "")
            dicc_equipos2 = get_dicc_equipos(rawfile2)
            dicc_buses2 = make_dicc_buses_numero(rawfile2)

            try:
                # Grafica el panel de RAW 1
                estatus1 = dicc_buses1[numero_bus]["IDE"]
                self.equipos_graficar_1 = dicc_equipos1[numero_bus]
                
                grafica_bus(numero_bus, dicc_equipos1, dicc_buses1,
                            self.mf.RAWDiagram1_Panel._fig_diagrama,
                            self.mf.RAWDiagram1_Panel._axes_diagrama)
                self.mf.RAWDiagram1_Panel._canvas_diagrama.draw()
                                
                self.OnSetRamas(self.RAW1_listCtrl, self.equipos_graficar_1)
                    
            except Exception as e:
                print(f"El BUS {numero_bus} no se encuentra en el RAW 1 ")
                pass
                
            try:
                # Grafica el panel de RAW 2
                estatus2 = dicc_buses2[numero_bus]["IDE"]
                self.equipos_graficar_2 = dicc_equipos2[numero_bus]
                # print("Con el self",self.equipos_graficar_2)
                
                grafica_bus(numero_bus, dicc_equipos2, dicc_buses2,
                            self.mf.RAWDiagram2_Panel._fig_diagrama,
                            self.mf.RAWDiagram2_Panel._axes_diagrama)
                self.mf.RAWDiagram2_Panel._canvas_diagrama.draw()
                
                self.OnSetRamas(self.RAW2_listCtrl, self.equipos_graficar_2)
                
            except Exception as e:
                print(f"El BUS {numero_bus} no se encuentra en el RAW 2 ")
                pass
                
        else:
            self.mf.SetStatusText(
                'Proceso ocupado, espere a finalizar el anterior.')
            return
        self.mf.SetStatusText(u'Proceso de graficación terminado.')

    def OnSetRamas(self, RAW_listCtrl, equipos):
        # print("entra en la lista de ramas")
        if self._rowCambiar is not None and self._colCambiar is not None:
            # RAW_listCtrl.DeleteAllItems()
            # print(equipos)
            # Agregar los datos al ListCtrl
            for index, row in enumerate(equipos):
                RAW_listCtrl.InsertItem(index, str(row[0]))  # Insertar el primer elemento de cada fila en la primera columna
                for col_index, col_value in enumerate(row[1:], start=1):
                    RAW_listCtrl.SetItem(index, col_index, str(col_value))  # Insertar los demás elementos de la fila en las siguientes columnas
            
    def _presentar_lineas_abiertas(self, event):
        """Grafica en el panel de estatus de ramsa todas las lineas con al menos
        una hora abierta"""

        rojo = wx.Colour(238,46,46)
        verde = wx.Colour(86,219,65)
        negro = WX_NEGRO
        blanco = wx.Colour(255,255,255)
        if self.mf.worker is None and len(self._statusRamas) != 0:

            for rama in self._statusRamas:
                if rama in self._ramasEnTabla:
                    continue
                status = self._statusRamas[rama]["estatus"]
                if not any((x==0 for x in status)):
                    continue

                datos = self._statusRamas[rama]["datos"]
                if datos[-1] != "LT":
                    continue

                numRowsEstatus = self._status_grid.GetNumberRows()
                self._status_grid.InsertRows(numRowsEstatus,1)
                self._status_grid.SetCellValue(numRowsEstatus,0,rama)
                self._status_grid.SetReadOnly(numRowsEstatus,0,True)

                for i,ele in enumerate(status):
                    self._status_grid.SetCellValue(numRowsEstatus,i+1,str(ele))
                    self._status_grid.SetReadOnly(numRowsEstatus,i+1,True)

                    if ele == 0:
                        self._status_grid.SetCellBackgroundColour(numRowsEstatus,i+1,WX_ROJO)
                    else:
                        self._status_grid.SetCellBackgroundColour(numRowsEstatus,i+1,WX_VERDE)

                self._ramasEnTabla.append(rama)
            self._status_grid.ForceRefresh()

        event.Skip()

    def _presentar_transformadores_abiertos(self, event):
        """Grafica en el panel de estatus de ramsa todas las lineas con al menos
        una hora abierta"""

        rojo = wx.Colour(238,46,46)
        verde = wx.Colour(86,219,65)
        negro = WX_NEGRO
        blanco = wx.Colour(255,255,255)
        if self.mf.worker is None and len(self._statusRamas) != 0:

            for rama in self._statusRamas:
                if rama in self._ramasEnTabla:
                    continue
                status = self._statusRamas[rama]["estatus"]
                if not any((x==0 for x in status)):
                    continue

                datos = self._statusRamas[rama]["datos"]
                if datos[-1] != "T":
                    continue

                numRowsEstatus = self._status_grid.GetNumberRows()
                self._status_grid.InsertRows(numRowsEstatus,1)
                self._status_grid.SetCellValue(numRowsEstatus,0,rama)
                self._status_grid.SetReadOnly(numRowsEstatus,0,True)

                for i,ele in enumerate(status):
                    self._status_grid.SetCellValue(numRowsEstatus,i+1,str(ele))
                    self._status_grid.SetReadOnly(numRowsEstatus,i+1,True)

                    if ele == 0:
                        self._status_grid.SetCellBackgroundColour(numRowsEstatus,i+1,WX_ROJO)
                    else:
                        self._status_grid.SetCellBackgroundColour(numRowsEstatus,i+1,WX_VERDE)

                self._ramasEnTabla.append(rama)
            self._status_grid.ForceRefresh()

        event.Skip()


    def _presentar_buses_abiertos(self, event):
        """Grafica en el panel de estatus de buses todao las buses con al menos
        una hora abierta"""
        rojo = wx.Colour(238,46,46)
        verde = wx.Colour(86,219,65)
        negro = WX_NEGRO
        blanco = wx.Colour(255,255,255)

        if self.mf.worker is None and len(self._statusBuses) != 0:

            for bus in self._statusBuses:
                if bus in self._busesEnTabla:
                    continue
                status = self._statusBuses[int(bus)]["estatus"]
                if not any((x==0 for x in status)):
                    continue
                name = self._statusBuses[int(bus)]["datos"][1]
                nombre =  "{}({})".format(bus,name)
                numRowsEstatus = self._status_elm_grid.GetNumberRows()
                self._status_elm_grid.InsertRows(numRowsEstatus,1)
                self._status_elm_grid.SetCellValue(numRowsEstatus,0,nombre)
                self._status_elm_grid.SetReadOnly(numRowsEstatus,0,True)

                for i,ele in enumerate(status):
                    self._status_elm_grid.SetCellValue(numRowsEstatus,i+1,str(ele))
                    self._status_elm_grid.SetReadOnly(numRowsEstatus,i+1,True)

                    if ele == 0:
                        self._status_elm_grid.SetCellBackgroundColour(numRowsEstatus,i+1,WX_ROJO)
                    else:
                        self._status_elm_grid.SetCellBackgroundColour(numRowsEstatus,i+1,WX_VERDE)

                self._busesEnTabla.append(nombre)
            self._status_grid.ForceRefresh()


        event.Skip()

        
        
def get_dicc_equipos(rawfile):
  """Crea el diccionario de equipos por bus a partir de un objeto RAWFile"""
  buses = rawfile.getBus()
  lineas = rawfile.getBranch()
  transformadores = rawfile.getTransformer()
  generadores = rawfile.getGenerator()
  shunts = rawfile.getShunt()
  sw_shunts = rawfile.getSW_Shunt()
  cargas = rawfile.getLoad()
  dicc_equipos = make_dicc_branches_x_bus(lineas, transformadores, cargas,
                                        generadores, shunts, sw_shunts)
  return dicc_equipos

def make_dicc_buses_numero(rawfile):
  """Crea un diccionario con los numeros de bus"""
  buses = rawfile.getBus()
  out = {}
  for bus in buses:
    out[bus["I"]] = bus

  return out

def make_dicc_branches_x_bus(lineas, transformadores, cargas, generadores, shunts, sw_shunts):
  """Crea un diccionario de las lineas conectadas a un bus"""
  dicc_equipos = defaultdict(lambda: set())
  for linea in lineas:
    dicc_equipos[linea["I"]].add((linea["KEY"], linea["J"], linea["ST"], "LT"))
    dicc_equipos[linea["J"]].add((linea["KEY"], linea["I"], linea["ST"], "LT"))

  for trans in transformadores:
    dicc_equipos[trans["I"]].add((trans["KEY"], trans["J"], trans["STAT"], "T"))
    dicc_equipos[trans["J"]].add((trans["KEY"], trans["I"], trans["STAT"], "T"))

  for carga in cargas:
    dicc_equipos[carga["I"]].add((carga["KEY"], None, carga["STATUS"], "L"))

  for generador in generadores:
    dicc_equipos[generador["I"]].add((generador["KEY"], None, generador["STAT"], "G"))

  for shunt in shunts:
    dicc_equipos[shunt["I"]].add((shunt["KEY"], None, shunt["STATUS"], "SH"))

  for sw_shunt in sw_shunts:
    dicc_equipos[sw_shunt["I"]].add((sw_shunt["KEY"], None, sw_shunt["STAT"], "SS"))

  return dicc_equipos

def grafica_bus(num_bus, dicc_equipos_x_bus, dicc_buses, fig, ax):
  """grafica las lineas y transformadores de un bus"""
  
#  print(dicc_buses)
  if num_bus not in dicc_buses:
    raise BusNoExiste("El bus no esta en el raw")
#   print(num_bus)
  estatus = dicc_buses[num_bus]["IDE"]

  equipos_graficar = dicc_equipos_x_bus[num_bus]
#   print("Dentro de la fun", equipos_graficar)
  num_equipos = len(equipos_graficar)
  equipos_x_lado = (num_equipos + 1)//2 if num_equipos else 1

  unidades_vertical = 1
  ancho_ventana = float(equipos_x_lado*unidades_vertical) * 2
  relacion_separacion_horizontal = 0.1
  separacion = ancho_ventana * relacion_separacion_horizontal
  escala = unidades_vertical*equipos_x_lado
  radio = 0.02

  size = fig.get_size_inches()*fig.dpi

  pixel = ancho_ventana/size[0]

  ax.set_xlim(0,ancho_ventana)
  ax.set_ylim(0, equipos_x_lado*unidades_vertical)

  #Bus principal
  if estatus != 4:
    ax.add_patch( Rectangle((ancho_ventana/2, 0), ancho_ventana*0.01, ancho_ventana, fc='k', ec='k', lw=2))
  else:
    ax.add_patch( Rectangle((ancho_ventana/2, 0), ancho_ventana*0.01, ancho_ventana, fc='#AEB6B6', ec='k', lw=2, ls='dashed'))

  #graficar buses de conexion
  cont = 0
  columna = 0
  y_pos = equipos_x_lado * unidades_vertical - unidades_vertical/2.0

  for clave, bus, estatus, tipo in sorted(equipos_graficar, key=lambda x:x[3]):

    fmt = "k"
    if estatus == 0:
      fmt = ":k"

    puntos_x = (separacion + columna*(ancho_ventana-2*separacion), ancho_ventana/2.0)
    puntos_y = (y_pos, y_pos)
    punto_medio = (max(puntos_x) + min(puntos_x)) / 2.0

    if bus:
      st = dicc_buses[bus]["IDE"]

    if tipo in ["LT", "T"]:
      #Nodos
      if st != 4:
        ax.add_patch(Circle((separacion + columna*(ancho_ventana-2*separacion), y_pos),
                            0.01*escala, fc='k', ec='k'))
      else:
        ax.add_patch(Circle((separacion + columna*(ancho_ventana-2*separacion), y_pos),
                            0.01*escala, fc='#AEB6B6', ec='k', ls='dashed'))
      #Etiquetas de los nodos
      textstr = "%d\n[%s]"%(bus, dicc_buses[bus]["KEY"])
      ax.text((separacion + columna*(ancho_ventana-2*separacion)),
               y_pos + 0.02*escala, textstr, fontsize=8)

      #Etiquetas de las lineas y los transformadores
      textstr = clave
      ax.text((punto_medio)-ancho_ventana*0.08,
               y_pos - radio*escala - pixel * 10, textstr, fontsize=8)


      if tipo == "T":

        ax.add_patch(Circle((punto_medio + radio*escala/2.0, y_pos),
                             radio*escala, ec='k', fill=False))
        ax.add_patch(Circle((punto_medio - radio*escala/2.0, y_pos),
                             radio*escala, ec='k', fill=False))

        ax.plot((min(puntos_x), punto_medio-radio*escala*1.5), puntos_y, fmt)
        ax.plot((max(puntos_x), punto_medio+radio*escala*1.5), puntos_y, fmt)

      elif tipo == "LT":
        ax.plot(puntos_x, puntos_y, fmt)

    else:
      ax.plot((punto_medio,puntos_x[1]), puntos_y, fmt)
      #Etiquetas de las equipos de una terminal
      textstr = clave
      ax.text((punto_medio) + pixel * 10,
               y_pos - radio*escala - pixel * 10, textstr, fontsize=8)
      ax.plot([punto_medio, punto_medio], [y_pos, y_pos -pixel*8], fmt)

      if tipo == "L":
        puntos = [
          [punto_medio + radio*escala, y_pos - pixel*8],
          [punto_medio - radio*escala, y_pos - pixel*8],
          [punto_medio, y_pos - 1.73*radio*escala - pixel*8],

        ]
        ax.add_patch(Polygon(puntos, ec='k', fill=False))

      if tipo == "G":
        ax.add_patch(Circle((punto_medio, y_pos - radio*escala - pixel*8),
                             radio*escala, ec='k', fill=False))

      if tipo in ["SS", "SH"]:
        x, y = puntos_semicircle(radio*escala/2, [punto_medio, y_pos-pixel*8-radio*escala/2], 50)
        ax.plot(x, y, "k")
        x, y = puntos_semicircle(radio*escala/2, [punto_medio, y_pos-pixel*8-radio*escala/2-radio*escala], 50)
        ax.plot(x, y, "k")

    cont += 1
    y_pos -= unidades_vertical
    if cont >= equipos_x_lado:
      columna = 1
      cont = 0
      y_pos = equipos_x_lado * unidades_vertical - unidades_vertical/2.0

  ax.set_title("%d[%s]"%(num_bus, dicc_buses[num_bus]["KEY"]))
  ax.axis('off')
  
def puntos_semicircle(radio, center, num_puntos):
  """imprime un semicirculo"""

  paso = radio/(num_puntos/2)
  x = []
  for i in range(num_puntos//2):
    x.append(paso*i)
  r2 = radio**2
  ymas = [(r2 - xs**2)**0.5 for xs in x]
  ymenos = [-ys for ys in sorted(ymas)]

  x = [xs for xs in x]
  x = x + sorted(x, reverse=True)
  y = ymas + ymenos
  x = [center[0] + xs for xs in x]
  y = [center[1] + ys for ys in y]
  return x, y

class BusNoExiste(Exception):
    """Se lanza cuando un bus no esta en el archivo raw"""
    pass

class LectorRamas(Thread):

    def __init__(self, mf, raws, sistema=0):
        Thread.__init__(self)
        self._mf = mf
        self._raws = raws
        self._sistema = sistema
        

    def run(self):
        # self._mf.RAWParameters_Panel.limpiar()
        self._mf.RAWDiag_Panel.limpiar()
        # self._mf.RAWParameters_Panel._recargar_raws.Enable(True)
        
        num_horas = len(self._raws)

        rojo = wx.Colour(238,46,46)
        verde = wx.Colour(86,219,65)
        negro = wx.Colour(0,0,0)
        blanco = wx.Colour(255,255,255)

        # self._mf.RAWDiag_Panel._statusRamas = defaultdict(
        #     lambda: {"estatus" : [0 for x in range(num_horas)],
        #              "datos" : [],
        #              "zona_carga": set(),
        #              "raw" : [] })
        self._mf.RAWDiag_Panel._statusBuses = defaultdict(
            lambda: {"estatus" : [0 for x in range(num_horas)],
                     "datos" : [],
                     "zona_carga": set(),
                     "raw" : []})
        
        self._mf.RAWDiag_Panel.aux_statusRamas = defaultdict(
            lambda: {"estatus" : [0 for x in range(num_horas)],
                     "datos" : [],
                     "zona_carga": set(),
                     "raw" : [] })
        self._mf.RAWDiag_Panel.aux_statusBuses = defaultdict(
            lambda: {"estatus" : [0 for x in range(num_horas)],
                     "datos" : [],
                     "zona_carga": set(),
                     "raw" : []})

        for num, raw in enumerate(self._raws):
            self._mf.SetStatusText("Leyendo ramas de %s" % path.basename(raw))
            find = RAW_REGEX.search(raw)
            
            i = num

            rawfile = RAWFile2(raw, self._sistema, 'verificador_imm_raw.PYRAW')
            
            lineas = rawfile.getBranch()
            transformadores = rawfile.getTransformer()
            buses = rawfile.getBus()
            
            for ln in lineas:
                self._mf.RAWDiag_Panel.aux_statusRamas[(ln["KEY"],num)]["estatus"][i] = ln["ST"]
                # if 'MMT' in (ln["KEY"],num):
                #     print((ln["KEY"],num),ln["ST"],ln["I"],ln["J"])
            for tr in transformadores:
                self._mf.RAWDiag_Panel.aux_statusRamas[tr["KEY"]]["estatus"][i] = tr["STAT"]
            for bus in buses:
                self._mf.RAWDiag_Panel.aux_statusBuses[bus["I"]]["estatus"][i] = 0 if bus["IDE"] == 4 else 1

            print(raw)
            rawfile.make_dict_buses_by_num()
            for ln in lineas:
                
                self._mf.RAWDiag_Panel.aux_statusRamas[(ln["KEY"],num)]["datos"] = [ln["I"],ln["J"],ln["CKT"],"LT"]
                self._mf.RAWDiag_Panel.aux_statusRamas[(ln["KEY"],num)]["zona_carga"].add(rawfile._dict_buses_by_num[ln["I"]]["WINPOL"])
                self._mf.RAWDiag_Panel.aux_statusRamas[(ln["KEY"],num)]["zona_carga"].add(rawfile._dict_buses_by_num[ln["J"]]["WINPOL"])
                # self._mf.RAWDiag_Panel.aux_statusRamas[(ln["KEY"],num)]["raw"].append(num)
                # if 'MMT' in ln['KEY']:
                #     print(self._mf.RAWDiag_Panel.aux_statusRamas[(ln["KEY"],num)])
            
            for tr in transformadores:
                self._mf.RAWDiag_Panel.aux_statusRamas[(tr["KEY"],num)]["datos"] = [tr["I"],tr["J"],tr["CKT"],"T"]
                self._mf.RAWDiag_Panel.aux_statusRamas[(tr["KEY"],num)]["zona_carga"].add(rawfile._dict_buses_by_num[tr["I"]]["WINPOL"])
                self._mf.RAWDiag_Panel.aux_statusRamas[(tr["KEY"],num)]["zona_carga"].add(rawfile._dict_buses_by_num[tr["J"]]["WINPOL"])
                # self._mf.RAWDiag_Panel.aux_statusRamas[(tr["KEY"],num)]["raw"].append(num)
                # if 'MMT' in tr['KEY']:
                #     print(self._mf.RAWDiag_Panel.aux_statusRamas[(tr["KEY"],num)])
            for bus in buses:
                self._mf.RAWDiag_Panel.aux_statusBuses[(bus["I"],num)]["datos"] = [bus["I"], "{}-{:5.2f}".format(bus["NAME"], bus["BASKV"]), "BUS"]
                self._mf.RAWDiag_Panel.aux_statusBuses[(bus["I"],num)]["zona_carga"].add(bus["WINPOL"])
                # self._mf.RAWDiag_Panel.aux_statusBuses[(bus["I"],num)]["raw"].append(num)
        
        # print(self._mf.RAWDiag_Panel.aux_statusRamas)

        # Crear un diccionario para almacenar los elementos únicos
        self._mf.RAWDiag_Panel._statusRamas = {}

        # Iterar sobre el diccionario original
        for key, value in self._mf.RAWDiag_Panel.aux_statusRamas.items():
            # Obtener el primer elemento de la clave
            first_element = key[0]

            # Verificar si el primer elemento ya existe en el diccionario único
            if first_element in self._mf.RAWDiag_Panel._statusRamas:
                # print(key[1])
                # Comparar los contenidos
                if self._mf.RAWDiag_Panel._statusRamas[first_element]["datos"] == value["datos"]:
                    # Si los contenidos son iguales, conservar solo una de las claves
                    self._mf.RAWDiag_Panel._statusRamas[first_element]["raw"] = [0,1]
                    self._mf.RAWDiag_Panel._statusRamas[first_element]["estatus"] = [1,1]
                    # if "MMT" in first_element:
                    #     print("Iguales",self._mf.RAWDiag_Panel._statusRamas[first_element])
                    continue
                else:
                    # Si los contenidos son diferentes, conservar ambas claves
                    # self._mf.RAWDiag_Panel._statusRamas[first_element, key[1]] = value
                    # self._mf.RAWDiag_Panel._statusRamas[first_element, key[1]]["raw"] = [key[1]]
                    self._mf.RAWDiag_Panel._statusRamas[first_element + "   dif"] = value
                    self._mf.RAWDiag_Panel._statusRamas[first_element + "   dif"]["raw"] = [key[1]]
                    # if "MMT" in first_element:
                    #     print("diferentes",self._mf.RAWDiag_Panel._statusRamas[first_element ,key[1]])
            else:
                # Si el primer elemento no existe en el diccionario único, agregarlo
                
                self._mf.RAWDiag_Panel._statusRamas[first_element] = value
                self._mf.RAWDiag_Panel._statusRamas[first_element]["raw"] = [key[1]]
                
        # for key, value in self._mf.RAWDiag_Panel._statusRamas.items():
        #     if "MMT" in key:
        #         print(key, value)
            

        self._mf.RAW_searchCtrl.Enable(True)
        
        self._mf.SetStatusText(u"Terminó la actividad")
        wx.PostEvent(self._mf, ResultEvent(True))
    
class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""

    def __init__(self, completed, data={}):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.completed = completed
        self.data = data
        
class RAWDiag1_Panel(wx.Panel):
# class RAWDiag1_Panel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, main_frame, tipos = None, etiquetas = None, data = None):
        wx.Panel.__init__(self, parent)
        # super().__init__(parent)
        
        
        # print("parent de grafica", parent)
        self.page = wx.Panel(parent)
        parent.AddPage(self.page, "RAW")
        # print("panel de page", self.page)
        self.mf = main_frame
        self._statusRamas = []
        self._statusBuses = []
        self._fig_diagrama = Figure()
        self._axes_diagrama = self._fig_diagrama.add_subplot(111)
        self._canvas_diagrama = FigureCanvas(self.page, -1, self._fig_diagrama)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._canvas_diagrama,1, wx.EXPAND,3)
        
        self.page.SetSizer(sizer)
        # self.SetupScrolling()
        
    def limpiar(self):
        self._axes_diagrama.clear()
        self._canvas_diagrama.draw()
        
        
class Grid2(gridlib.Grid):

    def __init__(self, panel, thread_verificar = None,  buscar = 1, copiar = 1,
                 pegar = 1, filtrar = 0, size=None):
        if size:
            gridlib.Grid.__init__(self, panel, size=size)
        else:
            gridlib.Grid.__init__(self, panel)
        # print(panel)
        self._buscar_flag = buscar
        self._copiar_flag = copiar
        self._pegar_flag = pegar
        self._filtrar_flag = filtrar
        self._th_verificar = thread_verificar
        self.mf = panel
        self.data = []
        self.row_labels = []
        self._popupID_contiene = wx.NewId()
        self._popupID_borrar_filtro = wx.NewId()
        self._popupID_inicia = wx.NewId()
        self._popupID_termina = wx.NewId()
        self._popupID_es_igual = wx.NewId()
        self.Col = 0
        self.Row = 0

        self.Bind(wx.EVT_MENU, self.OnContiene,
            id = self._popupID_contiene)
        self.Bind(wx.EVT_MENU, self.OnInicia,
            id = self._popupID_inicia)
        self.Bind(wx.EVT_MENU, self.OnTermina,
            id = self._popupID_termina)
        self.Bind(wx.EVT_MENU, self.OnEsIgual,
            id = self._popupID_es_igual)
        self.Bind(wx.EVT_MENU, self.OnBorrarFiltro,
            id = self._popupID_borrar_filtro)

    def resizeCols(self, cols, ad_cols = 0, lab_ad_cols = []):
        """
        Verifica que el grid tenga el tamaño adecuado de columnas
        """
        cols_now = self.GetNumberCols()
        diff_cols = (cols + ad_cols) - cols_now
        if diff_cols == 0:
            return 0
        elif diff_cols > 0:
            self.InsertCols(cols_now, diff_cols)
        else:
            self.DeleteCols(0, abs(diff_cols))
        for i, lab in enumerate(lab_ad_cols + [str(x) for x in range(cols)]):
            self.SetColLabelValue(i, lab)

    def resizeLabels(self, ancho, columnas_ad = [], proporcion = 1):
        """
        Cambia el ancho de las columnas para ajustarse al tamaño de la ventana
        """
        cols = self.GetNumberCols()
        row_label_size = self.GetRowLabelSize()
        ancho_adicional = sum(columnas_ad)

        new_tam = float(ancho * proporcion - row_label_size - 50 - ancho_adicional) / cols
        def_tam = self.GetDefaultColSize()
        if new_tam > def_tam:
            for i, size in enumerate(columnas_ad +                             \
                [new_tam]*(cols - len(columnas_ad))):
                self.SetColSize(i, size)
        else:
            for i, size in enumerate(columnas_ad +                             \
                [def_tam]*(cols - len(columnas_ad))):
                self.SetColSize(i, size)

    def clear(self):
        """
        Borrar el contenido de la tabla y cambia el color de fondo de las celdas
        a blanco y el color del font negro.
        """
        self.ClearGrid()
        cols = self.GetNumberCols()
        rows = self.GetNumberRows()
        for row in range(rows):
            for col in range(cols):
                self.SetCellBackgroundColour(row, col, WX_BLANCO)
                self.SetCellTextColour(row, col, WX_NEGRO)

    def OnLabelRclick(self, event):
        """
        Ejecuta la funcion de busqueda en una columna de la tabla.
        """

        col = event.GetCol()
        dlg = wx.TextEntryDialog(self.mf, 'Buscar','Buscar:')
        dlg.SetValue('')
        if dlg.ShowModal() == wx.ID_OK:
            busqueda = dlg.GetValue()
            num_rows = self.GetNumberRows()
            if num_rows != 0:
                text = ['' for ele in range(num_rows)]
                if col >= 0:
                    for ele in range(num_rows):
                        text[ele] = self.GetCellValue(ele,col)
                else:
                    for ele in range(num_rows):
                        text[ele] = self.GetRowLabelValue(ele)

                regex = r'(.*'+ re.escape(busqueda) + r'.*)'
                REGEX = re.compile(regex)
                for i,ele in enumerate(text):
                    res = REGEX.match(ele)
                    if res is not None:
                        if col >= 0:
                            self.SetGridCursor(i,col)
                            cell_coords = self.CellToRect(i,col)
                        else:
                            self.SetGridCursor(i,0)
                            cell_coords = self.CellToRect(i,0)

                        ppunit = self.GetScrollPixelsPerUnit()
                        y = cell_coords.y / ppunit[1]
                        self.Scroll(0, y)
                        dlg.Destroy()
                        event.Skip()
                        return

        else:
            dlg.Destroy()
            event.Skip()
            return
        dlg.Destroy()
        wx.MessageBox('No se pudo encontrar lo que se estaba buscando',\
                            'Info',wx.OK | wx.ICON_INFORMATION)
        event.Skip()

    def OnCellRclick(self, event):
        self.Col = event.Col
        self.Row = event.Row
        menu = wx.Menu()
        menu.Append(self._popupID_contiene, "Contiene ...")
        menu.Append(self._popupID_inicia, "Inicia con ...")
        menu.Append(self._popupID_termina, "Termina con ...")
        menu.Append(self._popupID_es_igual, "Es igual a ...")
        menu.Append(self._popupID_borrar_filtro, "Quitar filtro")
        self.PopupMenu(menu)
        menu.Destroy()

    def filtrar(self, regex):
        if regex:
            num_rows = self.GetNumberRows()
            num_cols = self.GetNumberCols()
            curr_col =  self.Col
            data_filtrada = []
            row_labels = []
            if num_rows != 0:
                text = ['' for ele in range(num_rows)]
                for ele in range(num_rows):
                    text[ele] = self.GetCellValue(ele,curr_col)

                for i,ele in enumerate(text):
                    res = regex.match(ele)
                    if res is not None:
                        aux = []
                        for col in range(num_cols):
                            aux.append(self.GetCellValue(i,col))
                        row_labels.append(self.GetRowLabelValue(i))
                        data_filtrada.append(aux)

                if len(data_filtrada) != 0:
                    self.DeleteRows(numRows = num_rows)
                    self.InsertRows(0,len(data_filtrada))
                    for (i, data), row_label in zip(enumerate(data_filtrada), row_labels):
                        for j, col in enumerate(data):
                            self.SetCellValue(i,j,col)
                            self.SetReadOnly(i,j,True)
                        self.SetRowLabelValue(i,row_label)
                    self.SetGridCursor(0,curr_col)
                else:
                    self.DeleteRows(numRows = num_rows)
                    self.InsertRows(0,1)
                    self.SetGridCursor(0,curr_col)

                self.ForceRefresh()

    def OnContiene(self, event):
        dlg = wx.TextEntryDialog(self.mf, 'Contiene','Filtrar')
        dlg.SetValue('')

        if dlg.ShowModal() == wx.ID_OK:
            filtro = dlg.GetValue()
            regex = r'.*' + filtro + r'.*'
            REGEX = re.compile(regex)
            self.filtrar(REGEX)

        dlg.Destroy()
        event.Skip()
        return

    def OnInicia(self, event):
        dlg = wx.TextEntryDialog(self.mf, 'Inicia','Filtrar')
        dlg.SetValue('')

        if dlg.ShowModal() == wx.ID_OK:
            filtro = dlg.GetValue()
            regex = r"^" + filtro + r'.*'
            REGEX = re.compile(regex)
            self.filtrar(REGEX)

        dlg.Destroy()
        event.Skip()
        return

    def OnTermina(self, event):
        dlg = wx.TextEntryDialog(self.mf, 'Termina','Filtrar')
        dlg.SetValue('')

        if dlg.ShowModal() == wx.ID_OK:
            filtro = dlg.GetValue()
            regex = r".*" + filtro + r'$'
            REGEX = re.compile(regex)
            self.filtrar(REGEX)

        dlg.Destroy()
        event.Skip()
        return

    def OnEsIgual(self, event):
        dlg = wx.TextEntryDialog(self.mf, 'Es igual','Filtrar')
        dlg.SetValue('')

        if dlg.ShowModal() == wx.ID_OK:
            filtro = dlg.GetValue()
            regex = re.escape(filtro)
            REGEX = re.compile(regex)
            self.filtrar(REGEX)

        dlg.Destroy()
        event.Skip()
        return

    def OnBorrarFiltro(self, event):
        num_rows = self.GetNumberRows()
        if len(self.data) != 0:
            self.DeleteRows(numRows = num_rows)
            self.InsertRows(0,len(self.data))
            for (i, data), row_label in zip(enumerate(self.data), self.row_labels):
                if isinstance(data, list):
                    for j, col in enumerate(data):
                        self.SetCellValue(i,j,col)
                        self.SetReadOnly(i,j,True)
                else:
                    self.SetCellValue(i,0,data)
                    self.SetReadOnly(i,0,True)

                self.SetRowLabelValue(i,row_label)
            self.SetGridCursor(0,0)
        self.ForceRefresh()

        if event is not None:
            event.Skip()

    def OnCTRL(self,event):
        """
        Ejecuta las funciones de copiar, pegar y buscar mediante comandos del
        tipo CTRL +
        """
        if self.mf.worker is None:
            keycode = event.GetKeyCode()
            controlDown = event.CmdDown()
            if controlDown:
                if keycode == 2 and self._buscar_flag: #Buscar
                    dlg = wx.TextEntryDialog(self.mf, 'Buscar','Buscar:')
                    dlg.SetValue('')
                    if dlg.ShowModal() == wx.ID_OK:
                        busqueda = dlg.GetValue()
                        num_rows = self.GetNumberRows()
                        curr_row = self.GetGridCursorRow() + 1
                        if num_rows != 0:
                            text = ['' for ele in range(curr_row,num_rows)]
                            for ele in range(curr_row,num_rows):
                                text[ele - curr_row] =                         \
                                          self.GetCellValue(ele,0)
                            regex = r'(.*'+ re.escape(busqueda) + r'.*)'
                            REGEX = re.compile(regex)
                            for i,ele in enumerate(text):
                                res = REGEX.match(ele)
                                if res is not None:
                                    self.SetGridCursor(i+curr_row,0)
                                    cell_coords = self.CellToRect(i+curr_row,0)
                                    ppunit = self.GetScrollPixelsPerUnit()
                                    y = cell_coords.y / ppunit[1]
                                    self.Scroll(0, y)
                                    dlg.Destroy()
                                    event.Skip()
                                    return
                        else:
                            dlg.Destroy()
                            event.Skip()
                            return

                    dlg.Destroy()
                    wx.MessageBox('No se pudo encontrar lo que se estaba '
                                  'buscando','Info',wx.OK|wx.ICON_INFORMATION)

                elif keycode == 3 and self._copiar_flag: #Copiar al clipboard
                    try:
                        top_left =  self.GetSelectionBlockTopLeft()[0]
                        bottom_right = self.GetSelectionBlockBottomRight()[0]
                        self.ClearSelection()
                    except IndexError:
                        top_left = [0,0]
                        top_left[0] = self.GetGridCursorRow()
                        top_left[1] = self.GetGridCursorCol()
                        bottom_right = top_left

                    text = ''
                    for row in range(top_left[0],bottom_right[0]+1):
                        for col in range(top_left[1],bottom_right[1]+1):

                            text += '%s' % self.GetCellValue(row,col)
                            if col != bottom_right[1]:
                                text += delimitador
                        if row != bottom_right[0]:
                            text += '\r'

                    if not wx.TheClipboard.IsOpened():
                        clipdata = wx.TextDataObject()
                        clipdata.SetText(text)
                        wx.TheClipboard.Open()
                        wx.TheClipboard.SetData(clipdata)
                        wx.TheClipboard.Close()

                elif keycode == 22 and self._pegar_flag: #Pegar del clipboard
                    if not wx.TheClipboard.IsOpened():
                        do = wx.TextDataObject()
                        wx.TheClipboard.Open()
                        success = wx.TheClipboard.GetData(do)
                        wx.TheClipboard.Close()
                        if success:
                            aux = do.GetText()
                            aux = aux.replace('\n', '\r')

                            if len(aux) == 0:
                                wx.MessageBox(u'No hay información en el '
                                    u'portapapeles', u'Información',
                                    wx.OK | wx.ICON_INFORMATION)
                                return 1

                            if aux[-1] == '\r':
                                aux = aux[:-1]
                            aux = aux.split('\r')
                            text = []
                            for fila in aux:
                                text.append(fila.split('\t'))

                            try:
                                top_left = self.GetSelectionBlockTopLeft()[0]
                                bottom_right =                                 \
                                          self.GetSelectionBlockBottomRight()[0]
                                self.ClearSelection()
                            except IndexError:
                                top_left = [0,0]
                                top_left[0] = self.GetGridCursorRow()
                                top_left[1] = self.GetGridCursorCol()
                                bottom_right = top_left


                            if len(text) == bottom_right[0] - top_left[0] + 1 \
                            and len(text[0]) == bottom_right[1] -top_left[1] +1:
                                for row, i in zip(text, range(top_left[0],
                                                          bottom_right[0] + 1)):
                                    for col, j in zip(row, range(top_left[1],
                                                          bottom_right[1] + 1)):
                                        if not self.IsReadOnly(i,j):
                                            self.SetCellValue(i,j,col)
                            else:
                                wx.MessageBox(u'La selección y la información '
                                              u'almacenada en el portapapeles '
                                              u'no coincide en tamaño',
                                              u'Información',                  \
                                              wx.OK | wx.ICON_INFORMATION)
                                return 1

                            if self._th_verificar is not None:
                                wx.CallLater(100, self._th_verificar, None)

                        else:
                            wx.MessageBox(u'No hay información en el '
                                          u'portapapeles', u'Información',
                                          wx.OK | wx.ICON_INFORMATION)
                            return 1
        else:
            self.mf.SetStatusText("Proceso ocupado")

        event.Skip()

    def OnCellSelected(self,event):
        self._string = self.GetCellValue(event.Row, event.Col)
        event.Skip()

    def OnCellChange(self, event):
        val = self.GetCellValue(event.Row, event.Col)
        try:
            val = float (val)
        except ValueError:
            wx.MessageBox('El valor introducido no puede convertirse en float' \
                          '\n Hora : %d \n %s no modificado' %                 \
                           (event.Col, self._string), 'Warning',
                           wx.OK | wx.ICON_WARNING)
            self.SetCellValue(event.Row, event.Col, self._string)
            return

        self.SetCellValue(event.Row, event.Col,"%0.2f" % val)

