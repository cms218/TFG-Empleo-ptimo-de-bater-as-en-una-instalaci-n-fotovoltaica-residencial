import os
from funciones import precios
from funciones import generación2
from funciones import co2

def comprobar_existencia(año_generación, archivo_salida_precios, carpeta_precios, archivo_salida_generación, ruta_archivo_generación, nombre_origen_co2, archivo_co2):
    """
    Comprueba si existe el archivo excel de los precios y el archivo csv de generación (ambos para un año concreto). Si no existen, los genera.

    Parámetros:
        año_generación (int): Año de los datos de generación.
        archivo_salida_precios (str): Ruta del archivo de salida para los precios.
        carpeta_precios (str): Ruta de la carpeta que contiene los archivos de precios.
        archivo_salida_generación (str): Ruta del archivo de salida para los datos de generación.
        ruta_archivo_generación (str): Ruta del archivo CSV con los datos de generación.
        potencia_nominal (float): Potencia nominal del sistema fotovoltaico.
    """
    if os.path.isfile(archivo_salida_precios):
            print(f"El archivo '{archivo_salida_precios}' ya existe.")
    else:
        print(f"El archivo '{archivo_salida_precios}' no existe. Generándolo...")
        archivo_salida_precios = precios.combinar_excels_precios(carpeta_precios, archivo_salida_precios)

    if os.path.isfile(archivo_salida_generación):
            print(f"El archivo '{archivo_salida_generación}' ya existe.")
    else:
        print(f"El archivo '{archivo_salida_generación}' no existe. Generándolo...")
        df = generación2.leer_y_filtrar_csv(ruta_archivo_generación, año_generación, archivo_salida_generación)

    if os.path.isfile(archivo_co2):
            print(f"El archivo '{archivo_co2}' ya existe.")
    else:
        print(f"El archivo '{archivo_co2}' no existe. Generándolo...")
        df_co2 = co2.crear_co2(nombre_origen_co2, archivo_co2)
