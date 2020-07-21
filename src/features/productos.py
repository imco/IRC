#!/usr/bin/env python

import pandas as pd
import numpy as np

DataFrame = pd.DataFrame


def contratos_fraccionados(df_procs: DataFrame,
                           df_maximos: DataFrame, **kwargs) -> DataFrame:
    """
    Calcula indicadores para encontrar si se fraccionaron contratos
    para no rebasar el monto permitido en una AD.
    A nivel contrato se calcula:
    1. Número de la semana por cada contrato.
    2. Monto acumulado de contratos AD en el mismo día por empresa por UC.
    3. Monto acumulado de contratos AD en la misma semana por empresa por UC
    4. Número de contratos AD por semana por empresa por UC.
    5. Número de contratos AD por día por empresa por UC.
    6. Contrato fraccionado?
    """
    if 'year' in kwargs:
        años_validos = set([kwargs['year']])
    else:
        raise TypeError('Falta especificar año')

    # Máximos del año para Adjudicación directa por distintos Tipos
    df_maximos = df_maximos.loc[df_maximos.Año.isin(años_validos)]
    df_maximos = df_maximos[['Tipo de contratación', 'Adjudicación directa']]
    df_maximos.rename(columns={'Adjudicación directa': 'maximo_permitido'}, inplace=True)

    # Sólo ADJUDICACION DIRECTA
    df = df_procs.copy()
    df = df.loc[df.TIPO_PROCEDIMIENTO == 'ADJUDICACION DIRECTA']

    # 1. Número de la semana por cada contrato
    df = df.assign(semana=df.FECHA_INICIO.dt.week)

    # 2. Monto acumulado de contratos AD en el mismo día por empresa por UC.
    # TODO

    # 3. Monto acumulado de contratos AD en la misma semana por empresa por UC
    group_keys = ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'TIPO_CONTRATACION', 'semana']
    monto_semanal = (df.groupby(group_keys, as_index=False)
                     .IMPORTE_PESOS.sum()
                     .rename(columns={'IMPORTE_PESOS': 'monto_semanal_empresa'}))

    # 4. Número de contratos AD por semana por empresa por UC.
    contratos_semanales = (df.groupby(group_keys, as_index=False)
                           .NUMERO_PROCEDIMIENTO.count()
                           .rename(columns={'NUMERO_PROCEDIMIENTO': 'contratos_semanales_empresa'}))

    # 5. Número de contratos AD por día por empresa por UC.
    # TODO

    # 6. Contrato fraccionado?
    # Si en una semana una UC otorga a una empresa más de 1 contrato AD y el
    # monto acumulado supera máximos autorizados para AD en ese año.

    # Obtiene los máximos
    monto_semanal = pd.merge(monto_semanal, df_maximos,
                             left_on='TIPO_CONTRATACION',
                             right_on='Tipo de contratación')

    monto_semanal.drop('Tipo de contratación', axis=1, inplace=True)

    # Marca los que exceden
    monto_semanal = pd.merge(monto_semanal, contratos_semanales)
    fraccionado = (
        (monto_semanal.monto_semanal_empresa > monto_semanal['maximo_permitido']) &
        (monto_semanal.contratos_semanales_empresa > 1))
    monto_semanal = monto_semanal.assign(fraccionado=fraccionado)

    # Agrega las variables 3, 4, y 6 al resultado
    df = df.merge(monto_semanal)

    # Mezcla con la tabla de procedimientos original
    return df_procs.merge(df, how='left')


def falta_transparencia_pnt(df_procs: DataFrame,
                            df_sipot: DataFrame) -> DataFrame:
    """
    Agrega indicadores a nivel procedimiento para identificar
    Falta de transparencia y violación a la ley:
        1. Adjudicación directa sin autorización del ejercicio de la opción (dictamen).
        2. Adjudicación directa sin cotización (posibles contratantes)
        3. Adjudicación directa sin contrato
        4. INV3 y/o LP sin convocatoria.
        5. INV3 y/o LP sin fallo de adjudicación.
        6. INV3 y/o LP sin contrato.
        7. INV3 y/o LP sin finiquito.
        8. Inconsistencias en el monto reportado entre la PNT y Compranet.
        9. Inconsistencias entre lo publicado en Compranet y en PNT
    """
    ad_cols = ['LIGA_AUTORIZACION', 'REF_COTIZACIONES', 'LIGA_CONTRATO']
    lp_cols = ['LIGA_CONVOCATORIA', 'LIGA_FALLO', 'LIGA_CONTRATO', 'LIGA_FINIQUITO']
    id_cols = [
        'NUMERO_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        'TIPO_CONTRATACION',
        'PROVEEDOR_CONTRATISTA'
    ]

    merged = df_procs.merge(df_sipot, on=id_cols, how='left', indicator=True)

    # Fallas
    is_adj = merged['TIPO_PROCEDIMIENTO'] == 'ADJUDICACION DIRECTA'
    is_lic = ((merged['TIPO_PROCEDIMIENTO'] == 'LICITACION PUBLICA') |
              (merged['TIPO_PROCEDIMIENTO'] == 'INVITACION A CUANDO MENOS TRES'))
    missing = merged['_merge'] == 'left_only'
    f1 = ~missing & is_adj & merged.LIGA_AUTORIZACION.isnull()
    f2 = ~missing & is_adj & merged.REF_COTIZACIONES.isnull()
    f3 = ~missing & is_adj & merged.LIGA_CONTRATO.isnull()
    f4 = ~missing & is_lic & merged.LIGA_CONVOCATORIA.isnull()
    f5 = ~missing & is_lic & merged.LIGA_FALLO.isnull()
    f6 = ~missing & is_lic & merged.LIGA_CONTRATO.isnull()
    f7 = ~missing & is_lic & merged.LIGA_FINIQUITO.isnull()
    f8 = ~missing & (merged.IMPORTE_PESOS != merged.PRECIO_TOTAL)
    f9 = merged._merge == 'left_only'

    # Agrega features de fallas como 1/0
    fallas = pd.concat([f1, f2, f3, f4, f5, f6, f7, f8, f9], axis=1)
    fallas = fallas.astype(int)
    fallas.columns = [
        'ad_sin_autorizacion',
        'ad_sin_cotizacion',
        'ad_sin_contrato',
        'inv3_lp_sin_convocatoria',
        'inv3_lp_sin_fallo',
        'inv3_lp_sin_contrato',
        'inv3_lp_sin_finiquito',
        'inconsistencias_monto_pnt_compranet',
        'inconsistencias_publicacion_pnt_compranet'
    ]

    # Remueve columnas utilizadas para los cálculos
    merged.drop(ad_cols + lp_cols + ['PRECIO_TOTAL', '_merge'], axis=1, inplace=True)

    df_feature = pd.concat([merged, fallas], axis=1)

    return df_feature


def plazos_cortos(df_procs: DataFrame,
                  df_parts: DataFrame) -> DataFrame:
    """
    Calcula indicadores necesarios por contratos para calcular Plazos cortos.
    P. ej. si existió competencia o si los procesos limitaron la participación.
        1. Diferencia entre la Fecha de publicación del anuncio y Fecha de apertura de propuestas
        2. Número de empresas que presentaron propuesta
        3. Plazos cortos nacionales
        4. Plazos cortos internacionales
        5. Plazos cortos internacionales bajo la cobertura de tratados

    Utiliza las tablas de procedimientos y participantes
    """
    res = df_procs.copy()

    # 1. Diferencia de días entre ambas fechas.
    f1 = (res['FECHA_APERTURA_PROPOSICIONES'] - res['PROC_F_PUBLICACION']).dt.days
    res = res.assign(diff_anuncio_apertura=f1)

    # 2. Número total de propuestas por proceso.
    # Para esto debemos ligar procedimientos y participaciones
    # A pesar de que CODIGO_CONTRATO es único en la tabla de procedimientos
    # La tabla de participantes no tiene este identificador, y usa NUMERO_PROCEDIMIENTO
    # el cual tiene alrededor de 25% de duplicados en los procedimientos.
    # Usando una llave compuesta reducimos los duplicados a menos del 1%:
    keys = [
        'NUMERO_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        'TIPO_CONTRATACION',
        'FECHA_INICIO'
    ]
    # La manera de agrupar las participaciones (encontradas en el SIPOT de la PNT)
    # es utilizando la columna REF_PARTICIPANTES que hace referencia a un identificador
    # utilizado para ligar la tabla principal con el detalle de participantes por proceso.
    participaciones = (df_parts.groupby(keys + ['REF_PARTICIPANTES'])
                       .PROVEEDOR_CONTRATISTA.count()
                       .reset_index()
                       .rename(columns={'PROVEEDOR_CONTRATISTA': 'num_propuestas'}))

    # Anexamos num. de participaciones a la tabla resultado
    res = res.merge(participaciones, on=keys, how='left')
    # Podemos asumir que aunque no esten en la tabla de participantes, al menos tuvieron 1 ganador
    res['num_propuestas'] = res['num_propuestas'].fillna(1)
    res['num_propuestas'] = res['num_propuestas'].astype(int)
    res = res.drop('REF_PARTICIPANTES', axis=1)

    # Cuenta el número de empresas que presentaron propuesta cuando hay corto plazo;
    # cero de lo contrario.
    # 3. Si diff entre fechas de anuncio y apertura de propuestas <15
    res['plazos_cortos_nacionales'] = np.where(res['diff_anuncio_apertura'] < 15,
                                               res['num_propuestas'], 0)
    # 4. Si diff entre fechas de anuncio y apertura de propuestas <20
    res['plazos_cortos_internacionales'] = np.where(res['diff_anuncio_apertura'] < 20,
                                                    res['num_propuestas'], 0)
    # 5. Si diff entre fechas de anuncio y apertura de propuestas <40
    res['plazos_cortos_internacionales_bajo_tratados'] = np.where(res['diff_anuncio_apertura'] < 40,
                                                                  res['num_propuestas'], 0)

    return res
