import wx

# Datos del diccionario
data = {('02ANG-400   A3T30   02THP-400', 20000, 1, 'LT'), ('02ANG-400   A3030   02MMT-400', 20016, 1, 'LT'), ('02ANG-400   R1', None, 1, 'SH'), ('02ANG-400   A2060   02ANG-115', 21000, 1, 'T'), ('02ANG-400   A2050   02ANG-13.8', 20012, 1, 'T'), ('02ANG-400   A2010   02ANG-13.8', 20008, 1, 'T'), ('02ANG-400   A2040   02ANG-13.8', 20011, 1, 'T'), ('02ANG-400   A2020   02ANG-13.8', 20009, 1, 'T'), ('02ANG-400   A3T60   02SAB-400', 20013, 1, 'LT'), ('02ANG-400   A2030   02ANG-13.8', 20010, 1, 'T')}

# Convertir el conjunto de tuplas a una lista de listas
data_list = [list(item) for item in data]

# Crear una aplicación wx
app = wx.App()
frame = wx.Frame(None, title="ListCtrl Example", size=(400, 300))
panel = wx.Panel(frame)

# Crear un ListCtrl
list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
list_ctrl.InsertColumn(0, "Column 1")
list_ctrl.InsertColumn(1, "Column 2")
list_ctrl.InsertColumn(2, "Column 3")
list_ctrl.InsertColumn(3, "Column 4")

# Agregar los datos al ListCtrl
for index, row in enumerate(data_list):
    list_ctrl.InsertItem(index, str(row[0]))  # Insertar el primer elemento de cada fila en la primera columna
    for col_index, col_value in enumerate(row[1:], start=1):
        list_ctrl.SetItem(index, col_index, str(col_value))  # Insertar los demás elementos de la fila en las siguientes columnas

# Mostrar el marco
frame.Show()
app.MainLoop()
