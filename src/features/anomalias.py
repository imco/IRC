#!/usr/bin/env python

# Created by Raul Peralta-Lozada (11/10/17)
import pandas as pd
from typing import List, Tuple

DataFrame = pd.DataFrame


def monto_con_rfc_fantasma(df_procs: DataFrame,
                           df_rfc_fantasma: DataFrame,
                           **kwargs) -> DataFrame:
    """
    Usa tabla de procedimientos y la RFCs (apocrifos)
    Indicador:
        Monto asignado a empresas fantasma.
    """
    df_feature = pd.DataFrame(
        data=df_procs.CLAVEUC.unique(), columns=['CLAVEUC'])
    df = pd.merge(df_procs, df_rfc_fantasma,
                  on='PROVEEDOR_CONTRATISTA', how='inner')
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False).IMPORTE_PESOS.sum()
    # número de proveedores fantasma por uc
    pocs_distintos = monto_por_contrato.groupby(
        'CLAVEUC').PROVEEDOR_CONTRATISTA.nunique()
    pocs_distintos = pocs_distintos.reset_index()
    pocs_distintos = pocs_distintos.rename(
        columns={'PROVEEDOR_CONTRATISTA': 'num_proveedores_fantasma'})
    # número de contratos con rfc fantasmas por uc
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'contratos_con_fantasmas'})
    contratos_total = contratos_total.groupby(
        'CLAVEUC', as_index=False).contratos_con_fantasmas.sum()
    # monto con rfc fantasmas por uc
    monto_uc_contratos = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.groupby('CLAVEUC',
        as_index=False).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.rename(
        columns={'IMPORTE_PESOS': 'monto_con_rfc_fantasma'})
    # TODO: separar los features en otras funciones
    # join the features
    df_feature = pd.merge(df_feature, pocs_distintos,
                          on='CLAVEUC', how='left')
    df_feature = pd.merge(df_feature, contratos_total,
                          on='CLAVEUC', how='left')
    df_feature = pd.merge(df_feature, monto_uc_contratos,
                          on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    df_feature = df_feature.loc[:, ['CLAVEUC', 'monto_con_rfc_fantasma']]
    return df_feature


def monto_con_sancionados(df_procs: DataFrame,
                          df_sancionados: DataFrame,
                          **kwargs) -> DataFrame:
    """
    Usa tabla de procedimientos y la de sancionados
    Indicador:
        Monto asignado a empresas sancionadas.
    """
    df_feature = pd.DataFrame(
        data=df_procs.CLAVEUC.unique(), columns=['CLAVEUC'])
    df = pd.merge(df_procs, df_sancionados,
                  on='PROVEEDOR_CONTRATISTA', how='inner')
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False).IMPORTE_PESOS.sum()
    # número de proveedores fantasma por uc
    pocs_distintos = monto_por_contrato.groupby(
        'CLAVEUC').PROVEEDOR_CONTRATISTA.nunique()
    pocs_distintos = pocs_distintos.reset_index()
    pocs_distintos = pocs_distintos.rename(
        columns={'PROVEEDOR_CONTRATISTA': 'num_proveedores_sancionados'})
    # número de contratos con rfc fantasmas por uc
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'contratos_con_sancionados'})
    contratos_total = contratos_total.groupby('CLAVEUC',
        as_index=False).contratos_con_sancionados.sum()
    # monto con rfc fantasmas por uc
    monto_uc_contratos = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.groupby(
        'CLAVEUC', as_index=False).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.rename(
        columns={'IMPORTE_PESOS': 'monto_con_sancionados'})
    # join the features
    df_feature = pd.merge(df_feature, pocs_distintos,
                          on='CLAVEUC', how='left')
    df_feature = pd.merge(df_feature, contratos_total,
                          on='CLAVEUC', how='left')
    df_feature = pd.merge(
        df_feature, monto_uc_contratos, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    df_feature = df_feature.loc[:, ['CLAVEUC', 'monto_con_sancionados']]
    return df_feature


def pc_contratos_con_convenio(df: DataFrame, **kwargs) -> DataFrame:
    """
    Usa tabla de procedimientos
    Indicador:
        Porcentaje de procedimientos con convenio modificatorio.
    """
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC',
         'PROVEEDOR_CONTRATISTA', 'NUMERO_PROCEDIMIENTO',
         'CODIGO_CONTRATO', 'CONVENIO_MODIFICATORIO'],
        as_index=False).IMPORTE_PESOS.sum()

    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO',
         'CONVENIO_MODIFICATORIO']).CODIGO_CONTRATO.nunique()

    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.groupby(
        ['CLAVEUC', 'CONVENIO_MODIFICATORIO'],
        as_index=False).CODIGO_CONTRATO.sum()
    contratos_total = contratos_total.pivot(index='CLAVEUC',
        columns='CONVENIO_MODIFICATORIO', values='CODIGO_CONTRATO')
    contratos_total = contratos_total.fillna(0)

    num_contratos = contratos_total.sum(axis=1)
    # TODO: cambiar toda esta parte, el nombre final es otro
    contratos_total = contratos_total.rename(
        columns={
            c: 'pc_contratos_convenio_' + c.lower().replace(' ', '_')
            for c in contratos_total.columns
        }
    )

    contratos_total = contratos_total * 100
    contratos_total = contratos_total.divide(num_contratos, axis='index')

    # 2013 parece que no trae convenios así que llenamos una columna con ceros.
    if 'pc_contratos_convenio_si' not in contratos_total.columns:
        contratos_total['pc_contratos_convenio_si'] = 0

    contratos_total.columns.name = ''
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'pc_contratos_convenio_si': 'pc_contratos_con_convenio'})
    df_feature = contratos_total.loc[:, ['CLAVEUC', 'pc_contratos_con_convenio']]
    return df_feature


def pc_licitaciones_nacionales_menor_15_dias(df: DataFrame,
                                             **kwargs) -> DataFrame:
    """
    Porcentaje de licitaciones nacionales
    cuyo plazo entre publicacion y apertura fue
    menor a 15 días
    Indicador:
        Porcentaje de las licitaciones nacionales cuyo plazo fue menor a 15 días.
    """
    df = df.copy()
    df_feature = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    # Sólo licitaciones nacionales
    tipos_validos = {'LICITACION PUBLICA',
                     'INVITACION A CUANDO MENOS TRES',
                     'LICITACION PUBLICA CON OSD'}
    df = df.loc[
        (df.CARACTER == 'NACIONAL') &
        (df.TIPO_PROCEDIMIENTO.isin(tipos_validos))
    ]
    # columnas de interés
    cols = [
        'CLAVEUC', 'NUMERO_PROCEDIMIENTO',
        'FECHA_APERTURA_PROPOSICIONES',
        'PROC_F_PUBLICACION'
    ]
    df = df.loc[:, cols].drop_duplicates()
    delta_dias = (
        df.FECHA_APERTURA_PROPOSICIONES - df.PROC_F_PUBLICACION
    ).dt.days
    df = df.assign(delta_dias=delta_dias.fillna(0))
    df = df.assign(licitaciones_menor_15=(df.delta_dias < 15))
    df = (df.groupby(['CLAVEUC', 'licitaciones_menor_15'])
            .NUMERO_PROCEDIMIENTO.nunique()
            .reset_index()
            .pivot(index='CLAVEUC',
                   columns='licitaciones_menor_15',
                   values='NUMERO_PROCEDIMIENTO')
            .rename(columns={True: 'pc_licitaciones_menor_15'}))
    valor_pc = (df.pc_licitaciones_menor_15 * 100).divide(df.sum(axis=1))
    df = (df.assign(pc_licitaciones_menor_15=valor_pc.fillna(0))
            .reset_index()
            .loc[:, ['CLAVEUC', 'pc_licitaciones_menor_15']])
    # left join
    df_feature = pd.merge(df_feature, df, on='CLAVEUC', how='left')
    feature = df_feature.pc_licitaciones_menor_15.fillna(0)
    df_feature = df_feature.assign(
        pc_licitaciones_nacionales_menor_15_dias=feature
    )
    df_feature = df_feature.loc[
                 :, ['CLAVEUC', 'pc_licitaciones_nacionales_menor_15_dias']]
    return df_feature


def pc_licitaciones_internacionales_menor_20_dias(df: DataFrame,
                                                  **kwargs) -> DataFrame:
    """
    Porcentaje de licitaciones internacionales
    cuyo plazo entre publicacion y apertura fue
    menor a 20 días
    Indicador:
        Porcentaje de las licitaciones internacionales cuyo plazo fue menor a 20 días.
    """
    df = df.copy()
    df_feature = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    # Sólo licitaciones nacionales
    tipos_validos = {'LICITACION PUBLICA',
                     'INVITACION A CUANDO MENOS TRES',
                     'LICITACION PUBLICA CON OSD'}
    df = df.loc[
        (df.TIPO_PROCEDIMIENTO.isin(tipos_validos)) &
        (df.CARACTER.isin({'INTERNACIONAL', 'INTERNACIONAL ABIERTA'}))
    ]
    # columnas de interés
    cols = [
        'CLAVEUC', 'NUMERO_PROCEDIMIENTO',
        'FECHA_APERTURA_PROPOSICIONES',
        'PROC_F_PUBLICACION'
    ]
    df = df.loc[:, cols].drop_duplicates()
    delta_dias = (
        df.FECHA_APERTURA_PROPOSICIONES - df.PROC_F_PUBLICACION
    ).dt.days
    df = df.assign(delta_dias=delta_dias.fillna(0))
    df = df.assign(licitaciones_menor_20=(df.delta_dias < 20))
    df = (df.groupby(['CLAVEUC', 'licitaciones_menor_20'])
            .NUMERO_PROCEDIMIENTO.nunique()
            .reset_index()
            .pivot(index='CLAVEUC',
                   columns='licitaciones_menor_20',
                   values='NUMERO_PROCEDIMIENTO')
            .rename(columns={True: 'pc_licitaciones_menor_20'}))

    if 'pc_licitaciones_menor_20' not in df.columns:
        df['pc_licitaciones_menor_20'] = 0

    valor_pc = (df.pc_licitaciones_menor_20 * 100).divide(df.sum(axis=1))
    df = (df.assign(pc_licitaciones_menor_20=valor_pc.fillna(0))
            .reset_index()
            .loc[:, ['CLAVEUC', 'pc_licitaciones_menor_20']])
    # left join
    df_feature = pd.merge(df_feature, df, on='CLAVEUC', how='left')
    feature = df_feature.pc_licitaciones_menor_20.fillna(0)
    df_feature = df_feature.assign(
        pc_licitaciones_internacionales_menor_20_dias=feature
    )
    df_feature = df_feature.loc[
                 :, ['CLAVEUC', 'pc_licitaciones_internacionales_menor_20_dias']
    ]
    return df_feature


def pc_licitaciones_internacionales_menor_40_dias(df: DataFrame,
                                                  **kwargs) -> DataFrame:
    """
    Porcentaje de licitaciones internacionales
    bajo la cobertura de tratados cuyo plazo
    entre publicacion y apertura fue menor a 40 días
    Indicador:
        Porcentaje de las licitaciones internacionales bajo la cobertura de tratados cuyo plazo fue menor a 40 días.
    """
    df = df.copy()
    df_feature = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    # Sólo licitaciones nacionales
    tipos_validos = {'LICITACION PUBLICA',
                     'INVITACION A CUANDO MENOS TRES',
                     'LICITACION PUBLICA CON OSD'}
    df = df.loc[
        (df.TIPO_PROCEDIMIENTO.isin(tipos_validos)) &
        (df.CARACTER == 'INTERNACIONAL BAJO TLC')
    ]
    # columnas de interés
    cols = [
        'CLAVEUC', 'NUMERO_PROCEDIMIENTO',
        'FECHA_APERTURA_PROPOSICIONES',
        'PROC_F_PUBLICACION'
    ]
    df = df.loc[:, cols].drop_duplicates()
    delta_dias = (
        df.FECHA_APERTURA_PROPOSICIONES - df.PROC_F_PUBLICACION
    ).dt.days
    df = df.assign(delta_dias=delta_dias.fillna(0))
    df = df.assign(licitaciones_menor_40=(df.delta_dias < 40))
    df = (df.groupby(['CLAVEUC', 'licitaciones_menor_40'])
            .NUMERO_PROCEDIMIENTO.nunique()
            .reset_index()
            .pivot(index='CLAVEUC',
                   columns='licitaciones_menor_40',
                   values='NUMERO_PROCEDIMIENTO')
            .rename(columns={True: 'pc_licitaciones_menor_40'}))

    if 'pc_licitaciones_menor_40' not in df.columns:
        df['pc_licitaciones_menor_40'] = 0

    valor_pc = (df.pc_licitaciones_menor_40 * 100).divide(df.sum(axis=1))
    df = (df.assign(pc_licitaciones_menor_40=valor_pc.fillna(0))
            .reset_index()
            .loc[:, ['CLAVEUC', 'pc_licitaciones_menor_40']])
    # left join
    df_feature = pd.merge(df_feature, df, on='CLAVEUC', how='left')
    feature = df_feature.pc_licitaciones_menor_40.fillna(0)
    df_feature = df_feature.assign(
        pc_licitaciones_internacionales_menor_40_dias=feature
    )
    df_feature = df_feature.loc[
                 :, ['CLAVEUC', 'pc_licitaciones_internacionales_menor_40_dias']
    ]
    return df_feature


def pc_estratificacion_mal_reportada(df: DataFrame,
                                     **kwargs) -> DataFrame:
    """
    Indicador:
        Estratificación de la empresa reportado por la UC y por la empresa no coinciden.
    """
    df = df.copy()
    cols = [
        'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
        'NUMERO_PROCEDIMIENTO',
        'CODIGO_EXPEDIENTE', 'CODIGO_CONTRATO'
    ]
    df = df.drop_duplicates(subset=cols)
    df = df.loc[:, cols + ['ESTRATIFICACION_MUC', 'ESTRATIFICACION_MPC']]
    estratificacion_igual = df.ESTRATIFICACION_MUC == df.ESTRATIFICACION_MPC
    df = df.assign(estratificacion_igual=estratificacion_igual)
    df_feature = (df.groupby(['CLAVEUC', 'estratificacion_igual'],
                             as_index=False)
                    .PROVEEDOR_CONTRATISTA.count())
    df_feature = df_feature.pivot(index='CLAVEUC',
                                  columns='estratificacion_igual',
                                  values='PROVEEDOR_CONTRATISTA')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = df_feature.fillna(0)
    if False not in df_feature.columns:
        # O todos reportaron su valor correctamente
        # O talvez no reportaron Estratificación,
        # como es el caso de 2018-2019.
        df_feature[False] = 0

    col_feature = 'pc_estratificacion_mal_reportada'
    df_feature = df_feature.rename(columns={False: col_feature})
    df_feature = (df_feature.reset_index()
                  .loc[:, ['CLAVEUC', col_feature]])
    df_feature.columns.name = ''
    return df_feature

# Requiere la tabla de máximos


def pc_adj_directas_excedieron_monto(df: DataFrame,
                                     df_maximos: DataFrame,
                                     **kwargs) -> DataFrame:
    """
    Indicador:
        % de las Adjudicaciones directas que rebasaron el máximo permitido.
    """
    if 'tipo_contratacion' in kwargs:
        tipo_contratacion = kwargs['tipo_contratacion']
    else:
        raise TypeError('Falta especificar tipo_contratacion')

    if 'year' in kwargs:
        años_validos = set([kwargs['year']])
    else:
        años_validos = set(range(2012, 2017))

    # df > df_procs_<tipo>
    # df_maximos es tipos maximos
    df_maximos = df_maximos.loc[
        (df_maximos.Año.isin(años_validos)) &
        (df_maximos['Tipo de contratación'] == tipo_contratacion)
    ]
    df_maximos = df_maximos.drop(['Tipo de contratación', 'INV3'], axis=1)
    df = df.copy()
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    # Sólo ADJUDICACION DIRECTA
    df = df.loc[df.TIPO_PROCEDIMIENTO == 'ADJUDICACION DIRECTA']
    df = df.assign(Año=df.FECHA_INICIO.dt.year)
    df = df.loc[df.Año.isin(años_validos)]
    monto_por_contrato = df.groupby(
        ['CLAVEUC', 'Año', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_por_proc = monto_por_contrato.groupby(
        ['CLAVEUC', 'Año', 'NUMERO_PROCEDIMIENTO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_por_proc = pd.merge(monto_por_proc, df_maximos,
                              on='Año', how='inner')
    es_mayor_al_max = (monto_por_proc.IMPORTE_PESOS >
                       monto_por_proc['Adjudicación directa'])
    monto_por_proc = monto_por_proc.assign(es_mayor_al_max=es_mayor_al_max)
    monto_por_proc = (monto_por_proc.groupby(['CLAVEUC', 'Año', 'es_mayor_al_max'])
                                    .NUMERO_PROCEDIMIENTO.nunique()
                                    .reset_index()
                                    .pivot_table(index=['CLAVEUC', 'Año'],
                                                 columns=['es_mayor_al_max'],
                                                 values='NUMERO_PROCEDIMIENTO')
                                    .rename(columns={True: 'num_excedidas_si',
                                                     False: 'num_excedidas_no'})
                                    .fillna(0))
    pc_adj_directas_excedidas = monto_por_proc.num_excedidas_si.divide(monto_por_proc.sum(axis=1))
    monto_por_proc = (monto_por_proc.assign(pc_adj_directas_excedidas=pc_adj_directas_excedidas * 100)
                                    .reset_index()
                                    .pivot(index='CLAVEUC',
                                           columns='Año',
                                           values='pc_adj_directas_excedidas')
                                    .fillna(0)
                                    .assign(pc_adj_excedidas_prom=lambda data: data.mean(axis=1))
                                    .drop(años_validos, axis=1)
                                    .reset_index())
    # left join
    df_feature = pd.merge(df_claves, monto_por_proc,
                          on='CLAVEUC', how='left')
    feature = df_feature.pc_adj_excedidas_prom.fillna(0)
    df_feature = df_feature.assign(
        pc_adj_directas_excedieron_monto=feature
    )
    df_feature = df_feature.loc[
                 :, ['CLAVEUC', 'pc_adj_directas_excedieron_monto']]
    return df_feature


def pc_invitaciones_excedieron_monto(df: DataFrame,
                                     df_maximos: DataFrame,
                                     **kwargs) -> DataFrame:
    """
    Indicador:
        % de las INV3 que rebasaron el máximo permitido.
    """
    if 'tipo_contratacion' in kwargs:
        tipo_contratacion = kwargs['tipo_contratacion']
    else:
        raise TypeError('Falta especificar tipo_contratacion')

    if 'year' in kwargs:
        años_validos = set([kwargs['year']])
    else:
        años_validos = set(range(2012, 2017))

    # df > df_procs_<tipo>
    # df_maximos es tipos maximos
    df_maximos = df_maximos.loc[
        (df_maximos.Año.isin(años_validos)) &
        (df_maximos['Tipo de contratación'] == tipo_contratacion)
        ]
    df_maximos = df_maximos.drop(
        ['Tipo de contratación', 'Adjudicación directa'], axis=1)
    df = df.copy()
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    # Sólo INV3
    df = df.loc[df.TIPO_PROCEDIMIENTO == 'INVITACION A CUANDO MENOS TRES']
    df = df.assign(Año=df.FECHA_INICIO.dt.year)
    df = df.loc[df.Año.isin(años_validos)]
    monto_por_contrato = df.groupby(
        ['CLAVEUC', 'Año', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_por_proc = monto_por_contrato.groupby(
        ['CLAVEUC', 'Año', 'NUMERO_PROCEDIMIENTO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_por_proc = pd.merge(monto_por_proc, df_maximos, on='Año', how='inner')
    es_mayor_al_max = monto_por_proc.IMPORTE_PESOS > monto_por_proc['INV3']
    monto_por_proc = monto_por_proc.assign(es_mayor_al_max=es_mayor_al_max)

    monto_por_proc = (monto_por_proc.groupby(['CLAVEUC', 'Año', 'es_mayor_al_max'])
                      .NUMERO_PROCEDIMIENTO.nunique()
                      .reset_index()
                      .pivot_table(index=['CLAVEUC', 'Año'],
                                   columns=['es_mayor_al_max'],
                                   values='NUMERO_PROCEDIMIENTO')
                      .rename(columns={True: 'num_excedidas_si',
                                       False: 'num_excedidas_no'})
                      .fillna(0))

    # Parece que en SERVICIOS 2019 no se encontró esta anomalía
    if 'num_excedidas_si' not in monto_por_proc.columns:
        monto_por_proc['num_excedidas_si'] = 0

    pc_inv3_excedidas = monto_por_proc.num_excedidas_si.divide(monto_por_proc.sum(axis=1))
    monto_por_proc = (monto_por_proc.assign(pc_inv3_excedidas=pc_inv3_excedidas * 100)
                      .reset_index()
                      .pivot(index='CLAVEUC',
                             columns='Año',
                             values='pc_inv3_excedidas')
                      .fillna(0)
                      .assign(pc_inv3_excedidas_prom=lambda data: data.mean(axis=1))
                      .drop(años_validos, axis=1)
                      .reset_index())
    # left join
    df_feature = pd.merge(df_claves, monto_por_proc,
                          on='CLAVEUC', how='left')
    feature = df_feature.pc_inv3_excedidas_prom.fillna(0)
    df_feature = df_feature.assign(
        pc_invitaciones_excedieron_monto=feature
    )
    df_feature = df_feature.loc[:,
                 ['CLAVEUC', 'pc_invitaciones_excedieron_monto']]
    return df_feature


# Features scraper

def promedio_convenios_por_proc(df: DataFrame,
                                **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el promedio de contratos modificatorios por
    procedimiento
    Indicador:
        Promedio de convenios por procedimiento.
    """
    df = df.copy()
    df_convenios_prom = (df.loc[df.numero_convenios > 0]
                           .groupby('CLAVEUC').numero_convenios.mean())
    df_feature = pd.merge(df.loc[:, ['CLAVEUC']].drop_duplicates(),
                          df_convenios_prom.reset_index(),
                          on='CLAVEUC', how='left')
    df_feature = df_feature.rename(
        columns={'numero_convenios': 'promedio_convenios'})
    df_feature = df_feature.assign(
        promedio_convenios_por_proc=df_feature.promedio_convenios.fillna(0))
    df_feature = df_feature.loc[
                 :, ['CLAVEUC', 'promedio_convenios_por_proc']]
    return df_feature


def pc_procs_sin_convocatoria(df: DataFrame,
                              tipos_validos=None,
                              **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos sin archivo de convocatoria
    Indicador:
        Porcentaje de licitaciones e INV3 sin convocatoria.
    """
    if tipos_validos is None:
        # solo aplica para INV a 3 y Licitaciones publicas
        tipos_validos = {
            'INVITACION A CUANDO MENOS TRES',
            'LICITACION PUBLICA',
            'LICITACION PUBLICA CON OSD'
        }
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)].copy()
    df_feature = (df.groupby(['CLAVEUC', 'archivo_convocatoria'],
                             as_index=False).CODIGO_EXPEDIENTE.count()
                    .pivot(index='CLAVEUC', columns='archivo_convocatoria',
                           values='CODIGO_EXPEDIENTE')
                    .fillna(0)
                    .rename(columns={0: 'pc_procs_sin_convocatoria'}))
    columnas = list(df_feature.columns.values)
    if 'pc_procs_sin_convocatoria' not in columnas:
        raise ValueError('Todos los procedimientos tienen '
                         'archivo de convocatoria')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', 'pc_procs_sin_convocatoria']])
    df_feature.columns.name = ''
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def procs_con_incumplimiento_de_exclusividad_mipyme(df_procs: DataFrame,
                                                    df_scraper: DataFrame) -> DataFrame:
    """
    Procedimientos publicados como exclusivos para MiPYMES
    que incumplen esta condición.
    Indicador:
        - Incumplimiento de procedimientos exclusivos para MYPYMES
    """
    df = df_procs.copy()
    cols = ['CLAVEUC', 'CODIGO_EXPEDIENTE']

    df = df.drop_duplicates(subset=cols)
    df = df.loc[:, cols + ['ESTRATIFICACION_MPC']]

    exclusividad = df_scraper[['CODIGO_EXPEDIENTE', 'exclusivo_mipymes']].drop_duplicates(subset=['CODIGO_EXPEDIENTE'])
    df = df.merge(exclusividad, how='left')
    df['incumplimiento'] = ((df.exclusivo_mipymes == 1) &
                            (df.ESTRATIFICACION_MPC.isin(['NO MIPYME'])))

    df_feature = (df.groupby(['CLAVEUC', 'incumplimiento'], as_index=False)
                  .CODIGO_EXPEDIENTE.count())
    df_feature = df_feature.pivot(index='CLAVEUC',
                                  columns='incumplimiento',
                                  values='CODIGO_EXPEDIENTE')
    df_feature.fillna(0, inplace=True)

    col_feature = 'procs_con_incumplimiento_de_exclusividad_mipyme'
    df_feature = df_feature.rename(columns={True: col_feature})
    df_feature = (df_feature.reset_index()
                  .loc[:, ['CLAVEUC', col_feature]])
    df_feature.columns.name = ''

    return df_feature


def pc_adj_directas_excedieron_monto_fraccionado(df: DataFrame,
                                                 df_maximos: DataFrame,
                                                 **kwargs) -> DataFrame:
    """
    Indicador que busca identificar el riesgo de fraccionar contratos
    para no rebasar el monto permitido para realizar una AD.

    Cálculo: Si # de contratos AD por semana por empresa por UC > 1 y
    monto acumulado de contratos AD en la misma semana por empresa
    por UC supera montos máximos autorizados para adjudicación directa Año.

    NOTA:
        - asume que el dataframe 'df' es de un año específico
        - sin embargo se requiere el parametro 'year' para filtrar los montos máx.

    Indicador:
        % de contratos AD a una misma empresa que rebasan el monto permitido (UC)
    """
    if 'year' in kwargs:
        años_validos = set([kwargs['year']])
    else:
        raise TypeError('Falta especificar año')

    df = df.copy()
    df_claves = pd.DataFrame(data=df.CLAVEUC.unique(), columns=['CLAVEUC'])

    # Sólo ADJUDICACION DIRECTA
    df = df.loc[df.TIPO_PROCEDIMIENTO == 'ADJUDICACION DIRECTA']
    df = df.assign(Semana=df.FECHA_INICIO.dt.week)

    # Máximos del año para Adjudicación directa por distintos Tipos
    df_maximos = df_maximos.loc[df_maximos.Año.isin(años_validos)]
    df_maximos = df_maximos[['Tipo de contratación', 'Adjudicación directa']]

    group_keys = ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'TIPO_CONTRATACION', 'Semana']

    # monto semanal por proveedor de UC
    monto_semanal = df.groupby(group_keys, as_index=False).IMPORTE_PESOS.sum()
    # numero de contratos por proveedor de UC
    contratos_semanales = (df.groupby(group_keys, as_index=False)
                           .NUMERO_PROCEDIMIENTO.count()
                           .rename(columns={'NUMERO_PROCEDIMIENTO': 'Contratos'}))

    # Obtiene los máximos
    monto_semanal = pd.merge(monto_semanal, df_maximos,
                             left_on='TIPO_CONTRATACION',
                             right_on='Tipo de contratación',
                             how='inner')

    # Concatena el numero de contratos involucrados en la suma semanal
    monto_semanal = pd.merge(monto_semanal, contratos_semanales)
    del contratos_semanales

    # Marca los que exceden
    excede = (monto_semanal.IMPORTE_PESOS > monto_semanal['Adjudicación directa'])
    monto_semanal = monto_semanal.assign(excede=excede)

    # Crea tabla que cuenta los procedimientos que excedieron
    monto_semanal = (monto_semanal.groupby(['CLAVEUC', 'excede'])
                     .Contratos.sum()
                     .reset_index()
                     .pivot_table(index=['CLAVEUC'],
                                  columns=['excede'],
                                  values='Contratos')
                     .rename(columns={True: 'num_excedidas_si', False: 'num_excedidas_no'})
                     .fillna(0))

    pc_fraccionados = monto_semanal.num_excedidas_si.divide(monto_semanal.sum(axis=1))
    df_fraccionados = pd.DataFrame(data=pc_fraccionados, columns=['pc_fraccionados'])

    df_feature = pd.merge(df_claves, df_fraccionados, on='CLAVEUC', how='left')
    df_feature.pc_fraccionados = df_feature.pc_fraccionados.fillna(0)

    col_name = 'pc_adj_directas_excedieron_monto_fraccionado'
    df_feature = df_feature.rename(columns={'pc_fraccionados': col_name})

    return df_feature

