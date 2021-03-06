#!/usr/bin/env python

# Created by Raul Peralta-Lozada (16/10/17)

import pandas as pd

DataFrame = pd.DataFrame

# todos usan tabla de procedimientos


def monto_total(df: DataFrame,
                   **kwargs) -> DataFrame:
    """Calcula el monto de la unidad compradora"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    monto_por_uc = monto_por_contrato.groupby(
        'CLAVEUC', as_index=False).IMPORTE_PESOS.sum()
    monto_por_uc = monto_por_uc.rename(
        columns={'IMPORTE_PESOS': 'monto_total'}
    )
    return monto_por_uc


def monto_total_por_tipo(df: DataFrame,
                         **kwargs) -> DataFrame:
    """
    Calcula el monto de la unidad compradora
    por tipo de procedimiento.
    """
    col_mapping = {
        'ADJUDICACION DIRECTA': 'monto_AD',
        'LICITACION PUBLICA': 'monto_LP',
        'INVITACION A CUANDO MENOS TRES': 'monto_INV3'
    }

    # Solo de los 3 Tipos de interés
    sub_df =df[df['TIPO_PROCEDIMIENTO'].isin(col_mapping.keys())]

    monto_por_contrato = sub_df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'TIPO_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()

    monto_por_uc = (monto_por_contrato.groupby(['CLAVEUC', 'TIPO_PROCEDIMIENTO'], as_index=False)
                    .IMPORTE_PESOS.sum()
                    .pivot_table(columns='TIPO_PROCEDIMIENTO',
                                 values='IMPORTE_PESOS',
                                 index='CLAVEUC')
                    .fillna(0)
                    .rename_axis(None, axis=1)
                    .reset_index())

    monto_por_uc = monto_por_uc.rename(columns=col_mapping)

    return monto_por_uc


def num_proveedores_unicos(df: DataFrame,
                           **kwargs) -> DataFrame:
    """Calcula el número de proveedores distintos por unidad compradora"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    pocs_distintos = monto_por_contrato.groupby('CLAVEUC').PROVEEDOR_CONTRATISTA.nunique()
    pocs_distintos = pocs_distintos.reset_index()
    pocs_distintos = pocs_distintos.rename(
      columns={'PROVEEDOR_CONTRATISTA': 'num_proveedores_unicos'})
    return pocs_distintos


def conteo_procedimientos(df: DataFrame,
                          **kwargs) -> DataFrame:
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    # procedimientos distintos
    procs_distintos = (monto_por_contrato.groupby('CLAVEUC')
                                         .NUMERO_PROCEDIMIENTO.nunique())
    procs_distintos = procs_distintos.reset_index()
    procs_distintos = procs_distintos.rename(
      columns={'NUMERO_PROCEDIMIENTO': 'conteo_procedimientos'})
    return procs_distintos


def numero_contratos(df: DataFrame, **kwargs) -> DataFrame:
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    # Numero de contratos
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'numero_contratos'})
    contratos_total = (contratos_total.groupby('CLAVEUC', as_index=False)
                                      .numero_contratos.sum())
    return contratos_total


def numero_contratos_por_tipo(df: DataFrame, **kwargs) -> DataFrame:
    """
    Calcula el número de contratos por UC
    y por TIPO_PROCEDIMIENTO
    """
    col_mapping = {
        'ADJUDICACION DIRECTA': 'numero_contratos_AD',
        'LICITACION PUBLICA': 'numero_contratos_LP',
        'INVITACION A CUANDO MENOS TRES': 'numero_contratos_INV3'
    }

    # Solo de los 3 Tipos de interés
    sub_df =df[df['TIPO_PROCEDIMIENTO'].isin(col_mapping.keys())]

    monto_por_contrato = sub_df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'TIPO_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()

    # Numero de contratos
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'TIPO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'numero_contratos'})

    contratos_total = (contratos_total.groupby(['CLAVEUC', 'TIPO_PROCEDIMIENTO'], as_index=False)
                       .numero_contratos.sum()
                       .pivot_table(columns='TIPO_PROCEDIMIENTO',
                                    values='numero_contratos',
                                    index='CLAVEUC'))

    sin_registros = [k for k in col_mapping if k not in contratos_total.columns]
    for k in sin_registros:
        contratos_total[k] = 0

    contratos_total = (contratos_total.rename(columns=col_mapping)
                       .fillna(0)
                       .rename_axis(None, axis=1)
                       .reset_index())

    return contratos_total
