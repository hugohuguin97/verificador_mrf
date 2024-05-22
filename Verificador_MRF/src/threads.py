import re
import wx
import wx.grid as gridlib
import logging

from os import path
from threading import Thread
from collections import defaultdict
from usolibpy.rawfile import RAWFile2

from .otros import comparar_topologia

RAW_REGEX = re.compile(r'.*\d{2}\w{3}\d{4}_(\d{2}).r?R?a?A?w?W?')
EVT_RESULT_ID = wx.NewId()
WX_ROJO = wx.Colour(238,46,46)
WX_VERDE = wx.Colour(86,219,65)
WX_NEGRO = wx.Colour(0, 0, 0)
WX_BLANCO = wx.Colour(255,255,255)
delimitador = '\t'

log = logging.getLogger('VERIFICADOR')

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

        # rojo = wx.Colour(238,46,46)
        # verde = wx.Colour(86,219,65)
        # negro = wx.Colour(0,0,0)
        # blanco = wx.Colour(255,255,255)

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
        
class CompararTopologia(Thread):

    def __init__(self, mf, opc):
        Thread.__init__(self)
        self._mf = mf
        self._opc = opc

    def run(self):
        logging.getLogger("comp_log").setLevel(logging.CRITICAL)
        if self._opc["sistema1"] != self._opc["sistema2"]:
            log.error("No se pueden comparar raws de diferentes sistemas") 
            wx.PostEvent(self._mf, ResultEvent(False))
            return None

        self._mf.raw1_dif_topol, self._mf.raw2_dif_topol = comparar_topologia(
            self._opc["raw_sp71"], self._opc["raw_sp72"], self._opc["sistema1"],
            self._opc["tipo_raw1"], self._opc["tipo_raw2"], self._opc["ruta_almacenaje"]
        )

        wx.PostEvent(self._mf, ResultEvent(True)) 
  
  
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

