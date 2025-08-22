import pandas as pd
from datetime import timedelta

def leer_y_filtrar_csv(ruta_archivo, año_generación, archivo_salida):
    """
    Lee el archivo con los datos de generación descargados desde la página de la Unión Europea y obtiene un archivo csv con los datos del año de interés.
    
    Parámetros:
        ruta_archivo (str): Ruta del archivo CSV a leer.
        año_generación (int): Año para filtrar los datos.
        archivo_salida (str): Nombre del archivo CSV de salida.
    
    Retorna:
        generación_filtrado: DataFrame con los datos del archivo CSV.
    """
    try:
        # Leer el archivo CSV adaptándose al formato específico de este
        generación = pd.read_csv(ruta_archivo, skiprows=10, low_memory=False)

        columnas_esperadas = {"time", "P", "G(i)", "H_sun", "T2m", "WS10m", "Int"}
        if not columnas_esperadas.issubset(generación.columns):
            raise ValueError("El archivo CSV no contiene las columnas esperadas.")

        # Eliminar las últimas 7 filas, ya que no son de interés
        generación = generación.iloc[:-7]

        generación['time'] = pd.to_datetime(generación['time'], format='%Y%m%d:%H%M', errors='coerce', utc=True)
        
        # Ajustar la hora a en punto para que luego la referencia sea la misma que en el archivo de consumos y precios (originalmente está en formato HH:10)
        generación['fecha_utc'] = generación['time'] - timedelta(minutes=10)
        generación['fecha_madrid'] = generación['time'].dt.tz_convert('Europe/Madrid')

        # Convertir la columna 'P' a numérico y dividir por 1000 para pasar de W a kW
        generación['P'] = pd.to_numeric(generación['P'], errors='coerce') / 1000

        generación.drop(columns=['time', 'G(i)', "H_sun", "T2m", "WS10m", "Int"], inplace=True)

        generación_filtrado = generación[generación['fecha_madrid'].dt.year == año_generación]

        # Reordenar las columnas para que las columnas de fechas sean las primeras
        generación_filtrado = generación_filtrado[['fecha_utc', 'fecha_madrid', 'P']]

        generación_filtrado.to_csv(archivo_salida, index=False)
        
        return generación_filtrado
    except Exception as e:
        print(f"Error al leer el archivo CSV: {e}")
        return None
