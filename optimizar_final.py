import numpy as np
from scipy.optimize import minimize
import time
import pandas as pd

def optimizar(df, C_bateria, P_max, P_contratada, ef_carga, ef_descarga, epsilon, estado_ini=0.0, E_bat_0=None):
    """
    Optimiza el comportamiento de las baterías de la instalación para minimizar la factura.

    Parámetros:
        df (df): DataFrame que contiene los datos de consumo, generación y precios.
        C_bateria (float): Capacidad de almacenamiento de la batería (kWh).
        P_max (float): Potencia máxima de carga/descarga de la batería (kW).
        ef_carga (float): Eficiencia de carga de la batería (0 <= ef_carga <= 1).
        ef_descarga (float): Eficiencia de descarga de la batería (0 <= ef_descarga <= 1).
        epsilon (float): Tolerancia para la optimización, para evitar problemas de convergencia.
        estado_ini (float): Estado inicial de la batería (kWh).

    """
    consumo = df['Consumo kWh'].values
    generación = df['P'].values
    precio_compra = df['PVPC_total'].values
    precio_venta = df['Precio_energía_excedentaria'].values
    T = len(consumo)

    def energia_real(E_bat):
        # E_bat>0 → carga
        # E_bat<0 → descarga
        return np.where(E_bat >= 0, E_bat * ef_carga, E_bat / ef_descarga)
        
    def calcular_estado(E_bat): # Calcula el estado de la batería en cada hora
        E_real = energia_real(E_bat)
        estado_bat = np.cumsum(np.insert(E_real, 0, estado_ini))[:-1]  # El estado de la batería en la hora t es el estado de la hora anterior + el comportamiento en la hora t
        return estado_bat

    def coste_total(E_bat):
        red_compra = np.maximum(0, (consumo + E_bat) - generación)
        red_venta = np.maximum(0, generación - (consumo + E_bat))
        coste_total = np.sum(red_compra * precio_compra - red_venta * precio_venta)
        return coste_total
    
    def restricciones(E_bat):
        estado_bat = calcular_estado(E_bat)
        red_compra = np.maximum(0, (consumo + E_bat) - generación)
        red_venta = np.maximum(0, generación - (consumo + E_bat))
        restric_values = np.concatenate([
            estado_bat,                 # estado ≥ 0 (el estado de una hora es el de la hora anterior + la carga o descarga de esa hora)
            C_bateria - estado_bat,     # estado ≤ C_bateria
            P_contratada - red_compra,  # red_compra ≤ P_contratada
            P_contratada - red_venta,   # red_venta ≤ P_contratada
            # Se impone que la batería quede cerca de la mitad de su capacidad
            np.array([(estado_bat[-1]+E_bat[-1]) - (C_bateria/2 - epsilon)]),  
            np.array([(C_bateria/2 + epsilon) - (estado_bat[-1]+E_bat[-1])]),
        ])
        return restric_values

    # Restricciones en formato 'ineq' → ≥ 0
    restric = {'type': 'ineq', 'fun': restricciones}

    # Límites por hora para E_bat
    bounds = [(-P_max, P_max)] * T

    start_opt = time.time()
    res = minimize(
        coste_total,
        E_bat_0,
        method='SLSQP',
        bounds=bounds,
        constraints=[restric],
        options={'disp': True, 'maxiter': 50, 'ftol': 0.01}
    )
    res.execution_time = time.time() - start_opt
    print(f"Tiempo optimización: {res.execution_time:.6f} segundos")

    E_bat_opt = res.x
    estado_bat = calcular_estado(E_bat_opt)
    red_compra_opt = np.maximum(0, (consumo + E_bat_opt) - generación)
    red_venta_opt = np.maximum(0, generación - (consumo + E_bat_opt))

    # Almacenar los resultados de la optimización en un DataFrame
    df_opt = pd.DataFrame({
        'Fecha': df['Fecha'],
        'Fecha_UTC': df['Fecha_UTC'],
        'E_bat_kWh': E_bat_opt,
        'Estado_bat_kWh': estado_bat,
        'Consumo_kWh': consumo,
        'Generación_kWh': generación,
        'Precio compra_kWh': precio_compra,
        'Precio venta_kWh': precio_venta,
        'Precio CO2 Kg/kW': df['CO2 Kg/kWh'],
        'Red compra_kWh': red_compra_opt,
        'Red venta_kWh': red_venta_opt,
        }, index=df.index[:len(E_bat_opt)])

    return res, df_opt

