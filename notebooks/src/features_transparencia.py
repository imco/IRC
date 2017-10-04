#!/usr/bin/env python

# Created by Raul Peralta-Lozada (28/09/17)
import pandas as pd


def porcentaje_procedimientos_presenciales(df):
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'FORMA_PROCEDIMIENTO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    conteo_formas = monto_por_contrato.groupby(
        ['CLAVEUC', 'FORMA_PROCEDIMIENTO']
    ).NUMERO_PROCEDIMIENTO.nunique().reset_index()
    conteo_formas = conteo_formas.pivot(
        index='CLAVEUC', columns='FORMA_PROCEDIMIENTO',
        values='NUMERO_PROCEDIMIENTO'
    ).fillna(0)
    total_procedimientos = conteo_formas.sum(axis=1)
    conteo_formas = conteo_formas * 100
    conteo_formas = conteo_formas.divide(total_procedimientos, axis='index')
    # TODO: cambiar el nombre de las columnas
    conteo_formas = conteo_formas.reset_index()
    conteo_formas.columns.name = ''
    conteo_formas = conteo_formas.rename(
        columns={'PRESENCIAL': 'pc_procedimientos_presenciales'}
    )
    return conteo_formas.loc[:, ['CLAVEUC', 'pc_procedimientos_presenciales']]


def contratos_promedio_por_procedimimento(df):
    """Agrupación de contratos en un mismo procedimiento"""
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    contratos_por_proc = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_por_proc = contratos_por_proc.reset_index()

    contratos_por_proc = contratos_por_proc.groupby(
        'CLAVEUC', as_index=False
    ).CODIGO_CONTRATO.mean()
    contratos_por_proc = contratos_por_proc.rename(
        columns={'CODIGO_CONTRATO': 'contratos_promedio_por_proc'}
    )
    return contratos_por_proc
