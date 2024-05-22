import wx
import os
import csv
import re
import openpyxl
import logging
import wx.lib.scrolledpanel
import wx.lib.agw.aui as aui
import wx.richtext as rt
import networkx as nx
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import wx.xrc as xrc
import wx.adv as adv
import traceback
from glob import glob
from os.path import join, basename, getmtime
from datetime import datetime, timedelta, date
from os import path
from threading import Thread
from typing import Any
from pandas import ExcelWriter
from openpyxl.drawing.image import Image
from collections import defaultdict
from src.arbol_mage import SP7Object, crear_arbol_mage, aniadir_terminales
from usolibpy.otros import leer_csv

ruta_base = path.abspath(path.join(__file__, "../.."))
ruta_resultados = path.join(ruta_base,"resultados")
ruta_data = path.join(ruta_base,"data")
log = logging.getLogger("verificador_imm_MAGE")
log.setLevel(logging.INFO)
# Formatea la fecha y hora
name_archivo = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

# Guardar el archivo con el nombre basado en la fecha
archivo_xlsx = f"ValidacionesTNA{name_archivo}.xlsx"
path_exp = path.join(ruta_resultados, archivo_xlsx)

def valor_defecto():
    return [[], set()]

def valor_defecto1():
    return []

def valor_defecto2():
    return [set(), set(), set()]

def valor_defecto3():
    return [[], set(), set(), set()]

def valor_defecto4():
    return [set(), set(), set(), set()]


patronId = re.compile(r'(UN|UN)(\d{1,2})')
patron = re.compile(r'(CP|RE)-(\d{1,2})')
cev_rgx = re.compile(r'(CEV|CE)(\d{1,2}|\b)')
gen_SIN_rgx = re.compile(r'\d{2}[A-Z]{3}-U\d{1,2}$')
gen_BCA_rgx = re.compile(r'\d{2}\s{3}[A-Z]{3}-U\d{2}$')
gen_BCS_rgx = re.compile(r'\d{2}([A-Z]{6}|[A-Z]{3})-U\d{2}$')
loadAux_rgx = re.compile(r'([a-z,A-Z]{3})(A{1})(\d{1,2})(\d{1}|[A]{1})(1)')
rgx_Operating= re.compile(r'[A-Z]+(_T|_D)')
rgx_TR_name = re.compile(r'\d{2}[A-Z]{3}\s{1}(TCEV|AT\d{2}|T\d{2})\s{1}[0-9.]+\\[0-9.]+')
rgx_TR_name2 = re.compile(r'\d{2}[A-Z]{3}\s{2}(TCEV|AT\d{2}|T\d{2})\s{1}[0-9.]+\\[0-9.]+')
str_match={'PTA','PQ1','PQ2'}

cs_rgx = re.compile(r'.*-CS.*')
CAname_rgx = re.compile(r'(\d{2}[A-Z]{3})+(T|AT)(\d{2})([A-Z]|\d)*|\d*$')
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
        
       
class MAGE_panel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, main_frame):
        # wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        super().__init__(parent)
        self.mf = main_frame
        
        # Agrgar imagen de CENACE
        icons_path = path.join(ruta_base, "iconos")
        cen_bm = path.join(icons_path,"CENACE-logo-completo.png")
        self.mf.logo_cen1.SetBitmap(wx.Bitmap( cen_bm, wx.BITMAP_TYPE_ANY ))
        
        self.log = log
        self.mage_log_textCtrl = self.mf.mage_log_textCtrl
        txt_handler = CustomConsoleLogHandler(self.mage_log_textCtrl)
        txt_handler.setFormatter(
            logging.Formatter('%(name)-12s %(levelname)9s: %(message)s'))
        txt_handler.setLevel(logging.INFO)
        self.log.addHandler(txt_handler)
        logging.getLogger("arbol_mage").addHandler(txt_handler)
        
        self.MAGEselected_path = ''
        self.mf.hoja_resultante = set()
        self.mf.archivos_requeridos = {}
        
        self.nombres_checkbox = [
            'Verificar interruptores y cuchillas',
            'Verificar límites de GeneratingUnit',
            'Verificar cargas Auxiliares',
            'Verificar link de LoadGroup con una carga modelada',
            'Verificar Conforming Load con Zero MW/MVAR percentages',
            'Verificar Cargas con al menos un alimentador',
            'Verificar Name de los TR del SIN',
            'Verificar los parametros x_pu y r_pu de los devanados',
            'Verificar umbral de los TAPs',
            'Verificar ligas a curvas de capabilidad',
            'Verificar que las SynchronousMachines tengan liga a una Generating Unit',
            'Verificar existencia de turbinas de vapor',
            'Verificar mRID repetidos',
            'Verificar info (y1<y2) en curvas de capabilidad',
            'Verificar niveles de tensión asociados a los transformadores',
            'Verificar niveles de tensión asociados a lineas de transmisión',
            'Verificar niveles de tensión asociados a VoltageLevel',
            'Verificar islas electricas sin tomar en cuenta la NAFlag',
            'Verificar islas electricas tomando en cuenta la NAFlag',
            'Verificar link de equipos reguladores',
            'Verificar existencia de curvas de calor incremental',
            'Verificar existencia de curvas hidro',
            'Verificar ID duplicados de Conformload, NConformload',
            'Verificar que los Busbarsection tengan definida una MarketLoadZone',
            'Verificar el NodoPkey y el ID de los SynchronousMachine',
            'Verificar el NodoPkey de los StaticVarCompensator',
            'Verificar el ShortId de los ShuntCompensator',
            'Verificar los PI TAGs de los SynchronousMachine',
            'Verificar BusbasSections por subestación y nivel de voltage',
            'Verificar BusNumber del BusNameMarker',
            ]
        
        self.Val_checkBoxList = self.mf.Val_checkBoxList
        self.Val_checkBoxList.Set(self.nombres_checkbox)

        # Obtener la MAGE path data
        self.MAGE_pathSel = self.mf.MAGE_pathSel
        self.MAGE_pathSel.Bind(wx.EVT_DIRPICKER_CHANGED, self.MAGEpath_select)
        
        self.bto_preprocesar_archivos = self.mf.bto_preprocesar_archivos
        self.bto_preprocesar_archivos.Bind(
            wx.EVT_BUTTON, lambda event: self.inicializar_thread(event, ProcesadorArchivos, self.mf, "Preprocesando archivos *.csv")
        )
        
        # Vincular la accion de los checkbox
        self.Val_checkBoxList = self.mf.Val_checkBoxList
        self.Val_checkBoxList.Bind(wx.EVT_CHECKLISTBOX, self.clic_checkbox_validaciones)
        self.Maestro_checkBox = self.mf.Maestro_checkBox
        self.Maestro_checkBox.Bind(wx.EVT_CHECKBOX, self.OnMasterCheckBox)
        
        self.bto_verificar = self.mf.bto_verificar_mage
        self.bto_verificar.Bind(
            wx.EVT_BUTTON, lambda event: self.inicializar_thread(event, Verificador, self.mf, "Realizando validaciones")
        )

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
    
    
    # Define una función que será el objetivo del hilo
    # def run_preprocesador_archivos(self):
    #     PreprocesadorArchivos(self.mf).run()  # Suponiendo que tengas un método run() en la clase PreprocesadorArchivos

    def MAGEpath_select(self, event):
        self.MAGEselected_path = self.mf.MAGE_pathSel.GetPath()
        # self.preprocesador_archivos.set_directory(self.MAGEselected_path)
        self.log.info(f"Se cargó la carpeta {self.MAGEselected_path}")
        # print(self.MAGEselected_path)
        
    def OnMasterCheckBox(self, event):
        # Obtener el estado del checkbox maestro
        master_checked = self.mf.Maestro_checkBox.GetValue()
        
        # Establecer el estado de todos los checkboxes en el checklistbox
        for i in range(self.mf.Val_checkBoxList.GetCount()):
            self.mf.Val_checkBoxList.Check(i, master_checked)
        
        # Actualizar las listas y el TextCtrl
        self.UpdateListsAndTextCtrl()
        
    def clic_checkbox_validaciones(self, event):
        # Actualizar las listas y el TextCtrl
        self.UpdateListsAndTextCtrl()

    def UpdateListsAndTextCtrl(self):
        """Despliega la lista de archivos necesarios par efectuar las validaciones
        seleccionadas"""
        self.mf.ValDesc_textCtrl.Clear()
        
        # Limpiar las listas
        self.mf.hoja_resultante.clear()
        self.mf.archivos_requeridos.clear()
        
        # Obtener el estado de los checkboxes en el checklistbox
        for i in range(self.mf.Val_checkBoxList.GetCount()):
            if self.mf.Val_checkBoxList.IsChecked(i):
                if i == 0:
                    self.mf.hoja_resultante.add("Switch_devices")
                    self.mf.archivos_requeridos[i] = {
                        "discrete.csv",
                        "equipos.csv"
                    }
                elif i == 1:
                    self.mf.hoja_resultante.add("Lim_Gen_Unit")
                    self.mf.archivos_requeridos[i] = {
                        "GeneratingUnit_MAX_MIN.csv",
                        "equipos.csv"
                    }
                elif i == 2:
                    self.mf.hoja_resultante.add("Aux_Load")
                    self.mf.archivos_requeridos[i] = {
                        "ConformLoad_Auxiliary.csv"
                    }
                elif i == 3:
                    self.mf.hoja_resultante.add("Load_Group")
                    self.mf.archivos_requeridos[i] = {
                        "conformload_voltage.csv",
                        "ConformLoad_Auxiliary.csv",
                        "LoadGroup_Conform.csv",
                        "LoadGroup_NonConform.csv", "Feeder.csv"
                    }
                elif i == 4:
                    self.mf.hoja_resultante.add("ConformLoad_Percentage")
                    self.mf.archivos_requeridos[i] = {
                        "conformload_voltage.csv",
                        "ConformLoad_Auxiliary.csv",
                        "LoadGroup_Conform.csv",
                        "LoadGroup_NonConform.csv", "Feeder.csv"
                    }
                elif i == 5:
                    self.mf.hoja_resultante.add("ConformLoad_Alimentadores")
                    self.mf.archivos_requeridos[i] = {
                        "conformload_voltage.csv",
                        "ConformLoad_Auxiliary.csv",
                        "LoadGroup_Conform.csv",
                        "LoadGroup_NonConform.csv", "Feeder.csv"
                    }
                elif i == 6:
                    self.mf.hoja_resultante.add("TR_Name")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "PowerTransformer_ID.csv" 
                    }
                elif i == 7:
                    self.mf.hoja_resultante.add("TR_Parameters")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "TransformerWinding.csv"
                        # "Network.csv"
                    }
                elif i == 8:
                    self.mf.hoja_resultante.add("Umbral_TAP")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "tap_changer_step_voltage_reg_terminal.csv",
                        "TransformerWinding.csv"
                        # "Network.csv"
                    }
                elif i == 9:
                    self.mf.hoja_resultante.add("Cuvas_Capavilidad_Link")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "ReactiveCapabilityCurve.csv",
                        "SynchronousMachine.csv"
                    }
                elif i == 10:
                    self.mf.hoja_resultante.add("Turbina_Vapor")
                    self.mf.archivos_requeridos[i] =  {
                        "equipos.csv",
                        "liga_a_generating.csv",
                        "subtipo_unidades_termicas.csv"
                    }
                elif i == 11:
                    self.mf.hoja_resultante.add("Gen_Unit_Link")
                    self.mf.archivos_requeridos[i] =  {
                        "equipos.csv",
                        "liga_a_generating.csv",
                    }
                elif i == 12:
                    self.mf.hoja_resultante.add("mRID")
                    self.mf.archivos_requeridos[i] = {
                        "mRID.csv"
                    }
                elif i == 13:
                    self.mf.hoja_resultante.add("Curva_Capabilidad")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "datos_curvas_capabilidad.csv"
                    }
                elif i == 14:
                    self.mf.hoja_resultante.add("Nivel_Tension_TR")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "Terminal.csv",
                        "winding_voltage.csv"
                    }
                elif i == 15:
                    self.mf.hoja_resultante.add("Nivel_Tension_LT")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "Terminal.csv",
                        "aclinesegments_voltage.csv"
                    }
                elif i == 16:
                    self.mf.hoja_resultante.add("Nivel_Tension")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "Terminal.csv",
                        "voltages.csv"
                    }
                elif i == 17:
                    self.mf.hoja_resultante.add("Islas_sin_NA")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "Terminal.csv",
                    }
                elif i == 18:
                    self.mf.hoja_resultante.add("Islas_con_NA")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "Terminal.csv",
                    }
                elif i == 19:
                    self.mf.hoja_resultante.add("Eqp_Regulados_Link")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "Terminal.csv",
                        "staticvar_reg_terminal.csv",
                        "shunt_reg_terminal.csv",
                        "synchmachine_reg_terminal.csv",
                        "tap_changer_reg_terminal.csv",
                        "tipos_transformadores.csv"
                    }
                elif i == 20:
                    self.mf.hoja_resultante.add("Carvas_Calor")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "bandera_agc.csv"
                    }
                elif i == 21:
                    self.mf.hoja_resultante.add("Curva_Hidro")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "bandera_agc.csv"
                    }
                elif i == 22:
                    self.mf.hoja_resultante.add("NoC_ConforLoad_ID")
                    self.mf.archivos_requeridos[i] = {
                        "conformload_voltage.csv",
                        "ConformLoad_Auxiliary.csv",
                        "LoadGroup_Conform.csv",
                        "LoadGroup_NonConform.csv", "Feeder.csv"
                    }
                elif i == 23:
                    self.mf.hoja_resultante.add("MarketLoadZone")
                    self.mf.archivos_requeridos[i] = {
                        "Busbar_MarketLoadZone.csv",
                        "Busbar_ZC_ZT_ZD.csv"
                    }
                elif i == 24:
                    self.mf.hoja_resultante.add("SynchronousMachine_NP")
                    self.mf.archivos_requeridos[i] = {
                        "SynchronousMachine_nodePKey.csv" 
                    }
                elif i == 25:
                    self.mf.hoja_resultante.add("StaticVarCompensator_NP")
                    self.mf.archivos_requeridos[i] = {
                        "StaticVarCompensator_id.csv"
                    }
                elif i == 26:
                    self.mf.hoja_resultante.add("ShuntCompensator_ID")
                    self.mf.archivos_requeridos[i] = {
                        "ShuntCompensator_id.csv"
                    }
                elif i == 27:
                    self.mf.hoja_resultante.add("SynchronousMachine_PI_TAGs")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "SynchronousMachine.csv",
                        "synchmachine_reg_terminal.csv",
                        "AnalogValue_AnalogSE_Terminal.csv",
                    }
                elif i == 28:
                    self.mf.hoja_resultante.add("Busbar_VoltageLevel")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv"
                    }
                elif i == 29:
                    self.mf.hoja_resultante.add("BusNameMarker_BusNumber")
                    self.mf.archivos_requeridos[i] = {
                        "equipos.csv",
                        "BusNameMarker.csv"
                    }
                    
        self.mf.ValDesc_textCtrl.AppendText("")
        self.mf.ValDesc_textCtrl.AppendText(
            "Listado de archivos para realizar las validaciones, para mayor "
            "información consulta la sección que queries en el menú de ayuda:\n\n"
        )
        result = list(self.mf.archivos_requeridos[i] for i in self.mf.archivos_requeridos)
        self.lista_requerida = list(set([item for conjunto in result for item in conjunto]))

        for archivo in self.lista_requerida:
            self.mf.ValDesc_textCtrl.WriteText(f" *{archivo}\n")

        # self.mf.ValDesc_textCtrl.SetValue("")
        self.mf.ValDesc_textCtrl.WriteText(
            "\nNombre de la hoja resultante:\n\n"
        )
        for tabla in self.mf.hoja_resultante:
            self.mf.ValDesc_textCtrl.WriteText(f" *{tabla}\n")                 

        # Verificar si hay algún checkbox seleccionado
        any_checked = any(self.mf.Val_checkBoxList.IsChecked(i) for i in range(self.mf.Val_checkBoxList.GetCount()))
        
        # Limpiar el TextCtrl si no hay ningún checkbox seleccionado
        if not any_checked:
            # print(any_checked)
            self.mf.ValDesc_textCtrl.Clear()
            self.mf.hoja_resultante = set()

def get_encabezados(file):
	"""Analiza los archivos obtenidos de MAGE y obtienen los encabezados para
	convertir el archivo en un csv convecional.

	Parameters
	----------
	file: str
		Ruta del archivo a analizar.

	Returns
	-------
	encabezados: lista
		Lista con los encabezados el archivo csv.
	cuerpo: lista
		Lista con el resto de renglones del archivo.
	"""
	encabezados = []
	cuerpo = []
	flg = 0
	str_aux = ""
	with open(file) as fp:
		for i, row in enumerate(fp):
			str_aux += row.replace("\n", "")
			if ":\n" not in row:
				if i == 0:
					return None, None
				break
			if i == 0:
				element_type = str_aux.replace(":", "").replace("\"", "")
		for row in fp:
			cuerpo.append(row)
	for campo in str_aux.split(","):
		campo_desglosado = campo.replace("\"", "").split(":")
		if campo_desglosado[0] == element_type:
			encabezados.append("_".join(campo_desglosado[1:]))
		else:
			encabezados.append("_".join(campo_desglosado))
	return encabezados, cuerpo


def replace_csv_format(file, encabezados, cuerpo):
	"""Toma la lista de encabezados y el cuerpo del archivo csv para crear un
	nuevo archivo con el formato csv que usamos comunmente.

	Parameters
	----------
	file: str
		Ruta del archivo que se va a escribir.
	encabezados: lista
		Lista con los encabezados el archivo csv.
	cuerpo: lista
		Lista con el resto de renglones del archivo.
	"""
	with open(file, "w", newline="") as fp:
		fp.write(",".join(encabezados)+"\n")
		for row in cuerpo:
			fp.write(row)
		fp.close()
  
class ProcesadorArchivos(Thread):
    """Convierte los archivos *.csv que se exportan desde IMM-MAGE a un formato
    csv más tradicional.

    Los archivos csv que se transforman son todos aquellos en la ruta
    establecida en la variable carpeta_insumos.
    """
    def __init__(self, parent, mf):
        Thread.__init__(self)
        self.mf = parent
        self.mfp = mf

    def run(self):
        if path.isdir(self.mf.MAGEselected_path) == False:
            mensaje = (
                f"La carpeta elegida no es una carpeta válida:{self.mf.MAGEselected_path}"
            )
            dial = wx.MessageDialog( None, mensaje, "", wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            self.mfp.SetStatusText("Carpeta inválida, no se procesaron los archivos")
            self.mfp.worker = None
            return None
        for file in glob(path.join(self.mf.MAGEselected_path, "*.csv")):
            encabezado, cuerpo = get_encabezados(file)
            if encabezado is not None:
                replace_csv_format(file, encabezado, cuerpo)
                self.mf.log.info(f"Se procesó el archivo {file}")
        self.mfp.SetStatusText("Terminó la actividad")
        self.mfp.worker = None           

class Verificador(Thread):
    """Realiza las verificaciones seleccionadas.
    """
    def __init__(self, parent, mf):
        Thread.__init__(self)
        self.mf = parent
        self.mfp = mf
        self.coleccion_df = {clave: None for clave in self.mfp.hoja_resultante}
        self.lista_ok = []
        
    def run(self):
        
        # try:
        if path.isdir(self.mf.MAGEselected_path) == False:
            mensaje = (
                f"La carpeta elegida no es una carpeta válida:{self.mf.MAGEselected_path}"
            )
            dial = wx.MessageDialog( None, mensaje, "", wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            self.mfp.SetStatusText("Carpeta inválida, no se efecturaron las validaciones")
            self.mfp.worker = None
            return None
        archivos_csv = [path.basename(x) for x in glob(path.join(self.mf.MAGEselected_path, "*.csv"))]
        archivos_faltantes = []
        for file in self.mf.lista_requerida: 
            if file not in archivos_csv:
                archivos_faltantes.append(file)
        if len(archivos_faltantes) != 0:
            enter = '\n'
            mensaje = (
                f"Los siguientes archivos requeridos por las válidaciones no se "
                f"encontraron en la carpeta de insumos:{enter} "
                f"{enter.join(archivos_faltantes)}"
            )
            dial = wx.MessageDialog( None, mensaje, "", wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            self.mfp.SetStatusText("Información faltante, no se efecturaron las validaciones")
            self.mfp.worker = None
            return None
        
        self.mf.mage_log_textCtrl.SetValue("")
        
        # Obtener el estado de los checkboxes en el checklistbox
        for i in range(self.mf.Val_checkBoxList.GetCount()):
            if self.mf.Val_checkBoxList.IsChecked(i):
                try:
                    if i == 0:
                        self.mf.log.info("APLICANDO VALIDACION A LOS INTERRUPTORES Y CUCHILLAS")
                        self.verificar_switching_status()
                    elif i == 1:
                        self.mf.log.info("APLICANDO VALIDACION AL ID DE LAS CARGAS")
                        self.verificar_cargas_Aux()
                    elif i == 2:
                        self.mf.log.info("APLICANDO VALIDACION DE LOADGROUPS")
                        self.verificar_link_LoadGroup()
                    elif i == 3:
                        self.mf.log.info("APLICANDO VALIDACION AL PORCENAJE DE LAS CARGAS")
                        self.verificar_Conformload_ZeroMW_percentages()
                    elif i == 4:
                        self.mf.log.info("APLICANDO VALIDACION A ALIMENTADORES")
                        self.verificar_Conformload_feeder()
                    elif i == 5:
                        self.mf.log.info("APLICANDO VALIDACION DE UMBRAL DE LOS TAPS")
                        self.verificar_umbral_TAP()
                    elif i == 6:
                        self.mf.log.info("APLICANDO VALIDACION A PARAMETROS DE LOS TR")
                        self.verificar_winding_xpu()
                    elif i == 7:
                        self.mf.log.info("APLICANDO VALIDACION DEL FORMATO DEL NAME DE LOS TR")
                        self.new_TR_names()
                    elif i == 8:
                        self.mf.log.info("APLICANDO VALIDACION DE LIGAS A CURVAS DE CAPABILIDAD")
                        self.verificar_curvas_ligas_curvas_capabilidad()
                    elif i == 9:
                        self.mf.log.info("APLICANDO VALIDACION A LAS TURBINAS DE VAPOR")
                        self.verificar_existencia_turbinas_vapor()
                    elif i == 10:
                        self.mf.log.info("APLICANDO VALIDACION A LIGAS ENTRE SYNCHRONOUSMACHINES Y GENERATING UNITS")
                        self.verificar_ligas_a_generating_unit()
                    elif i == 11:
                        self.mf.log.info("APLICANDO VALIDACION pssebusBoundary_SeriesCompensator")
                        self.verificar_pssebusBoundary_SeriesCompensator()
                    elif i == 12:
                        self.mf.log.info("APLICANDO VALIDACION A MRID")
                        self.verificar_mrids()
                    elif i == 13:
                        self.mf.log.info("APLICANDO VALIDACIONES A LA INFORMACIÓN DE LAS CURVAS DE CAPABILIDAD")
                        self.verificar_info_curvas_capabilidad()
                    elif i == 14:
                        self.mf.log.info("APLICANDO VALIDACIONES A LOS NIVELES DE TENSION DE LOS TRANSFORMADORES")
                        self.verificar_niveles_tension_transformadores()
                    elif i == 15:
                        self.mf.log.info("APLICANDO VALIDACIONES A LOS NIVELES DE TENSION DE LAS LINEAS")
                        self.verificar_niveles_tension_lineas()
                    elif i == 16:
                        self.mf.log.info("APLICANDO VALIDACIONES A LOS NIVELES DE TENSION ASOCIADOS A VOLTAGELEVEL")
                        self.verificar_niveles_tension_voltage_level()
                    elif i == 17:
                        self.mf.log.info("APLICANDO VALIDACION DE ISLAS ELECTRICAS SIN NAFLAG")
                        self.verificar_islas_electricas(True)#False
                    elif i == 18:
                        self.mf.log.info("APLICANDO VALIDACION DE ISLAS ELECTRICAS CON NAFLAG")
                        self.verificar_islas_electricas(False)#True
                    elif i == 19:
                        self.mf.log.info("APLICANDO VALIDACION A LINK DE EQUIPOS REGULADOS")
                        self.verificar_link_equipos_reguladores()
                    elif i == 20:
                        self.mf.log.info("APLICANDO VALIDACION CURVAS DE CALOR INCREMENTAL")
                        self.verificar_existencia_curvas_calor_incremental()
                    elif i == 21:
                        self.mf.log.info("APLICANDO VALIDACION CURVAS HIDRO")
                        self.verificar_existencia_curvas_hidro()
                    elif i == 22:
                        self.mf.log.info("APLICANDO VALIDACION AL ID DE LAS CARGAS")
                        self.verificar_Conformload_NConformload_ID()
                    elif i == 23:
                        self.mf.log.info("APLICANDO VALIDACION A LINK DE MARKETLOADZONE")
                        self.verificar_Busbarsection_MarketLoadZone()
                    elif i == 24:
                        self.mf.log.info("APLICANDO VALIDACION A NODOP DE GEN")
                        self.verificar_SynchronousMachine_NodePKey_ID()
                    elif i == 25:
                        self.mf.log.info("APLICANDO VALIDACION A ID DE MÁQUINAS SÍNCRONAS")
                        self.verificar_StaticVarCompensator_NodePkey()
                    elif i == 26:
                        self.mf.log.info("APLICANDO VALIDACION A ID DE REACTORES Y CAPACITORES")
                        self.verificar_ShuntCompensator_ID()
                    elif i == 27:
                        self.mf.log.info("APLICANDO VALIDACION AL PI TAGS DE MÁQUINAS SÍNCRONAS")
                        self.verificar_SynchronousMachine_PI_TAGs()
                    elif i == 28:
                        self.mf.log.info("APLICANDO VALIDACION A BUSBARSECTIONS")
                        self.verificar_busbarsection_by_voltagelevel()
                    elif i == 29:
                        self.mf.log.info("APLICANDO VALIDACION A BUS NUMBER DEL BUSNAMEMARKER")
                        self.verificar_BusNumber_BusName_Marker()
                        # elif i == 29:
                        # self.mf.log.info("APLICANDO VALIDACION pssebusBoundary_SeriesCompensator")
                        # self.verificar_pssebusBoundary_SeriesCompensator()
                        # pass
                        
                    wx.CallAfter(self.process_finished)
                    self.mfp.SetStatusText("Terminó la actividad")
                    self.mfp.worker = None
                    
                except KeyError as ke:
                    # print(ke)
                    # i = self.mf.Val_checkBoxList.GetSelection()
                    label = self.mf.Val_checkBoxList.GetString(i)
                    traceback.print_exc()
                    # wx.CallAfter(self.process_error(ke))
                    self.process_error(ke,label)
                    pass
                    # pass
                except AssertionError as ae:
                    label = self.mf.Val_checkBoxList.GetString(i)
                    # print(ke)
                    traceback.print_exc()
                    # wx.CallAfter(self.process_error(ke))
                    self.process_error(ae,label)
                    pass
                    # pass
                except Exception as e:
                    label = self.mf.Val_checkBoxList.GetString(i)
                    # print(e)
                    traceback.print_exc()
                    self.process_error(e,label)
                    continue
                    # pass
        
        
    def process_finished(self):
        # Cambiar el color del botón a verde
        self.mf.bto_verificar.SetBackgroundColour(wx.Colour(40, 160, 30))
        self.mf.bto_verificar.SetForegroundColour(wx.WHITE)
        self.mf.Refresh()  # Actualizar la apariencia del botón
        
    def process_error(self, e, label):
        # Cambiar el color del botón a rojo
        self.mf.bto_verificar.SetBackgroundColour(wx.RED)
        self.mf.bto_verificar.SetForegroundColour(wx.BLACK)
        self.mf.Refresh()  # Actualizar la apariencia del botón
        self.mf.log.error(f"-------OCURRIO UN ERROR '{e}' en '{label}'-----------")
        self.mfp.SetStatusText(f"OCURRIO UN ERROR '{e}'")
        self.mfp.worker = None
            

    def verificar_switching_status(self):
        """Verifica los TAPs dentro de +-1, para posteriormente ver cuales contienen 
        impedancias menores a 0.007 pu
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_mediciones = path.join(self.mf.MAGEselected_path, "discrete.csv")
        archivo_switches = path.join(self.mf.MAGEselected_path, "switch_devices.csv")
        # archivo_network = path.join(self.mf.MAGEselected_path, "Network.csv")
        network = crear_arbol_mage(archivo_equipos)
        dicc_base_mediciones, _, _ = leer_csv(archivo_mediciones, ["ID"])
        dicc_base_switches, _, _ = leer_csv(archivo_switches, ["ID"])

        lista_switch = []
        lista_mediciones = []
        for breaker in network.dicc_arbol.values():
            # print(breaker)

            if (breaker.tipo != "Disconnector") and (breaker.tipo != "Breaker"):
                continue
            if breaker.na_flag != True:
                continue
                
            # if breaker.scada_flag != True:
            #     continue
            lista_switch.append([breaker.id, breaker.na_flag, breaker.scada_flag])

        df_switch = pd.DataFrame(lista_switch, columns=["ID", "NAFlag", "SCADAFlag"])
        # print(df_switch)

        for elemento, valor in dicc_base_mediciones.items():
            if valor["Parent"] not in df_switch["ID"].tolist():
                continue
            else:
                nombre = valor.get("Name","")
                if not (nombre.startswith("IN") or nombre.startswith("CU")):
                    continue
                else:
                    if valor["MeasurementType"] == "Switch status":
                        continue
                    else:
                        # print(valor["ID"])
                        flags = df_switch[df_switch["ID"] == valor["Parent"]]

                        if nombre.startswith("IN"):
                            self.mf.log.warning (f"Interruptor {valor['Path']} con {valor['MeasurementType']} cambiar a: 'Switch status'")
                            lista_mediciones.append([valor["MeasurementType"], valor["Path"], valor["Name"], flags.iloc[0]["NAFlag"], flags.iloc[0]["SCADAFlag"]])
                            continue
                        if nombre.startswith("CU"):
                            self.mf.log.warning (f"Cuchilla {valor['Path']} con {valor['MeasurementType']} cambiar a: 'Switch status'")
                            lista_mediciones.append([valor["MeasurementType"], valor["Path"], valor["Name"], flags.iloc[0]["NAFlag"], flags.iloc[0]["SCADAFlag"]])
                            continue
        df_mediciones = pd.DataFrame(lista_mediciones, columns=["MeasurementType", "Path", "Name", "NAFlag", "SCADAFlag"])
        nombre_hoja = "Switch_devices"
        self.coleccion_df[nombre_hoja] = df_mediciones

        network.reset_arbol()

    def verificar_umbral_TAP(self):
        """Verifica los TAPs dentro de +-1, para posteriormente ver cuales contienen 
        impedancias menores a 0.007 pu
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_tap_voltage_reg = path.join(self.mf.MAGEselected_path, "tap_changer_step_voltage_reg_terminal.csv")
        archivo_transformer_winding = path.join(self.mf.MAGEselected_path, "TransformerWinding.csv")
        # archivo_network = path.join(self.mf.MAGEselected_path, "Network.csv")
        network = crear_arbol_mage(archivo_equipos)
        dicc_base_taps, _, _ = leer_csv(archivo_tap_voltage_reg, ["ID"])
        dicc_base_trs, _, _ = leer_csv(archivo_transformer_winding, ["ID"])

        lista_umbral = []
        lista_devanados = []
        lista_taps = []
        #Extra los TAPS que entran en el umbral
        umbral = 1.0
        for taps in dicc_base_taps.values():
            taps_arbol = network.dicc_arbol[taps["ID"]]

            if taps_arbol.na_flag == False:
                continue

            tap = float(taps["stepVoltageIncrement"])

            if tap == 0:
                continue

            if tap == "" :
                continue
            if (tap >= -umbral) & (tap <= umbral):
                lista_umbral.append(taps_arbol.padre)
                lista_taps.append(taps["stepVoltageIncrement"])
        # print(lista_umbral)
        self.mf.log.info  (f"Los devanados en los que el TAP entra dentro del umbral de +- {umbral} son:")
        for devanados in network.dicc_arbol.values():
            if devanados.id in lista_umbral:
                self.mf.log.error  (f"{devanados.get_ta([])}")
                lista_devanados.append([devanados.get_ta([]), devanados.nombre])
        for i, sublista in enumerate(lista_devanados):
            sublista.append(lista_taps[i])
        df_taps = pd.DataFrame(lista_devanados, columns=["Path", "Name", "stepVoltageIncrement"])
        nombre_hoja = "Umbral_TAP"
        self.coleccion_df[nombre_hoja] = df_taps

        network.reset_arbol()

    def verificar_winding_xpu(self):
        """Verifica los parametros x_pu y r_pu solo existan en el devanado de AT o en su defecto que la suma de los parametros de AT 
        y BT sean equivalentes al valor total
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_transformer_winding = path.join(self.mf.MAGEselected_path, "TransformerWinding.csv")
        network = crear_arbol_mage(archivo_equipos)
        dicc_base_trs, _, _ = leer_csv(archivo_transformer_winding, ["ID"])

        lista_devanados_baja = []
        lista_devanados_alta_set_x = []
        lista_devanados_alta_set_r = []
        lista_devanados_alta_set_mix = []

        lista_devanados_at = []
        lista_devanados_bt = []
        #Extrae los devanados 
        for devanados in dicc_base_trs.values():
            # devanados.xpu = devanados["x_pu"]
            devanados_arbol = network.dicc_arbol[devanados["ID"]]

            if devanados_arbol.na_flag == False:
                continue
            if devanados["x_pu"] == "":
                continue
            if float(devanados["x_pu"]) == 0:
                continue

            if devanados["Name"] == "Baja":
                lista_devanados_baja.append(devanados_arbol.id)

            if devanados["Name"] == "Alta":
                if float(devanados["x_pu"]) < 0.0007:
                    if devanados["r_pu"] != "":
                        if float(devanados["r_pu"]) != 0:
                            if float(devanados["r_pu"]) < 0.0007:
                                lista_devanados_alta_set_mix.append(devanados_arbol.id)
                            lista_devanados_alta_set_x.append(devanados_arbol.id)
                    else:
                        lista_devanados_alta_set_x.append(devanados_arbol.id)
                elif devanados["r_pu"] == "":
                    continue
                elif float(devanados["r_pu"]) == 0:
                    continue
                elif float(devanados["r_pu"]) < 0.0007:
                    lista_devanados_alta_set_r.append(devanados_arbol.id)

        self.mf.log.info  (f"Los devanados que superan el límite minimo de 'x_pu' y 'r_pu' < 0.0007 son: ")
        for devanados in network.dicc_arbol.values():
            if devanados.id in lista_devanados_alta_set_mix:
                self.mf.log.error  (f"En x_pu y r_pu: {devanados.get_ta([])}")
                lista_devanados_at.append([devanados.get_ta([]), "PARAMETROS < 0.0007"])
            if devanados.id in lista_devanados_alta_set_x:
                self.mf.log.error  (f"En x_pu: {devanados.get_ta([])}")
                lista_devanados_at.append([devanados.get_ta([]), "PARAMETROS < 0.0007"])
            if devanados.id in lista_devanados_alta_set_r:
                self.mf.log.error  (f"En r_pu: {devanados.get_ta([])}")
                lista_devanados_at.append([devanados.get_ta([]), "PARAMETROS < 0.0007"])
        devanados_at = pd.DataFrame(lista_devanados_at, columns=["Path", "State"])
        devanados_at = devanados_at.drop_duplicates()
        # print(devanados_at)


        self.mf.log.info  (f"Los devanados que contienen parametros en baja tensión: ")
        for devanados in network.dicc_arbol.values():
            if devanados.id in lista_devanados_baja:
                self.mf.log.error  (f"{devanados.get_ta([])}")
                lista_devanados_bt.append([devanados.get_ta([]),"PARAMETROS EN BT"])
        devanados_bt = pd.DataFrame(lista_devanados_bt, columns=["Path", "State"])
        # print(devanados_bt)

        df_devanados = pd.concat([devanados_at,devanados_bt])

        nombre_hoja = "TR_Parameters"
        self.coleccion_df[nombre_hoja] = df_devanados
        network.reset_arbol()


    def verificar_curvas_ligas_curvas_capabilidad(self):
        """Verifica las ligas entre las SynchronousMachines y las curvas de
        capabilidad.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_sync_mach = path.join(self.mf.MAGEselected_path, "SynchronousMachine.csv")
        archivo_curvas_cap = path.join(self.mf.MAGEselected_path, "ReactiveCapabilityCurve.csv")
        network = crear_arbol_mage(archivo_equipos)
        dicc_curvas_capabilidad, _, _ = leer_csv(archivo_curvas_cap, ["ID"])

        lista_maquinas = []
        for clave in dicc_curvas_capabilidad.values():
            curva_capabilidad = network.dicc_arbol[clave["ID"]]
            curva_capabilidad.liga_a_synchronous_machine = clave["SynchronousMachineHasDefaultReactiveCapabilityCurve_SynchronousMachine_ID"]
        dicc_synchronous_machine, _, _ = leer_csv(archivo_sync_mach, ["ID"])
        for clave in dicc_synchronous_machine.values():
            synchronous = network.dicc_arbol[clave["ID"]]
            synchronous.liga_a_curva_capabilidad =  clave["ReactiveCapabilityCurveMemberOfSynchronousMachine_ReactiveCapabilityCurve_ID"]
        for synchronous_machine in network.dicc_arbol.values():
            if (synchronous_machine.tipo != "SynchronousMachine" or
                    synchronous_machine.na_flag != True):
                continue
            try:
                curva_capabilidad = network.dicc_arbol[synchronous_machine.liga_a_curva_capabilidad]
            except KeyError:
                self.mf.log.error(f"Las ligas de la unidad {synchronous_machine.get_ta([])} a su curva de capabilidad esta dañada {synchronous_machine.liga_a_curva_capabilidad}")
                lista_maquinas.append([synchronous_machine.get_ta([]), synchronous_machine.liga_a_curva_capabilidad, "LIGA DE LA UNIDAD"])
                continue
            try:
                aux_synchronous_machine = network.dicc_arbol[curva_capabilidad.liga_a_synchronous_machine]
            except KeyError:
                self.mf.log.error(f"Las ligas de la curva de capabilidad {curva_capabilidad.get_ta([])} a su generador esta dañada {curva_capabilidad.liga_a_curva_capabilidad}")
                lista_maquinas.append([curva_capabilidad.get_ta([]), curva_capabilidad.liga_a_curva_capabilidad, "LIGA DE LA CURVA DE CAPABILIDAD"])
                continue
            if synchronous_machine.id != aux_synchronous_machine.id:
                self.mf.log.error(f"Las ligas de la maquina {synchronous_machine.get_ta([])} y su curva de capabilidad no se referencian mutuamente")
                lista_maquinas.append([synchronous_machine.get_ta([]), "", "LAS LIGAS NO COINCIDEN"])
        df_maquinas = pd.DataFrame(lista_maquinas, columns=["Path", "ID", "Link"])

        nombre_hoja = "Cuvas_Capavilidad_Link"
        self.coleccion_df[nombre_hoja] = df_maquinas
        network.reset_arbol()

    def verificar_existencia_turbinas_vapor(self):
        """Verifica que las unidades termicas del subtipo steam turbine tengan
        asociada una steam turbine en su SynchronousMachine asociada.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_subtipos = path.join(self.mf.MAGEselected_path, "subtipo_unidades_termicas.csv")
        archivo_ligas = path.join(self.mf.MAGEselected_path, "liga_a_generating.csv")
        network = crear_arbol_mage(archivo_equipos)
        #Añadimos las ligas entre SynchronousMachine y GEnerating Units
        dicc_synchronous, _, _ = leer_csv(archivo_ligas, ["ID"])
        for clave in dicc_synchronous.values():
            synchronous = network.dicc_arbol[clave["ID"]]
            synchronous.liga_a_generating = clave["SynchronousMachineMemberOfGeneratingUnit_GeneratingUnit_ID"]
        #Añadimos los subtipos a las unidades generadoras termicas
        dicc_unidades_termicas, _, _ = leer_csv(archivo_subtipos, ["ID"])
        for clave in dicc_unidades_termicas.values():
            unidad_termica = network.dicc_arbol[clave["ID"]]
            unidad_termica.subtipo = clave["PhysicalUnitType"]

        lista_turbinas = []
        for gen in network.dicc_arbol.values():
            if gen.tipo != "SynchronousMachine":
                continue
            if gen.na_flag != True:
                continue
            try:
                generating_unit = network.dicc_arbol[gen.liga_a_generating]
            except KeyError:
                continue
            if generating_unit.tipo != "ThermalGeneratingUnit":
                continue
            steam_flg = False
            for hijo in gen.hijos:
                if hijo.tipo == "SteamTurbine":
                    steam_flg = True
                    break
            if steam_flg == False and generating_unit.subtipo == "Fossil Fired Steam":
                self.mf.log.error (f"Generador {gen.get_ta([])} sin steamturbine, {generating_unit.subtipo}")
                lista_turbinas.append([gen.get_ta([]), generating_unit.subtipo, "SIN STREAMTURBINE"])
        df_turbinas = pd.DataFrame(lista_turbinas, columns=["Path", "PhysicalUnitType", "State"])

        nombre_hoja = "Turbina_Vapor"
        self.coleccion_df[nombre_hoja] = df_turbinas
        network.reset_arbol()

    def verificar_ligas_a_generating_unit(self):
        """Verifica las ligas entre ls SynchronousMachine y las generatingUnits.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_ligas = path.join(self.mf.MAGEselected_path, "liga_a_generating.csv")
        network = crear_arbol_mage(archivo_equipos)
        #Añadimos las ligas entre SynchronousMachine y GEnerating Units
        dicc_synchronous, _, _ = leer_csv(archivo_ligas, ["ID"])
        for clave in dicc_synchronous.values():
            synchronous = network.dicc_arbol[clave["ID"]]
            synchronous.liga_a_generating = clave["SynchronousMachineMemberOfGeneratingUnit_GeneratingUnit_ID"]

        #Validar que tonos los qgeneradorres tenga una generating unit con la NAFlag activada
        lista_gen = []
        for gen in network.dicc_arbol.values():
            if gen.tipo != "SynchronousMachine":
                continue
            if gen.na_flag != True:
                continue
            try:
                generating_unit = network.dicc_arbol[gen.liga_a_generating]
            except KeyError:
                self.mf.log.error  (f"Liga invalida a generating unit del generador {gen.get_ta([])}")
                lista_gen.append([gen.get_ta([]), generating_unit.get_ta([]), "Link invalido"])
                continue
            if generating_unit.na_flag == False:
                self.mf.log.error  (f"Generador {gen.get_ta([])} con generating unit {generating_unit.get_ta([])} con na_flag desactivada")
                lista_gen.append([gen.get_ta([]), generating_unit.get_ta([]), "NAFlag False"])
        df_gen = pd.DataFrame(lista_gen, columns=["Generation", "GeneratingUnit", "State"])

        nombre_hoja = "Gen_Unit_Link"
        self.coleccion_df[nombre_hoja] = df_gen
        network.reset_arbol()

    def verificar_mrids(self):
        """Verifica los mrids repetidos de algunos equipos electricos de IMM-MAGE.
        """
        archivo_mrids = path.join(self.mf.MAGEselected_path, "mRID.csv")
        dicc_mRID, _, _ = leer_csv(archivo_mrids, ["ID"])
        aux = set()
        lista_mrid = []
        for clave in dicc_mRID.values():
            if clave["TableName"] in ["ReactiveCapabilityCurve", "SteamTurbine", "CombinedCyclePlant", "VoltageLevel", "Solar Plant", "HydroPowerPlant", "ThermalPowerPlant", "TapChanger", "TransformerWinding", "SynchronousMachine", "Substation", "Geographical Region", "Wind Plant", "BaseVoltage", "Sub Geographical Region"]:
                continue
            if (clave["mRID"], clave["TableName"]) in aux:
                self.mf.log.error (f"mRID [{clave['mRID']}] duplicado para el equipo {clave['Name']} y tabla {clave['TableName']}")
                lista_mrid.append([clave['mRID'], clave['Name'], clave['TableName']])
                continue
            key = (clave["mRID"], clave["TableName"])
            aux.add(key)
        df_mrid = pd.DataFrame(lista_mrid, columns=["mRID", "Equipo", "Tabla"])

        nombre_hoja = "mRID"
        self.coleccion_df[nombre_hoja] = df_mrid

    def verificar_info_curvas_capabilidad(self):
        """Verifica la información de las curvas de capabilidad."""
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_curvas = path.join(self.mf.MAGEselected_path, "datos_curvas_capabilidad.csv")
        network = crear_arbol_mage(archivo_equipos)
        #Añadimos la informacion de los datos de las curvas de curva_capabilidad
        dicc_curvas, _, _ = leer_csv(archivo_curvas, ["ID"])
        for clave in dicc_curvas.values():
            curva_capabilidad = network.dicc_arbol[clave["ID"]]
            try:
                curva_capabilidad.X = float(clave["xAxisData"])
            except:
                pass
            try:
                curva_capabilidad.Y1 = float(clave["y1AxisData"])
            except:
                pass
            try:
                curva_capabilidad.Y2 = float(clave["y2AxisData"])
            except:
                pass
        #Aplicamos la validacion de las curvas de los datos de la curva de capabilidad
        lista_capabilidad = []
        for  curva in network.dicc_arbol.values():
            if curva.tipo != "CurveData":
                continue
            if "Network/.Generation" in curva.get_ta([]):
                continue
            if curva.Y1 is None :
                self.mf.log.error (f"Error en el valor Y1 de la curva {curva.get_ta([])}")
                lista_capabilidad.append([curva.get_ta([]), "Y1", "Vacío"])
                continue
            if curva.Y2 is None :
                self.mf.log.error (f"Error en el valor Y2 de la curva {curva.get_ta([])}")
                lista_capabilidad.append([curva.get_ta([]), "Y2", "Vacío"])
                continue
            if curva.Y2 < curva.Y1:
                self.mf.log.error (f"Error en la curva {curva.get_ta([])}, Y1: {curva.Y1} mayor que Y2: {curva.Y2}")
                lista_capabilidad.append([curva.get_ta([]), "'Y1', 'Y2'", "Y2 < Y1"])
        df_mrid = pd.DataFrame(lista_capabilidad, columns=["Path", "Value", "State"])

        nombre_hoja = "Curva_Capabilidad"
        self.coleccion_df[nombre_hoja] = df_mrid
        network.reset_arbol()

    def verificar_niveles_tension_transformadores(self):
        """Verifica la congruencia de los niveles de tension asociado a los
        transformadores.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
        archivo_voltajes = path.join(self.mf.MAGEselected_path, "winding_voltage.csv")
        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)

        dicc_base_vol, _, _ = leer_csv(archivo_voltajes, ["ID"])
        for clave in dicc_base_vol.values():
            winding = network.dicc_arbol[clave["ID"]]
            winding.link_base_voltage = clave["ConductingEquipmentUsesABaseVoltage_BaseVoltage_ID"]

        #Validar los niveles de tension
        lista_kv = []
        for obj in network.dicc_arbol.values():
            if obj.tipo != "TransformerWinding":
                continue
            if obj.na_flag == False:
                continue
            try:
                nivel_tension_base  = network.dicc_arbol[obj.link_base_voltage].nombre
                nivel_tension_base = float(nivel_tension_base.replace("Base", ""))
            except KeyError:
                self.mf.log.error (f"Winding sin link a nivel de tensión {obj.get_ta([])}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, "", "SIN LINK AL NIVEL DE TENSIÓN"])
                continue
            bus = obj.get_connectivity_nodes(use_na_flag=True, nodos=set())
            if len(bus) != 1:
                self.mf.log.error (f"Error al buscar el nodo de conectividad asociado al winding {obj.get_ta([])}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, bus.get_voltaje_level(), "SIN NC"])
                continue
            bus = network.dicc_arbol[list(bus)[0]]
            nivel_tension =  bus.get_voltaje_level()
            if abs(nivel_tension_base - nivel_tension) > 0.1:
                self.mf.log.error (f"Niveles de tension incorrectos en el winding {obj.get_ta([])}: BaseVoltage {nivel_tension_base}, VoltageLevel {nivel_tension}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, nivel_tension, "INCORRECTO"])
        df_tr_kv = pd.DataFrame(lista_kv, columns=["Path", "BaseVoltage", "VoltageLevel", "State"])

        nombre_hoja = "Nivel_Tension_TR"
        self.coleccion_df[nombre_hoja] = df_tr_kv
        network.reset_arbol()

    def verificar_niveles_tension_lineas(self):
        """Verifica la congruencia de los niveles de tension asociado a las
        lineas de tension.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
        archivo_voltajes = path.join(self.mf.MAGEselected_path, "aclinesegments_voltage.csv")
        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        dicc_base_vol, _, _ = leer_csv(archivo_voltajes, ["ID"])
        for clave in dicc_base_vol.values():
            line = network.dicc_arbol[clave["ID"]]
            line.link_base_voltage = clave["ConductingEquipmentUsesABaseVoltage_BaseVoltage_ID"]
        #Validar los niveles de tension
        lista_kv = []
        for obj in network.dicc_arbol.values():
            if obj.tipo != "ACLineSegment":
                continue
            if obj.na_flag == False:
                continue
            try:
                nivel_tension_base  = network.dicc_arbol[obj.link_base_voltage].nombre
                nivel_tension_base = float(nivel_tension_base.replace("Base", ""))
            except KeyError:
                self.mf.log.error (f"ACLineSegment sin link a nivel de tension {obj.get_ta([])}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, "", "", "SIN LINK AL NIVEL DE TENSIÓN"])
                continue
            buses = obj.get_connectivity_nodes(use_na_flag=True, nodos=set())
            if len(buses) != 2:
                self.mf.log.error (f"Error al buscar el nodo de conectividad asociado a la linea {obj.get_ta([])}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, "", "", "SIN NC"])
                continue
            bus = network.dicc_arbol[list(buses)[0]]
            nivel_tension1 =  bus.get_voltaje_level()
            if abs(nivel_tension_base - nivel_tension1) > 0.1:
                self.mf.log.error (f"Niveles de tension incorrectos en la linea {obj.get_ta([])}: BaseVoltage {nivel_tension_base}, VoltageLevel {nivel_tension1}, Bus: {bus.get_ta([])}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, nivel_tension1, bus.get_ta([]), "INCORRECTO"])
            bus = network.dicc_arbol[list(buses)[1]]
            nivel_tension2 =  bus.get_voltaje_level()
            if abs(nivel_tension_base - nivel_tension2) > 0.1:
                self.mf.log.error (f"Niveles de tension incorrectos en la linea {obj.get_ta([])}: BaseVoltage {nivel_tension_base}, VoltageLevel {nivel_tension2}, Bus: {bus.get_ta([])}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, nivel_tension2, bus.get_ta([]), "INCORRECTO"])
        df_lt_kv = pd.DataFrame(lista_kv, columns=["Path", "BaseVoltage", "VoltageLevel_1", "VoltageLevel_2", "State"])

        nombre_hoja = "Nivel_Tension_LT"
        self.coleccion_df[nombre_hoja] = df_lt_kv
        network.reset_arbol()

    def verificar_niveles_tension_voltage_level(self):
        """Verifica la congruencia de los niveles de tension asociado a las
        lineas de tension.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
        archivo_voltajes = path.join(self.mf.MAGEselected_path, "voltages.csv")
        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        dicc_base_vol, _, _ = leer_csv(archivo_voltajes, ["ID"])
        for clave in dicc_base_vol.values():
            if clave["ID"] == "_20c24fd7-a4d6-4856-b122-d9577d6f7d47": #Nivel de tension en SCADA Only
                continue
            voltage_level = network.dicc_arbol[clave["ID"]]
            voltage_level.link_base_voltage = clave["VoltageLevelHasABaseVoltage_BaseVoltage_ID"]

        #Validar los niveles de tension
        lista_kv = []
        for obj in network.dicc_arbol.values():
            if obj.tipo != "VoltageLevel":
                continue
            if obj.na_flag == False:
                continue
            try:
                nivel_tension_base  = network.dicc_arbol[obj.link_base_voltage].nombre
                nivel_tension_base = float(nivel_tension_base.replace("Base", ""))
            except KeyError:
                self.mf.log.error (f"VoltageLevel sin link a nivel de tension {obj.get_ta([])}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, "", "SIN LINK AL NIVEL DE TENSIÓN"])
                continue
            nivel_tension =  obj.get_voltaje_level()
            if abs(nivel_tension_base - nivel_tension) > 0.1:
                self.mf.log.error (f"Niveles de tension incorrectos en el voltage level {obj.get_ta([])}: BaseVoltage {nivel_tension_base}, VoltageLevel {nivel_tension}")
                lista_kv.append([obj.get_ta([]), nivel_tension_base, nivel_tension, "INCORRECTO"])
        df_kv = pd.DataFrame(lista_kv, columns=["Path", "BaseVoltage", "VoltageLevel", "State"])

        nombre_hoja = "Nivel_Tension"
        self.coleccion_df[nombre_hoja] = df_kv
        network.reset_arbol()

    def verificar_islas_electricas(self, force_na_flag):
        """Verifica la existencia de islas electricas en el modelo de IMM-MAGE.

        Por definición el modelo contempla la existencia de tres islas SIN, BCA,
        BCS.

        Parameters
        ----------
        force_na_flag: bool
            Bandera para forzar la NAFlag de todos los equipos como verdadera.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
        network = crear_arbol_mage(archivo_equipos, force_na_flag)
        aniadir_terminales(network, archivo_terminales)
        self.mf.log.info("Listado de buses sin equipos electricos asociados")
        for nodo_aislado in  sorted(network.dicc_arbol[x].get_ta([]) for x in  network.get_buses_aislados()):
            self.mf.log.info(nodo_aislado)
        coleccion_equipo = network.crear_grafo(usar_na_flag=True, ignorar_buses_aislados=True)
        self.mf.log.info("Reporte por islas electricas detectadas")
        aux = defaultdict(set)
        for i, isla in enumerate(sorted(nx.connected_components(network.grafo), key=lambda x:len(x), reverse=True)):
            if i < 3:
                continue
            self.mf.log.info(f"Isla detectada con {len(isla)} elementos:")
            for nodo in isla:
                obj = network.dicc_arbol[nodo]
                ruta = obj.get_ta([])
                sub = obj.get_subestacion(use_name_marker=False)
                self.mf.log.info(ruta)
                aux[sub].add(ruta)
        self.mf.log.info("Reporte de buses en isla agrupados por subestacion")
        for llave, clave in aux.items():
            self.mf.log.info(f"Subestación con elementos aislados: {llave}")
            for ele in clave:
                self.mf.log.info(f"{ele}")
        if force_na_flag == True:
            nombre_hoja = "Islas_sin_NA"
            df_islas_sin_na = pd.DataFrame()
            self.coleccion_df[nombre_hoja] = df_islas_sin_na
        else:
            nombre_hoja = "Islas_con_NA"
            df_islas_con_na = pd.DataFrame()
            self.coleccion_df[nombre_hoja] = df_islas_con_na

        network.reset_arbol()

    def verificar_link_equipos_reguladores(self):
        """"""
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)

        files = (
            "staticvar_reg_terminal.csv", "shunt_reg_terminal.csv",
            "synchmachine_reg_terminal.csv",
        )
        lista_equipo = []
        for file in files:
            dicc_data, _, _ = leer_csv(path.join(self.mf.MAGEselected_path, file), ["ID"])
            for row in dicc_data.values():
                obj = network.dicc_arbol[row["ID"]]
                reg_flag = True
                if file == "shunt_reg_terminal.csv":
                    reg_flag = False if row["VoltageControlFlag"] == "false" else True
                if file == "synchmachine_reg_terminal.csv":
                    reg_flag = False if row["VoltRegStatus"] == "No Regulation" else True
                if reg_flag == True:
                    obj.link_a_terminal_regulada = row["RegulatingCondEqRegulatesTerminal_Terminal_ID"]
                    obj.regulacion_flag = True

        dicc_data, _, _ = leer_csv(path.join(self.mf.MAGEselected_path, "tap_changer_reg_terminal.csv"), ["ID"])
        for row in dicc_data.values():
            obj = network.dicc_arbol[row["ID"]]
            if row["TapMovability"] == "false":
                continue
            obj.link_a_terminal_regulada = row["TapChangerRegulatesTerminal_Terminal_ID"]
            obj.regulacion_flag = True

        dicc_data, _, _ = leer_csv(path.join(self.mf.MAGEselected_path, "tipos_transformadores.csv"), ["ID"])
        for row in dicc_data.values():
            obj = network.dicc_arbol[row["ID"]]
            reg_flag = False if row["transformerType"] in ["fix", ""] else True
            obj.regulacion_flag = reg_flag

        #Validar los links de las terminales reguladas
        for obj in network.dicc_arbol.values():
            if obj.tipo not in ["SynchronousMachine", "ShuntCompensator", "StaticVarCompensator", "ComplexTransformer", "PowerTransformer"]:
                continue
            if obj.na_flag == False:
                continue
            if obj.regulacion_flag == False:
                continue
            if obj.tipo in ["PowerTransformer", "ComplexTransformer"]:
                objetos = []
                for winding in [x for x in obj.hijos if x.tipo == "TransformerWinding"]:
                    for obj in winding.hijos:
                        if obj.tipo == "TapChanger" and obj.regulacion_flag:
                            objetos.append(obj)
            else:
                objetos = [obj]

            for objeto in objetos:
                if objeto.link_a_terminal_regulada is None or objeto.link_a_terminal_regulada== "":
                    self.mf.log.error (f"Terminal de regulacion no asignada en el equipo {objeto.get_ta([])}")
                    lista_equipo.append(["TERMINAL DE REGULACION NO ASIGNADA EN EQUIPO",objeto.get_ta([])])
                    continue
                terminal = network.dicc_arbol[objeto.link_a_terminal_regulada]
                if network.dicc_arbol[terminal.padre].tipo == "BusbarSection":
                    continue
                bus = terminal.nodo_conectividad
                equipos = network.get_equipos_conectados_a_bus(bus)

                bus_bar_flg = False
                for equipo in equipos:
                    if equipo.tipo == "BusbarSection":
                        bus_bar_flg = True
                        break

                if bus_bar_flg == False:
                    self.mf.log.error (f"Equipo {objeto.get_ta([])} con bus regulado no asociado a un busbarsection")
                    lista_equipo.append(["BUS REGULADO NO ASOCIADO A UN BUSBARSECTION",objeto.get_ta([])])

        df_equipo = pd.DataFrame(lista_equipo, columns=["State", "Path"])
        nombre_hoja = "Eqp_Regulados_Link"
        self.coleccion_df[nombre_hoja] = df_equipo
        network.reset_arbol()

    def verificar_existencia_curvas_calor_incremental(self):
        """"""
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        network = crear_arbol_mage(archivo_equipos)
        #Poblar la bandera AGC_FLAG
        dicc_agc, _, _ = leer_csv(path.join(self.mf.MAGEselected_path, "bandera_agc.csv"), ["ID"])
        for clave in dicc_agc.values():
            obj = network.dicc_arbol[clave["ID"]]
            obj.agc_flag = False if clave["AGCFlag"] == "false" else True

        #Validar que todas las generating unit termicas tienen una curva de calor incremental
        lista_curva = []
        for obj in network.dicc_arbol.values():
            if obj.agc_flag == False:
                continue
            if obj.tipo not in ("ThermalGeneratingUnit", "CombinedCycleConfiguration"):
                continue
            incremental_heat_flg = False
            for hijo in obj.hijos:
                if hijo.tipo == "IncrementalHeatRateCurve":
                    incremental_heat_flg = True
                    break
            if incremental_heat_flg == False:
                # print(hijo)
                # print(incremental_heat_flg)
                self.mf.log.error (f"Unidad {obj.get_ta([])} sin curva de calor incremental")
                lista_curva.append([obj.nombre, obj.get_ta([])])
        df_curva = pd.DataFrame(lista_curva, columns=["ThermalGeneratingUnit", "Path"])
        nombre_hoja = "Carvas_Calor"
        self.coleccion_df[nombre_hoja] = df_curva
        network.reset_arbol()

    def verificar_existencia_curvas_hidro(self):
        """"""
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        network = crear_arbol_mage(archivo_equipos)
        #Poblar la bandera AGC_FLAG
        dicc_agc, _, _ = leer_csv(path.join(self.mf.MAGEselected_path, "bandera_agc.csv"), ["ID"])
        for clave in dicc_agc.values():
            obj = network.dicc_arbol[clave["ID"]]
            obj.agc_flag = False if clave["AGCFlag"] == "false" else True
        #Validar que todas las unidades hydro tengan 5 curvas de costo
        lista_curva = []
        for obj in network.dicc_arbol.values():
            if obj.agc_flag == False:
                continue
            if obj.tipo != "HydroGeneratingUnit":
                continue
            hydro_power_discharge_curve_count = 0
            for hijo in obj.hijos:
                if hijo.tipo == "HydroPowerDischargeCurve":
                    hydro_power_discharge_curve_count += 1
            if hydro_power_discharge_curve_count != 5:
                self.mf.log.error (f"Unidad {obj.get_ta([])} no tiene el numero correcto de curvas hydro. Numero encontrado {hydro_power_discharge_curve_count}")
                lista_curva.append([obj.nombre, obj.get_ta([]), hydro_power_discharge_curve_count])
        df_curva = pd.DataFrame(lista_curva, columns=["HydroGeneratingUnit", "Path", "Number"])
        nombre_hoja = "Curva_Hidro"
        self.coleccion_df[nombre_hoja] = df_curva
        network.reset_arbol()

    def verificar_Conformload_NConformload_ID(self):
        """Función que verifica que los PSS/e Load_ID de las cargas, sean únicos por SE y por nivel de tensión
        """
        archivo_ShortID = path.join(self.mf.MAGEselected_path, "conformload_voltage.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_cargas, _, _ = leer_csv(archivo_ShortID, ["ID"])
        dicc_aux = defaultdict(valor_defecto1)

        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)

        self.mf.log.info(
            "Inicia el proceso de validación de PSS/e ShortID de las cargas por subestación y nivel de tensión"
        )
        lista_load = []
        load = {}
        for clave in dicc_cargas.values():
            obj = network.dicc_arbol[clave["ID"]]
            llave = (clave['ShortID'], obj.get_subestacion()),obj.get_voltaje_level()
            temp = clave["Name"], clave['ShortID']#, obj.get_voltaje_level()
            dicc_aux[llave].append(temp)

        for key, value in dicc_aux.items():
            if len(value) > 1:
                self.mf.log.info("Corregir el ID de la Carga.")
                self.mf.log.info(f"ID de cargas repetido: {key, value}")
                short_id, SE, NT = (*key[0], key[1])
                for i, tupla in enumerate(value):
                    load = tupla[0]
                lista_load.append([short_id, SE, NT, load])
                # print(lista_load)
        df_load = pd.DataFrame(lista_load, columns=["ShortID", "SE", "kV", "Load"])
        nombre_hoja = "NoC_ConforLoad_ID"
        self.coleccion_df[nombre_hoja] = df_load
        network.reset_arbol()

    def verificar_generating_unit_limites(self):
        """Función que verifica que los limites de los GeneratingUnits tengan valor
        """
        archivo_gen_unit = path.join(self.mf.MAGEselected_path, "GeneratingUnit_MAX_MIN.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        # archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
        network = crear_arbol_mage(archivo_equipos)

        dicc_Gen_Unit, _, _ = leer_csv(archivo_gen_unit, ["ID"])

        lista_unidades = []
        max_dteMW = []
        min_dteMW = []
        max_opP = []
        min_opP = []
        rtd_maxP = []
        rtd_minP = []

        for clave in dicc_Gen_Unit.values():
            if clave["TableName"] != "GeneratingUnit":
                continue
            obj = network.dicc_arbol[clave["ID"]]
            # print(obj.na_flag)
            if clave["AGCFlag"] == "false":
                continue
            if (clave["MaximumDeratedMW"] == "") or (clave["MinimumDeratedMW"] == "") or (clave["maxOperatingP"] == "") or (clave["minOperatingP"] == "") or (clave["ratedNetMaxP"] == "") or (clave["ratedNetMinP"] == ""):
                # print(obj.id)
                lista_unidades.append(obj.id)
                # self.mf.log.error(f"Unidad: {obj.get_ta([])}")

            if clave["MaximumDeratedMW"] == "":
                self.mf.log.error(f"MaximumDeratedMW vacio en: {obj.nombre}, {obj.get_ta([])}")
                max_dteMW.append([obj.nombre,obj.get_ta([]),"MaximumDeratedMW"])
            if clave["MinimumDeratedMW"] == "":
                self.mf.log.error(f"MinimumDeratedMW vacio en: {obj.nombre}, {obj.get_ta([])}")
                min_dteMW.append([obj.nombre,obj.get_ta([]),"MinimumDeratedMW"])
            if clave["maxOperatingP"] == "":
                self.mf.log.error(f"maxOperatingP vacio en: {obj.nombre}, {obj.get_ta([])}")
                max_opP.append([obj.nombre,obj.get_ta([]),"maxOperatingP"])
            if clave["minOperatingP"] == "":
                self.mf.log.error(f"minOperatingP vacio en: {obj.nombre}, {obj.get_ta([])}")
                min_opP.append([obj.nombre,obj.get_ta([]),"minOperatingP"])
            if clave["ratedNetMaxP"] == "":
                self.mf.log.error(f"ratedNetMaxP vacio en: {obj.nombre}, {obj.get_ta([])}")
                rtd_maxP.append([obj.nombre,obj.get_ta([]),"ratedNetMaxP"])
            if clave["ratedNetMinP"] == "":
                self.mf.log.error(f"ratedNetMinP vacio en: {obj.nombre}, {obj.get_ta([])}")
                rtd_minP.append([obj.nombre,obj.get_ta([]),"ratedNetMinP"])
        lista_gen = max_dteMW + min_dteMW + max_opP + min_opP + rtd_maxP + rtd_minP
        df_units = pd.DataFrame(lista_gen)
        nombre_col = {0:"Name",1:"Path",2:"Lim"}
        df_units = df_units.rename(columns=nombre_col)
        # print(df_units)

        nombre_hoja = "Lim_Gen_Unit"

        self.coleccion_df[nombre_hoja] = df_units
        # self.export_report(nombre_hoja,df_units)
        
        network.reset_arbol()


    def verificar_cargas_Aux(self):
        """Función que verifica que los PSS/e Load_ID de las cargas, sean Ãºnicos por SE y por nivel de tensión
        """
        archivo_Load_AUX = path.join(self.mf.MAGEselected_path, "ConformLoad_Auxiliary.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_Load_AUX, _, _ = leer_csv(archivo_Load_AUX, ["ID"])
        
        dicc_aux = defaultdict(valor_defecto1)

        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        aux = set()
        
        self.mf.log.info(
            "Inicia el proceso de verificación de cargas Auxiliares"
        )
        aux = defaultdict(set)
        aux_sin_estandar = defaultdict(set)

        lista_cargas = []

        for clave in dicc_Load_AUX.values():
            obj = network.dicc_arbol[clave["ID"]]
            if obj.tipo != "ConformLoad":
                continue
            if obj.na_flag==False:
                continue
            if clave["IsAuxiliary"]=='true':
                #print(clave)
                ruta=obj.get_ta()
                rgx_res = loadAux_rgx.search(clave['ODBName'])
                if rgx_res:
                    SE = rgx_res.group(1)
                    AX = rgx_res.group(2)
                    ID = rgx_res.group(3)
                    NT = rgx_res.group(4)
                    U = rgx_res.group(5)
                #    print(SE, AX, ID, NT, U)
                    if AX=='A':
                        key=(obj.get_ta([]), clave['ODBName'])
                        aux[clave['ID']].add(key)
                else:
                    key=(obj.get_ta([]), clave['ODBName'])
                    aux_sin_estandar[clave['ID']].add(key)

        for llave, valor in aux.items():
            self.mf.log.info(f"Cargas Auxiliares: {valor} ")
            # print(valor)
            n_valor = set()
            for tupla in valor:
                nueva_tupla = tupla + ("CUMPLE",)
                n_valor.add(nueva_tupla)
            lista_cargas.append(list(n_valor))

        for llave, valor in aux_sin_estandar.items():
            self.mf.log.info(f"Cargas Auxiliares, el ODBName no sigue el estandar : {valor} ")
            n_valor = set()
            for tupla in valor:
                nueva_tupla = tupla + ("NO CUMPLE",)
                n_valor.add(nueva_tupla)
            lista_cargas.append(list(n_valor))

        Path = [elem[0] for conjunto in lista_cargas for elem in conjunto]
        ODBName = [elem[1] for conjunto in lista_cargas for elem in conjunto]
        STD = [elem[2] for conjunto in lista_cargas for elem in conjunto]

        df_cargas = pd.DataFrame({"Path": Path, "ODBName": ODBName, "State": STD})
        nombre_hoja = "Aux_Load"
        self.coleccion_df["Aux_Load"] = df_cargas
        network.reset_arbol()

    def verificar_link_LoadGroup(self):
        """Función que validación de link LoadGroup con una carga modelada
        """
        archivo_ConformLoad_Group = path.join(self.mf.MAGEselected_path, "LoadGroup_Conform.csv")
        archivo_NonConformLoad_Group = path.join(self.mf.MAGEselected_path, "LoadGroup_NonConform.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_ConformLoad_Group, _, _ = leer_csv(archivo_ConformLoad_Group, ["ID"])
        dicc_NonConformLoad_Group, _, _ = leer_csv(archivo_NonConformLoad_Group, ["ID"])
        
        dicc_aux = defaultdict(valor_defecto1)
        dicc_aux_load_ID = defaultdict(valor_defecto3)

        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        aux = set()


        lista_cargas = []

        self.mf.log.info(
            "Inicia el proceso de validación de link LoadGroup (Network/.LoadAreas/) con una carga modelada"
        )
        for clave in dicc_ConformLoad_Group.values():
            if clave["ConformLoadAssignedToConformLoadGroup_ConformLoad_ID"]!="":
                obj = network.dicc_arbol[clave["ConformLoadAssignedToConformLoadGroup_ConformLoad_ID"]]
                if obj.tipo != "ConformLoad":
                    continue
                if obj.na_flag==False:
                    continue
                if clave['ConformLoadAssignedToConformLoadGroup_ConformLoad_ID'] in network.dicc_arbol:
                   print(clave)
            else:
                self.mf.log.error (f"El grupo de carga: {clave['Name']} no está asociada a una carga modelada. ")
                lista_cargas.append([clave["Name"],clave["ObjectType"]])


        for clave in dicc_NonConformLoad_Group.values():
            if clave["NonConformLoadAssignedToNonConformLoadGroup_NonConformLoad_ID"]!="":
                obj = network.dicc_arbol[clave["NonConformLoadAssignedToNonConformLoadGroup_NonConformLoad_ID"]]
                if obj.tipo != "NonConformLoad":
                    continue
                if obj.na_flag==False:
                    continue
                if clave['NonConformLoadAssignedToNonConformLoadGroup_NonConformLoad_ID'] in network.dicc_arbol:
                    print(clave)    
            else:
                self.mf.log.error (f"El grupo de carga: {clave['Name']} no está asociada a una carga modelada.")
                lista_cargas.append([clave["Name"],clave["ObjectType"]])

        df_loadgroups = pd.DataFrame(lista_cargas,columns = ["Load", "Type"])
        # print(df_loadgroups)
        nombre_hoja = "Load_Group"
        self.coleccion_df[nombre_hoja] = df_loadgroups

        network.reset_arbol()


    def verificar_Conformload_ZeroMW_percentages(self):
        """Función que verifica Conforming Load con Zero MW/MVAR percentages
        """
        archivo_Load_ID = path.join(self.mf.MAGEselected_path, "conformload_voltage.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_Load_ID, _, _ = leer_csv(archivo_Load_ID, ["ID"])
        
        dicc_aux = defaultdict(valor_defecto1)
        dicc_aux_load_ID = defaultdict(valor_defecto3)

        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        aux = set()

        lista_cargas = []
        self.mf.log.info(
            "Inicia el proceso de validación de Conforming Load con Zero MW/MVAR percentages"
        )
        for clave in dicc_Load_ID.values():
            obj = network.dicc_arbol[clave["ID"]]
            if obj.na_flag==False:
                continue
            if int(clave['pfixedPct']) != 100 or int(clave['qfixedPct']) !=100:
                ruta = (obj.get_ta([]), clave['Name'])
                self.mf.log.error (f"{clave['Path']}, {clave['Name']}, {clave['pfixedPct']}, {clave['qfixedPct']})")
                lista_cargas.append([clave['Path'],clave['Name'],clave['pfixedPct'],clave['qfixedPct']])
            if int(clave['pfixedPct']) == "" or int(clave['qfixedPct']) == "":
                ruta = (obj.get_ta([]), clave['Name'])
                self.mf.log.error (f"{clave['Path']}, {clave['Name']}, {clave['pfixedPct']}, {clave['qfixedPct']})")
                lista_cargas.append([clave['Path'],clave['Name'],clave['pfixedPct'],clave['qfixedPct']])
        df_cargas = pd.DataFrame(lista_cargas, columns = ["Path", "Name", "pfixedPct", "qfixedPct"])

        nombre_hoja = "ConformLoad_Percentage"
        self.coleccion_df[nombre_hoja] = df_cargas
        network.reset_arbol()

    def verificar_Conformload_feeder(self):
        """Función que verifica Cargas con al menos un alimentador
        """
        archivo_Load_ID = path.join(self.mf.MAGEselected_path, "conformload_voltage.csv")
        archivo_Load_AUX = path.join(self.mf.MAGEselected_path, "ConformLoad_Auxiliary.csv")
        archivo_load_feeder = path.join(self.mf.MAGEselected_path, "Feeder.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_Load_ID, _, _ = leer_csv(archivo_Load_ID, ["ID"])
        dicc_Load_AUX, _, _ = leer_csv(archivo_Load_AUX, ["ID"])
        dicc_load_feeder, _, _ = leer_csv(archivo_load_feeder, ["ID"])
        
        dicc_aux = defaultdict(valor_defecto1)
        dicc_aux_feeder = defaultdict(set)
        dicc_aux_load_ID = defaultdict(valor_defecto3)

        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        aux = set()

        self.mf.log.info(
            "Inicia el proceso de validación de Cargas con al menos un alimentador"
        )
        """Construye el diccionario de los alimentadores"""
        for clave in dicc_load_feeder.values():
            llave=clave['Parent']
            valor=(clave['FeederCode'],clave['FeederMWPercent'],clave['FeederMVARPercent'])
            dicc_aux_feeder[llave].add(valor)

        """Valida que para todas las cargas modeladas, debe tener al menos, un alimentador."""
        for clave in dicc_Load_ID.values():
            obj = network.dicc_arbol[clave["ID"]]
            if obj.tipo != "ConformLoad" or obj.tipo != "NonConformLoad":
                continue
            if obj.na_flag==False:
                continue
            if clave[0] in dicc_aux_feeder:
                self.mf.log.error(f"La carga modelada con al menos un alimentador.")
#                continue
            else:
                self.mf.log.error(f"La carga no tiene modelado al menos un alimentador.")

        self.mf.log.info(
            "Inicia el proceso de validación Sumatoria de MWPercent y MVARPercent de los alimentadores"
        )

        lista_load = []
        lista_cargas = []
        for llave, valor in dicc_aux_feeder.items():
            # print("carga: ",llave)
            sumaMWPercent=0
            sumaMVarPercent=0
            # print(valor)
            valor = list(valor)
            for feeder in valor:
                print("ID:",llave,"Feeder:",feeder[0],"MWPercent:",feeder[1], "MVarPercent:",feeder[2])
                set1=float(feeder[1])
                set2=float(feeder[2])
                # print(set1, set2)
                sumaMWPercent+=set1
                sumaMVarPercent+=set2
            # print(sumaMWPercent, sumaMVarPercent)
            if (sumaMWPercent<99.99) or (sumaMVarPercent<99.99):
                # print("carga: ",llave, valor)
                # self.mf.log.error (f"Carga: {obj.get_ta([])} {llave}, {valor}")
                lista_load.append(llave)

        for clave in dicc_Load_ID.values():
            obj = network.dicc_arbol[clave["ID"]]
            if obj.id in lista_load:
                self.mf.log.error (f"Carga: {obj.get_ta([])}")
                lista_cargas.append([obj.get_ta([]),obj.nombre])
        df_cargas = pd.DataFrame(lista_cargas, columns = ["Path", "Name"])

        nombre_hoja = "ConformLoad_Alimentadores"
        self.coleccion_df[nombre_hoja] = df_cargas

        network.reset_arbol()




    def verificar_Busbarsection_MarketLoadZone(self):
#        Función que verifica que los Busbarsection contengan:
#        1. la liga a las MarketLoadZone y que sea unica por Subestación
#        2. al atributo CTCP no sea NULL
#        3. esté definida la liga a las Zonas de Transmisión y Distribución 
#        4. la bandera de NodoP sea unica por Subestación y por nivel de tensióN
#        5. valida catalogo OperatingParticipants

        archivo_Busbar_marketZone = path.join(self.mf.MAGEselected_path, "Busbar_MarketLoadZone.csv")
        archivo_Busbar_ZT_ZD = path.join(self.mf.MAGEselected_path, "Busbar_ZC_ZT_ZD.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")


        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)

        dicc_busbar_marketZone, _, _ = leer_csv(archivo_Busbar_marketZone, ["ID"])
        dicc_Busbar_ZT_ZD, _, _ = leer_csv(archivo_Busbar_ZT_ZD, ["ID","OperatingShareForPowerSystemResource_OperatingShare_ID"])
        
        dicc_aux = defaultdict(valor_defecto)
        dicc_aux_ctcp = defaultdict(valor_defecto)
        dicc_aux_zt_zd = defaultdict(valor_defecto2)


        self.mf.log.info(
            "Inicia el proceso de verificación del link a las MarketLoadZone por cada Busbarsection "
        )
        lista_market = []
        for clave in dicc_busbar_marketZone.values():
            obj = network.dicc_arbol[clave["ID"]]

            if obj.tipo != "BusbarSection":
                continue
            if obj.na_flag==False:
                continue

            """liga MarketLoadZone"""
            if clave['MarketLoadZone_Name'] == "":
                self.mf.log.error (f"El siguiente elemento no tiene una MarketLoadZone definida: {obj.get_ta([])}")
                lista_market.append(["SIN MARKETLOADZONE DEFINIDA", obj.get_ta([]),obj.nombre,obj.tipo, ""])
                continue
            key = obj.get_subestacion([])
            dicc_aux[key][0].append(clave['Name'])
            dicc_aux[key][1].add(clave['MarketLoadZone_Name'])
        
        #print(dicc_aux)    
        self.mf.log.info("Reporte de buses con distinta MarketLoadZone por subestación.")
        for llave, clave in dicc_aux.items():
            #print(llave,clave)
            if len(clave[1])>1:
                self.mf.log.info(f"Agrupados por Subestación: {llave}")
                for ele in clave:
                    #print(dicc_Busbar_ZT_ZD)
                    self.mf.log.info(f"{ele}")


        self.mf.log.info(
            "Inicia el proceso de verificación de la Región de Precio (CTCP) por cada Busbarsection "
        )
        for clave in dicc_busbar_marketZone.values():
            obj = network.dicc_arbol[clave["ID"]]
            if obj.tipo != "BusbarSection":
                continue
            if obj.na_flag==False:
                continue
            
            if clave['ctcpRegion'] =="":
                self.mf.log.warning (f"El siguiente elemento no tiene definida una Region de Precio CTCP: {obj.get_ta([])}")
                continue
            key = obj.get_subestacion([])
            dicc_aux_ctcp[key][0].append(clave['Name'])
            dicc_aux_ctcp[key][1].add(clave["ctcpRegion"]) 

        self.mf.log.info("Reporte de buses con Region CTCP diferente por subestación.")
        self.mf.log.info(f"Agrupados por Subestación. ")
        for llave, clave in dicc_aux_ctcp.items():
            if len(clave[1])>1:
                self.mf.log.info(f"Subestación: {llave}")
                for ele in clave:
                    for i in ele:
                        for bus in dicc_busbar_marketZone:
                            if i == dicc_busbar_marketZone[bus]['Name']:
                                id_bus=dicc_busbar_marketZone[bus]['ID']
                                obj= network.dicc_arbol[dicc_busbar_marketZone[bus]['ID']]
                                self.mf.log.warning(f"{obj.get_ta([])}, CTCP Price Region: {dicc_busbar_marketZone[bus]['ctcpRegion']}")
                                break
                    break
        #network.reset_arbol()

        self.mf.log.info(
            "Inicia el proceso de verificación del link OperatingShare_Name(Zona de Transmisión y Distribución) por cada Busbarsection "
        )
        for clave in dicc_Busbar_ZT_ZD.values():
            obj = network.dicc_arbol[clave["ID"]]
            if obj.tipo != "BusbarSection":
                continue
            if obj.na_flag==False:
                continue
            
            if clave['OperatingShare_Path'] =="":
                self.mf.log.error (f"No tiene definido el link OperatingShare_Name: {obj.get_ta([])}")
                lista_market.append(["LINK NO DEFINIDO EN OPERATINSHARE_NAME", obj.get_ta([]),obj.nombre,obj.tipo, ""])
                continue
            key = obj.get_subestacion([])
            dicc_aux_zt_zd[key][0].add(clave['Name'])
            #Zona de Transmision
            if '_T' in clave["OperatingShare_Path"]:
                if clave["OperatingShare_Path"] in dicc_aux_zt_zd:
                    continue
                rgx_res = rgx_Operating.search(clave["OperatingShare_Path"])
                if rgx_res:
                    Operating_T= rgx_res[0]
                    dicc_aux_zt_zd[key][1].add(Operating_T) 
            #Zona de Distribucion
            if '_D' in clave["OperatingShare_Path"]:
                if clave["OperatingShare_Path"] in dicc_aux_zt_zd:
                    continue
                rgx_res = rgx_Operating.search(clave["OperatingShare_Path"])
                if rgx_res:
                    Operating_D = rgx_res[0]
                    dicc_aux_zt_zd[key][2].add(Operating_D) 

        self.mf.log.info("Reporte de buses con distintos OperatingShare_Name por subestación.")
        self.mf.log.info(f"Agrupados por Subestación.")
        for llave, valor in dicc_aux_zt_zd.items():
            #print(valor)
            if len(valor[1])>1:
                self.mf.log.info(f"Subestación: {llave}, OperatingShare_Name: {valor[1]}")
                for ele in valor:
                    for i in ele:
                        for bus in dicc_Busbar_ZT_ZD:
                            if i == dicc_Busbar_ZT_ZD[bus]['Name']:
                                id_bus=dicc_Busbar_ZT_ZD[bus]['ID']
                                if '_T' in dicc_Busbar_ZT_ZD[bus]["OperatingShare_Path"]:
                                    self.mf.log.warning(f"OperatingShare_Name: {dicc_Busbar_ZT_ZD[bus]['OperatingShare_Path']}")
            if len(valor[2])>1:
                self.mf.log.info(f"Subestación: {llave}, OperatingShare_Name: {valor[2]}")
                for ele in valor:
                    for i in ele:
                        for bus in dicc_Busbar_ZT_ZD:
                            if i == dicc_Busbar_ZT_ZD[bus]['Name']:
                                id_bus=dicc_Busbar_ZT_ZD[bus]['ID']
                                if '_D' in dicc_Busbar_ZT_ZD[bus]["OperatingShare_Path"]:
                                    self.mf.log.warning(f"OperatingShare_Name: {dicc_Busbar_ZT_ZD[bus]['OperatingShare_Path']}")                                
                                break
                        #break
        network.reset_arbol()


        self.mf.log.info(
            "Inicia el proceso de verificación del catalogo OperatingParticipants. "
        )

        archivo_OperatingParticipants = path.join(self.mf.MAGEselected_path, "OperatingParticipants.csv")
        dicc_OperatingParticipants, _, _ = leer_csv(archivo_OperatingParticipants, ["ID"])
        aux = set()
        for clave in dicc_OperatingParticipants.values():
            if (clave["OwnerNumber"]) in aux:
                if (clave["OwnerNumber"]) in ('400','401','402','403','404','405','502','552'):
                    continue
                else:
                    self.mf.log.error (f"OwnerNumber [{clave['OwnerNumber']}] duplicado para el equipo {clave['Name']} y tabla {clave['ObjectType']}")
                    lista_market.append(["OWNERNUMBER DUPLICADO", "",clave["Name"],clave["ObjectType"], clave["OwnerNumber"]])
                    continue
            key = (clave["OwnerNumber"])
            aux.add(key)
#        print(aux)



        self.mf.log.info(
            "Inicia el proceso de verificación del BusNumber repetidos. "
        )

        archivo_BusNameMarker = path.join(self.mf.MAGEselected_path, "BusNameMarker.csv")
        dicc_BusNameMarker, _, _ = leer_csv(archivo_BusNameMarker, ["ID"])
        aux = set()
        for clave in dicc_BusNameMarker.values():
            # print(clave)

            if (clave["BusNumber"]) in aux:
                if (clave["BusNumber"]) == "" and clave["ConnectivityNodeHasABusNameMarker_ConnectivityNode_ID"] =="":
                    self.mf.log.error (f"{clave['Path']}, BusNameMarker con BusNumber y ConnectivityNode vacíos")
                    lista_market.append(["BNM CON BN Y CN", clave["Path"],clave["Name"],clave["ObjectType"], ""])
                    continue
                if (clave["BusNumber"]) == "" and clave["ConnectivityNodeHasABusNameMarker_ConnectivityNode_ID"] !="":
                    self.mf.log.error (f"{clave['Path']}, BusNumber vacío, ConnectivityNode: {clave['ConnectivityNode_Path']}")
                    lista_market.append(["BNM CON CN SIN BN", clave["Path"],clave["Name"],clave["ObjectType"], clave["ConnectivityNode_Path"]])
                    continue                    
                else:
                    self.mf.log.error (f"[{clave['BusNumber']}], BusNameMarker duplicado para el equipo {clave['Path']}")
                    lista_market.append(["BNM DUPLICADO", clave["BusNumber"],clave["Path"],clave["ObjectType"], ""])
                    continue
            key = (clave["BusNumber"])
            aux.add(key)
        df_market = pd.DataFrame(lista_market,columns= ["State", "Element", "Path", "Type", "Parent"])
        hoja_resultante = "MarketLoadZone"
        self.coleccion_df[hoja_resultante] = df_market



    def verificar_SynchronousMachine_NodePKey_ID(self):
        """*Función que verifica que ID de los los SynchronousMachine corresponda con el Name de la UCE
        * verifica que el campo Descripcion contega valores y que sea distinto de PTA
        """

        archivo_id = path.join(self.mf.MAGEselected_path, "SynchronousMachine_nodePKey.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_ID, _, _ = leer_csv(archivo_id, ["ID"])
        aux = set()

        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        self.mf.log.info(
            "Inicia el proceso de validación del ID del SynchronousMachine"
        )
        lista_nodop = []
        for clave in dicc_ID.keys():
            obj = network.dicc_arbol[dicc_ID[clave]['ID']]
            if obj.tipo == "SynchronousMachine" and obj.na_flag=='true':
                ruta = obj.get_ta([])
                ShortId=dicc_ID[clave]['ShortID']                
                rgx_res = patronId.search(dicc_ID[clave]['Name'])
                if rgx_res:
                    NEW_ID = int(rgx_res.group(2))
                    if int(ShortId)!=NEW_ID:
                        self.mf.log.info(f"{ruta}, el ID: {NEW_ID}, es diferente al ShortID: {ShortId} ")
                        lista_nodop.append(["DIFERENTE SHORTID", ruta, NEW_ID, ShortId])
                else:
                    self.mf.log.info(f"{ruta}, el Name {dicc_ID[clave]['Name']} no cumple con el estandar, ShortId:[{ShortId}]")
                    lista_nodop.append(["NAME NO CUMPLE CON ESTANDAR", "", dicc_ID[clave]['Name'], ShortId])


        self.mf.log.info(
            "Inicia el proceso de validación al campo Descripción de los Synchronous Machine, no debe estar vacío"
        )
        for clave in dicc_ID.values():
            obj = network.dicc_arbol[clave['ID']]

            if obj.tipo != "SynchronousMachine":
                continue
            if obj.na_flag == False:
                continue

            """Valida Descricion"""
            if clave['Description'] =="":
                self.mf.log.error (f"Error en el atributo Description {obj.get_ta([])} está vacío.")
                lista_nodop.append(["DESCRIPCION VACIA", obj.get_ta([]), "", ""])
                continue
            else:
                if "Network/Companies/SIN" in obj.get_ta([]):
                    rgx_res = gen_SIN_rgx.search(clave['Description'])
                elif "Network/Companies/BCA" in obj.get_ta([]) or "Network/Companies/WECC" in obj.get_ta([]):
                    rgx_res = gen_BCA_rgx.search(clave['Description'])
                elif "Network/Companies/BCS" in obj.get_ta([]):
                    rgx_res = gen_BCS_rgx.search(clave['Description'])
#                else:
#                    rgx_res = gen_SIN_rgx.search(clave['Description'])
                if not rgx_res:
                    self.mf.log.info(f" {obj.get_ta([])}  no cumple con el estandar {clave['Description']} ")
                    lista_nodop.append(["DESCRIPCION NO CUMPLE CON ESTANDAR", obj.get_ta([]), clave['Description'], ""])
        df_nodop = pd.DataFrame(lista_nodop, columns=["State", "Path", "Element", "Aux"])
        nombre_hoja = "SynchronousMachine_NP"
        self.coleccion_df[nombre_hoja] = df_nodop

        network.reset_arbol()

    # def verificar_SynchronousMachine_NodePKey(self):    
    #     """Función que verifica que en los Busbarsection este correctamente definada la bandera NodoP y región de CTCP
    #     """
    #     archivo_id = path.join(self.mf.MAGEselected_path, "SynchronousMachine_id_nodePKey.csv")
    #     archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
    #     archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
    #     dicc_ID, _, _ = leer_csv(archivo_id, ["ID"])
    #     aux = set()
    #     network = crear_arbol_mage(archivo_equipos)
    #     aniadir_terminales(network, archivo_terminales)

    #     self.mf.log.info(
    #         "Inicia el proceso de validación de la bandera NodePKey"
    #     )
    #     lista_nop_SVC = []
    #     for clave in dicc_ID.keys():
    #         obj = network.dicc_arbol[dicc_ID[clave]['ID']]
    #         #print(dicc_ID[clave]['Name'])
    #         if obj.tipo == "SynchronousMachine" and obj.na_flag=='true':
    #             ruta = obj.get_ta([])
    #             #print(ruta)
    #             rgx_res = patronId.search(dicc_ID[clave]['Name'])
    #             if rgx_res:
    #                 if dicc_ID[clave]['nodePkey']=="" :
    #                     self.mf.log.info(f"{ruta}, definir un NodePkey para SynchronousMachine  {dicc_ID[clave]['Name']}")
    #                     lista_nop_SVC.append(["DEFINIR NODOP", dicc_ID[clave]['Name']])
    #             else:
    #                 if dicc_ID[clave]['nodePkey']=="":
    #                     self.mf.log.info(f"{ruta}, el Synchronous Machine NodeP key deberá ser 'NA'")
    #                     lista_nop_SVC.append(["KEY DEBE SER NA", ruta])
    #     df_nodop_SVC = pd.DataFrame(lista_nop_SVC, columns=["State", "Path"])
    #     print(df_nodop_SVC)
    #     nombre_hoja = "StaticVarCompensator_NP"

    #     self.coleccion_df[nombre_hoja] = df_nodop_SVC


    #     network.reset_arbol()


    def verificar_StaticVarCompensator_NodePkey(self):
        """Función que verifica que en los Busbarsection este correctamente definada la bandera NodoP y región de CTCP
        """
        fecha = datetime.today()

        archivo_svc = path.join(self.mf.MAGEselected_path, "StaticVarCompensator_id.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_SVC, _, _ = leer_csv(archivo_svc, ["ID"])
        aux = set()

        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        self.mf.log.info(
            "Inicia el proceso de validación del StaticVarCompensator NodeP key"
        )
        lista_nodop_SVC = []
        for clave in dicc_SVC.keys():
            obj = network.dicc_arbol[dicc_SVC[clave]['ID']]
            #print(dicc_SVC[clave]['Name'])
            if obj.tipo == "StaticVarCompensator" and dicc_SVC[clave]['NAFlag']=='true':
                ruta = obj.get_ta([])
                #print(ruta)
                self.mf.log.info(f"{ruta}, StaticVarCompensator NodeP key para {dicc_SVC[clave]['Name']}")   
                lista_nodop_SVC.append(["STATICVARCOMPENSATOR NODO P KEY", ruta, dicc_SVC[clave]['Name']])
        df_nodop_SVC = pd.DataFrame(lista_nodop_SVC, columns=["State", "Path", "Key"])
        nombre_hoja = "StaticVarCompensator_NP"

        self.coleccion_df[nombre_hoja] = df_nodop_SVC 
        network.reset_arbol()

    def verificar_ShuntCompensator_ID(self):
        """Función que verifica el PSS/e ShortId de los ShuntCompensator
        """
        archivo_id = path.join(self.mf.MAGEselected_path, "ShuntCompensator_id.csv")
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")

        dicc_ID, _, _ = leer_csv(archivo_id, ["ID"])
        network = crear_arbol_mage(archivo_equipos)
        aniadir_terminales(network, archivo_terminales)
        self.mf.log.info("Verificando PSS/E SHORT ID de ShuntCompensator.")
        aux = defaultdict(set)
        lista_shunt = []
        for clave in dicc_ID.keys():
            obj = network.dicc_arbol[dicc_ID[clave]['ID']]
            if obj.tipo == "ShuntCompensator":
                ruta = obj.get_ta([])
                ShortId=dicc_ID[clave]['ShortID']
                rgx_res = patron.search(dicc_ID[clave]['Name'])
                if rgx_res:
                    NEW_ID=(rgx_res.group(1)[0]+str(int(rgx_res.group(2))))
                    if ShortId!=NEW_ID:
                        self.mf.log.info(f"{ruta}, el ID: {NEW_ID}, es diferente al ShortID: {ShortId} ")
                        lista_shunt.append(["ID DIFERENTE AL SHORTID", "", NEW_ID, ruta, ShortId])
                else:
                    self.mf.log.info(f"{ruta}, Verificar estandar en el nombre del equipo {dicc_ID[clave]['Name']} con ShortId: {ShortId}")
                    lista_shunt.append(["VERIFICAR ESTANDAR ENE L NOMBRE DEL EQUIPO", dicc_ID[clave]['Name'],"", ruta, ShortId])
        df_shunt = pd.DataFrame(lista_shunt, columns = ["State", "Element", "ID","Path", "ShortID"])

        nombre_hoja = "ShuntCompensator_ID"
        self.coleccion_df[nombre_hoja] = df_shunt
        network.reset_arbol()

    def verificar_SynchronousMachine_PI_TAGs(self):
        """Esta función obtiene los PI TAGS de las unidades generadoras
"""
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_synchronous_machine = path.join(self.mf.MAGEselected_path, "SynchronousMachine.csv")
        archivo_link_synchronous_machine = path.join(self.mf.MAGEselected_path, "synchmachine_reg_terminal.csv")
        archivo_analog_se_terminal = path.join(self.mf.MAGEselected_path, "AnalogValue_AnalogSE_Terminal.csv")
        network = crear_arbol_mage(archivo_equipos)

        dicc_synchronous_machine, _, _ = leer_csv(archivo_synchronous_machine, ["ID"])
        dicc_link_synchronous_machine, _, _ = leer_csv(archivo_link_synchronous_machine, ["ID"])
        dicc_analog_se_terminal, _, _ = leer_csv(archivo_analog_se_terminal, ["ID"])

        aux = set()
        self.mf.log.info(
            "Inicia el proceso para obtener los PI TAGS de las SynchronousMachine"
        )
        lista_PITAGS = []
        for clave in dicc_synchronous_machine.values():
            flg=True
            tot_uce=len(dicc_synchronous_machine)
            obj = network.dicc_arbol[clave["ID"]]
            fecha = datetime.today()
    
            if obj.tipo != "SynchronousMachine":
                continue
            if obj.na_flag == False:
                continue
            # Encontrar clave
            #print(clave['ID'])
            #for aux_clv in list(dicc_link_synchronous_machine.keys()):
            #    if clave['ID'] in aux_clv:
            #        print('Clave encontrada',aux_clv[0], clave['ID'])
            #        print(dicc_link_synchronous_machine[aux_clv]['Description'])
            # End encontrar clave
            for key, valor in dicc_analog_se_terminal.items():
                if clave['ID'] != valor['Terminal_Parent']:
                    continue
                elif valor['MeasurementType'] != 'Real power':
                    continue
                else:
                    for aux_clv in list(dicc_link_synchronous_machine.keys()):
                        if clave['ID'] in aux_clv:
                            #print('Clave encontrada',aux_clv[0], clave['ID'])
                            #print(dicc_link_synchronous_machine[aux_clv]['Description'])
                            descripcion=dicc_link_synchronous_machine[aux_clv]['Description']
                            break

                    flg=False
                    if valor['AnalogValue_PITagName']!="":
                        self.mf.log.info(
                            f"UCE: {clave['ReactiveCapabilityCurve_Name']}, {descripcion},PI_TAG: {valor['AnalogValue_PITagName']},{valor['IncludeInSE']}, {valor['MeasurementType']}"
                        )
                        lista_PITAGS.append(["INFO", clave['ReactiveCapabilityCurve_Name'], descripcion, valor['AnalogValue_PITagName'], valor['IncludeInSE'], valor['MeasurementType']])
                    else:
                        self.mf.log.warning(f"Medición sin TAG. UCE: {clave['ReactiveCapabilityCurve_Name']}, {descripcion},  PI_TAG: {valor['AnalogValue_PITagName']}, {valor['IncludeInSE']}, {valor['MeasurementType']}")
                        lista_PITAGS.append(["MEDICION SIN TAG UCE", clave['ReactiveCapabilityCurve_Name'], descripcion, valor['AnalogValue_PITagName'], valor['IncludeInSE'], valor['MeasurementType']])
            if flg:
                for aux_clv in list(dicc_link_synchronous_machine.keys()):
                    if clave['ID'] in aux_clv:
                        descripcion=dicc_link_synchronous_machine[aux_clv]['Description']
                        self.mf.log.error(f"No existe medición para la UCE: {clave['ReactiveCapabilityCurve_Name']}, {descripcion}")
                        lista_PITAGS.append(["NO EXISTE MEDICION PARA LA UCE", clave['ReactiveCapabilityCurve_Name'], descripcion, "","",""])
        nombre_hoja = "SynchronousMachine_PI_TAGs"
        df_pitags = pd.DataFrame(lista_PITAGS, columns=["State", "ReactiveCapabilityCurve_Name", "Description", "AnalogValue_PITagName", "IncludeInSE", "MeasurementType"])
        self.coleccion_df[nombre_hoja] = df_pitags
        network.reset_arbol()

    def verificar_busbarsection_by_voltagelevel(self):
        """Esta función verifica que exista al menos un busbarsection por nivel de tensión
        en cada subestación.
        """
        #import pdb;pdb.set_trace()
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_terminales = path.join(self.mf.MAGEselected_path, "Terminal.csv")
        network = crear_arbol_mage(archivo_equipos)

        self.mf.log.info(
            "Inicia el proceso de validación de BusbarSection por subestación y nivel de tensión"
        )
        lista_buses = []
        for obj in network.dicc_arbol.values():
            if obj.tipo != "Substation":
                continue
            if obj.na_flag==False:
                continue
            #pdb.set_trace()
            for nivel_voltage in obj.hijos:
                if nivel_voltage.tipo != "VoltageLevel":
                    continue
                flg = True
                for busbar_sections in nivel_voltage.hijos:
                    if busbar_sections.tipo == "BusbarSection":
                        flg = False
                        break
                if flg:
                    flg2=False
                    for connectivity_node in nivel_voltage.hijos:
                        if connectivity_node.tipo == "ConnectivityNode":
                            flg2 = True
                            break
                    if flg2:
                        self.mf.log.error(
                            f"El siguiente elemento no tiene busbarsection {nivel_voltage.get_ta([])}"
                        )
                        lista_buses.append(["SIN BUSBARSECTION" , nivel_voltage.nombre, nivel_voltage.get_ta([])])
                    else:
                        self.mf.log.warning(
                            f"El siguiente elemento no tiene busbarsection {nivel_voltage.get_ta([])}"
                        )
                        lista_buses.append(["SIN BUSBARSECTION" , nivel_voltage.nombre, nivel_voltage.get_ta([])])
        nombre_hoja = "Busbar_VoltageLevel"
        df_buses = pd.DataFrame(lista_buses, columns=["State", "BusBar", "Path"])
        self.coleccion_df[nombre_hoja] = df_buses
        network.reset_arbol()

    def verificar_pssebusBoundary_SeriesCompensator(self):
        """Esta función verifica que exista al menos un busbarsection por nivel de tensión
        en cada subestación.
        """
        #import pdb;pdb.set_trace()
        Powername_rgx = rgx_TR_name #re.compile(r'((T|AT)-(\d){2})(.*(\d{2,3}\/\d{2,3}|.*))')


        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        network = crear_arbol_mage(archivo_equipos)

        dicc_aux = defaultdict(valor_defecto1)

        #Validar los niveles de tension
        df = pd.DataFrame()
        for obj in network.dicc_arbol.values():
            # print(obj)

            if obj.tipo != "PowerTransformer":
                continue
            if obj.na_flag==False:
                continue
            #print(obj.nombre)

            rgx_res = Powername_rgx.search(obj.nombre)
            str_name = str(obj.nombre)

            if rgx_res:
                # print(rgx_res)
                old_name = str(obj.nombre)
                # tipo = rgx_res.group(1)
                # print(rgx_res.group(0))
                # relacion = rgx_res.group(4)
                new_name = ""#str(obj.get_subestacion()[0:2] + obj.get_subestacion()[-3:] + " " + tipo.replace("-","") + " " + relacion.replace(" ",""))
                self.mf.log.info(
                    f"{obj.id}, {obj.get_ta([])}, {old_name}, {new_name}"
                )
            else:
                print(rgx_res)
                self.mf.log.warning(
                    f"{obj.id}, {obj.get_ta([])}, {str_name}"
                )
        
        network.reset_arbol()

    def new_TR_names(self):
        """Esta función crea la lista de los nuevos nombres de los transformadores segun
        un nuevo estandar.
        """
        archivo_equipos = path.join(self.mf.MAGEselected_path, "equipos.csv")
        archivo_transformadores = path.join(self.mf.MAGEselected_path, "PowerTransformer_ID.csv")
        network = crear_arbol_mage(archivo_equipos)
        
        new_name = []
        new_list = []

        dicc_base_trs, _, _ = leer_csv(archivo_transformadores, ["ID"])
        for clave in dicc_base_trs.values():
            tr_name = network.dicc_arbol[clave["ID"]]
            # print(tr_name.nombre)

            if tr_name.na_flag == False:
                continue
            # if ("ERC" in tr_name.get_ta([])) | ("BEL" in tr_name.get_ta([])) | ("GUA" in tr_name.get_ta([])):
            #     continue

            if tr_name.nombre == "":
                self.mf.log.error (f'Error en el nombre del PowerTransformer {tr_name.get_ta([])} esta vacio.')
                continue
            else:
                # print(clave["Name"])
                # print(rgx_TR_name.search(clave["Name"]))
                if not (rgx_TR_name.search(clave["Name"])) and not (rgx_TR_name2.search(clave["Name"])):
                    self.mf.log.warning(f" {tr_name.get_ta([])} no cumple con el estandar {tr_name.nombre}")

                    # tr_name.get_ta = clave["ID"]
                    # print(tr_name)
                    new = tr_name.get_ta([]).split('/')
                    path_edit = new[4]#+new[6:8]
                    new[4] = path_edit[:2] + path_edit[5:]
                    new[5] = new[5].replace("-","")
                    new_list = new[4]+ " " +new[5]
                    new_path = tr_name.get_ta([]).split("/")
                    new_cadena = "/".join(new_path[:-1])

                    new_name.append([new_cadena,tr_name.nombre,new_list,tr_name.tipo])

        nombre_hoja = "TR_Name"
        df_TR_Name = pd.DataFrame(new_name)
        nombre_col = {0:"Path",1:"OldName",2:"Name",3:"ObjectType"}
        df_TR_Name = df_TR_Name.rename(columns=nombre_col)
        df_TR_Name["Name"] = np.nan
        self.coleccion_df[nombre_hoja] = df_TR_Name
        
        network.reset_arbol()
        
        
    def verificar_BusNumber_BusName_Marker(self):
        """Esta función obtiene los buses con BusNumber repetido
        """
        archivo_BusNameMarker = path.join(self.mf.MAGEselected_path, "BusNameMarker.csv")
        archivo_BusNameMarker_num = path.join(self.mf.MAGEselected_path, 'BusNameMarker_num.csv')
        # Leer el archivo CSV de entrada
        with open(archivo_BusNameMarker, 'r', newline='') as f:
            reader = csv.reader(f)
            filas = list(reader)
        # Agregar un encabezado y numerar las filas
        encabezado = ['Elemento'] + filas[0]  # Agregar encabezado a la primera fila
        filas_con_numeros = [encabezado]  # Inicializar lista con encabezado
        for i, fila in enumerate(filas[1:], start=1):  # Empezar desde la segunda fila
            fila_con_numero = [i] + fila  # Añadir número de fila al inicio de cada fila
            filas_con_numeros.append(fila_con_numero)
        with open(archivo_BusNameMarker_num, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(filas_con_numeros)
        
        dicc_BusNameMarker, _, _ = leer_csv(archivo_BusNameMarker_num, ["Elemento"])
        
        aux = set()

        self.mf.log.info(
            "Los BusNameMarkers sin BusNumber son:"
        )
        lista_bnm = []
        aux = defaultdict(valor_defecto1)
        for clave in dicc_BusNameMarker.values():
            if clave["BusNumber"] == "":
                self.mf.log.warning(f"BusNameMarker sin BusNumber: {clave['Name'], clave['Path']}")
                lista_bnm.append(["BNM SIN BUSNUMBER", clave["Name"], clave["BusNumber"], clave["Path"]])
                continue
            key = (clave['Name'])
            aux[key].append((clave["BusNumber"],clave["Path"],clave["Name"],clave["ConnectivityNode_Path"]))
        # print(aux["04   HLU-7B"])

        self.mf.log.info(
            "Inicia el proceso buscando nodos con Número de Bus repetido"
        )
        
        new_aux = []
        new_aux2 = []
        new_aux3 = []
        
        #BusNumber Repetidos
        for key, value in aux.items():
            new_aux.append(value[0][0])
            if new_aux.count(value[0][0]) > 1:
                new_aux2.append(value[0])
            lista_plana2 = [elemento for sublista in new_aux2 for elemento in sublista]
            
        #BusNameMarker repetido
        for key, value in aux.items():
            new_aux.append(value[0][2])
            if len(value) > 1:
                for elm in value:
                    new_aux3.append(elm[3])
            lista_plana3 = new_aux3
        
        self.mf.log.info("Corregir el BusNameMarker.")
        for key, value in aux.items():
            if value[0][0] in lista_plana2:
                self.mf.log.error(f"BusNumber repetido (BusNameMarker, BusNumber): {key, value[0][0]}")
                lista_bnm.append(["BUSNUMBER REPETIDOS", key, value[0][0], value[0][1], value[0][3]])
            for tupla in value:
                if tupla[3] in lista_plana3:
                    self.mf.log.error(f"BusNameMarker repetido (BusNameMarker, BusNumber): {key, tupla[0]}")
                    lista_bnm.append(["BUSNAMEMARKER REPETIDOS", key, tupla[0], tupla[1], tupla[3]])
        nombre_hoja = "BusNameMarker_BusNumber"
        df_bnm = pd.DataFrame(lista_bnm, columns= ["State", "Element", "BusNumber", "Path", "ConnectivityNode_Path"])
        self.coleccion_df[nombre_hoja] = df_bnm
        
        return dicc_BusNameMarker