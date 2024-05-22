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
from collections import defaultdict
from pyraw import RAWFile
# from usolibpy.rawfile import RAWFile2

from .threads import LectorRamas, CompararTopologia, Grid2

from .otros import get_dicc_equipos, make_dicc_buses_numero, make_dicc_branches_x_bus, \
                      grafica_bus, puntos_semicircle

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

WX_ROJO = wx.Colour(238,46,46)
WX_VERDE = wx.Colour(86,219,65)
WX_NEGRO = wx.Colour(0, 0, 0)
WX_BLANCO = wx.Colour(255,255,255)

ruta_base = path.abspath(path.join(__file__, "../.."))
ruta_resultados = path.join(ruta_base,"results")
ruta_data = path.join(ruta_base,"data")
log = logging.getLogger("verificador_imm_raw")
log.setLevel(logging.INFO)
# Formatea la fecha y hora
# name_archivo = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
name_archivo = datetime.now().strftime("%d_%m_%Y_%H")

# Guardar el archivo con el nombre basado en la fecha
topol_txt = f"Comp_Topol_{name_archivo}.txt"
topol_exp = path.join(ruta_resultados, topol_txt)
param_txt = f"Comp_Param_{name_archivo}.txt"
param_exp = path.join(ruta_resultados, param_txt)

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
        
        # Agrgar imagen de CENACE
        icons_path = path.join(ruta_base, "iconos")
        cen_bm = path.join(icons_path,"CENACE-logo-completo.png")
        self.mf.logo_cen3.SetBitmap(wx.Bitmap( cen_bm, wx.BITMAP_TYPE_ANY ))
        self.mf.logo_cen31.SetBitmap(wx.Bitmap( cen_bm, wx.BITMAP_TYPE_ANY ))
        
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
        self.mf.raw1_dif_topol = []
        self.mf.raw2_dif_topol = []
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
        self.mf.RAWselected_path_1 = path_raw1
        self.mf.RAWselected_path_2 = path_raw2
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
        
        # Declara las banderas de formato de los RAW
        self._raw_flg1 = self.mf.raw_flag1
        self._raw_flg2 = self.mf.raw_flag2
        # Declara los botones de comparacion
        self._comp_topol_bto = self.mf.comp_topol_bto
        self._comp_param_bto = self.mf.comp_param_bto
        self._comp_topol_bto.Bind(wx.EVT_BUTTON, self._comparar_topologia)
        # self._comp_param_bto.Bind(wx.EVT_BUTTON, self._comparar_parametros)
        
        
    def on_check(self, event):
        checked_item = event.GetSelection()
        num_items = self._sistema.GetCount()
        for i in range(num_items):
            if i != checked_item:
                self._sistema.Check(i, False)
        self.sistema = checked_item

    def RAWpath_select1(self, event):
        self.mf.RAWselected_path_1 = self.RAW_pathSel1.GetPath()
        print("El RAW 1 es",self.mf.RAWselected_path_1)
    def RAWpath_select2(self, event):
        self.mf.RAWselected_path_2 = self.RAW_pathSel2.GetPath()
        print("El RAW 2 es",self.mf.RAWselected_path_2)

    def _recargar(self, event):

        # print(self.mf._archivos_raw)
        # self.sistema = self._sistema.GetSelection()
        # print("El sistema seleccionado es:", self.sistema)
        # print(self.mf.worker)
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

    def _comparar_topologia(self, event):
        # print(self.mf.worker)
        if self.mf.worker is None:
            self.mf.reporte_comparacion = topol_exp
            opc = {
                "raw_sp71": self.mf.RAWselected_path_1,
                "sistema1": self.mf._sistema,
                "tipo_raw1": self._raw_flg1.GetValue(),
                "raw_sp72": self.mf.RAWselected_path_2,
                "sistema2": self.mf._sistema,
                "tipo_raw2": self._raw_flg2.GetValue(),
                "ruta_almacenaje":  self.mf.reporte_comparacion,
            }
            # print(opc)
            self.mf.worker = CompararTopologia(self.mf, opc)
            self.mf.worker.start()
            self.mf.diff_branch_bto.Enable()
        else:
            self.mf.SetStatusText(
                'Proceso ocupado, espere a finalizar el anterior.')

        event.Skip()

class RAWDiag_Panel(wx.lib.scrolledpanel.ScrolledPanel):
    
    def __init__(self, parent, main_frame, tipos = None, etiquetas = None, data = None):
        super().__init__(parent)
        # wx.Panel.__init__(self, parent)
        self.mf = main_frame
        self.val_raw = parent
        self._statusRamas = []
        self._statusBuses = []
        self.mf.equipos_graficar_1 = {}
        self.mf.equipos_graficar_2 = {}
        
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
        
        # Delcara el boton de diferencia de topología
        self.show_dif = self.mf.diff_branch_bto
        self.show_dif.Bind(wx.EVT_BUTTON, self._mostrar_dif_topol)
        
        
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
        self.subRama_Stext.SetLabel("")
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
                print(f"Numero de Bus de {listCtrl}:", numero_bus)
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
            # for key, value in dicc_equipos1.items():
            #     print(dicc_equipos1)
            #     if "ANG" in key:
            #         print(dicc_equipos1)
            dicc_buses1 = make_dicc_buses_numero(rawfile1)
            # print(dicc_buses1)
            
            rawfile2 = self.mf.rawfile2 #RAWFile(self.mf._archivos_raw[1], sistema, "")
            dicc_equipos2 = get_dicc_equipos(rawfile2)
            dicc_buses2 = make_dicc_buses_numero(rawfile2)

            try:
                # Grafica el panel de RAW 1
                estatus1 = dicc_buses1[numero_bus]["IDE"]
                self.mf.equipos_graficar_1 = dicc_equipos1[numero_bus]
                
                grafica_bus(numero_bus, dicc_equipos1, dicc_buses1,
                            self.mf.RAWDiagram1_Panel._fig_diagrama,
                            self.mf.RAWDiagram1_Panel._axes_diagrama)
                self.mf.RAWDiagram1_Panel._canvas_diagrama.draw()
                                
                self.OnSetRamas(self.RAW1_listCtrl, self.mf.equipos_graficar_1)
                    
            except Exception as e:
                print(f"El BUS {numero_bus} no se encuentra en el RAW 1 ")
                pass
                
            try:
                # Grafica el panel de RAW 2
                estatus2 = dicc_buses2[numero_bus]["IDE"]
                self.mf.equipos_graficar_2 = dicc_equipos2[numero_bus]
                # print("Con el self",self.mf.equipos_graficar_2)
                
                grafica_bus(numero_bus, dicc_equipos2, dicc_buses2,
                            self.mf.RAWDiagram2_Panel._fig_diagrama,
                            self.mf.RAWDiagram2_Panel._axes_diagrama)
                self.mf.RAWDiagram2_Panel._canvas_diagrama.draw()
                
                self.OnSetRamas(self.RAW2_listCtrl, self.mf.equipos_graficar_2)
                
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
    
    def _mostrar_dif_topol(self, event):
        
        for index, row in enumerate(self.mf.raw1_dif_topol):
            self.RAW1_listCtrl.InsertItem(index, str(row[0]))  # Insertar el primer elemento de cada fila en la primera columna
            for col_index, col_value in enumerate(row[1:], start=1):
                self.RAW1_listCtrl.SetItem(index, col_index, str(col_value))  # Insertar los demás elementos de la fila en las siguientes columnas
    
        for index, row in enumerate(self.mf.raw2_dif_topol):
            self.RAW2_listCtrl.InsertItem(index, str(row[0]))  # Insertar el primer elemento de cada fila en la primera columna
            for col_index, col_value in enumerate(row[1:], start=1):
                self.RAW2_listCtrl.SetItem(index, col_index, str(col_value))  # Insertar los demás elementos de la fila en las siguientes columnas
    
        
        
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
        
        