import os
import pandas as pd
import time
from funciones import obtener_dataframes as dataframes
from funciones import existencia
from funciones import optimizar_final as optimizar
from funciones.factura import calcular_factura

def main(potencial_nominal, C_bateria):  
    año=2023
    año_generación=2023     # Inicialmente, este código se preparó para simular con datos de generación de otros años distintos al de precio y consumo
    carpeta_precios = f"(Insertar directorio de la carpeta donde estén los archivos del detalle diario del PVPC)"
    ruta_archivo_generación=r"(Insertar directorio del archivo csv con los datos de la generación fotovoltaica, aunque sea de varios años)"
    nombre_origen_co2 = f"CO2_{año}.csv"  
    archivo_salida_precios = f"Precios {año}.xlsx"
    archivo_consumo = f"Consumos {año}.xlsx"
    archivo_salida_generación= f"Generación {año_generación}.csv"
    archivo_co2 = f"CO2_{año}_tratado.csv"

    P_max=1
    P_contratada=5.75
    ef_carga=1
    ef_descarga=1
    epsilon=0.001*C_bateria  # Tolerancia para el estado final de la batería

    # Comprobar si existe el archivo del año y si no, generarlo
    existencia.comprobar_existencia(año_generación, archivo_salida_precios, carpeta_precios, archivo_salida_generación, ruta_archivo_generación, nombre_origen_co2, archivo_co2)
    df_precios, df_consumo, df_generación, df_co2 = dataframes.homogeneizar(año, año_generación, archivo_salida_precios, archivo_consumo, archivo_salida_generación, archivo_co2)
    df = dataframes.unir_dfs(df_precios, df_consumo, df_generación, df_co2, potencia_nominal)

    # Verificar si la columna 'Fecha' ya tiene información de zona horaria
    if df['Fecha'].dt.tz is None:
        print("La columna 'Fecha' no tiene información de zona horaria, localizando a UTC y luego convirtiendo a Europe/Madrid.")
        df['Fecha'] = df['Fecha'].dt.tz_localize('Europe/Madrid')
    else:
        print(f"La columna 'Fecha' ya tiene zona horaria: {df['Fecha'].dt.tz}, convirtiendo directamente a Europe/Madrid.")
        df['Fecha'] = df['Fecha'].dt.tz_convert('Europe/Madrid')

    df = df.sort_values('Fecha')    # Asegurar que las fechas están ordenadas según la nueva zona horaria
    df['Batería'] = 0

    # Establecer las fechas de inicio y fin del bucle de optimización
    fecha_inicio = pd.Timestamp('2023-01-01 00:00:00', tz='Europe/Madrid')
    fecha_fin = pd.Timestamp('2024-01-01 00:00:00', tz='Europe/Madrid')
    fecha_actual = fecha_inicio

    estado_inicial_bucle = C_bateria/2  # Estado inicial de la batería para el primer bucle

    df_total=pd.DataFrame()
    resultados_optimizacion = []  # Para almacenar resultados por día

    # Optimizar en ventanas de 1 día
    while fecha_actual <= fecha_fin:
        fecha_dia_siguiente = (fecha_actual + pd.DateOffset(days=1)).normalize()

        df_periodo = df[(df['Fecha'] >= fecha_actual) & (df['Fecha'] < fecha_dia_siguiente)]

        if df_periodo.empty:
            print(f"No hay datos para el periodo {fecha_actual} a {fecha_dia_siguiente}.")
            break

        E_bat_previous = None

        res, df_opt = optimizar.optimizar(df_periodo, C_bateria, P_max, P_contratada,
                                  ef_carga, ef_descarga, epsilon,
                                  estado_ini=estado_inicial_bucle,
                                  E_bat_0=E_bat_previous)  
        
        E_bat_previous = res.x.copy()   # Se asigna el comportamiento obtenido como valor inicial para la siguiente optimización y así intentar reducir el tiempo de ejecución
        
        resultado_opt_dia = {
            'Fecha': fecha_inicio.strftime("%Y-%m-%d"),
            'Potencia_nominal': potencia_nominal,
            'C_bateria': C_bateria,
            'Coste_optimo': res.fun,
            'Iteraciones': getattr(res, 'nit', None),
            'Exito': res.success,
            'Status': res.status,
            'Mensaje': res.message,
            'Tiempo_s': round(res.execution_time, 3) if hasattr(res, 'execution_time') else None
        }
        resultados_optimizacion.append(resultado_opt_dia)

        # Añadir df_opt optimizado al total para guardarlo después
        df_total = pd.concat([df_total, df_opt], ignore_index=True)

        # Guardar el DataFrame total en archivo (sobrescribiendo cada vez)
        df_total = df_total.sort_values('Fecha')
        df_total.to_csv(f"día_fact_opt_total_P{potencia_nominal}_C{C_bateria}.csv", index=False)

        # Actualizar el estado inicial para el siguiente bucle
        estado_inicial_siguiente = df_opt['Estado_bat_kWh'].iloc[-1] + df_opt['E_bat_kWh'].iloc[-1]  # El estado inicial para el siguiente bucle es el último estado final más el comportamiento de carga/descarga de la batería en esa hora
        estado_inicial_bucle = estado_inicial_siguiente

        # Actualizar la fecha de inicio para el siguiente bucle
        fecha_actual = fecha_dia_siguiente

        E_bat_optimo = res.x
        df.loc[df_periodo.index, 'Batería'] = E_bat_optimo.astype(float)  # Asignar los valores de E_bat_optimo al período correspondiente

        total_anual_sin_placas, total_anual_con_placas, total_anual_con_baterías, total_mensual, total_co2_mensual, df_final = calcular_factura(df, df['Batería'].copy())

        #print(f"Precio total anual sin placas: {total_anual_sin_placas:.2f} €")
        #print(f"Precio total anual con placas: {total_anual_con_placas:.2f} €")
        #print(f"Precio total anual con baterías: {total_anual_con_baterías:.2f} €")
        #print("Precio por mes en €:")
        #print(total_mensual)
        #print("CO2 por mes en Kg:")
        #print(total_co2_mensual)

    # Guardar los resultados totales anuales
    df_resultados_anuales = pd.DataFrame([{
        "Potencia_nominal": potencia_nominal,
        "C_bateria": C_bateria,
        "Total_sin_placas": total_anual_sin_placas,
        "Total_con_placas": total_anual_con_placas,
        "Total_con_baterias": total_anual_con_baterías
    }])

    archivo_acumulado = "día_fact_resumen_anual_todas_las_combinaciones.csv"

    # Si el archivo ya existe, cargarlo y concatenar los nuevos resultados
    if os.path.exists(archivo_acumulado):
        df_existente = pd.read_csv(archivo_acumulado)
        df_existente = df_existente[
            ~((df_existente["Potencia_nominal"] == potencia_nominal) &
            (df_existente["C_bateria"] == C_bateria))
        ]
        df_total = pd.concat([df_existente, df_resultados_anuales], ignore_index=True)
        df_total.to_csv(archivo_acumulado, index=False)
    else:
        df_resultados_anuales.to_csv(archivo_acumulado, index=False)

    # Guardar costes y emisiones mensuales y resultados de optimización
    df_coste_mensual = total_mensual.copy()
    archivo_coste = f"día_fact_coste_mensual_P{potencia_nominal}_C{C_bateria}.csv"
    df_coste_mensual.to_csv(archivo_coste, index=False)

    df_co2_mensual = total_co2_mensual.copy()
    archivo_co2 = f"día_fact_co2_mensual_P{potencia_nominal}_C{C_bateria}.csv"
    df_co2_mensual.to_csv(archivo_co2, index=False)

    df_resultados_opt = pd.DataFrame(resultados_optimizacion)
    archivo_opt = f"día_fact_resultados_optimizacion_P{potencia_nominal}_C{C_bateria}.csv"
    df_resultados_opt.to_csv(archivo_opt, index=False)

# Ejecutar el código para las diferentes combinaciones de potencia nominal y capacidad de batería
if __name__ == '__main__':
    first = True
    for potencia_nominal in range(0, 5):  # De 0 a 4
        for C_bateria in range(0, 6):     # De 0 a 5
            start_ejecucion = time.time()
            print(f"\nEjecutando con potencia_nominal={potencia_nominal}, C_bateria={C_bateria}")
            main(potencia_nominal, C_bateria)
            end_ejecucion = time.time()
            print(f"\nTiempo total de ejecución: {end_ejecucion - start_ejecucion:.2f} segundos")
            #guardar tiempo de ejecución para cada caso en un csv
            df_tiempos = pd.DataFrame({
                "Potencia nominal [kW]": [potencia_nominal],
                "Capacidad batería [kWh]": [C_bateria],
                "Tiempo de ejecución [s]": [end_ejecucion - start_ejecucion]
            })

            archivo_tiempos = "día_tiempos_ejecucion.csv"
            if first:
                df_tiempos.to_csv(archivo_tiempos, index=False)
                first = False
            else:
                df_tiempos.to_csv(archivo_tiempos, mode='a', header=False, index=False)
