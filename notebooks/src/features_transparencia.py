#!/usr/bin/env python

# Created by Raul Peralta-Lozada (28/09/17)
import bisect
# import pandas as pd


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


def contratos_por_duracion(df, breakpoints=None, labels=None):
    """Cuenta el número de contratos que la unidad compradora tuvo
    en los intervalos de tiempo especificados"""
    if breakpoints is None:
        breakpoints = [0, 1, 5, 10, 20]
    if labels is None:
        labels = [
            'dias_sin_rango',
            'mismo_dia', 'uno_cinco_dias', 'cinco_diez_dias',
            'diez_veinte_dias', 'veinte_o_mas_dias'
        ]
    # TODO: verificar sizes de breapoints y labels
    monto_por_contrato = df.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'NUMERO_PROCEDIMIENTO',
         'CODIGO_CONTRATO', 'FECHA_INICIO', 'FECHA_FIN'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    delta_dias = (monto_por_contrato.FECHA_FIN - monto_por_contrato.FECHA_INICIO).dt.days
    monto_por_contrato = monto_por_contrato.assign(delta_dias=delta_dias)

    # adding labels
    monto_por_contrato = monto_por_contrato.assign(
        grupo_dias=monto_por_contrato.delta_dias.map(
            lambda d: labels[bisect.bisect(breakpoints, d)]
        )
    )
    monto_por_contrato = monto_por_contrato.loc[
                         :, ['CLAVEUC', 'delta_dias', 'grupo_dias', 'CODIGO_CONTRATO']]
    conteo_contratos = monto_por_contrato.groupby(
        ['CLAVEUC', 'grupo_dias'], as_index=False
    ).CODIGO_CONTRATO.count()
    conteo_contratos = conteo_contratos.rename(
        columns={'CODIGO_CONTRATO': 'num_contratos'})
    conteo_contratos = conteo_contratos.pivot(
        index='CLAVEUC', columns='grupo_dias', values='num_contratos'
    )
    # ordenar salida
    conteo_contratos = conteo_contratos.loc[:, labels[1:]]
    conteo_contratos = conteo_contratos.rename(
        columns={c: 'contratos_' + c for c in conteo_contratos.columns}
    )
    conteo_contratos = conteo_contratos.reset_index()
    conteo_contratos.columns.name = ''
    conteo_contratos = conteo_contratos.fillna(0)
    return conteo_contratos


def monto_por_duracion(df, breakpoints=None, labels=None):
    """Suma el monto que la unidad compradora usó
    en los intervalos de tiempo especificados"""
    if breakpoints is None:
        breakpoints = [0, 1, 5, 10, 20]
    if labels is None:
        labels = [
            'dias_sin_rango',
            'mismo_dia', 'uno_cinco_dias', 'cinco_diez_dias',
            'diez_veinte_dias', 'veinte_o_mas_dias'
        ]
    # TODO: verificar sizes de breapoints y labels
    monto_por_contrato = df.groupby(
        ['CLAVEUC', 'PROVEEDOR_CONTRATISTA', 'NUMERO_PROCEDIMIENTO',
         'CODIGO_CONTRATO', 'FECHA_INICIO', 'FECHA_FIN'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    delta_dias = (monto_por_contrato.FECHA_FIN - monto_por_contrato.FECHA_INICIO).dt.days
    monto_por_contrato = monto_por_contrato.assign(delta_dias=delta_dias)
    # adding labels
    monto_por_contrato = monto_por_contrato.assign(
        grupo_dias=monto_por_contrato.delta_dias.map(
            lambda d: labels[bisect.bisect(breakpoints, d)]
        )
    )
    monto_por_contrato = monto_por_contrato.loc[
                         :, ['CLAVEUC', 'delta_dias', 'grupo_dias', 'IMPORTE_PESOS']]
    monto_contratos = monto_por_contrato.groupby(
        ['CLAVEUC', 'grupo_dias'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_contratos = monto_contratos.rename(
        columns={'IMPORTE_PESOS': 'monto'})
    monto_contratos = monto_contratos.pivot(
        index='CLAVEUC', columns='grupo_dias', values='monto'
    )
    # ordenar salida
    monto_contratos = monto_contratos.loc[:, labels[1:]]
    monto_contratos = monto_contratos.rename(
        columns={c: 'monto_' + c for c in monto_contratos.columns}
    )
    monto_contratos = monto_contratos.reset_index()
    monto_contratos.columns.name = ''
    monto_contratos = monto_contratos.fillna(0)
    return monto_contratos
