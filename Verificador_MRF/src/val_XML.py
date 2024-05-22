import wx
import os
import wx.xrc as xrc
import wx.adv as adv
import wx.dataview as dv
import wx.stc as stc
import logging
import wx.lib.scrolledpanel
import wx.lib.agw.aui as aui
from glob import glob
from os.path import join, basename, getmtime
from datetime import datetime, timedelta, date
from threading import Thread
from os import path
import xml.etree.ElementTree as ET
import time
ruta_base = path.abspath(path.join(__file__, "../.."))
ruta_resultados = path.join(ruta_base,"resultados")
ruta_data = path.join(ruta_base,"data")
log = logging.getLogger("verificador_imm_xml")
log.setLevel(logging.INFO)
# Formatea la fecha y hora
name_archivo = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
# Guardar el archivo con el nombre basado en la fecha
archivo_xlsx = f"ValidacionesXML{name_archivo}.xlsx"
path_exp = path.join(ruta_resultados, archivo_xlsx)

TIPOS_VALIDOS = [
    "NAFlag",
    "sysNetworkCategory",
    "sysNetworkConfig",
    "sysNetCompanies",
    "GeographicalRegion",
    "SubGeographicalRegion",
    "Substation",
    "VoltageLevel",
    "BusbarSection",
    "ConnectivityNode",
    "SynchronousMachine",
    "StaticVarCompensator",
    "ConformLoad",
    "NonConformLoad",
    "Disconnector",
    "GroundDisconnector",
    "Breaker",
    "ShuntCompensator",
    "SeriesCompensator",
    "PowerTransformer",
    "ComplexTransformer",
    "TransformerWinding",
    "TapChanger",
    "LineVoltageLevel",
    "ACLineSegment",
    "Terminal",
    "ReactiveCapabilityCurve",
    "SteamTurbine",
    "sysGenPowerPlants",
    "CombinedCyclePlant",
    "HydroPowerPlant",
    "SolarPlant",
    "WindPlant",
    "ThermalPowerPlant",
    "HydroGeneratingUnit",
    "SolarGeneratingUnit",
    "ThermalGeneratingUnit",
    "WindGeneratingUnit",
    "CombinedCycleConfiguration",
    "CurveData",
    "BaseVoltage",
    "IncrementalHeatRateCurve",
    "HydroPowerDischargeCurve",
]

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
        
        
class XML_panel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, main_frame):
        # wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        super().__init__(parent)
        self.mf = main_frame
        self.parent = parent
        
        # Agrgar imagen de CENACE
        icons_path = path.join(ruta_base, "iconos")
        cen_bm = path.join(icons_path,"CENACE-logo-completo.png")
        self.mf.logo_cen2.SetBitmap(wx.Bitmap( cen_bm, wx.BITMAP_TYPE_ANY ))
        
        self.log = log
        self.xml_log_textCtrl = self.mf.xml_log_textCtrl
        txt_handler = CustomConsoleLogHandler(self.xml_log_textCtrl)
        txt_handler.setFormatter(
            logging.Formatter('%(name)-12s %(levelname)9s: %(message)s'))
        txt_handler.setLevel(logging.INFO)
        self.log.addHandler(txt_handler)
        logging.getLogger("arbol_mage").addHandler(txt_handler)
        # Agrega el margen para los marcadores
        self.XML_TextCtrl = self.mf.XML_TextCtrl
        self.XML_TextCtrl.SetMarginType(1, stc.STC_MARGIN_SYMBOL)
        self.XML_TextCtrl.SetMarginWidth(1, 30)  # Ancho del margen para los números de línea
        #Define los marcadores
        self.XML_TextCtrl.MarkerDefine(1, stc.STC_MARK_ROUNDRECT, "red", "red")
        self.XML_TextCtrl.MarkerDefine(2, stc.STC_MARK_ROUNDRECT, "red", "yellow")
        self.XML_TextCtrl.MarkerDefine(3, stc.STC_MARK_ROUNDRECT, "blue", "blue")
        self.XML_TextCtrl.MarkerDefine(4, stc.STC_MARK_ROUNDRECT, "blue", "yellow")
        self.XML_TextCtrl.MarkerDefine(10, stc.STC_MARK_ARROW, "blue", "blue")
        self.mf.worker = None
        
        self.XMLselected_path = ''
        self.ruta_base = ruta_base
        self.lista_ok = []
        self.index_start = 0
        self.word_aux = ''
        self.cont = 0
        self.start_date_aux = 0
        self.end_date_aux = 0
        # Diccionario para almacenar los estilos aplicados a cada palabra
        self.word_styles = {}
        self.word_styles_aux = {}
        self.fg_color = wx.BLUE
        self.bg_color = wx.YELLOW
        # Directorio XML
        directorio_mage = r'C:\Users\E0139\OneDrive - CENACE\ACTIVACIONES MAGE'
        # directorio_mage = '/Users/victorhernandez/Library/CloudStorage/OneDrive-CENACE/ACTIVACIONES MAGE'
        self.XMLselected_path = directorio_mage
        # Obtener la hora actual y restarle una hora
        current_time = datetime.now()
        hora_cero = timedelta(hours=current_time.hour,minutes=current_time.minute,seconds=current_time.second)
        start_time = current_time - hora_cero + timedelta(hours=0) #Horas en atrazo
        end_time = current_time - hora_cero + timedelta(hours=23,minutes=59) #Horas en atrazo
        
        # Obtener la XML path data
        self.XML_pathSel = self.mf.XML_pathSel
        self.XML_pathSel.SetPath(directorio_mage)
        self.XML_pathSel.Bind(wx.EVT_DIRPICKER_CHANGED, self.XMLpath_select)
        
        # Obtener la hora inicial y final
        self.start_tPicker = self.mf.start_tPicker
        self.start_tPicker.SetValue(start_time)
        self.end_tPicker = self.mf.end_tPicker
        self.end_tPicker.SetValue(end_time)
        
        
        # Obtener la fecha de consulta de los XML
        self.XML_ListCtrl = self.mf.XML_ListCtrl
        self.XML_ListCtrl.InsertColumn(0, 'Nombre del archivo', width=360)
        self.XML_ListCtrl.InsertColumn(1, 'Fecha', width=110)
        self.XML_ListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.procesar_xml)

        # Obtener la fecha de consulta de los XML
        self.Date_calendar = self.mf.Date_calendar
        self.Date_calendar.Bind(adv.EVT_CALENDAR, self.get_fecha)
        
        # Declara el control de texto XML
        self.XML_TextCtrl = self.mf.XML_TextCtrl
        
        # Ejecutar la busqueda 
        self.XML_searchCtrl = self.mf.XML_searchCtrl
        self.XML_searchCtrl.Bind(wx.EVT_CHAR_HOOK, self.on_search)
        
        # Declaramos el bto de verificar
        self.bto_verificar = self.mf.bto_verificar_xml
        self.bto_verificar.Bind(
            wx.EVT_BUTTON, lambda event: self.inicializar_thread(event, Verificador, self.mf, "Realizando validaciones")
        )
        
        self.search_textCtrl = self.mf.search_textCtrl
        self.verif_textCtrl = self.mf.verif_textCtrl
        
        self.verif_cBox = self.mf.verif_cBox
        self.verif_cBox.Bind(wx.EVT_COMBOBOX, self.on_combobox_select)
        
        pass
    
    def inicializar_thread(self, event, thread, parent, comentario):
        """Inicializa un thread"""
        if self.mf.worker is None:
            self.mf.SetStatusText(comentario)
            # print(thread)
            self.mf.worker = thread(self, parent)
            self.mf.worker.start()
        else:
            self.mf.SetStatusText('Proceso ocupado, espere a finalizar el anterior.')
        
    def XMLpath_select(self, event):
        self.XMLselected_path = self.XML_pathSel.GetPath()
        print(self.XMLselected_path)
    
    # Captura la hora inicial y final
    def get_fecha(self, event):
        self.update_lista_xml(event)
        
    def update_lista_xml(self, event):
        """Obtiene la lista de archivos xml segun el periodo.

        Parameters
        ----------
        carpeta_insumos:
            Variable de la carpeta elegida
            
        """
        start_time = self.start_tPicker.GetTime()
        end_time = self.end_tPicker.GetTime()
        start_hour, start_minute, start_second = start_time
        end_hour, end_minute, end_second = end_time
        hora_ini = wx.DateTime.FromHMS(*start_time).Format("%I:%M:%S %p")
        hora_fin = wx.DateTime.FromHMS(*end_time).Format("%I:%M:%S %p")
        
        if self.cont < 1:
            start_date = self.Date_calendar.GetDate()
            self.start_date_aux = start_date
            end_date = start_date
            self.end_date_aux = end_date
            self.cont = self.cont + 1
            fecha_ini = wx.DateTime(self.start_date_aux.GetDay(), self.start_date_aux.GetMonth(), self.start_date_aux.GetYear()).Format("%d/%m/%Y")
            start_datetime = wx.DateTime(self.start_date_aux.GetDay(), self.start_date_aux.GetMonth(), self.start_date_aux.GetYear(), start_hour, start_minute, start_second)
            end_datetime = wx.DateTime(self.end_date_aux.GetDay(), self.end_date_aux.GetMonth(), self.end_date_aux.GetYear(), end_hour, end_minute, end_second)
            self.log.info(f"El periodo de busqueda es del día {fecha_ini} de {hora_ini} a {hora_fin}")
        else:
            end_date = self.Date_calendar.GetDate()
            self.end_date_aux = end_date
            if end_date < self.start_date_aux:
                self.end_date_aux = self.start_date_aux
                self.start_date_aux = end_date
                self.cont = 0
            start_datetime = wx.DateTime(self.start_date_aux.GetDay(), self.start_date_aux.GetMonth(), self.start_date_aux.GetYear(), start_hour, start_minute, start_second)
            str_start_date = start_datetime.Format("%d/%m/%Y")
            end_datetime = wx.DateTime(self.end_date_aux.GetDay(), self.end_date_aux.GetMonth(), self.end_date_aux.GetYear(), end_hour, end_minute, end_second)
            str_end_date = end_datetime.Format("%d/%m/%Y")
            self.log.info(f"El periodo de busqueda es: {str_start_date} al {str_end_date}")
            self.cont = 0
        archivos_seleccionados = sorted(glob(path.join(self.XMLselected_path, "*.xml")), key=os.path.getatime)
        
        # Ordenar los archivos por fecha
        archivos_ordenados = sorted(archivos_seleccionados, key=lambda x: os.path.getmtime(x))
        # print(archivos_ordenados)
        self.XML_ListCtrl.DeleteAllItems()
        for idx, xml_file in enumerate(archivos_ordenados):
            file_name = basename(xml_file)
            file_date = datetime.fromtimestamp(getmtime(xml_file)).strftime('%d-%m-%Y %H:%M')
            file_time = wx.DateTime.FromTimeT(int(os.path.getmtime(xml_file)))
            if start_datetime <= file_time <= end_datetime:
                self.XML_ListCtrl.Append((basename(xml_file),file_date))
     
        self.mf.SetStatusText("Terminó la actividad")
        self.mf.worker = None
    
    #Seccion de funciones adicionales
    def procesar_xml(self, event ):
        # Obtener el índice del elemento seleccionado
        index = event.GetIndex()
        # Obtener el nombre del archivo seleccionado
        self.file_name = self.XML_ListCtrl.GetItemText(index)
        ruta_completa = path.join(self.XMLselected_path, self.file_name)
        codificaciones = ['utf-8', 'iso-8859-1', 'latin-1']
        
        try:
            # Leer el archivo XML como Unicode
            with open(ruta_completa, 'r', encoding='utf-8') as file:
                xml_content = file.read()
        except Exception as e:
            try:
                # Leer el archivo XML como Unicode
                with open(ruta_completa, 'r', encoding='iso-8859-1') as file:
                    xml_content = file.read()
            except Exception as e:
                wx.MessageBox(f"Error al cargar el archivo XML: {e}", "Error", wx.OK | wx.ICON_ERROR)

        # Analizar el contenido XML
        self.root = ET.fromstring(xml_content)
        xml_str = ET.tostring(self.root, encoding='utf-8').decode('utf-8')
        self.XML_TextCtrl.SetText(xml_str)
        # Almacenamos el contenido y formato original
        self.fmt_text_ini = self.XML_TextCtrl.GetText()
        self.fmt_style_ini = self.XML_TextCtrl.GetStyleBits()
        self.reset_panel(self)
        
        
    def on_search(self, event):
        
        count_list =  []
        keycode = event.GetKeyCode()
        # print(keycode)
        special_words = [('naflag', 'NAFlag'),
                         ('scadaflag', 'SCADAFlag'),
                         ('aclines', 'ACLines'),
                         'transformer',
                         'conformload',
                         ]
        
        # Crear una lista nueva de palabras con las condiciones dadas
        special_wordsM = [word[1] if isinstance(word, tuple) else word.capitalize() for word in special_words]

        if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
            search_word = self.XML_searchCtrl.GetValue()
            if search_word.strip() != '':
                self.XML_TextCtrl.MarkerDeleteAll(10)
                # Obtener la palabra a buscar
                search_word = self.XML_searchCtrl.GetValue().strip()

                # Iterar sobre cada palabra en la lista especial
                for word in special_wordsM:
                    # Comparar la palabra nueva con la palabra de la lista especial (ignorando mayúsculas y minúsculas)
                    if search_word.lower() == word.lower():
                        # Reasignar la palabra nueva con la palabra de la lista especial
                        search_word = word
                        break  # Salir del bucle una vez que se haya encontrado una coincidencia

                # Obtener el contenido del control de texto
                text_content = self.XML_TextCtrl.GetText()
                
                # Buscar la palabra en el texto
                if search_word != self.word_aux:# and self.word_aux != '':
                    index = 0
                    index = text_content.find(search_word)
                    self.word_styles_aux = {}
                    for word_ind in self.word_styles.items():
                        # print(word_ind)
                        self.XML_TextCtrl.StartStyling(word_ind[0])
                        self.XML_TextCtrl.SetStyling(len(self.word_aux), word_ind[1])
                else:
                    index = text_content.find(search_word)
                if index == -1:
                    # La palabra no fue encontrada, mostrar un mensaje
                    wx.MessageBox(f"La palabra '{search_word}' no fue encontrada.", "Advertencia", wx.OK | wx.ICON_WARNING)
                    
                while index != -1:
                    # Aplicar estilo a la palabra encontrada
                    self.apply_style(index, len(search_word),search_word)
                    # Actualizar el índice para buscar la próxima ocurrencia
                    index = text_content.find(search_word, index + 1)
                    count_list.append(index)
            else:
                # Restauramos el contenido y formato original
                for word_ind in self.word_styles.items():
                    self.XML_TextCtrl.StartStyling(word_ind[0])
                    self.XML_TextCtrl.SetStyling(len(self.word_aux), word_ind[1])
                        
                self.reset_panel_par(self)
                return
            self.search_textCtrl.SetValue(str(len(count_list)) + ' coincidencias')
        event.Skip()
        
    def apply_style(self, start, length, word):
        self.cont = self.cont + 1
        # Obtener el estilo actual en la posición de inicio
        current_style = self.XML_TextCtrl.GetStyleAt(start)
        # Almacenar el estilo aplicado para esta palabra
        self.word_styles[start] = current_style
        # Aplicar el estilo al texto
        self.XML_TextCtrl.StartStyling(start)
        
        self.XML_TextCtrl.SetStyling(length, stc.STC_H_SCRIPT)
        self.XML_TextCtrl.StyleSetForeground(stc.STC_H_SCRIPT, wx.RED)
        self.XML_TextCtrl.StyleSetBackground(stc.STC_H_SCRIPT, wx.GREEN)
        self.word_aux = word
        # Agregar marcadores en algunas líneas
        line = self.XML_TextCtrl.LineFromPosition(start)
        self.XML_TextCtrl.MarkerAdd(line, 10)
        # Obtener el estilo actual en la posición de inicio
        current_style_aux = self.XML_TextCtrl.GetStyleAt(start)
        # Almacenar el estilo aplicado para esta palabra
        self.word_styles_aux[start] = [current_style_aux,word,line]
        self.Refresh()  # Actualizar la apariencia del botón
        
    def on_combobox_select(self, event):
        
        self.XML_TextCtrl.SetText(self.fmt_text_ini)
        self.XML_TextCtrl.SetStyleBits(self.fmt_style_ini)
        selected_text = self.verif_cBox.GetValue()
        self.resaltar_instancias(self.root, selected_text, '', self.fg_color, self.bg_color, 1 )
        
    def resaltar_instancias(self, root, elementos, instancia_cierre, fg_color, bg_color, marker):
        
        start_pos = 0
        start_pos_aux = 0
        self.count_list = []
        
        if self.word_styles_aux == {}:
            pass
        else:
            # print(self.word_styles_aux)
            for word_ind in self.word_styles_aux.items():
                print(word_ind)
                self.XML_TextCtrl.StartStyling(word_ind[0])
                self.XML_TextCtrl.SetStyling(len(word_ind[1][1]), word_ind[1][0])
                self.XML_TextCtrl.MarkerAdd(word_ind[1][2], 10)
        try:
            while True:
                
                start_pos = self.XML_TextCtrl.FindText(start_pos, self.XML_TextCtrl.GetLength(), elementos, stc.STC_FIND_WHOLEWORD)
                start_pos_aux = start_pos[0]
                if start_pos == -1:
                    break
                
                if instancia_cierre != '':
                    end_pos = self.XML_TextCtrl.FindText(start_pos_aux-1, self.XML_TextCtrl.GetLength(), instancia_cierre)#, stc.STC_FIND_WHOLEWORD)
                    # start_pos_aux = end_pos[1]
                    end_pos = end_pos[0]
                else:
                    end_pos = start_pos[1]
                # print("Fin", end_pos)
                if end_pos == -1:
                    break
                # Agregar marcadores en algunas líneas
                line = self.XML_TextCtrl.LineFromPosition(start_pos[0])
                self.XML_TextCtrl.MarkerAdd(line, marker)
                self.XML_TextCtrl.StartStyling(start_pos_aux)  # Comenzar el resaltado en la posición correcta
                self.XML_TextCtrl.SetStyling(end_pos - start_pos_aux + len(instancia_cierre), stc.STC_H_DOUBLESTRING)  # Establecer el estilo de resaltado
                
                self.XML_TextCtrl.StyleSetForeground(stc.STC_H_DOUBLESTRING, fg_color)
                self.XML_TextCtrl.StyleSetBackground(stc.STC_H_DOUBLESTRING, bg_color)
                
                start_pos = end_pos + len(instancia_cierre)
                time.sleep(.1)
                # print("No se atoro")
                self.count_list.append(start_pos_aux)
                self.verif_textCtrl.SetValue(str(len(self.count_list)) + f' {elementos}')
                self.Refresh()  # Actualizar la apariencia del botón
                
        except Exception as e:
            print("El error es el siguiente: \n", e)
            pass
            
    def reset_panel(self, event):
        # Limpia los marcadores 
        self.XML_TextCtrl.MarkerDeleteAll(10)
        # Limpia el panel de busqueda
        self.search_textCtrl.Clear()
        # Limpia el panel de validaciones
        self.verif_textCtrl.Clear()
        # Limpia la lista de elementos
        self.verif_cBox.Clear()
        # Escribe Validaciones en la lsita de elementos
        self.verif_cBox.SetValue("Validaciones")
        # Cambiar el color del botón de nuevo a su color original
        self.bto_verificar.SetBackgroundColour(wx.NullColour)  # Restaurar el color original
        self.bto_verificar.SetForegroundColour(wx.BLACK)
        self.bto_verificar.Enable()  # Habilitar el botón una vez que ha terminado el proceso
        self.word_styles_aux = {}
        self.Refresh()  # Actualizar la apariencia del botón
        
    def reset_panel_par(self, event):
        self.XML_TextCtrl.MarkerDeleteAll(10)
        self.search_textCtrl.Clear()
        self.word_styles_aux = {}
        self.Refresh()  # Actualizar la apariencia del botón
        
class Verificador(Thread):
    """Realiza las verificaciones seleccionadas.
    """
    def __init__(self, parent, mf):
        Thread.__init__(self)
        self.mf = parent
        self.mfp = mf
        self.lista_ok = []
        self.count_list = []

    def run(self):
        try:
            # print(self.mf.root)
            root = self.mf.root
        except:
            mensaje = (
                f"Seleccionar un archivo .xml"
            )
            dial = wx.MessageDialog( None, mensaje, "", wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            self.mfp.SetStatusText("No seleccionó un archivo, no se efecturaron las validaciones")
            self.mfp.worker = None
            return None
            
        self.mf.log.info(f"APLICANDO BUSQUEDA EN EL JOB '{self.mf.file_name}'")
        
        self.verificar_naflags(root)
        self.mfp.SetStatusText("Terminó la actividad")
        self.mfp.worker = None
            
    def verificar_naflags(self, root):
        
        # Deshabilitar el botón mientras se realiza el proceso
        self.mf.bto_verificar.Disable()  # Desactivar el botón mientras se ejecuta el proceso
        self.mf.Refresh()  # Actualizar la apariencia del botón
        
        # Analizar el XML
        instances_with_naflag = []
        elementos = []
        elementos_end = []
        val_list = set()
        instances_with_naflag_set = set()
        
        # Iterar sobre los elementos 'Parent'
        for parent in root.findall('.//Parent'):
            for instance in parent:
                for indice, elemento in enumerate(TIPOS_VALIDOS):
                    # print(elemento, instance, instance.attrib)
                    # Verificar si la instancia contiene 'ELEMENTOS'
                    if elemento in instance.tag or elemento in instance.attrib:
                        # Verificar si el elemento ya está en el conjunto
                        if (indice, elemento) not in val_list:
                            # Agregar el elemento al conjunto
                            val_list.add((indice, elemento))
                        path = parent.attrib.get('Path', '')
                        name = instance.attrib.get('Name', '')
                        scada_flag = instance.attrib.get('SCADAFlag', '')
                        na_flag = instance.attrib.get('NAFlag', '')
                        elem = instance.tag
                        if (path, name, scada_flag, na_flag, elem) not in instances_with_naflag_set:
                            instances_with_naflag.append({'Path': path, 
                                                        'Name': name, 
                                                        'SCADAFlag': scada_flag, 
                                                        'NAFlag': na_flag, 
                                                        'Element': elem,})
                            instances_with_naflag_set.add((path, name, scada_flag, na_flag, elem))  # Agregar elemento al conjunto

                        elementos.append(elem)
                        
                        elementos_end.append(f"</{elem}>")
        # Agregar elementos al ComboBox
        for index, value in val_list:
            self.mf.verif_cBox.Append(value)
        time.sleep(0.1)
        # Imprimir los resultados
        for instance in instances_with_naflag:
            # print(instance)
            if instance['NAFlag'] != '' and instance['SCADAFlag'] != '':
                self.mf.log.info(f"El '{instance['Element']}' en: {instance['Path']}/{instance['Name']} se encuentran las banderas NAFlag a: '{instance['NAFlag']}' y SCADAFlag a '{instance['SCADAFlag']}'")
            elif instance['SCADAFlag'] != '':
                self.mf.log.info(f"El '{instance['Element']}' en: {instance['Path']}/{instance['Name']} se encuentra la bandera SCADAFlag a: '{instance['SCADAFlag']}'")
            elif instance['NAFlag'] != '':
                self.mf.log.info(f"El '{instance['Element']}' en: {instance['Path']}/{instance['Name']} se encuentra la bandera NAFlag a: '{instance['NAFlag']}'")
            elif instance == '':
                self.mf.log.info(f"Validacion completa, sin banderas.")
                
        wx.CallAfter(self.process_finished)
        
    def process_finished(self):
        # Cambiar el color del botón a verde
        self.mf.bto_verificar.SetBackgroundColour(wx.Colour(40, 160, 30))
        self.mf.bto_verificar.SetForegroundColour(wx.WHITE)
        self.mf.Refresh()  # Actualizar la apariencia del botón
        
        