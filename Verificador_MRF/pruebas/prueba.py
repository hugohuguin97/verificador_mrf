# Entrada
data = [
    ({'09LBR-400   A3T00   02THP-400'}, 90030, 1, 'lineas'),
    ({'09MMT-400   A3T00   02MMT-400', '09MMT-230   A3T00   02MMT-230'}, 987465, 1, 'lineas')
]

# Proceso para transformar el diccionario
processed_data = []

for entry in data:
    conjuntos, num, val, label = entry
    # Para cada elemento en el conjunto, crear una nueva tupla y agregarla a processed_data
    for item in conjuntos:
        processed_data.append((item, num, val, label))

# Salida
print(processed_data)
