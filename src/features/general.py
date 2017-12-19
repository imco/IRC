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

