import pandas as pd
import calendar

def procesar_consumo(nombre_consumo):
    """
    Esta función selecciona los datos de interés del archivo que contiene los datos del consumo de la vivienda.

    Se ha diseñado teniendo en cuenta la existencia de las siguientes columnas:
        'Fecha'
        'Hora' (tomando la primera hora del día como 1)
        'Consumo kWh'

    Parámetros:
        nombre_consumo (str): Nombre del archivo (con extensión) en el que se encuentran los datos del consumo de la vivienda (ej. "Consumos 2023.xlsx").
    
    Retorna:
        consumo_filtrado (dataframe): Dataframe con los datos de interés para calcular la factura
    """
    # Leer el archivo Excel
    excel_consumo = pd.read_excel(nombre_consumo, engine='openpyxl')

    # Verificar que todos los valores sean numéricos
    if excel_consumo['Consumo kWh'].astype(str).str.contains(',').any():  # Comprobar si alguna celda tiene coma
        excel_consumo['Consumo kWh'] = excel_consumo['Consumo kWh'].astype(str).str.replace(',', '.').astype(float)  # Reemplazar comas por puntos
    excel_consumo['Consumo kWh'] = excel_consumo['Consumo kWh'].apply(pd.to_numeric, errors='coerce')

    excel_consumo['Fecha'] = pd.to_datetime(excel_consumo['Fecha'], dayfirst=True)
    consumo_filtrado = excel_consumo[['Fecha', 'Hora', 'Consumo kWh']].copy()   # Seleccionar columnas de interés
    consumo_filtrado['Hora'] -= 1   # Ajustar la hora para que empiece desde 0

    # Combinar fecha y hora en un solo string
    consumo_filtrado["fecha_completa"] = consumo_filtrado.apply(
    lambda row: f"{row['Fecha'].strftime('%Y-%m-%d')} {row['Hora']:02d}:00", axis=1
    )
    # Convertir a datetime
    consumo_filtrado["fecha_completa"] = pd.to_datetime(
    consumo_filtrado["fecha_completa"], format='%Y-%m-%d %H:%M', errors='coerce'
    )
    # Localizar al huso horario de Madrid y convertir a UTC
    consumo_filtrado['fecha_local'] = consumo_filtrado['fecha_completa'].dt.tz_localize('Europe/Madrid', ambiguous='infer')
    consumo_filtrado['fecha_utc'] = consumo_filtrado['fecha_local'].dt.tz_convert('UTC')
    return consumo_filtrado

def homogeneizar(año, año_generación, precios_excel, consumo_excel, archivo_salida_generación, archivo_co2):
    """
    Sólo me interesa cuando un año es bisiesto y el otro no. Si no, no hago nada.
    Igualmente, me da los dataframes de precios, consumo y generación.
    
    Parámetros:
        año (int): Año para filtrar los datos.
        año_generación (int): Año para filtrar los datos de generación.
        precios_excel (str): Ruta del archivo Excel con los precios.
        consumo_excel (str): Ruta del archivo Excel con los datos de consumo.
        archivo_salida_generación (str): Ruta del archivo CSV con los datos de generación.
    
    Retorna:
        pd.DataFrame: DataFrames homogéneos para los años especificados.
    """
    # Leo archivos y elimino información de la zona horaria
    df_precios = pd.read_excel(precios_excel)
    df_precios['fecha_utc_precios_y_consumo'] = pd.to_datetime(df_precios['fecha_utc_sin_tz'], errors='coerce')
    df_precios.drop(columns=['Fecha', 'Hora', 'fecha_completa_sin_tz', 'fecha_utc_sin_tz'], inplace=True)
    
    df_consumo = procesar_consumo(consumo_excel)
    df_consumo['fecha_utc_precios_y_consumo'] = df_consumo['fecha_utc'].dt.tz_localize(None)
    df_consumo.drop(columns=['Fecha', 'Hora', 'fecha_completa', 'fecha_local', 'fecha_utc'], inplace=True)
    
    df_generación = pd.read_csv(archivo_salida_generación)
    df_generación['fecha_utc_generación'] = pd.to_datetime(df_generación['fecha_utc'], errors='coerce')
    df_generación['fecha_utc_generación'] = df_generación['fecha_utc_generación'].dt.tz_localize(None)
    df_generación.drop(columns=['fecha_madrid'], inplace=True)

    df_co2 = pd.read_csv(archivo_co2, sep=',', low_memory=False)
    df_co2['fecha_utc_co2'] = pd.to_datetime(df_co2['fecha_utc_co2'], errors='coerce', utc=True)
    
    if año_generación != año:
        if calendar.isleap(año) and not calendar.isleap(año_generación):
            df_precios_homogeneo = df_precios[~((df_precios['fecha_utc_precios_y_consumo'].dt.month == 2) & (df_precios['fecha_utc_precios_y_consumo'].dt.day == 29))]
            df_consumo_homogeneo = df_consumo[~((df_consumo['fecha_utc_precios_y_consumo'].dt.month == 2) & (df_consumo['fecha_utc_precios_y_consumo'].dt.day == 29))]
            df_co2_homogeneo = df_co2[~((df_co2['fecha_utc_co2'].dt.month == 2) & (df_co2['fecha_utc_co2'].dt.day == 29))]
        else:
            df_precios_homogeneo = df_precios
            df_consumo_homogeneo = df_consumo
            df_co2_homogeneo = df_co2

        if calendar.isleap(año_generación) and not calendar.isleap(año):
            df_generación_homogeneo = df_generación[~((df_generación['fecha_utc_generación'].dt.month == 2) & (df_generación['fecha_utc_generación'].dt.day == 29))]
        else:
            df_generación_homogeneo = df_generación

        return df_precios_homogeneo, df_consumo_homogeneo, df_generación_homogeneo, df_co2_homogeneo
    else:
        return df_precios, df_consumo, df_generación, df_co2
    
def unir_dfs(df_precios, df_consumo, df_generación, df_co2, potencia_nominal):
    # Extraer mes, día y hora de fecha_utc
    for df in [df_precios, df_consumo]:
        df['Mes'] = df['fecha_utc_precios_y_consumo'].dt.month
        df['Día'] = df['fecha_utc_precios_y_consumo'].dt.day
        df['Hora'] = df['fecha_utc_precios_y_consumo'].dt.hour

    df_generación['Mes'] = df_generación['fecha_utc_generación'].dt.month
    df_generación['Día'] = df_generación['fecha_utc_generación'].dt.day
    df_generación['Hora'] = df_generación['fecha_utc_generación'].dt.hour
    df_generación['P'] = df_generación['P'] * potencia_nominal

    df_co2['Mes'] = df_co2['fecha_utc_co2'].dt.month
    df_co2['Día'] = df_co2['fecha_utc_co2'].dt.day
    df_co2['Hora'] = df_co2['fecha_utc_co2'].dt.hour

    # Unir datos por Mes, Día y Hora en UTC
    df_temp1 = pd.merge(df_precios, df_consumo, on=['Mes', 'Día', 'Hora'], how='outer').fillna(0)
    df_temp2 = pd.merge(df_temp1, df_generación, on=['Mes', 'Día', 'Hora'], how='outer').fillna(0).copy()
    df = pd.merge(df_temp2, df_co2, on=['Mes', 'Día', 'Hora'], how='outer').fillna(0)
    
    df.drop(columns=['fecha_utc_precios_y_consumo_y', 'fecha_utc', 'fecha_utc_co2'], inplace=True)
    df.rename(columns={'fecha_utc_precios_y_consumo_x': 'Fecha', 'fecha_utc_generación': 'Fecha_UTC'}, inplace=True)

    # Reordenar las columnas para que las columnas de fechas sean las primeras
    columnas_fecha = ['Fecha', 'Fecha_UTC', 'Mes', 'Día', 'Hora', 'PVPC_total', 'Consumo kWh', 'P', 'Precio_energía_excedentaria', 'CO2 Kg/kWh']
    otras_columnas = [col for col in df.columns if col not in columnas_fecha]
    df = df[columnas_fecha + otras_columnas].copy()

    # Una vez que se ha unido todo por UTC, se convierte una de las columnas de fecha a la zona horaria de Madrid, ya que es el formato de interés para el análisis
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', utc=True)
    df['Fecha'] = df['Fecha'].dt.tz_convert('Europe/Madrid')
    df = df.sort_values('Fecha')

    df['Mes'] = df['Fecha'].dt.month
    df['Día'] = df['Fecha'].dt.day
    df['Hora'] = df['Fecha'].dt.hour
    
    return df
