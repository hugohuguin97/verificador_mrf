import matplotlib
import logging

from os import path, remove
from collections import defaultdict
from matplotlib.patches import Rectangle, Ellipse, Circle, Polygon
from usolibpy.rawfile import RAWFile2

log = logging.getLogger('VERIFICADOR')

      
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


def main():
  logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
  #rev_bus_area(r'C:\Documents and Settings\Uriel\Escritorio\30Dic\30Dic2015_09.raw', 0)
  # dt = datetime(2019, 4, 6)
  # ajustaEdoUnidades(r'D:\10356.CENACE\OneDrive - Centro Nacional de Control de Energia (CENACE)\CENACE\2019\MTR_EXP\SIN\07Abr2019\EDO_UNIDADES_07Abr2019.csv',
  #                  dt, 0)

def get_diccionario_equipos(rawfile):
  equipos_subestaciones = defaultdict(
      lambda: {
          'lineas':set(), 'transformadores': set(), 'generadores': set(),
          'cargas': set(), 'shunts': set(), 'sw_sunts': set()
      }
  )
  for bus in rawfile.getBus():
    sub = bus["MKT_KEY"][:5]
    num = bus["I"]
    info = rawfile.busInfoByNum(num)
    # print(info)
    if not info:
      log.warning(f"Subestacion sin informacion [{sub}, {num}, {info}]")
      continue
    del info["NOMBRE"]
    for llave, clave in info.items():
      equipos_subestaciones[(sub,num)][llave] |= set(clave)
  return equipos_subestaciones

def nivel_tension(voltaje):

  if 700 >= voltaje > 500:
    return "B"
  if 500 >= voltaje > 230:
    return "A"
  if 230 >= voltaje > 160:
    return "9"
  if 160 >= voltaje > 115:
    return "8"
  if 115 >= voltaje > 70:
    return "7"
  if 70 >= voltaje > 44:
    return "6"
  if 44 >= voltaje > 16.5:
    return "5"
  if 16.5 >= voltaje > 7:
    return "4"
  if 7 >= voltaje > 4.16:
    return "3"
  if 4.16 >= voltaje > 2.4:
    return "2"
  if 2.4 >= voltaje > 0:
    return "1"
    
def invertir_claves(claves):

  out = set()
  for clave in claves:
    aux = clave.split("   ")
    baskv = float(aux[2].split('-')[-1])
    letra = nivel_tension(baskv)
    out.add(f"{aux[2]}   {letra}{aux[1][1:]}   {aux[0]}")
  return out

def comparar_topologia(raw1, raw2, sistema, modo_raw1=1, modo_raw2=1, file="reporte.txt"):

  rawfile1 = RAWFile2(raw1, sistema, "comp_log", modo_raw1)
  rawfile2 = RAWFile2(raw2, sistema, "comp_log", modo_raw2)
  numero_bus_1 = []
  numero_bus_2 = []
  
  equipos_sub1 = get_diccionario_equipos(rawfile1)
  # for key, valor in equipos_sub1.items():
  #   print(key)
  #   print(valor)
  #   if 'ANG' in key:
  #     print(equipos_sub1[key])
      
  equipos_sub2 = get_diccionario_equipos(rawfile2)
  # for key, valor in equipos_sub2.items():
  #   print(key)
  #   print(valor)
  #   if 'ANG' in key:
  #     print(equipos_sub2[key])
      
  subestaciones1 = set(equipos_sub1.keys())
  subestaciones2 = set(equipos_sub2.keys())
  with open(file, "w", newline='') as fp:
    fp.write(f"Subestaciones en {path.basename(raw1)} que no estan en {path.basename(raw2)}\n")
    fp.write(f"{subestaciones1 - subestaciones2}\n")
    fp.write(f"Subestaciones en {path.basename(raw2)} que no estan en {path.basename(raw1)}\n")
    fp.write(f"{subestaciones2 - subestaciones1}\n")
    diff_sub = defaultdict(
        lambda: {
            'lineas': [], 'transformadores': [], 'generadores': [],
            'cargas': [], 'shunts': [], 'sw_sunts': []
        }
    )
    for sub, datos in equipos_sub1.items():
      # print(datos)
      if sub not in equipos_sub2:
        continue
      for tipo_equipo in datos:
        diff_sub[sub][tipo_equipo] = [
            datos[tipo_equipo] - equipos_sub2[sub][tipo_equipo],
            equipos_sub2[sub][tipo_equipo] - datos[tipo_equipo]
        ]
        
    # Filtrar el diccionario para obtener solo las listas que no sean [set(), set()] en el segundo nivel
    filtered_data = {
        outer_key: {
            key: value for key, value in inner_dict.items() if value != [set(), set()]
        }
        for outer_key, inner_dict in diff_sub.items()
    }
    # Eliminar las claves del primer nivel que tengan diccionarios vacíos en el segundo nivel
    final_filtered_data = {
        outer_key: inner_dict for outer_key, inner_dict in filtered_data.items() if inner_dict
    }
    # print(final_filtered_data)
    # for key, valor in final_filtered_data.items():
    #   # print(key)
    #   # print(valor)
    #   if 'ANG' in key[0]:
    #     print(valor)
    
    #filtrado de diferencias
    for sub, diferencias in diff_sub.items():
      if diferencias['lineas'] == [set(), set()]:
        continue
      clave = diferencias["lineas"]
      clave1 = clave[0]
      clave2 = clave[1]
      if clave1 == invertir_claves(clave2):
        diferencias["lineas"] = [set(), set()]
    
    for sub, diferencias in diff_sub.items():
      if diferencias['transformadores'] == [set(), set()]:
        continue
      clave = diferencias["transformadores"]
      clave1 = clave[0]
      clave2 = clave[1]
      if clave1 == invertir_claves(clave2):
        diferencias["transformadores"] = [set(), set()]
          
    # for sub, diferencias in diff_sub.items():
    #   if diferencias['shunts'] == [set(), set()]:
    #     continue
    #   clave = diferencias["shunts"]
    #   clave1 = clave[0]
    #   clave2 = clave[1]
      # print(clave)
      # print(clave1)
      # if clave_abb == aumentar_claves(clave_sp7):
      #     diferencias["shunts"] = [set(), set()]
    # print(diff_sub)
    
    for sub, diferencias in diff_sub.items():
      del diferencias["shunts"]
      # if diferencias == {'lineas': [set(), set()], 'transformadores': [set(), set()], 'generadores': [set(), set()], 'cargas': [set(), set()], 'shunts': [set(), set()], 'sw_sunts': [set(), set()]}:
      if diferencias == {'lineas': [set(), set()], 'transformadores': [set(), set()], 'generadores': [set(), set()], 'cargas': [set(), set()], 'sw_sunts': [set(), set()]}:
        continue
      fp.write(f"Subestacion {sub} con diferencias encontradas:\n")
      for llave, clave in diferencias.items():
        if llave == "shunts":
          continue
        if clave == [set(), set()]:
          continue
        fp.write(f"    {llave}:\n      Equipos en {path.basename(raw1)} que no estan en {path.basename(raw2)} -> {clave[0]}\n      Equipos en {path.basename(raw2)} que no estan en {path.basename(raw1)} -> {clave[1]}\n" )
  
  eq_falt1 = []
  eq_falt2 = []
  RAW1_fatl = []
  RAW2_fatl = []
  
  for se, equipos in final_filtered_data.items():
    for key in equipos.keys():
      eq_falt1.append((equipos[key][0], se[1], 1, key))
      eq_falt2.append((equipos[key][1], se[1], 1, key))
  
  for entry in eq_falt1:
      conjuntos, num, val, label = entry
      # Para cada elemento en el conjunto, crear una nueva tupla y agregarla a processed_data
      for item in conjuntos:
          RAW1_fatl.append((item, num, val, label))
          
  for entry in eq_falt2:
      conjuntos, num, val, label = entry
      # Para cada elemento en el conjunto, crear una nueva tupla y agregarla a processed_data
      for item in conjuntos:
          RAW2_fatl.append((item, num, val, label))
        
  print(RAW1_fatl)
  
  return RAW1_fatl, RAW2_fatl


if __name__ == '__main__':
  main()