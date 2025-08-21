import os
import pandas as pd

def combinar_excels_precios(directorio, archivo_salida):
    """
    Lee todos los archivos de Excel en un directorio, usa las columnas del primer archivo ya que todos tienen las mismas columnas, combina todos los datos en un solo DataFrame y los guarda en un nuevo archivo de Excel.
    Los archivos tratados serán los archivos de PVPC detallado descargados de la web de Red Eléctrica Española en formato Excel. Por ello, habrá un archivo para cada día.
    
    Parámetros:
        directorio (str): Ruta donde se encuentran los archivos de Excel.
        archivo_salida (str): Nombre del archivo Excel de salida.

    Retorna:
        precios_unico_filtrado: DataFrame combinado con los datos de precios en el formato de interés.
    """
    # Verificar si los archivos están en formato Excel
    archivos = [f for f in os.listdir(directorio) if f.endswith('.xlsx') or f.endswith('.xls')]
    
    if not archivos:
        print("No se encontraron archivos de Excel en el directorio.")
        return
    
    dataframes = []
    
    # Leer el primer archivo con skiprows=4 para obtener las columnas del archivo (debido al formato de los archivos de REE)
    primer_archivo = archivos.pop(0)
    ruta = os.path.join(directorio, primer_archivo)
    df_base = pd.read_excel(ruta, skiprows=4)
    df_base["Archivo_Origen"] = primer_archivo
    dataframes.append(df_base)
    
    # Leer los demás archivos con skiprows=5 sin modificar las columnas
    for archivo in archivos:
        ruta = os.path.join(directorio, archivo)
        df = pd.read_excel(ruta, skiprows=5, header=None, names=df_base.columns)  # Mantener las columnas del primer archivo
        df["Archivo_Origen"] = archivo  # Agregar columna con el nombre del archivo de origen
        dataframes.append(df)
    
    df_combinado = pd.concat(dataframes, ignore_index=True)

    df_combinado.rename(columns={
        'Día': 'Fecha',
        'Término energía PVPC\nFEU = TEU + TCU\n€/MWh consumo': 'PVPC_total',
        'Total\nPMH\n€/MWh bc': 'Total_diario_intradiario',
        'Coste desvíos\n€/MWh bc': 'Desvíos'
    }, inplace=True)

    precios_unico_filtrado = df_combinado[['Fecha', 'Hora', 'PVPC_total', 'Total_diario_intradiario', 'Desvíos']].copy()
    precios_unico_filtrado[['Hora']] -= 1  # Resto 1 a la columna Hora para que empiece en 0 y no en 1


    # Combinar fecha y hora en un solo string
    precios_unico_filtrado["fecha_completa"] = precios_unico_filtrado["Fecha"].astype(str) + " " + precios_unico_filtrado["Hora"].astype(str)

    # Convertir a datetime
    precios_unico_filtrado["fecha_completa"] = pd.to_datetime(precios_unico_filtrado["fecha_completa"], format='%Y-%m-%d %H', errors='coerce')

    # Localizar al huso horario de Madrid y convertir a UTC
    precios_unico_filtrado['fecha_local'] = precios_unico_filtrado['fecha_completa'].dt.tz_localize('Europe/Madrid', ambiguous='infer')
    precios_unico_filtrado['fecha_utc'] = precios_unico_filtrado['fecha_local'].dt.tz_convert('UTC')

    # Crear columnas sin información de la zona horaria para exportar a Excel
    precios_unico_filtrado["fecha_completa_sin_tz"] = precios_unico_filtrado["fecha_completa"].dt.tz_localize(None)
    precios_unico_filtrado["fecha_utc_sin_tz"] = precios_unico_filtrado["fecha_utc"].dt.tz_localize(None)

    # Convertir a €/kWh
    precios_unico_filtrado[['PVPC_total', 'Total_diario_intradiario', 'Desvíos']] *= 1e-3

    # Obtener el precio de la energía excedentaria
    precios_unico_filtrado['Precio_energía_excedentaria'] = precios_unico_filtrado['Total_diario_intradiario'] - precios_unico_filtrado['Desvíos']
    precios_unico_filtrado.drop(columns=['Total_diario_intradiario', 'Desvíos'], inplace=True)

    # Exportar a Excel usando las columnas sin información de la zona horaria ya que si no, no es posible
    precios_unico_filtrado[['Fecha', 'Hora', 'PVPC_total', 'Precio_energía_excedentaria', 'fecha_completa_sin_tz', 'fecha_utc_sin_tz']].to_excel(archivo_salida, index=False)
    print(f"Archivo guardado exitosamente como {archivo_salida}")

    return precios_unico_filtrado