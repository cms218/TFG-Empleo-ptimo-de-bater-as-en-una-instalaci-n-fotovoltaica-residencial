import numpy as np

def calcular_factura(df_unido, bateria):
    df_unido['Batería'] = bateria

    # Calcular el coste
    df_unido['Coste_sin_placas'] = df_unido['PVPC_total'] * df_unido['Consumo kWh']

    df_unido['Coste_con_placas'] = np.where((df_unido['Consumo kWh'] - df_unido['P']) > 0,
                           df_unido['PVPC_total'] * (df_unido['Consumo kWh'] - df_unido['P']),
                           df_unido['Precio_energía_excedentaria'] * (df_unido['Consumo kWh'] - df_unido['P']))

    df_unido['Coste_con_baterías'] = np.where(((df_unido['Consumo kWh'] + df_unido['Batería']) - df_unido['P']) > 0,
                           df_unido['PVPC_total'] * ((df_unido['Consumo kWh'] + df_unido['Batería']) - df_unido['P']),
                           df_unido['Precio_energía_excedentaria'] * ((df_unido['Consumo kWh'] + df_unido['Batería']) - df_unido['P']))

    df_unido['CO2_sin_placas'] = df_unido['CO2 Kg/kWh']* df_unido['Consumo kWh']

    df_unido['CO2_con_placas'] = np.where((df_unido['Consumo kWh'] - df_unido['P']) > 0,
                           df_unido['CO2 Kg/kWh'] * (df_unido['Consumo kWh'] - df_unido['P']), 0)

    df_unido['CO2_con_placas_excedente'] = np.where((df_unido['Consumo kWh'] - df_unido['P']) < 0,
                           df_unido['CO2 Kg/kWh'] * (df_unido['Consumo kWh'] - df_unido['P']), 0)
    
    df_unido['CO2_con_baterías'] = np.where(((df_unido['Consumo kWh'] + df_unido['Batería']) - df_unido['P']) > 0,
                           df_unido['CO2 Kg/kWh'] * ((df_unido['Consumo kWh'] + df_unido['Batería']) - df_unido['P']), 0)
    
    df_unido['CO2_con_baterías_excedente'] = np.where(((df_unido['Consumo kWh'] + df_unido['Batería']) - df_unido['P']) < 0,
                           df_unido['CO2 Kg/kWh'] * ((df_unido['Consumo kWh'] + df_unido['Batería']) - df_unido['P']), 0)


     # Precio total por mes
    precio_por_mes = df_unido.groupby('Mes').agg({
        'Coste_sin_placas': 'sum',
        'Coste_con_placas': 'sum',
        'Coste_con_baterías': 'sum',
    }).round(2).reset_index()

    # Asegurar que los valores negativos se convierten a cero por mes porque, como mínimo, la factura es 0€. No me pueden pagar a final de mes por excedentes
    precio_por_mes.loc[precio_por_mes['Coste_con_placas'] < 0, 'Coste_con_placas'] = 0
    precio_por_mes.loc[precio_por_mes['Coste_con_baterías'] < 0, 'Coste_con_baterías'] = 0

    # Calcular precios anuales a partir de los mensuales para tener en cuenta lo anterior
    precio_total_anual_sin_placas = precio_por_mes['Coste_sin_placas'].sum()
    precio_total_anual_con_placas = precio_por_mes['Coste_con_placas'].sum()
    precio_total_anual_con_baterías = precio_por_mes['Coste_con_baterías'].sum()

    co2_por_mes = df_unido.groupby('Mes').agg({
        'CO2_sin_placas': 'sum',
        'CO2_con_placas': 'sum',
        'CO2_con_placas_excedente': 'sum',
        'CO2_con_baterías': 'sum',
        'CO2_con_baterías_excedente': 'sum'
    }).round(2).reset_index()

    return precio_total_anual_sin_placas, precio_total_anual_con_placas, precio_total_anual_con_baterías, precio_por_mes, co2_por_mes, df_unido
