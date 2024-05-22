from usolibpy.otros import leer_csv
from collections import defaultdict
import networkx as nx
from os import path
import logging
import pandas as pd
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SP7Object():
    """Esta clase tiene como objetivo crear un objeto para manipular el arbol de
    TNA de SP7.

    Attributes
    ----------
    nombre: str
        Nombre del objeto
    tipo: str
        Nombre de la tabla de donde se extrajo el elemento de mage.
    id: str
        RFID de mage que le corresponde al objeto.
    num_terminales: int(opcional)
        Número de terminales que tiene el objeto. El valor por defecto es cero.
    na_flag: bool(opcional)
        Bandera que indica si el objeto esta activo para TNA. El valor por defecto
        es verdadero.
    nodo_conectividad: None o str(opcional)
        RFID del nodo de conectividad asociado al elemento, solo los objetos del
        tipo terminal pueden tener poblado este elemento.
    hijos: list
        Lista de los objetos de SP7 hijos de este objeto.
    padre: str (opcional)
        RFID del objeto padre. El valor por defecto es None. Cuando el padre se
        deja sin poblar se considera el objeto padre de mayor jerarquía.
    """
    TIPOS_VALIDOS = [
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

    PADRES_HIJOS_PERMITIDOS = [
        ("sysNetworkCategory", "sysNetCompanies"),
        ("sysNetworkCategory", "sysNetworkConfig",),
        ("sysNetworkCategory", "sysGenPowerPlants"),
        ("sysNetworkConfig", "BaseVoltage"),
        ("sysNetCompanies", "GeographicalRegion"),
        ("SubGeographicalRegion", "Substation"),
        ("SubGeographicalRegion", "LineVoltageLevel"),
        ("Substation", "VoltageLevel"),
        ("Substation", "PowerTransformer"),
        ("VoltageLevel", "ConnectivityNode"),
        ("VoltageLevel", "BusbarSection"),
        ("BusbarSection", "Terminal"),
        ("VoltageLevel", "SynchronousMachine"),
        ("SynchronousMachine", "Terminal"),
        ("SynchronousMachine", "SteamTurbine"),
        ("VoltageLevel", "StaticVarCompensator"),
        ("StaticVarCompensator", "Terminal"),
        ("VoltageLevel", "ConformLoad"),
        ("ConformLoad", "Terminal"),
        ("VoltageLevel", "NonConformLoad"),
        ("NonConformLoad", "Terminal"),
        ("VoltageLevel", "ShuntCompensator"),
        ("ShuntCompensator", "Terminal"),
        ("VoltageLevel", "Disconnector"),
        ("Disconnector", "Terminal"),
        ("VoltageLevel", "GroundDisconnector"),
        ("GroundDisconnector", "Terminal"),
        ("VoltageLevel", "Breaker"),
        ("Breaker", "Terminal"),
        ("VoltageLevel", "SeriesCompensator"),
        ("SeriesCompensator", "Terminal"),
        ("PowerTransformer", "TransformerWinding"),
        ("ComplexTransformer", "TransformerWinding"),
        ("TransformerWinding", "Terminal"),
        ("TransformerWinding", "TapChanger"),
        ("LineVoltageLevel", "ACLineSegment"),
        ("ACLineSegment", "Terminal"),
        ("sysNetworkCategory", "ReactiveCapabilityCurve"),
        ("ReactiveCapabilityCurve", "CurveData"),
        ("sysGenPowerPlants", "CombinedCyclePlant"),
        ("sysGenPowerPlants", "HydroPowerPlant"),
        ("sysGenPowerPlants", "SolarPlant"),
        ("sysGenPowerPlants", "WindPlant"),
        ("sysGenPowerPlants", "ThermalPowerPlant"),
        ("WindPlant", "WindGeneratingUnit"),
        ("SolarPlant", "SolarGeneratingUnit"),
        ("HydroPowerPlant", "HydroGeneratingUnit"),
        ("CombinedCyclePlant", "ThermalGeneratingUnit"),
        ("CombinedCyclePlant","CombinedCycleConfiguration"),
        ("ThermalPowerPlant", "ThermalGeneratingUnit"),
        ("ThermalGeneratingUnit", "IncrementalHeatRateCurve"),
        ("HydroGeneratingUnit", "HydroPowerDischargeCurve"),
        ("HydroPowerDischargeCurve", "CurveData"),
        ("IncrementalHeatRateCurve", "CurveData"),
    ]

    dicc_arbol = {}
    grafo = None

    def __init__(self, nombre, _id, tipo, na_flag=True, scada_flag=True, num_terminales=0,
        nodo_conectividad=None, padre=None):
        assert tipo in self.TIPOS_VALIDOS
        assert _id not in self.dicc_arbol
        self.nombre = nombre
        self.id = _id
        self.tipo =  tipo
        self.na_flag = na_flag
        self.scada_flag = scada_flag
        self.num_terminales = num_terminales
        self.hijos = []
        self.padre = padre
        SP7Object.dicc_arbol[self.id] = self
        self.name_marker = None
        self.st_flag = False
        self.liga_a_curva_capabilidad = None
        self.liga_a_synchronous_machine = None
        self.liga_a_generating = None
        self.subtipo = None
        self.link_base_voltage = None
        self.link_a_terminal_regulada = None
        self.regulacion_flag = False
        self.X = None
        self.Y1 = None
        self.Y2 = None
        self.agc_flag = False
        self.x_pu = None
        self.r_pu = None
        self.b_pu = None
        if tipo == "Terminal":
            self.nodo_conectividad = nodo_conectividad
        else:
            self.nodo_conectividad = None
        self.colec_equipo = {}
        self.lista_equipo = []
        self.lista_dic = []
        # self.df_equipo =pd.DataFrame()

    def reset_arbol(self):
        SP7Object.dicc_arbol = {}


    def __str__(self):
        mensaje = (
            f"Objeto del tipo: {self.tipo}\n"
            f"Nombre: {self.nombre}\n"
            f"Número de hijos: {len(self.hijos)}\n"
            f"NAFlag: {self.na_flag}\n"
            f"SCADAFlag: {self.scada_flag}\n"
            f"ID: {self.id}\n"
            f"Padre: {self.padre}\n"
            f"Path: {self.get_ta([])}\n"
            f"BusNameMarker: {self.name_marker}\n"
        )
        return mensaje


    def add_hijo(self, hijo):
        """Agrega un hijo al objeto SP7Object.

        Los hijos deben ser SP7Objects y se deben cumplir las reglas de asignación.
        La estructura permitida es la siguiente:
        Network
        |-> GeographicalRegion
            |->SubGeographicalRegion
               |->Subestation
               |  |->VoltajeLevel
               |  |  |->ConnectivityNode (Max num hijos = 0)
               |  |  |->BusbarSection (Max num hijos = 1)
               |  |  |  |->Terminal
               |  |  |->SynchronousMachine (Max num hijos = 1)
               |  |  |  |->Terminal
               |  |  |->StaticVarCompensator (Max num hijos = 1)
               |  |  |  |->Terminal
               |  |  |->ConformLoad (Max num hijos = 1)
               |  |  |  |->Terminal
               |  |  |->NonConformLoad (Max num hijos = 1)
               |  |  |  |->Terminal
               |  |  |->ShuntCompensator (Max num hijos = 1)
               |  |  |  |->Terminal
               |  |  |->Disconnector (Max num hijos = 2)
               |  |  |  |->Terminal
               |  |  |->Breaker (Max num hijos = 2)
               |  |  |  |->Terminal
               |  |  |->SeriesCompensator (Max num hijos = 2)
               |  |  |  |->Terminal
               |  |  |->GroundDisconnector (Max num hijos = 1)
               |  |     |->Terminal
               |  |->PowerTransformer (Max num hijos = 2)
               |  |  |->TransformerWinding
               |  |     |->Terminal
               |  |     |->TapChanger
               |  |->ComplexTransformer (Max num hijos = 2)
               |     |->TransformerWinding
               |        |->Terminal
               |        |->TapChanger
               |->LineVoltajeLevel
                  |->ACLineSegment (Max num hijos = 2)
                     |->Terminal
        """
        assert isinstance(hijo, SP7Object)
        hijo.padre = self.id
        self.hijos.append(hijo)


    def get_ta(self, ruta = []):
        """Obtiene el path del objeto, esto lo logra por medio de recursividad
        hasta llegar a un objeto cuyo padre sea None.

        Parameters
        ----------
        ruta: Lista
            Lista vacia donde de forma recursiva se va poblando el path.
        """
        ruta.append(self.nombre)
        if self.padre is None:
            return "/".join(ruta[-1::-1])
        else:
            padre = self.dicc_arbol[self.padre]
            return padre.get_ta(ruta)

    def get_voltaje_level(self):
        """Obtiene el nivel de tension asociado a un elemento, esto lo logra por
        medio de recursividad hasta llegar a un objeto cuyo padre sea None o se
        llegue al nivel de tension.
        """
        if self.tipo == "VoltageLevel":
            return float(self.nombre)
        if self.padre is None:
            return None
        else:
            padre = self.dicc_arbol[self.padre]
            return padre.get_voltaje_level()

    def get_highest_parent(self):
        """Obtiene el padre de mayor jerarquia a partir de objeto de busqueda"""
        if self.padre is None:
            return self
        else:
            padre = self.dicc_arbol[self.padre]
            return padre.get_highest_parent()

    def get_subestacion(self, use_name_marker=True):
        """Obtiene la subestación en la que esta anidado un objeto.

        Este método no es válido para los tipos "Companies", "GeographicalRegion",
        "SubGeographicalRegion", "LineVoltageLevel", "ACLineSegment"

        Parameters
        ----------
        use_name_marker: bool
            Bandera que indica si se usa el BusNameMarker o no.
        """
        if self.tipo in ["Companies", "GeographicalRegion","SubGeographicalRegion",
            "LineVoltageLevel", "ACLineSegment"]:
            return None
        if self.tipo == "ConnectivityNode" and use_name_marker:
            if self.name_marker is not None:
                return self.name_marker
        if self.tipo == "Substation":
            return self.nombre
        else:
            if self.padre is None:
                return None
            else:
                padre = self.dicc_arbol[self.padre]
                return padre.get_subestacion()

    def get_subestaciones_linea(self):
        """Obtiene las subestaciones a las que esta ligada una línea de transmision.
        """
        if self.tipo not in ["ACLineSegment", "SeriesCompensator"]:
            return None
        if self.na_flag is False:
            return None
        #Obtenemos los buses de conectividad anidados en la linea de transmisión
        nodos_conectividad = set()
        for hijo in self.hijos:
            if hijo.tipo != "Terminal":
                continue
            if hijo.nodo_conectividad is None:
                continue
            nodos_conectividad.add(hijo.nodo_conectividad)
        #Todas las lineas encontradas deben tener solo dos nodos de conectividad
        assert len(nodos_conectividad) == 2
        return [self.dicc_arbol[x].get_subestacion() for x in nodos_conectividad]

    def get_connectivity_nodes(self, use_na_flag=True, nodos=set()):
        """Obtiene los nodos anidados a los objeto de busqueda.

        Parameters
        ----------
        use_na_flag: bool
            Bandera que indica si se toma en cuenta la bandera na_flag o no. En
            caso de que se tome en cuenta, solo se retornaran los buses cuya ruta
            desde el objeto base hasta la terminal tiene todos sus elementos con
            la bandera na_flag activa.
        nodos: set
            Conjunto donde se almacenan los buses encontrados.
        """
        if use_na_flag:
            if self.nodo_conectividad is not None and self.na_flag and self.nodo_conectividad != "":
                nodos.add(self.nodo_conectividad)
            if self.na_flag:
                for hijo in self.hijos:
                    hijo.get_connectivity_nodes(use_na_flag, nodos)
        else:
            if self.nodo_conectividad is not None and self.nodo_conectividad != "":
                nodos.add(self.nodo_conectividad)
            for hijo in self.hijos:
                hijo.get_connectivity_nodes(use_na_flag, nodos)
        return nodos

    def add_bus_name_marker(self, nombre):
        """Pobla el campo bus_name_marker del objeto si el tipo es ConnectivityNode.

        Parameters
        ----------
        nombre: str
            Nombre que se usa en lugar del nombre de la subestación en el archivo raw.
        """
        if self.tipo != "ConnectivityNode":
            return None
        self.name_marker = nombre

    def add_ramas_grafo(self, elementos_conectividad, use_na_flag=True):
        """Añade las ramas al grafo para los elementos de conectividad

        Parameters
        ----------
        elementos_conectividad: set
            Conjunto de elementos de dos terminales definidos como elementos de
            conectividad.
        use_na_flag: bool
            Bandera que indica si se toma el cuenta la na_flag para incorporar un
            elemento al estudio o no.
        """
        # print(self.colec_equipo)
        coleccion_equipo = {}
        # lista_equipo = []
        df_equipo1 =pd.DataFrame(columns=["Path", "CN", "Element", "NAFlag", "State"])
        columns = ["Path"]
        # for hijo in self.hijos:
        if use_na_flag:
            if self.na_flag:
                for hijo in self.hijos:
                    if hijo.tipo in elementos_conectividad:
                        nodos = hijo.get_connectivity_nodes(use_na_flag, nodos=set())
                        if len(nodos) == 2:
                            _from, _to = list(nodos)
                            _from_st_flag  = self.dicc_arbol[_from].st_flag
                            _to_st_flag  = self.dicc_arbol[_to].st_flag
                            if _from_st_flag and _to_st_flag:
                                SP7Object.grafo.add_edge(_from, _to)
                            else:
                                logger.warning (f"Equipo [{hijo.get_ta([])}] no agregado porque al menos uno de sus buses de conectividad no es elegible. Tipo equipo: {hijo.tipo}, NAFlag: {hijo.na_flag}")
                                self.lista_equipo.append([hijo.get_ta([]), "", hijo.tipo, hijo.na_flag, "BUS NO ELEGIBLE"])
                                # df_equipo1 = pd.DataFrame(self.lista_equipo, columns=["Path", "CN", "Element", "NAFlag", "State"])
                                # coleccion_equipo[hijo.nombre] = df_equipo1
                                # print("1")
                        else:
                            logger.warning (f"Equipo [{hijo.get_ta([])}] no agregado porque solo tiene {len(nodos)} buses de conectividad asociado. Tipo equipo: {hijo.tipo}, NAFlag: {hijo.na_flag}")
                            self.lista_equipo.append([hijo.get_ta([]), len(nodos), hijo.tipo, hijo.na_flag, "CN ASOCIADOS"])
                    else:
                        aux = hijo.add_ramas_grafo(elementos_conectividad, use_na_flag)
                        # print(aux)

        else:
            for hijo in self.hijos:
                if hijo.tipo in elementos_conectividad:
                    nodos = hijo.get_connectivity_nodes(use_na_flag, nodos=set())
                    if len(nodos) == 2:
                        _from, _to = list(nodos)
                        _from_st_flag  = self.dicc_arbol[_from].st_flag
                        _to_st_flag  = self.dicc_arbol[_to].st_flag
                        if _from_st_flag and _to_st_flag:
                            SP7Object.grafo.add_edge(_from, _to)
                        else:
                            logger.warning (f"Equipo [{hijo.get_ta([])}] no agregado porque al menos uno de sus buses de conectividad no es elegible. Tipo equipo: {hijo.tipo}, NAFlag: {hijo.na_flag}")
                            # self.lista_equipo.append([hijo.get_ta([]), "", hijo.tipo, hijo.na_flag, "BUS NO ELEGIBLE"])
                            # df_equipo1 = pd.DataFrame(self.lista_equipo, columns=["Path", "CN", "Element", "NAFlag", "State"])
                            # coleccion_equipo[hijo.nombre] = df_equipo1
                            # print("3")

                    else:
                        logger.warning (f"Equipo [{hijo.get_ta([])}] no agregado porque solo tiene {len(nodos)} buses de conectividad asociado. Tipo equipo: {hijo.tipo}, NAFlag: {hijo.na_flag}")
                        # self.lista_equipo.append([hijo.get_ta([]), len(nodos), hijo.tipo, hijo.na_flag, "CN ASOCIADOS"])
                        # df_equipo1 = pd.DataFrame(self.lista_equipo, columns=["Path", "CN", "Element", "NAFlag", "State"])
                        # coleccion_equipo[hijo.nombre] = df_equipo1
                        # print("4")

                else:
                    hijo.add_ramas_grafo(elementos_conectividad, use_na_flag)
            # print(df_equipo1)
            # df_equipo1 = pd.DataFrame(self.lista_equipo)
            # # print(df_equipo1)

            # if df_equipo1.empty:
            #     continue
            # else:
            #     print(df_equipo1)
            #     # self.df_equipo = pd.concat([self.df_equipo, df_equipo1], ignore_index=True)

            #     coleccion_equipo[hijo.nombre] = df_equipo1
            #     # self.colec_equipo[hijo.nombre] = df_equipo1
            #     self.colec_equipo.update(coleccion_equipo)
            #     # print("1 ",hijo.nombre)
            #     # print(self.colec_equipo)
            #     # print("2 ",hijo.nombre)
            #     self.lista_dic.append(self.colec_equipo)
        # self.colec_equipo.update(coleccion_equipo)
        # print(self.self.lista_dic)

        return self.colec_equipo

    def get_buses_aislados(self):
        """Obtiene un listado de los buses que no estan asociados a ningun
        elemento del tipo terminal.
        """
        nodos_conectividad = {x.id for x in self.dicc_arbol.values() if x.tipo == "ConnectivityNode"}
        nodos_asociados = {x.nodo_conectividad for x in self.dicc_arbol.values() if x.tipo == "Terminal"}
        return nodos_conectividad - nodos_asociados

    def consultar_status(self):
        """Determina para un nodo de conectividad si todo su arbol de conexión
        tiene activa la bandera na_flag.
        """
        if self.na_flag is False:
            return False
        if self.padre is None:
            return self.na_flag
        else:
            padre = self.dicc_arbol[self.padre]
            return padre.consultar_status()


    def crear_grafo(self, usar_na_flag=True, ignorar_buses_aislados=False):
        """Crea un grafo que representa la topología de la red.

        Parameters
        ----------
        usar_na_flag: bool(opcional)
            Bandera que indica si se toman solo los elementos cuya NAFlag
            esta activa durante todo el path. Este parametro es opcional y su
            valor por defecto es verdadero.
        """
        SP7Object.grafo = nx.Graph()
        padre = self.get_highest_parent()

        elementos_conectividad = {
            "Disconnector",
            "Breaker",
            "SeriesCompensator",
            "ACLineSegment",
            "PowerTransformer",
            "ComplexTransformer"
        }
        #Identificamos los buses que no tienen conectado ningun elemento
        buses_aislados = {}
        if ignorar_buses_aislados:
            buses_aislados = self.get_buses_aislados()
        #Añadimos los nodos al grafo
        for ele in (x for x in self.dicc_arbol.values() if x.tipo == "ConnectivityNode"):
            ele.st_flag = ele.consultar_status()
            if ele.id and ele.id not in buses_aislados:
                SP7Object.grafo.add_node(ele.id)

        #Añadimos las ramas al grafo
        # self.coleccion_equipo = {clave.nombre: None for clave.nombre in self.hijos}
        # print(self.coleccion_equipo)

        # lista_equipo = []
        col_equipo = padre.add_ramas_grafo(elementos_conectividad, usar_na_flag)
        print(col_equipo)
        return col_equipo

    def get_curva(self):
        """Obtiene la información de las curvas de datos para diferentes objetos"""

        if self.tipo not in ["HydroPowerDischargeCurve", "IncrementalHeatRateCurve", "ReactiveCapabilityCurve"]:
            return None
        out = set()
        for hijo in self.hijos:
            if hijo.tipo != "CurveData":
                continue
            out.add((hijo.X, hijo.Y1, hijo.Y2))
        return out

    def get_equipos_conectados_a_bus(self, bus):
        """Devuelve una lista de todos los equipos electricos cuya terminal esta
        conectada a un bus en especifico"""

        out = set()
        for obj in self.dicc_arbol.values():
            if obj.tipo != "Terminal":
                continue
            if obj.nodo_conectividad == bus:
                out.add(self.dicc_arbol[obj.padre])
        return out

    def get_parameters(self):
        """Devuelve los parametros electricos de un transformador"""
        if self.tipo not in ["PowerTransformer", "ComplexTransformer"]:
            return [], [], []
        r = []
        x = []
        b = []
        for hijo in self.hijos:
            if hijo.tipo != "TransformerWinding":
                continue
            if hijo.r_pu is not None:
                r.append(hijo.r_pu)
            if hijo.x_pu is not None:
                x.append(hijo.x_pu)
            if hijo.b_pu is not None:
                b.append(hijo.b_pu)
        return r, x, b





def crear_arbol_mage(archivo, force_na_flag=False):
    """Crea el arbol de mage a partir del archivo de equipos

    Parameters
    ----------
    archivo: str
        Ruta al archivo con la información de los equipos de mage.
    """
    network = SP7Object("Network", "_3a304648-8007-4a72-9f2c-ea4392803b98", "sysNetworkCategory")
    
    equipos_betados = {
        "_20c24fd7-a4d6-4856-b122-d9577d6f7d47", #Nivel de tension en SCADA Only
        "_2ab0c3da-941c-474e-a0ab-868b0f958b63", #ConnectivityNode en SCADA Only
        "_3d698d8d-05a8-4080-8d73-087980f752f6", #ConnectivityNode en SCADA Only
        "_9d971f22-94ef-4408-a050-7c22730b1586", #ConnectivityNode en SCADA Only
        "_738a6279-1746-4827-99f6-73f0e4bb8bae", #Cuchilla en SCADA Only
        "_782fb080-9ed9-46dd-8130-ef06464c95a8", #Interruptor en SCADA Only
        "_5E903B42-149E-4B6C-8B64-C6DF72010A69",
        "_59E7A955-A3A1-4FC8-8AA5-ECD9A4D43F6F",
        "_485E9643-28E0-46EF-9187-15BDAA7CA118",
    }
    #Separando la info de equipos por tipo de equipos
    dicc_equipos, _, _ = leer_csv(archivo, ["ID", "TableName"])
    aux_equipos = defaultdict(list)
    for clave in dicc_equipos.values():
        if clave["ID"] in equipos_betados:
            # print(clave)
            continue
        aux_equipos[clave["ObjectType"]].append(clave)

    orden_agregado = (
        "sysNetCompanies",
        "sysNetworkConfig",
        "sysGenPowerPlants",
        "GeographicalRegion",
        "SubGeographicalRegion",
        "Substation",
        "LineVoltageLevel",
        "VoltageLevel",
        "PowerTransformer",
        "ComplexTransformer",
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
        "TransformerWinding",
        "TapChanger",
        "ACLineSegment",
        "SteamTurbine",
        "ReactiveCapabilityCurve",
        "CombinedCyclePlant",
        "ThermalPowerPlant",
        "WindPlant",
        "SolarPlant",
        "HydroPowerPlant",
        "HydroGeneratingUnit",
        "SolarGeneratingUnit",
        "ThermalGeneratingUnit",
        "WindGeneratingUnit",
        "CombinedCycleConfiguration",
        "BaseVoltage",
        "IncrementalHeatRateCurve",
        "HydroPowerDischargeCurve",
        "CurveData",

    )
    #agregando las elementos al arbol_mage
    for tabla in orden_agregado:
        for reg in aux_equipos[tabla]:
            obj = network.dicc_arbol[reg["Parent"]]
            na_flag = False if reg["NAFlag"] == "false" else True
            if force_na_flag:
                na_flag=True
            obj.add_hijo(SP7Object(reg["Name"], reg["ID"], reg["ObjectType"], na_flag=na_flag))

    return network

def aniadir_terminales(sp7_object, ruta):
    """Añade los objetos del tipo terminal al arbol de mage

    Parameters
    ----------
    sp7_object: SP7Object
        Objeto de sp7 que contine el arbol de MAGE.
    archivo: str
        Ruta al archivo con la información de las terminales de mage.
    """
    equipos_betados = {
        "_1d1cf2c8-7ac1-4977-9ea6-35337ded7dcf", #Terminal en SCADA Only
        "_27da7f84-53ad-4f82-bc55-b2e6738b45b9", #Terminal en SCADA Only
        "_63f282e4-540b-48e4-ab66-2386c756b36e", #Terminal en SCADA Only
        "_856659c4-dd82-4d05-ad1d-efcaecad280a", #Terminal en SCADA Only
        "_20E610E8-C572-42CE-B2E5-637F9450551B",
        "_4941BEA1-DD5B-43C1-87E7-C186A5909A65",
        "_924A35AB-64AD-4D7B-9A60-E502D4378362",
        "_FDE56329-0D63-4CA1-BECA-3B16669738C9",
        "_F76F183B-BF35-4738-8416-5F442A332B78",
        "_21A344A3-C1B2-44AE-AF75-AADC24EEA182",
    }
    # #Agregar las terminale y los nodos de conectividad al arbol
    dicc_terminales, _, _ = leer_csv(ruta, ["ID"])
    for terminal in dicc_terminales.values():
        if terminal["ID"] in equipos_betados:
            # print(terminal['ID'])
            continue
        # print(terminal)
        obj = sp7_object.dicc_arbol[terminal["Parent"]]
        obj.add_hijo(
            SP7Object(
                terminal["Name"], terminal["ID"], terminal["ObjectType"],
                nodo_conectividad=terminal["TerminalConnectedToConnectivityNode_ConnectivityNode_ID"]
            )
        )
