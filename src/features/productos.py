#!/usr/bin/env python

"""
Los productos son nuevos subíndices calculados
a nivel contrato y año.

Algunos indicadores del IRC hacen uso de estos
cálculos pero los agrupan a nivel UC.
"""

import pandas as pd
import numpy as np

DataFrame = pd.DataFrame

# Columnas para cruzar Compranet con SIPOT (PNT)
id_cols = [
    'NUMERO_PROCEDIMIENTO',
    'TIPO_PROCEDIMIENTO',
    'TIPO_CONTRATACION',
    'PROVEEDOR_CONTRATISTA'
]


def favoritismo(df_procs: DataFrame,
                df_parts: DataFrame, **kwargs) -> DataFrame:
    """
    Indicadores para calcular Favoritismo.

    Favoritismo mide si las empresas han sido favorecidas por un alto número
    de contratos, monto adjudicado y éxito en sus participaciones.

    Para cada procedimiento se calculan anualmente
    por empresa ganadora y UC.

    Variables:
        1. Número de contratos ganados por empresa LP
        2. Número de contratos ganados por empresa IR
        3. Número de contratos ganados por empresa AD
        4. Número de propuestas presentadas por empresa LP.
        5. Número de propuestas presentadas por empresa IR.
        6. Monto adjudicado por empresa LP.
        7. Monto adjudicado por empresa IR.
        8. Monto adjudicado por empresa AD.
        9. Frecuencia de contratos ganados por LP.
        A. Frecuencia de contratos ganados por IR.
        B. Frecuencia de contratos ganados por AD.
        C. Porcentaje de éxito empresa por LP
        D. Porcentaje de éxito empresa por IR
        E. Empresa favorita LP
        F. Empresa favorita IR
        G. Empresa favorita AD
        H. Favoritismo
    """
    # Para descartar tipos de procedimientos marcados como OTRO
    tipo_procs = [
        'ADJUDICACION DIRECTA',
        'INVITACION A CUANDO MENOS TRES',
        'LICITACION PUBLICA'
    ]

    procs = df_procs.copy()
    procs = procs[procs.TIPO_PROCEDIMIENTO.isin(tipo_procs)]
    # De este no haremos copia, trabajaremos con la referencia
    parts = df_parts[df_parts.TIPO_PROCEDIMIENTO.isin(tipo_procs)]

    feature_keys = ['PROVEEDOR_CONTRATISTA', 'CLAVEUC']
    procs_index = [procs.PROVEEDOR_CONTRATISTA, procs.CLAVEUC]

    # Número de contratos (1 - 3)
    contratos = (pd.crosstab(index=procs_index,
                             columns=procs.TIPO_PROCEDIMIENTO,
                             margins=True,
                             margins_name='num_ganados')
                 .rename(columns={
                     'LICITACION PUBLICA': 'num_ganados_lp',
                     'INVITACION A CUANDO MENOS TRES': 'num_ganados_ir',
                     'ADJUDICACION DIRECTA': 'num_ganados_ad'
                 })
                 .drop('num_ganados', axis=0))

    if 'num_ganados_ad' not in contratos.columns:
        contratos['num_ganados_ad'] = 0
    if 'num_ganados_ir' not in contratos.columns:
        contratos['num_ganados_ir'] = 0
    if 'num_ganados_lp' not in contratos.columns:
        contratos['num_ganados_lp'] = 0

    # Frecuencia de contratos (9 - B)
    # Fórmula (para LP) =
    # Número de contratos ganados por empresa LP /
    # Máximo de contratos adjudicados por UC en el año * 100
    contratos_uc = (contratos.groupby('CLAVEUC')
                    .num_ganados.sum()
                    .reset_index()
                    .rename(columns={'num_ganados': 'contratos_uc'}))

    contratos = contratos.reset_index()
    frecuencias = contratos.merge(contratos_uc, on='CLAVEUC')

    frecuencias['frec_ganados_ad'] = frecuencias.num_ganados_ad.divide(frecuencias.contratos_uc) * 100
    frecuencias['frec_ganados_ir'] = frecuencias.num_ganados_ir.divide(frecuencias.contratos_uc) * 100
    frecuencias['frec_ganados_lp'] = frecuencias.num_ganados_lp.divide(frecuencias.contratos_uc) * 100

    # Monto adjudicado (6 - 8)
    monto = (pd.crosstab(index=procs_index,
                         columns=procs.TIPO_PROCEDIMIENTO,
                         values=procs.IMPORTE_PESOS,
                         aggfunc='sum',
                         margins=True,
                         margins_name='monto_ganado')
             .rename(columns={
                 'LICITACION PUBLICA': 'monto_ganado_lp',
                 'INVITACION A CUANDO MENOS TRES': 'monto_ganado_ir',
                 'ADJUDICACION DIRECTA': 'monto_ganado_ad'
             })
             .fillna(0)
             .drop('monto_ganado', axis=0))

    if 'monto_ganado_ad' not in monto.columns:
        monto['monto_ganado_ad'] = 0.0
    if 'monto_ganado_ir' not in monto.columns:
        monto['monto_ganado_ir'] = 0.0
    if 'monto_ganado_lp' not in monto.columns:
        monto['monto_ganado_lp'] = 0.0

    # Empezamos a juntar variables (1 - 3, 6 - 8, 9 - B)
    variables = frecuencias.merge(monto, on=feature_keys)

    # Propuestas presentadas (4 - 5)
    parts_index = [parts.PROVEEDOR_CONTRATISTA, parts.CLAVEUC]
    propuestas = (pd.crosstab(index=parts_index,
                              columns=parts.TIPO_PROCEDIMIENTO)
                  .rename(columns={
                      'LICITACION PUBLICA': 'num_propuestas_lp',
                      'INVITACION A CUANDO MENOS TRES': 'num_propuestas_ir'
                  })
                  .drop(['ADJUDICACION DIRECTA'], axis=1))

    if 'num_propuestas_ir' not in propuestas.columns:
        propuestas['num_propuestas_ir'] = 0
    if 'num_propuestas_lp' not in propuestas.columns:
        propuestas['num_propuestas_lp'] = 0

    # Éxito de la empresa (C - D)
    # Fórmula =
    #   Número de contratos ganados por empresa LP /
    #   Número de propuestas presentadas por empresa LP * 100
    # Dado que la tabla de participantes (parts) es un subconjunto de procs
    # Tendremos que hacer este cálculo solamente con parts
    # No podremos reciclar el dataframe contratos,
    # lo tenemos que hacer sobre las propuestas.
    tipo_procs = ['INVITACION A CUANDO MENOS TRES', 'LICITACION PUBLICA']
    m = ((parts.TIPO_PROCEDIMIENTO.isin(tipo_procs)) &
         (parts.ESTATUS_DE_PROPUESTA == 'GANADOR'))
    concursos_ganados = parts[m]
    parts_index = [concursos_ganados.PROVEEDOR_CONTRATISTA, concursos_ganados.CLAVEUC]
    concursos_ganados = (pd.crosstab(index=parts_index,
                                     columns=concursos_ganados.TIPO_PROCEDIMIENTO)
                         .rename(columns={
                             'LICITACION PUBLICA': 'exito_lp',
                             'INVITACION A CUANDO MENOS TRES': 'exito_ir'
                         }))

    propuestas = propuestas.merge(concursos_ganados, on=feature_keys, how='left')
    propuestas['pc_exito_ir'] = propuestas.exito_ir.divide(propuestas.num_propuestas_ir) * 100
    propuestas['pc_exito_lp'] = propuestas.exito_lp.divide(propuestas.num_propuestas_lp) * 100

    # Agregamos variables (4 - 5 y C - D)
    # Las variables que vienen de la tabla de participantes
    # hay que hacerles LEFT JOIN, porque algunos procs no estarán ahí.
    variables = variables.merge(propuestas, on=feature_keys, how='left')

    # Empresa favorita (E - G) =
    # Monto adjudicado por empresa LP * .40 +
    # Frecuencia de contratos ganados por LP * .20 +
    # Porcentaje de éxito empresa por LP * .40
    # Para AD la fórmula cambia =
    # Monto adjudicado por empresa AD * .66 +
    # Frecuencia de contratos ganados por AD * .33
    variables['favorita_ad'] = (variables['monto_ganado_ad'] * .66 +
                                variables['frec_ganados_ad'] * .33)
    variables['favorita_ir'] = (variables['monto_ganado_ir'] * .40 +
                                variables['frec_ganados_ir'] * .20 +
                                variables['pc_exito_ir'] * .40)
    variables['favorita_lp'] = (variables['monto_ganado_lp'] * .40 +
                                variables['frec_ganados_lp'] * .20 +
                                variables['pc_exito_lp'] * .40)

    # Favoritismo
    # Empresa favorita LP * .15 +
    # Empresa favorita IR * .35 +
    # Empresa favorita AD * .50
    f = ['favorita_ad', 'favorita_ir', 'favorita_lp']
    variables.loc[:, f] = variables.loc[:, f].fillna(0)
    variables['favoritismo'] = (variables['favorita_lp'] * .15 +
                                variables['favorita_ir'] * .35 +
                                variables['favorita_ad'] * .50)

    variables = variables.drop([
        'contratos_uc',
        'exito_ir',
        'exito_lp',
        'monto_ganado',
        'num_ganados'
    ], axis=1)

    # El último merge sí se hace con el dataframe original
    return df_procs.merge(variables, on=feature_keys, how='left')


def tajada_por_empresa(df_procs: DataFrame) -> DataFrame:
    """
    En cada UC y año calcula cuánto se lleva cada empresa
    1. Monto adjudicado por empresa
    2. Share por empresa
    """
    procs = df_procs.copy()

    # 1. Monto total adjudicado a cada empresa en cada UC y cada año.
    res = (procs.groupby(['CLAVEUC', 'PROVEEDOR_CONTRATISTA'])
           .IMPORTE_PESOS.sum()
           .reset_index()
           .rename(columns={'IMPORTE_PESOS': 'monto_por_empresa'}))

    # 2. Monto adjudicado por empresa / Monto total por UC por año
    tot = (procs.groupby(['CLAVEUC'])
           .IMPORTE_PESOS.sum()
           .reset_index()
           .rename(columns={'IMPORTE_PESOS': 'monto_total'}))

    res = res.merge(tot)

    res['share_por_empresa'] = res.monto_por_empresa.divide(res.monto_total)
    res.drop('monto_total', axis=1, inplace=True)

    return pd.merge(procs, res, how='left')


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
    daily_keys = ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'TIPO_CONTRATACION', 'FECHA_INICIO']
    monto_diario = (df.groupby(daily_keys, as_index=False)
                    .IMPORTE_PESOS.sum()
                    .rename(columns={'IMPORTE_PESOS': 'monto_diario_empresa'}))

    # 3. Monto acumulado de contratos AD en la misma semana por empresa por UC
    week_keys = ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'TIPO_CONTRATACION', 'semana']
    monto_semanal = (df.groupby(week_keys, as_index=False)
                     .IMPORTE_PESOS.sum()
                     .rename(columns={'IMPORTE_PESOS': 'monto_semanal_empresa'}))

    # 4. Número de contratos AD por semana por empresa por UC.
    contratos_semanales = (df.groupby(week_keys, as_index=False)
                           .NUMERO_PROCEDIMIENTO.count()
                           .rename(columns={'NUMERO_PROCEDIMIENTO': 'contratos_semanales_empresa'}))

    # 5. Número de contratos AD por día por empresa por UC.
    contratos_diarios = (df.groupby(daily_keys, as_index=False)
                         .NUMERO_PROCEDIMIENTO.count()
                         .rename(columns={'NUMERO_PROCEDIMIENTO': 'contratos_diarios_empresa'}))

    # 6. Contrato fraccionado?
    # Si en una semana una UC otorga a una empresa más de 1 contrato AD y el
    # monto acumulado supera máximos autorizados para AD en ese año.

    # Obtiene los máximos
    vars = (pd.merge(df_maximos, monto_diario,
                     left_on='Tipo de contratación',
                     right_on='TIPO_CONTRATACION')
            .drop('Tipo de contratación', axis=1))

    # Mezcla las columnas
    vars = vars.merge(monto_semanal)
    vars = vars.merge(contratos_semanales)
    vars = vars.merge(contratos_diarios)

    # Marca los que exceden
    fraccionado = (
        (vars.monto_semanal_empresa > vars['maximo_permitido']) &
        (vars.contratos_semanales_empresa > 1))
    vars = vars.assign(fraccionado=fraccionado)

    # Agrega las variables al resultado
    df = df.merge(vars)

    # Mezcla con la tabla de procedimientos original
    return df_procs.merge(df, how='left')


def convenios_entre_entes_publicos(df_procs: DataFrame,
                                   df_sipot: DataFrame) -> DataFrame:
    """
    Identifica aquellos procesos bajo los artículos 1 de la LAASSP
    o la LOPSRM en "Motivos y fundamentos legales para realizar la
    Adjudicación Directa".
    """
    ad_sipot = df_sipot.copy()
    ad_sipot = ad_sipot[ad_sipot.TIPO_PROCEDIMIENTO == 'ADJUDICACION DIRECTA']

    leyadq = (ad_sipot.MOTIVOS_ADJUDICACION
              .str.contains(r'LEY +DE +ADQ\w+ *Y? *AR\w+', regex=True, na=False))
    laassp = (ad_sipot.MOTIVOS_ADJUDICACION
              .str.contains('LAASSP', na=False))

    leyobr = (ad_sipot.MOTIVOS_ADJUDICACION
              .str.contains(r'LEY +DE +OBRAS? +PU', regex=True, na=False))
    lopsrm = (ad_sipot.MOTIVOS_ADJUDICACION
              .str.contains('LOPSRM', na=False))

    ad_sipot['LAASSP'] = (leyadq | laassp).astype(int)
    ad_sipot['LOPSRM'] = (leyobr | lopsrm).astype(int)

    # Mezclamos con la tabla de procedimientos
    convenios = ad_sipot[id_cols + ['LAASSP', 'LOPSRM']]
    return pd.merge(df_procs, convenios, how='left')


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

    merged = df_procs.merge(df_sipot, on=id_cols, how='left', indicator=True)
    merged = merged.rename(columns={
        'FECHA_INICIO_x': 'FECHA_INICIO',
        'CODIGO_EXPEDIENTE_x': 'CODIGO_EXPEDIENTE'
    })

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

    df_feature = pd.concat([merged, fallas], axis=1)

    # Va a filtrar columnas utilizadas para los cálculos
    cols = list(df_procs.columns) + list(fallas.columns)

    return df_feature.loc[:, cols]


def colusion(df_procs: DataFrame,
             df_parts: DataFrame,
             df_fantasma: DataFrame) -> DataFrame:
    """
    Calcula variables para detectar colusión.

    Utiliza la tabla de participantes para calcular las variables,
    y regresa una mezcla con la tabla principal de procedimientos.

    Los cálculos se hacen sobre participaciones de IR y LP con más
    de un participante.
    """

    """
    1. Participaciones totales por empresa.
    Número de participaciones totales (IR + LP) por cada empresa por UC por año.
    """
    # Selecciona el subconjunto de participaciones de IR|LP con más de un participante
    is_lic = ((df_parts['TIPO_PROCEDIMIENTO'] == 'LICITACION PUBLICA') |
              (df_parts['TIPO_PROCEDIMIENTO'] == 'INVITACION A CUANDO MENOS TRES'))
    by_ref = (df_parts.groupby('REF_PARTICIPANTES').size())
    con_participantes = df_parts.REF_PARTICIPANTES.isin(by_ref[by_ref > 1].index)

    df_parts_lic = df_parts.copy()[is_lic & con_participantes]

    participaciones_totales_empresa = (df_parts_lic.groupby(['PROVEEDOR_CONTRATISTA'])
                                       .NUMERO_PROCEDIMIENTO.count()
                                       .reset_index()
                                       .rename(columns={'NUMERO_PROCEDIMIENTO': 'participaciones_totales_empresa'}))

    """
    2. Número participaciones en conjunto de la empresa ganadora y las participantes.
    Número participaciones en conjunto de la empresa ganadora y cada una de las empresas
    participantes por proceso por UC por año.
    """

    # Columnas para agrupar participaciones
    p_cols = [c for c in id_cols if c != 'PROVEEDOR_CONTRATISTA']

    # Creamos filas por cada instancia de ganador vs perdedor por procedimiento
    # i.e. si tenemos un ganador y 2 perdedores, entonces tendremos 2 filas
    W = df_parts_lic[df_parts_lic.ESTATUS_DE_PROPUESTA == 'GANADOR']
    L = df_parts_lic[df_parts_lic.ESTATUS_DE_PROPUESTA == 'PERDEDOR']
    procs_con_tuplas = (pd.merge(W, L, on=p_cols, how='left')
                        .rename(columns={
                            'PROVEEDOR_CONTRATISTA_x': 'GANADOR',
                            'PROVEEDOR_CONTRATISTA_y': 'PERDEDOR',
                            'REF_PARTICIPANTES_x': 'REF_PARTICIPANTES'
                        })
                        .loc[:, p_cols + ['REF_PARTICIPANTES', 'GANADOR', 'PERDEDOR']])

    # Cuenta las ocurrencias de cada tupla encontrada en cada proceso
    parts_por_tupla = (pd.crosstab(procs_con_tuplas['GANADOR'], procs_con_tuplas['PERDEDOR'])
                       .stack()
                       .reset_index()
                       .rename(columns={0: 'num_participaciones_en_conjunto'}))

    en_conjunto = pd.merge(procs_con_tuplas,
                           parts_por_tupla,
                           left_on=['GANADOR', 'PERDEDOR'],
                           right_on=['GANADOR', 'PERDEDOR'])

    en_conjunto = (en_conjunto.groupby(p_cols + ['GANADOR'])
                   .num_participaciones_en_conjunto.sum()
                   .reset_index()
                   .rename(columns={'GANADOR': 'PROVEEDOR_CONTRATISTA'}))

    """
    3. Jaccard por proceso de compra
    Proporción en la que dos o más empresas participan de manera conjunta,
    en función del total de sus participaciones.
    # de participaciones conjuntas / (
        # de participaciones empresa ganadora + # de participaciones empresa n -
        # de participaciones conjuntas entre ganadora y n
    ) * 100

    Nota: Este campo es temporal para calcular la Participación conjunta (variable 4).
    """

    # Unimos la info de procesos que tiene las variaciones de ganador-perdedor
    # con las participaciones conjuntas correspondientes.
    tuplas_de_jaccard = pd.merge(procs_con_tuplas, parts_por_tupla)
    # Luego a través de las llaves GANADOR y PERDEDOR trae la cuenta total de cada empresa
    tuplas_de_jaccard = (tuplas_de_jaccard.merge(participaciones_totales_empresa,
                                                 left_on='GANADOR',
                                                 right_on='PROVEEDOR_CONTRATISTA',
                                                 how='left')
                         .drop('PROVEEDOR_CONTRATISTA', axis=1)
                         .rename(columns={'participaciones_totales_empresa': 'participaciones_totales_ganador'}))
    tuplas_de_jaccard = (tuplas_de_jaccard.merge(participaciones_totales_empresa,
                                                 left_on='PERDEDOR',
                                                 right_on='PROVEEDOR_CONTRATISTA',
                                                 how='left')
                         .drop('PROVEEDOR_CONTRATISTA', axis=1)
                         .rename(columns={'participaciones_totales_empresa': 'participaciones_totales_perdedor'}))

    tuplas_de_jaccard['jaccard'] = (tuplas_de_jaccard.num_participaciones_en_conjunto.divide(
        tuplas_de_jaccard.participaciones_totales_ganador +
        tuplas_de_jaccard.participaciones_totales_perdedor -
        tuplas_de_jaccard.num_participaciones_en_conjunto)) * 100

    """
    4. Participación conjunta (colusión)
    (Suma de Índices de Jaccard entre la empresa ganadora G y
     cada una de las empresas participantes P por proceso /
        Número de empresas que presentaron propuesta - 1) * 100
    """
    perdedores_por_proceso = (tuplas_de_jaccard.groupby(p_cols + ['GANADOR'])
                              .REF_PARTICIPANTES.count()
                              .reset_index()
                              .rename(columns={'REF_PARTICIPANTES': 'perdedores_por_proceso'}))

    res = (tuplas_de_jaccard.groupby(p_cols + ['GANADOR'])
           .jaccard.sum()
           .reset_index()
           .rename(columns={'jaccard': 'suma_jaccard'})
           .merge(perdedores_por_proceso))

    res['colusion'] = res.suma_jaccard.divide(res.perdedores_por_proceso) * 100

    """
    5. Propuestas artificiales
    Empresas participantes con match en base de datos del SAT de RFCs fantasma.

    Revisamos tanto ganador como perdedores del proceso.
    """
    con_propuestas_artificiales = (df_parts_lic.merge(df_fantasma)
                                   .rename(columns={'RFC': 'Fantasma'})
                                   .drop('Publicación página SAT definitivos', axis=1))
    tuplas_de_jaccard = (tuplas_de_jaccard.merge(con_propuestas_artificiales,
                                                 left_on='GANADOR',
                                                 right_on='PROVEEDOR_CONTRATISTA',
                                                 how='left')
                           .drop('PROVEEDOR_CONTRATISTA', axis=1)
                           .rename(columns={'Fantasma': 'fantasma_ganador'}))
    tuplas_de_jaccard = (tuplas_de_jaccard.merge(con_propuestas_artificiales,
                                                 left_on='PERDEDOR',
                                                 right_on='PROVEEDOR_CONTRATISTA',
                                                 how='left')
                           .drop('PROVEEDOR_CONTRATISTA', axis=1)
                           .rename(columns={'Fantasma': 'fantasma_perdedor'}))
    tuplas_de_jaccard.fantasma_ganador = tuplas_de_jaccard.fantasma_ganador.notna().astype(int)
    tuplas_de_jaccard.fantasma_perdedor = tuplas_de_jaccard.fantasma_perdedor.notna().astype(int)
    tuplas_de_jaccard['propuestas_artificiales'] = (tuplas_de_jaccard.fantasma_ganador +
                                                    tuplas_de_jaccard.fantasma_perdedor)

    # Ahora agregamos por proceso la suma de las propuestas artificiales que
    # pudieron haber entrado tanto a través del ganador como de los perdedores.
    procs_con_artificiales = (tuplas_de_jaccard.groupby(p_cols + ['REF_PARTICIPANTES'])
                              .propuestas_artificiales.sum()
                              .reset_index()
                              .drop('REF_PARTICIPANTES', axis=1))

    # Hace las ultimas concatenaciones y prepara el formato de regreso
    res.rename(columns={'GANADOR': 'PROVEEDOR_CONTRATISTA'}, inplace=True)
    res = res.merge(participaciones_totales_empresa, how='left')
    res = res.merge(en_conjunto, how='left')
    res = res.merge(procs_con_artificiales, how='left')

    return pd.merge(df_procs, res, how='left')


def ganador_mas_barato(df_procs: DataFrame,
                       df_parts: DataFrame) -> DataFrame:
    """
    Revisa si la empresa ganadora fue la propuesta más baja.
    """
    minimos = (df_parts.groupby('REF_PARTICIPANTES')
               .PRECIO_TOTAL.min()
               .reset_index()
               .rename(columns={'PRECIO_TOTAL':'PRECIO_MAS_BAJO'}))

    df = pd.merge(df_parts, minimos, how='left')
    ganador = df.ESTATUS_DE_PROPUESTA == 'GANADOR'
    masbara = df.PRECIO_TOTAL == df.PRECIO_MAS_BAJO
    df['mas_barato'] = (ganador & masbara).astype(int)

    df.drop(['ESTATUS_DE_PROPUESTA', 'REF_PARTICIPANTES'], axis=1, inplace=True)
    return pd.merge(df_procs, df, how='left')


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
