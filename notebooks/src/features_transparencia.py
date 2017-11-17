#!/usr/bin/env python

# Created by Raul Peralta-Lozada (28/09/17)
import bisect
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge


def porcentaje_procedimientos_presenciales(df, **kwargs):
    df = df.assign(
        FORMA_PROCEDIMIENTO=df.FORMA_PROCEDIMIENTO.fillna('NO REPORTADA')
    )
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
    conteo_formas = conteo_formas.loc[
        :, ['CLAVEUC', 'pc_procedimientos_presenciales']
    ]
    return conteo_formas


def contratos_promedio_por_procedimimento(df, **kwargs):
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


def contratos_por_duracion(df, breakpoints=None, labels=None, **kwargs):
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


def monto_por_duracion(df, breakpoints=None, labels=None, **kwargs):
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


def promedio_datos_faltantes_poc_contrato(df, cols=None, **kwargs):
    """Promedio de datos fatantes por contrato en la UC. Los datos
    son los que están en el parámetro 'cols'."""
    cols_id = [
        'DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
        'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO'
    ]
    if cols is None:
        # default cols
        cols = [
            'EXP_F_FALLO', 'PROC_F_PUBLICACION',
            'FECHA_APERTURA_PROPOSICIONES',
            'FORMA_PROCEDIMIENTO', 'ANUNCIO',
            'FECHA_CELEBRACION',
            'FECHA_INICIO', 'FECHA_FIN'
        ]
    df_cols = df.loc[:, cols_id + cols]
    monto_por_contrato = df.groupby(
        cols_id, as_index=False).IMPORTE_PESOS.sum()

    df_feature = pd.merge(monto_por_contrato, df_cols, on=cols_id, how='inner')
    df_feature = df_feature.assign(
        promedio_datos_faltantes=df_feature.loc[:, cols].isnull().sum(axis=1)
    )
    df_feature = df_feature.groupby(
        'CLAVEUC', as_index=False).promedio_datos_faltantes.mean()
    return df_feature

# Features del scraper


def porcentaje_procs_sin_contrato(df, **kwargs):
    """Usa tabla scraper.
    Calcula el porcentaje de procedimientos sin archivo de
    contrato"""
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_interes = 'archivo_contrato'
    col_feature = 'pc_sin_contrato'
    df = df.copy()
    df_feature = (df.groupby(['CLAVEUC', col_interes],
                             as_index=False).CODIGO_EXPEDIENTE.count()
                    .pivot(index='CLAVEUC', columns=col_interes,
                           values='CODIGO_EXPEDIENTE')
                    .fillna(0)
                    .rename(columns={0: col_feature}))
    columnas = list(df_feature.columns.values)
    if col_feature not in columnas:
        raise ValueError('Todos los procedimientos tienen '
                         'ese tipo de archivo')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', col_feature]])
    df_feature.columns.name = ''
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def porcentaje_procs_sin_fallo(df, tipos_validos=None, **kwargs):
    """Usa tabla scraper.
    Calcula el porcentaje de procedimientos sin archivo de
    fallo"""
    if tipos_validos is None:
        # solo aplica para INV a 3 y Licitaciones publicas
        tipos_validos = {
            'INVITACION A CUANDO MENOS TRES',
            'LICITACION PUBLICA',
            'LICITACION PUBLICA CON OSD'
        }
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_interes = 'archivo_fallo'
    col_feature = 'pc_sin_fallo'
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)].copy()
    df_feature = (df.groupby(['CLAVEUC', col_interes],
                             as_index=False).CODIGO_EXPEDIENTE.count()
                    .pivot(index='CLAVEUC', columns=col_interes,
                           values='CODIGO_EXPEDIENTE')
                    .fillna(0)
                    .rename(columns={0: col_feature}))
    columnas = list(df_feature.columns.values)
    if col_feature not in columnas:
        raise ValueError('Todos los procedimientos tienen '
                         'ese tipo de archivo')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', col_feature]])
    df_feature.columns.name = ''
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def porcentaje_procs_sin_apertura(df, tipos_validos=None, **kwargs):
    """Usa tabla scraper.
    Calcula el porcentaje de procedimientos sin archivo de
    apertura de proposiciones"""
    if tipos_validos is None:
        # solo aplica para INV a 3 y Licitaciones publicas
        tipos_validos = {
            'INVITACION A CUANDO MENOS TRES',
            'LICITACION PUBLICA',
            'LICITACION PUBLICA CON OSD'
        }
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_interes = 'archivo_apertura'
    col_feature = 'pc_sin_apertura'
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)].copy()
    df_feature = (df.groupby(['CLAVEUC', col_interes],
                             as_index=False).CODIGO_EXPEDIENTE.count()
                    .pivot(index='CLAVEUC', columns=col_interes,
                           values='CODIGO_EXPEDIENTE')
                    .fillna(0)
                    .rename(columns={0: col_feature}))
    columnas = list(df_feature.columns.values)
    if col_feature not in columnas:
        raise ValueError('Todos los procedimientos tienen '
                         'ese tipo de archivo')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', col_feature]])
    df_feature.columns.name = ''
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def porcentaje_procedimientos_sin_archivos(df, **kwargs):
    """Usa tabla scraper.
    Se calcula el porcentaje de procedimientos sin archivos por UC"""
    df_feature = (df.groupby(['CLAVEUC', 'numero_archivos'],
                             as_index=False).CODIGO_EXPEDIENTE.count()
                    .pivot(index='CLAVEUC', columns='numero_archivos',
                           values='CODIGO_EXPEDIENTE')
                    .fillna(0))
    # Se calcula el porcentaje
    df_feature = (df_feature * 100).divide(
        df_feature.sum(axis=1), axis='index')
    df_feature = (df_feature.rename(columns={0: 'pc_procs_sin_archivos'})
                            .reset_index()
                            .loc[:, ['CLAVEUC', 'pc_procs_sin_archivos']])
    df_feature.columns.name = ''
    return df_feature


def promedio_procs_por_archivo(df, **kwargs):
    """Usa tabla scraper.
    Calcula los archivos anexos promedio por procedimiento de la UC"""
    df_feature = (df.groupby('CLAVEUC', as_index=False)
                    .agg({'numero_archivos': 'mean',
                          'CODIGO_EXPEDIENTE': 'count'}))
    df_feature = df_feature.rename(
        columns={'numero_archivos': 'promedio_archivos_por_proc'})
    df_feature = df_feature.assign(
        promedio_procs_por_archivo=(
            1 / (df_feature.promedio_archivos_por_proc + 1)
        )
    )
    df_feature = df_feature.loc[:, ['CLAVEUC', 'promedio_procs_por_archivo']]
    return df_feature


def tendencia_no_publicacion_contratos(df, **kwargs):
    # scraper
    def _estimar_pendiente(row):
        # TODO: filtrar nans
        y = row.values.reshape(-1, 1)
        x = np.arange(0, y.shape[0]).reshape(-1, 1)
        model = Ridge()
        model.fit(x, y)
        pendiente = model.coef_.flatten()[0]
        pendiente *= -1
        return pendiente

    df = df.copy()
    df = df.assign(Year=df.FECHA_INICIO.dt.year)
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_interes = 'archivo_contrato'
    df_feature = (df.groupby(['CLAVEUC', 'Year', col_interes])
                  .NUMERO_PROCEDIMIENTO.nunique()
                  .reset_index()
                  .pivot_table(index=['CLAVEUC', 'Year'],
                               columns=[col_interes],
                               values='NUMERO_PROCEDIMIENTO')
                  .fillna(0)
                  .reset_index()
                  .rename(columns={1: 'pc_con_contrato',
                                   0: 'pc_sin_contrato'}))
    total = df_feature[
        ['pc_sin_contrato', 'pc_con_contrato']].sum(axis=1)

    df_feature = df_feature.assign(
        pc_con_contrato=(df_feature.pc_con_contrato * 100).divide(total)
    )
    df_feature = (df_feature.drop('pc_sin_contrato', axis=1)
                  .pivot(index='CLAVEUC',
                         columns='Year',
                         values='pc_con_contrato')
                  # .reset_index()
                  .drop(2017, axis=1)
                  .fillna(100))
    df_feature = df_feature.assign(
        tendencia_no_publicacion_contratos=df_feature.apply(
            _estimar_pendiente, axis=1)
    )
    df_feature = (df_feature.reset_index()
                  .loc[:, ['CLAVEUC',
                           'tendencia_no_publicacion_contratos']])
    # left join
    df_feature = pd.merge(df_claves, df_feature,
                          on='CLAVEUC', how='left')
    df_feature = df_feature.assign(
        tendencia_no_publicacion_contratos=df_feature.tendencia_no_publicacion_contratos.fillna(0)
    )
    return df_feature


def porcentaje_adjudicaciones_incompletas(df, **kwargs):
    """Usa tabla scraper.
    Calcula el porcentaje de procedimientos (adjudicaciones directas)
    con documentacion incompleta"""
    df_claves = pd.DataFrame(data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    tipos_validos = {'ADJUDICACION DIRECTA', }
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)].copy()
    df = df.reset_index(drop=True)
    # Archvios
    archivos = ['archivo_contrato', ]
    df = df.assign(
        suma_archivos=lambda dataframe: dataframe[archivos].sum(axis=1))
    df_feature = df.groupby(
        ['CLAVEUC', 'suma_archivos'], as_index=False
    ).CODIGO_EXPEDIENTE.count()
    df_feature = (df_feature.pivot(index='CLAVEUC',
                                   columns='suma_archivos',
                                   values='CODIGO_EXPEDIENTE')
                            .fillna(0))

    if len(archivos) not in df_feature.columns:
        raise ValueError('Nadie tuvo los archivos completos')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = df_feature.assign(
        pc_adjudicaciones_incompletas=df_feature.drop(
            {len(archivos)}, axis=1).sum(axis=1)
    )
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', 'pc_adjudicaciones_incompletas']])
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def porcentaje_invitaciones_incompletas(df, **kwargs):
    """Usa tabla scraper.
    Calcula el porcentaje de procedimientos (inv a 3)
    con documentacion incompleta"""
    df_claves = pd.DataFrame(data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    tipos_validos = {'INVITACION A CUANDO MENOS TRES', }
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)].copy()
    df = df.reset_index(drop=True)
    # Archvios
    archivos = [
        'archivo_convocatoria', 'archivo_apertura',
        'archivo_fallo', 'archivo_contrato'
    ]
    df = df.assign(
        suma_archivos=lambda dataframe: dataframe[archivos].sum(axis=1))
    df_feature = df.groupby(
        ['CLAVEUC', 'suma_archivos'], as_index=False
    ).CODIGO_EXPEDIENTE.count()
    df_feature = (df_feature.pivot(index='CLAVEUC',
                                   columns='suma_archivos',
                                   values='CODIGO_EXPEDIENTE')
                            .fillna(0))

    if len(archivos) not in df_feature.columns:
        raise ValueError('Nadie tuvo los archivos completos')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = df_feature.assign(
        pc_invitaciones_incompletas=df_feature.drop(
            {len(archivos)}, axis=1).sum(axis=1)
    )
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', 'pc_invitaciones_incompletas']])
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def porcentaje_licitaciones_incompletas(df, **kwargs):
    """Usa tabla scraper.
    Calcula el porcentaje de procedimientos (licitaciones publicas)
    con documentacion incompleta"""
    df_claves = pd.DataFrame(data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    tipos_validos = {'LICITACION PUBLICA', 'LICITACION PUBLICA CON OSD'}
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)].copy()
    df = df.reset_index(drop=True)
    # Archvios
    archivos = [
        'archivo_convocatoria', 'archivo_junta',
        'archivo_apertura', 'archivo_fallo', 'archivo_contrato'
    ]
    df = df.assign(
        suma_archivos=lambda dataframe: dataframe[archivos].sum(axis=1))
    df_feature = df.groupby(
        ['CLAVEUC', 'suma_archivos'], as_index=False).CODIGO_EXPEDIENTE.count()
    df_feature = (df_feature.pivot(index='CLAVEUC',
                                   columns='suma_archivos',
                                   values='CODIGO_EXPEDIENTE')
                            .fillna(0))
    if len(archivos) not in df_feature.columns:
        raise ValueError('Nadie tuvo los archivos completos')
    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = df_feature.assign(
        pc_licitaciones_incompletas=df_feature.drop(
            {len(archivos)}, axis=1).sum(axis=1)
    )
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', 'pc_licitaciones_incompletas']])
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature

