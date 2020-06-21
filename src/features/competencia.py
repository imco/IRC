#!/usr/bin/env python

# Created by Raul Peralta-Lozada (28/09/17)
from typing import Optional

import pandas as pd
import numpy as np
# import networkx as nx
# from networkx.algorithms import bipartite
from sklearn.linear_model import Ridge

DataFrame = pd.DataFrame


def contratos_por_proveedor(df: DataFrame, **kwargs) -> DataFrame:
    """Por cada unidad compradora calcula el número de contratos
    por proveedor diferente
    """
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    # Proveedores distintos
    pocs_distintos = monto_por_contrato.groupby(
        'CLAVEUC').PROVEEDOR_CONTRATISTA.nunique()
    pocs_distintos = pocs_distintos.reset_index()
    pocs_distintos = pocs_distintos.rename(
      columns={'PROVEEDOR_CONTRATISTA': 'proveedores_distintos'})
    # procedimientos distintos
    procedimientos_distintos = monto_por_contrato.groupby(
        'CLAVEUC').NUMERO_PROCEDIMIENTO.nunique()
    procedimientos_distintos = procedimientos_distintos.reset_index()
    procedimientos_distintos = procedimientos_distintos.rename(
      columns={'NUMERO_PROCEDIMIENTO': 'conteo_procedimientos'})
    # Numero de contratos
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'conteo_contratos'})
    contratos_total = contratos_total.groupby(
        'CLAVEUC', as_index=False).conteo_contratos.sum()
    df_feature = pd.merge(
        pocs_distintos, contratos_total, on='CLAVEUC', how='inner')
    df_feature = pd.merge(
        df_feature, procedimientos_distintos, on='CLAVEUC', how='inner')
    df_feature = df_feature.assign(
        contratos_por_proveedor=df_feature.conteo_contratos.divide(df_feature.proveedores_distintos)
    )
    df_feature = df_feature.loc[:, ['CLAVEUC', 'contratos_por_proveedor']]
    return df_feature


def pc_procedimientos_adj_directa_inv3(df: DataFrame,
                                       **kwargs) -> DataFrame:
    """De la tabla de procedimientos. Por cada unidad compradora
    calcula el porcentaje de procedimientos por
    adj directa e invitacion a 3)"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'TIPO_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    conteo_tipos = monto_por_contrato.groupby(
        ['CLAVEUC', 'TIPO_PROCEDIMIENTO']
    ).NUMERO_PROCEDIMIENTO.nunique().reset_index()
    conteo_tipos = conteo_tipos.pivot(
        index='CLAVEUC', columns='TIPO_PROCEDIMIENTO',
        values='NUMERO_PROCEDIMIENTO'
    ).fillna(0)
    # TODO: necesita un refactor
    adj_dir_e_inv3 = (conteo_tipos['ADJUDICACION DIRECTA'] +
                      conteo_tipos['INVITACION A CUANDO MENOS TRES'])
    drop_cols = ['ADJUDICACION DIRECTA', 'INVITACION A CUANDO MENOS TRES']
    conteo_tipos = (conteo_tipos.assign(ADJ_DIRECTA_INV3=adj_dir_e_inv3)
                                .drop(drop_cols, axis=1))
    total_procedimientos = conteo_tipos.sum(axis=1)
    conteo_tipos = conteo_tipos * 100
    conteo_tipos = conteo_tipos.divide(total_procedimientos, axis='index')
    conteo_tipos = conteo_tipos.rename(
        columns={
            col: 'pc_procedimientos_' + col.replace(' ', '_').lower()
            for col in conteo_tipos.columns
        }
    )
    conteo_tipos = conteo_tipos.reset_index()
    conteo_tipos.columns.name = ''
    df_feature = conteo_tipos.loc[
                 :, ['CLAVEUC', 'pc_procedimientos_adj_directa_inv3']]
    return df_feature


def pc_monto_adj_directa_inv3(df: DataFrame, **kwargs) -> DataFrame:
    """Por cada unidad compradora calcula el porcentaje
    del monto que da por adj directa e invitacion a 3)"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'TIPO_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_tipos = monto_por_contrato.groupby(
        ['CLAVEUC', 'TIPO_PROCEDIMIENTO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_tipos = monto_tipos.pivot(
        index='CLAVEUC', columns='TIPO_PROCEDIMIENTO',
        values='IMPORTE_PESOS'
    ).fillna(0)
    # TODO: necesita un refactor
    adj_dir_e_inv3 = (monto_tipos['ADJUDICACION DIRECTA'] +
                      monto_tipos['INVITACION A CUANDO MENOS TRES'])
    drop_cols = ['ADJUDICACION DIRECTA', 'INVITACION A CUANDO MENOS TRES']
    monto_tipos = (monto_tipos.assign(ADJ_DIRECTA_INV3=adj_dir_e_inv3)
                              .drop(drop_cols, axis=1))
    total_montos = monto_tipos.sum(axis=1)
    monto_tipos = monto_tipos * 100
    monto_tipos = monto_tipos.divide(total_montos, axis='index')
    monto_tipos = monto_tipos.rename(
        columns={
            col: 'pc_monto_' + col.replace(' ', '_').lower()
            for col in monto_tipos.columns
        }
    )
    monto_tipos = monto_tipos.reset_index()
    monto_tipos.columns.name = ''
    df_feature = monto_tipos.loc[
                 :, ['CLAVEUC', 'pc_monto_adj_directa_inv3']]
    return df_feature


def importe_promedio_por_contrato(df: DataFrame, **kwargs) -> DataFrame:
    """Calcula el monto promedio que se da por contrato"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'conteo_contratos'})
    contratos_total = (contratos_total.groupby('CLAVEUC', as_index=False)
                                      .conteo_contratos.sum())

    monto_uc_contratos = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.groupby(
        'CLAVEUC', as_index=False).IMPORTE_PESOS.sum()
    df_feature = pd.merge(monto_uc_contratos, contratos_total,
                          on='CLAVEUC', how='inner')
    importe_promedio = df_feature.IMPORTE_PESOS.divide(
        df_feature.conteo_contratos)
    df_feature = df_feature.assign(
        importe_promedio_por_contrato=importe_promedio
    )
    df_feature = df_feature.drop('conteo_contratos', axis=1)
    df_feature = df_feature.rename(columns={'IMPORTE_PESOS': 'monto_total'})
    df_feature = df_feature.loc[
                 :, ['CLAVEUC', 'importe_promedio_por_contrato']]
    return df_feature


def _calcular_ihh_contratos(df: DataFrame) -> DataFrame:
    """helper function. Solo se ocupa para calcular pasos intermedios"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    contratos_uc_poc = monto_por_contrato.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'NUMERO_PROCEDIMIENTO'],
    ).CODIGO_CONTRATO.nunique()
    contratos_uc_poc = contratos_uc_poc.reset_index()
    contratos_uc_poc = contratos_uc_poc.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA'], as_index=False
    ).CODIGO_CONTRATO.sum()
    contratos_uc = contratos_uc_poc.groupby(
        'CLAVEUC', as_index=False
    ).CODIGO_CONTRATO.sum()
    contratos_uc = contratos_uc.rename(
        columns={'CODIGO_CONTRATO': 'contratos_por_uc'}
    )
    contratos_uc_poc = pd.merge(
        contratos_uc_poc, contratos_uc, how='left', on='CLAVEUC'
    )
    share = contratos_uc_poc.CODIGO_CONTRATO.divide(contratos_uc_poc.contratos_por_uc)
    contratos_uc_poc = contratos_uc_poc.assign(Share=share * 100)
    contratos_uc_poc = contratos_uc_poc.assign(
        IHH_contratos=contratos_uc_poc.Share ** 2
    )
    contratos_uc_poc = contratos_uc_poc.drop(
        ['contratos_por_uc', 'Share'], axis=1)
    return contratos_uc_poc


def ihh_por_contratos(df: DataFrame, **kwargs) -> DataFrame:
    """Indice de Herfindahl e Hirschman"""
    contratos_uc_poc = _calcular_ihh_contratos(df)
    # IHH por uc
    uc_IHH = contratos_uc_poc.groupby(
        'CLAVEUC', as_index=False).IHH_contratos.sum()
    # uc_IHH = uc_IHH.rename(columns={'IHH_contratos': 'IHH_total_contratos'})
    uc_IHH = uc_IHH.rename(columns={'IHH_contratos': 'ihh_por_contratos'})
    return uc_IHH


def id_por_contratos(df: DataFrame, **kwargs) -> DataFrame:
    """Tabla de procedimientos"""
    contratos_uc_poc = _calcular_ihh_contratos(df)
    uc_IHH = contratos_uc_poc.groupby(
        'CLAVEUC', as_index=False).IHH_contratos.sum()
    uc_IHH = uc_IHH.rename(columns={'IHH_contratos': 'ihh_por_contratos'})
    # ID por uc
    contratos_uc_poc = pd.merge(
        contratos_uc_poc, uc_IHH, on='CLAVEUC', how='inner'
    )
    contratos_uc_poc = contratos_uc_poc.assign(
        ID_contratos=(
            contratos_uc_poc.IHH_contratos.divide(contratos_uc_poc.ihh_por_contratos)
        )
    )
    contratos_uc_poc = contratos_uc_poc.assign(
        ID_contratos=(contratos_uc_poc.ID_contratos * 100) ** 2
    )
    uc_ID = contratos_uc_poc.groupby(
        'CLAVEUC', as_index=False).ID_contratos.sum()
    uc_ID = uc_ID.rename(columns={'ID_contratos': 'id_por_contratos'})
    return uc_ID


def _calcular_ihh_monto(df: DataFrame) -> DataFrame:
    """helper function. Usa tabla de procedimientos"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc_poc = monto_por_contrato.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc = monto_uc_poc.groupby(
        'CLAVEUC', as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc = monto_uc.rename(columns={'IMPORTE_PESOS': 'monto_por_uc'})
    monto_uc_poc = pd.merge(monto_uc_poc, monto_uc,
                            how='left', on='CLAVEUC')
    share = monto_uc_poc.IMPORTE_PESOS.divide(monto_uc_poc.monto_por_uc)
    monto_uc_poc = monto_uc_poc.assign(Share=share * 100)
    monto_uc_poc = monto_uc_poc.assign(
        IHH_monto=monto_uc_poc.Share**2)
    monto_uc_poc = monto_uc_poc.drop(['Share', 'monto_por_uc'], axis=1)
    return monto_uc_poc


def ihh_por_monto(df: DataFrame, **kwargs) -> DataFrame:
    monto_uc_poc = _calcular_ihh_monto(df)
    uc_IHH = monto_uc_poc.groupby(
        'CLAVEUC', as_index=False).IHH_monto.sum()
    uc_IHH = uc_IHH.rename(columns={'IHH_monto': 'ihh_por_monto'})
    return uc_IHH


def id_por_monto(df, **kwargs) -> DataFrame:
    monto_uc_poc = _calcular_ihh_monto(df)
    uc_IHH = monto_uc_poc.groupby(
        'CLAVEUC', as_index=False).IHH_monto.sum()
    uc_IHH = uc_IHH.rename(columns={'IHH_monto': 'ihh_por_monto'})
    # ID por uc
    monto_uc_poc = pd.merge(monto_uc_poc, uc_IHH,
                            on='CLAVEUC', how='inner')
    monto_uc_poc = monto_uc_poc.assign(
        ID_monto=(
            monto_uc_poc.IHH_monto.divide(monto_uc_poc.ihh_por_monto)
        )
    )
    monto_uc_poc = monto_uc_poc.assign(
        ID_monto=(monto_uc_poc.ID_monto * 100) ** 2
    )
    uc_ID = monto_uc_poc.groupby('CLAVEUC', as_index=False).ID_monto.sum()
    uc_ID = uc_ID.rename(columns={'ID_monto': 'id_por_monto'})
    return uc_ID


def tendencia_adjudicacion_directa(df: DataFrame, **kwargs) -> DataFrame:
    """
    Usa la tabla de procedimientos. Calcula el incremento en el
    porcentaje de adjudicaciones directas que da la UC.
    Se calcula hasta el año indicado.
    """
    # TODO: falta poner pruebas a _estimat_pendiente
    def _estimar_pendiente(row):
        y = row.values.reshape(-1, 1)
        x = np.arange(0, y.shape[0]).reshape(-1, 1)
        # model = Ridge(fit_intercept=False)
        model = Ridge(fit_intercept=True)
        model.fit(x, y)
        pendiente = model.coef_.flatten()[0]
        return pendiente

    if df.shape[0] == 0:
        return None

    if 'year' in kwargs:
        year = kwargs['year']
    else:
        year = 1e5

    df = df.copy()
    adjudicacion_directa = df.TIPO_PROCEDIMIENTO == 'ADJUDICACION DIRECTA'
    df = df.assign(
        adjudicacion_directa=adjudicacion_directa
    )
    cols = [
        'CLAVEUC',
        'FECHA_INICIO',
        'NUMERO_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        'adjudicacion_directa'
    ]
    df = (df.loc[:, cols]
          .drop_duplicates()
          .assign(Year=df.FECHA_INICIO.dt.year))

    # Filtra el dataframe hasta el año indicado
    df = df[df['Year'] <= year]

    # Contabiliza adjudicaciones directas por UC y año
    df = (df.drop('FECHA_INICIO', axis=1)
          .groupby(['CLAVEUC', 'Year', 'adjudicacion_directa'])
          .NUMERO_PROCEDIMIENTO.nunique()
          .reset_index()
          .pivot_table(index=['CLAVEUC', 'Year'],
                       columns=['adjudicacion_directa'],
                       values='NUMERO_PROCEDIMIENTO')
          .fillna(0)
          .reset_index()
          .rename(columns={True: 'num_adj_si',
                           False: 'num_adj_no'}))

    total = df[['num_adj_no', 'num_adj_si']].sum(axis=1)
    df = df.assign(
        pc_adjudicacion=(df.num_adj_si.divide(total) * 100)
    )
    df = (df.pivot(index='CLAVEUC',
                   columns='Year',
                   values='pc_adjudicacion')
          .fillna(0))

    df = df.assign(
        tendencia_adjudicacion_directa=df.apply(
            _estimar_pendiente, axis=1)
    )
    df = (df.reset_index()
            .loc[:, ['CLAVEUC', 'tendencia_adjudicacion_directa']])
    df.columns.name = ''
    return df


def c4_monto_total(df: DataFrame, **kwargs) -> DataFrame:
    """Usa tabla de procedimientos"""
    df: DataFrame = df.copy()
    monto_por_proc = df.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'NUMERO_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_por_prov = monto_por_proc.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_total = (monto_por_prov.groupby('CLAVEUC', as_index=False)
                                 .IMPORTE_PESOS.sum()
                                 .rename(columns={'IMPORTE_PESOS': 'TOTAL'}))
    monto_por_prov = pd.merge(monto_por_prov, monto_total,
                              on='CLAVEUC', how='inner')
    pc_monto = monto_por_prov.IMPORTE_PESOS.divide(monto_por_prov.TOTAL)
    monto_por_prov = monto_por_prov.drop(['IMPORTE_PESOS', 'TOTAL'], axis=1)
    monto_por_prov = monto_por_prov.assign(pc_monto=pc_monto)
    groups = []
    for group, sub_df in monto_por_prov.groupby('CLAVEUC'):
        feature = sub_df.pc_monto.nlargest(4).sum()
        groups.append({'CLAVEUC': group, 'c4_monto_total': feature})
    return pd.DataFrame(groups)


def c4_num_procedimientos(df: DataFrame, **kwargs) -> DataFrame:
    """ Usa la tabla de procedimientos"""
    df: DataFrame = df.copy()
    procs_por_prov = df.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA'],
    ).NUMERO_PROCEDIMIENTO.nunique()
    procs_por_prov = procs_por_prov.reset_index()
    procs_total = (procs_por_prov.groupby('CLAVEUC', as_index=False)
                                 .NUMERO_PROCEDIMIENTO.sum()
                                 .rename(columns={'NUMERO_PROCEDIMIENTO': 'TOTAL'}))
    procs_por_prov = pd.merge(procs_por_prov, procs_total,
                              on='CLAVEUC', how='inner')
    pc_procs = procs_por_prov.NUMERO_PROCEDIMIENTO.divide(procs_por_prov.TOTAL)
    procs_por_prov = procs_por_prov.drop(['NUMERO_PROCEDIMIENTO', 'TOTAL'],
                                         axis=1)
    procs_por_prov = procs_por_prov.assign(pc_procs=pc_procs)
    groups = []
    for group, sub_df in procs_por_prov.groupby('CLAVEUC'):
        feature = sub_df.pc_procs.nlargest(4).sum()
        groups.append({'CLAVEUC': group, 'c4_num_procedimientos': feature})
    return pd.DataFrame(groups)


# Datos de la tabla participantes
# TODO: agregar una verificacion para las funciones que usan participantes
# preguntar algo especifico (tiene que ser rapido)

def pc_licitaciones_con_un_participante(df: DataFrame,
                                        **kwargs) -> Optional[DataFrame]:
    # usa tabla de participantes. Calcula el porcentaje de licitaciones e
    # invitaciones a 3 con un solo participante
    if df.shape[0] == 0:
        return None
    df: DataFrame = df.copy()
    df_feature = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_name = 'pc_licitaciones_con_un_participante'
    tipos_validos = {'LICITACION PUBLICA',
                     'INVITACION A CUANDO MENOS TRES'}
    # Filtro y saco uniques
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)]
    df = (df.groupby(['CLAVEUC', 'NUMERO_PROCEDIMIENTO'])
            .PROVEEDOR_CONTRATISTA.nunique()
            .reset_index()
            .rename(columns={'PROVEEDOR_CONTRATISTA': 'numero_proveedores'})
            .groupby(['CLAVEUC', 'numero_proveedores']).NUMERO_PROCEDIMIENTO.count()
            .reset_index()
            .rename(columns={'NUMERO_PROCEDIMIENTO': 'numero_procedimientos'})
            .pivot(index='CLAVEUC',  # TODO: Esta parte no me gusta
                   columns='numero_proveedores',
                   values='numero_procedimientos')
            .fillna(0))
    df = (df * 100).divide(df.sum(axis=1), axis='index')
    df = df.rename(columns={1: col_name})
    if col_name not in df.columns:
        df = df.assign(pc_licitaciones_con_un_participante=0)
    df = df.reset_index()
    # left join
    df_feature = pd.merge(df_feature, df.loc[:, ['CLAVEUC', col_name]],
                          on='CLAVEUC', how='left').fillna(0)
    return df_feature


def procs_promedio_por_participantes(df: DataFrame,
                                     **kwargs) -> Optional[DataFrame]:
    """Usa tabla participantes. Calcula cuantos procedimientos
    en promedio se dan por participante"""
    if df.shape[0] == 0:
        return None
    df: DataFrame = df.copy()
    df_feature = (df.groupby(['CLAVEUC', 'NUMERO_PROCEDIMIENTO'])
                    .PROVEEDOR_CONTRATISTA.nunique()
                    .reset_index()
                    .groupby('CLAVEUC', as_index=False)
                    .PROVEEDOR_CONTRATISTA.mean()
                    .assign(procs_promedio_por_participantes=lambda x: 1 / x.PROVEEDOR_CONTRATISTA)
                    .loc[:, ['CLAVEUC', 'procs_promedio_por_participantes']])
    return df_feature


def pc_partipaciones_promedio(df: DataFrame,
                              **kwargs) -> Optional[DataFrame]:
    """Usa la tabla de participantes"""
    if df.shape[0] == 0:
        return None
    df: DataFrame = df.copy()
    df_participaciones = (df.groupby(['CLAVEUC', 'PROVEEDOR_CONTRATISTA'])
                            .NUMERO_PROCEDIMIENTO.nunique()
                            .reset_index()
                            .rename(columns={'NUMERO_PROCEDIMIENTO': 'participaciones'}))
    total_participaciones = (df_participaciones.groupby('CLAVEUC', as_index=False)
                                               .participaciones.sum()
                                               .rename(columns={'participaciones': 'tot_parts'}))
    df_feature = pd.merge(df_participaciones,
                          total_participaciones,
                          on='CLAVEUC', how='inner')
    df_feature = df_feature.assign(
        pc_partipaciones=df_feature.participaciones.divide(df_feature.tot_parts)
    )
    df_feature = (df_feature.groupby('CLAVEUC', as_index=False)
                            .pc_partipaciones.max()
                            .rename(columns={'pc_partipaciones': 'pc_partipaciones_promedio'}))
    df_feature = df_feature.loc[:, ['CLAVEUC', 'pc_partipaciones_promedio']]
    return df_feature


def procs_por_participantes_unicos(df: DataFrame,
                                   **kwargs) -> Optional[DataFrame]:
    """Usa la tabla de participantes"""
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df_procs = (df.groupby('CLAVEUC')
                  .NUMERO_PROCEDIMIENTO.nunique()
                  .reset_index())
    df_parts = (df.groupby('CLAVEUC')
                  .PROVEEDOR_CONTRATISTA.nunique()
                  .reset_index())
    df_feature = pd.merge(df_procs, df_parts, on='CLAVEUC', how='inner')
    df_feature = df_feature.assign(
        procs_por_participantes_unicos=df_feature.NUMERO_PROCEDIMIENTO / df_feature.PROVEEDOR_CONTRATISTA
    )
    df_feature = df_feature.loc[
                 :, ['CLAVEUC', 'procs_por_participantes_unicos']]
    return df_feature


def disminucion_en_participacion(df: DataFrame,
                                 **kwargs) -> Optional[DataFrame]:
    """Usa la tabla de participantes"""
    def _estimar_pendiente(row):
        # TODO: falta filtrar por nans y poner tests
        y = row.values.reshape(-1, 1)
        x = np.arange(0, y.shape[0]).reshape(-1, 1)
        # model = Ridge(fit_intercept=False)
        model = Ridge(fit_intercept=True)
        model.fit(x, y)
        pendiente = model.coef_.flatten()[0]
        pendiente *= -1
        return pendiente
    if df.shape[0] == 0:
        return None
    df = df.copy()
    df = df.assign(
        Year=df.NUMERO_PROCEDIMIENTO.map(lambda x: int(x.split('-')[3]))
    )
    df = (df.groupby(['CLAVEUC', 'Year', 'NUMERO_PROCEDIMIENTO'])
            .PROVEEDOR_CONTRATISTA.nunique()
            .reset_index())
    df = df.groupby(
        ['CLAVEUC', 'Year'], as_index=False
    ).PROVEEDOR_CONTRATISTA.mean()
    df = (df.pivot(index='CLAVEUC',
                   columns='Year',
                   values='PROVEEDOR_CONTRATISTA')
            .loc[:, list(range(2012, 2018))]
            .fillna(0))
    df = df.assign(
        disminucion_en_participacion=df.apply(
            _estimar_pendiente, axis=1)
    ).reset_index()
    df = df.loc[:, ['CLAVEUC', 'disminucion_en_participacion']]
    return df
