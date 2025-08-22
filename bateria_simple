import os
import time
import pandas as pd
from funciones import obtener_dataframes_prueba as dataframes
from funciones import existencia
from funciones.factura import calcular_factura

def bateria_simple(df, capacidad_max, carga_inicial, potencia_max_carga, potencia_max_descarga, eficiencia_carga, eficiencia_descarga, potencia_contratada):

    carga_bateria = carga_inicial
    historial = []

    for i, row in df.iterrows():
        estado_inicial = carga_bateria

        generacion = row["P"]
        consumo = row["Consumo kWh"]
        excedente = generacion - consumo
        
        uso_bateria = 0
        uso_red = 0
        vertido = 0

        if excedente > 0:
            # Hay exceso solar: cargar batería
            energia_disponible = min(excedente, potencia_max_carga)
            energia_almacenable = energia_disponible * eficiencia_carga
            espacio_libre = capacidad_max - carga_bateria
            energia_a_cargar = min(energia_almacenable, espacio_libre)
            carga_bateria += energia_a_cargar
            uso_bateria = energia_a_cargar / eficiencia_carga  # energía realmente tomada del excedente
            vertido = excedente - uso_bateria
        else:
            # Hay déficit: descargar batería
            demanda = -excedente
            energia_posible = min(potencia_max_descarga, carga_bateria * eficiencia_descarga)
            energia_a_usar = min(demanda, energia_posible)
            carga_bateria -= energia_a_usar / eficiencia_descarga
            uso_bateria = -energia_a_usar
            uso_red = demanda - energia_a_usar

            if potencia_contratada is not None:
                uso_red = min(uso_red, potencia_contratada)  # no exceder lo contratado

        historial.append({
            "Estado_bat_kWh": estado_inicial,
            "E_bat_kWh": uso_bateria,
            "Red compra_kWh": uso_red,
            "Red venta_kWh": vertido,
        })

    resultados_df = pd.DataFrame(historial, index=df.index)
    return pd.concat([df, resultados_df], axis=1)

def main(potencia_nominal, C_bateria):  
    año = 2023
    año_generación = 2023
    carpeta_precios = f"(Insertar directorio de la carpeta donde estén los archivos del detalle diario del PVPC)"
    ruta_archivo_generación = r"(Insertar directorio del archivo csv con los datos de la generación fotovoltaica, aunque sea de varios años)"
    archivo_salida_precios = f"Precios {año}.xlsx"
    archivo_consumo = f"Consumos {año}.xlsx"
    archivo_salida_generación = f"Generación {año_generación}.csv"
    archivo_co2 = f"CO2_{año}_tratado.csv"

    P_contratada = 5.75  # kW
    ef_carga = 1
    ef_descarga = 1

    existencia.comprobar_existencia(año_generación, archivo_salida_precios, carpeta_precios, archivo_salida_generación, ruta_archivo_generación, nombre_origen_co2, archivo_co2)
    df_precios, df_consumo, df_generación, df_co2 = dataframes.homogeneizar(año, año_generación, archivo_salida_precios, archivo_consumo, archivo_salida_generación, archivo_co2)
    df = dataframes.unir_dfs(df_precios, df_consumo, df_generación, df_co2, potencia_nominal)

    # Simulación con batería simple
    df_resultado = bateria_simple(df.copy(), capacidad_max=C_bateria, carga_inicial=C_bateria/2, potencia_max_carga=1.0, potencia_max_descarga=1.0, eficiencia_carga=ef_carga, eficiencia_descarga=ef_descarga, potencia_contratada=P_contratada)

    # Calcular facturas y CO2
    total_anual_sin_placas, total_anual_con_placas, total_anual_con_baterías, mensual, co2_mensual, df_final = calcular_factura(df_resultado, df_resultado["E_bat_kWh"].copy())

    # Guardar resultados anuales
    df_resultados = pd.DataFrame([{
        "Potencia_nominal": potencia_nominal,
        "C_bateria": C_bateria,
        "Total_sin_placas": total_anual_sin_placas,
        "Total_con_placas": total_anual_con_placas,
        "Total_con_baterias": total_anual_con_baterías
    }])

    resumen_file = "batería_simple_resumen_anual_todas_las_combinaciones.csv"
    if os.path.exists(resumen_file):
        df_existente = pd.read_csv(resumen_file)
        df_existente = df_existente[
            ~((df_existente["Potencia_nominal"] == potencia_nominal) &
              (df_existente["C_bateria"] == C_bateria))
        ]
        df_actualizado = pd.concat([df_existente, df_resultados], ignore_index=True)
        df_actualizado.to_csv(resumen_file, index=False)
    else:
        df_resultados.to_csv(resumen_file, index=False)

    # Guardar facturas mensuales
    mensual.to_csv(f"batería_simple_coste_mensual_P{potencia_nominal}_C{C_bateria}.csv", index=False)

    # Guardar emisiones mensuales
    co2_mensual.to_csv(f"batería_simple_co2_mensual_P{potencia_nominal}_C{C_bateria}.csv", index=False)

    # Guardar archivo detallado de resultados por hora
    df_resultado.to_csv(f"batería_simple_resultados_P{potencia_nominal}_C{C_bateria}.csv", index=False)

    print(f"Finalizado P={potencia_nominal}, C={C_bateria} | Coste sin placas: {total_anual_sin_placas:.2f} €, con placas: {total_anual_con_placas:.2f} €, con baterías: {total_anual_con_baterías:.2f} €")


if __name__ == '__main__':
    first = True
    for potencia_nominal in range(0, 5):  # De 0 a 4
        for C_bateria in range(0, 6):     # De 0 a 5
            start_ejecucion = time.time()
            print(f"\n--- Ejecutando batería simple con P={potencia_nominal}, C={C_bateria} ---")
            main(potencia_nominal, C_bateria)

            end_ejecucion = time.time()
            print(f"\nTiempo total de ejecución: {end_ejecucion - start_ejecucion:.2f} segundos")
            #guardar tiempo de ejecución para cada caso en un csv
            df_tiempos = pd.DataFrame({
                "Potencia nominal [kW]": [potencia_nominal],
                "Capacidad batería [kWh]": [C_bateria],
                "Tiempo de ejecución [s]": [end_ejecucion - start_ejecucion]
            })

            archivo_tiempos = "bt_tiempos_ejecucion.csv"
            if first:
                df_tiempos.to_csv(archivo_tiempos, index=False)
                first = False
            else:
                df_tiempos.to_csv(archivo_tiempos, mode='a', header=False, index=False)
