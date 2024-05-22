#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Proyecto: Actualización del verificador_mage
-Verificador de JOBS, archivos .xml
"""

__author__ = "Victor Hernandez"
__copyright__ = "CENACE, 2024"
__credits__ = ["USO"]
__version__ = "2.0.1"
__maintainer__ = "Victor Hugo Hernandez"
__email__ = "hugo.hernandez@cenace.gob.mx"
__status__ = "Prototype"

from threading import Thread
from typing import Any
import wx
from os import path
from glob import glob

import logging

log = logging.getLogger("verificador_imm_MAGE")
log.setLevel(logging.INFO)

#Seccion de threads
class PreprocesadorArchivos(Thread):
    
    def __init__(self, mf):
        Thread.__init__(self)
        self.mf = mf
        self.mf.path = self.mf.MAGE_pathSel.GetPath()
        
    """Convierte los archivos *.csv que se exportan desde IMM-MAGE a un formato
    csv más tradicional.

    Los archivos csv que se transforman son todos aquellos en la ruta
    establecida en la variable carpeta_insumos.
    """
    # def __init__(self, mf):
    #     Thread.__init__(self)
    #     self.mf = mf
    #     self.ruta_base = path.abspath(path.join(__file__, "../.."))
    #     self.ruta_data_aux = path.join(self.ruta_base,"data")
        
        # print(self.carpeta_insumos)
    # def __call__(self):
    #     self.run()
        
    
    # def set_directory(self, path):
    #     print(self.ruta_data_aux)
    #     # print("-----",path)
    #     # ruta_consulta =
    #     if self.ruta_data_aux != path:
    #         self.ruta_data_aux = path
    #         # print("Entra: ",path)
    #     else:
    #         # print("Entra: ",path)
    #         print("La ruta de consulta es: ", self.ruta_data_aux)

    def inicializar_thread(self, event, thread, comentario):
        """Inicializa un thread"""
        if self.worker is None:
            self.SetStatusText(comentario)
            self.worker = thread(self)
            self.worker.start()
        else:
            self.SetStatusText('Proceso ocupado, espere a finalizar el anterior.')


            
    def run(self):
        self.ruta_data = self.mf.path
        # print(self.ruta_data)
        if path.isdir(self.ruta_data) == False:
            mensaje = (
                f"La carpeta elegida no es una carpeta válida:{self.ruta_data}"
            )
            dial = wx.MessageDialog( None, mensaje, "", wx.OK | wx.ICON_ERROR)
            dial.ShowModal()
            self.mf.SetStatusText("Carpeta inválida, no se procesaron los archivos")
            self.mf.worker = None
            return None
        for file in glob(path.join(self.ruta_data, "*.csv")):
            encabezado, cuerpo = get_encabezados(file)
            if encabezado is not None:
                replace_csv_format(file, encabezado, cuerpo)
                self.mf.GetLogger().info(f"Se procesó el archivo {file}")
        self.mf.SetStatusText("Terminó la actividad")
        self.mf.worker = None

#Seccion de funciones adicionales
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