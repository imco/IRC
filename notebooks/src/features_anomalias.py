#!/usr/bin/env python

# Created by Raul Peralta-Lozada (11/10/17)
import pandas as pd


def interaccion_rfc_fantasma(df_procs, df_rfc_fantasma):
    df_feature = pd.DataFrame(
        data=df_procs.CLAVEUC.unique(),
        columns=['CLAVEUC']
    )
    df = pd.merge(
        df_procs, df_rfc_fantasma,
        on='PROVEEDOR_CONTRATISTA', how='inner'
    )
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    # número de proveedores fantasma por uc
    pocs_distintos = monto_por_contrato.groupby('CLAVEUC').PROVEEDOR_CONTRATISTA.nunique()
    pocs_distintos = pocs_distintos.reset_index()
    pocs_distintos = pocs_distintos.rename(
        columns={'PROVEEDOR_CONTRATISTA': 'num_proveedores_fantasma'})
    # número de contratos con rfc fantasmas por uc
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO']).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.rename(
        columns={'CODIGO_CONTRATO': 'contratos_con_fantasmas'})
    contratos_total = contratos_total.groupby('CLAVEUC',
                                              as_index=False).contratos_con_fantasmas.sum()
    # monto con rfc fantasmas por uc
    monto_uc_contratos = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.groupby('CLAVEUC', as_index=False).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.rename(columns={'IMPORTE_PESOS': 'monto_fantasma'})
    # join the features
    df_feature = pd.merge(df_feature, pocs_distintos, on='CLAVEUC', how='left')
    df_feature = pd.merge(df_feature, contratos_total, on='CLAVEUC', how='left')
    df_feature = pd.merge(df_feature, monto_uc_contratos, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def interaccion_sancionados(df_procs, df_sancionados):
    df_feature = pd.DataFrame(
        data=df_procs.CLAVEUC.unique(),
        columns=['CLAVEUC']
    )
    df = pd.merge(
        df_procs, df_sancionados,
        on='PROVEEDOR_CONTRATISTA', how='inner'
    )
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    # número de proveedores fantasma por uc
    pocs_distintos = monto_por_contrato.groupby('CLAVEUC').PROVEEDOR_CONTRATISTA.nunique()
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
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.groupby('CLAVEUC', as_index=False).IMPORTE_PESOS.sum()
    monto_uc_contratos = monto_uc_contratos.rename(
        columns={'IMPORTE_PESOS': 'monto_con_sancionados'})
    # join the features
    df_feature = pd.merge(df_feature, pocs_distintos, on='CLAVEUC', how='left')
    df_feature = pd.merge(df_feature, contratos_total, on='CLAVEUC', how='left')
    df_feature = pd.merge(df_feature, monto_uc_contratos, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def porcentaje_contratos_por_convenio(df):
    monto_por_contrato = df.groupby(
        ['DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
         'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'CONVENIO_MODIFICATORIO'],
        as_index=False
    ).IMPORTE_PESOS.sum()
    contratos_total = monto_por_contrato.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CONVENIO_MODIFICATORIO']
    ).CODIGO_CONTRATO.nunique()
    contratos_total = contratos_total.reset_index()
    contratos_total = contratos_total.groupby(
        ['CLAVEUC', 'CONVENIO_MODIFICATORIO'], as_index=False
    ).CODIGO_CONTRATO.sum()
    contratos_total = contratos_total.pivot(
        index='CLAVEUC', columns='CONVENIO_MODIFICATORIO', values='CODIGO_CONTRATO')
    contratos_total = contratos_total.fillna(0)
    num_contratos = contratos_total.sum(axis=1)
    contratos_total = contratos_total.rename(
        columns={
            c: 'pc_contratos_convenio_' + c.lower().replace(' ', '_')
            for c in contratos_total.columns
        }
    )
    contratos_total = contratos_total * 100
    contratos_total = contratos_total.divide(num_contratos, axis='index')
    contratos_total.columns.name = ''
    contratos_total = contratos_total.reset_index()
    return contratos_total