#!/usr/bin/env python


# Created by Raul Peralta-Lozada (28/09/17)
import bisect
from features.productos import falta_transparencia_pnt
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge

DataFrame = pd.DataFrame


def porcentaje_procs_presenciales(df: DataFrame,
                                  **kwargs) -> DataFrame:
    """
    Usa tabla de procedimientos. Calcula el porcentaje de
    procedimientos presenciales
    Indicador:
        Porcentaje de procedimientos presenciales
    """
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
        columns={'PRESENCIAL': 'porcentaje_procs_presenciales'}
    )
    conteo_formas = conteo_formas.loc[
        :, ['CLAVEUC', 'porcentaje_procs_presenciales']
    ]
    return conteo_formas


def contratos_promedio_por_procedimimento(df: DataFrame,
                                          **kwargs) -> DataFrame:
    """Agrupación de contratos en un mismo procedimiento. Usa tabla
    de procedimientos"""
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
        columns={'CODIGO_CONTRATO': 'contratos_promedio_por_procedimimento'}
    )
    return contratos_por_proc


def promedio_datos_faltantes_por_contrato(df: DataFrame,
                                          cols=None,
                                          **kwargs) -> DataFrame:
    """
    Promedio de datos fatantes por contrato en la UC. Los datos
    son los que están en el parámetro 'cols' y de la tabla de procs.
    Indicador:
        Datos faltantes en la base de Compranet (procedimientos de contratación)
    """
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

    df_feature = pd.merge(monto_por_contrato, df_cols,
                          on=cols_id, how='inner')
    df_feature = df_feature.assign(
        promedio_datos_faltantes=df_feature.loc[:, cols].isnull().sum(axis=1)
    )
    df_feature = df_feature.groupby(
        'CLAVEUC', as_index=False).promedio_datos_faltantes.mean()
    feature_name = {
        'promedio_datos_faltantes': 'promedio_datos_faltantes_por_contrato'
    }
    df_feature = df_feature.rename(
        columns=feature_name)
    return df_feature

# Features del scraper
# TODO: se debe normalizar las UC que se tienen en todas las bases


def pc_procs_sin_contrato(df: DataFrame, **kwargs) -> DataFrame:
    """
    Usa tabla scraper. Calcula el porcentaje de procedimientos
    sin archivo de contrato
    Indicador:
        Porcentaje de procedimientos sin contrato publicado
    """
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_interes = 'archivo_contrato'
    col_feature = 'pc_procs_sin_contrato'
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
    df_feature = pd.merge(df_claves, df_feature,
                          on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def pc_procs_sin_fallo(df: DataFrame,
                       tipos_validos=None,
                       **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos sin archivo de
    fallo
    Indicador:
        Porcentaje de procedimientos sin fallo publicado
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
    col_interes = 'archivo_fallo'
    col_feature = 'pc_procs_sin_fallo'
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


def pc_procs_sin_apertura(df: DataFrame,
                          tipos_validos=None,
                          **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos sin archivo de
    apertura de proposiciones
    Indicador:
        Porcentaje de procedimientos sin apertura de proposiciones
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
    col_interes = 'archivo_apertura'
    col_feature = 'pc_procs_sin_apertura'
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


def pc_procs_sin_archivos(df: DataFrame, **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Se calcula el porcentaje de procedimientos sin archivos por UC
    Indicador:
        Porcentaje de procedimiento sin ningún anexo
    """
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


def promedio_procs_por_archivo(df: DataFrame, **kwargs) -> DataFrame:
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


def tendencia_no_publicacion_contratos(df: DataFrame,
                                       **kwargs) -> DataFrame:
    """
    Usa la tabla del scraper. Calcula el decremento
    en publicación de contratos hasta el año indicado.
    Indicador:
        Diferencia entre el porcentaje de contratos públicados en 2016 vs 2012-2013
    """
    def _estimar_pendiente(row):
        # TODO: filtrar nans
        y = row.values.reshape(-1, 1)
        x = np.arange(0, y.shape[0]).reshape(-1, 1)
        model = Ridge()
        model.fit(x, y)
        pendiente = model.coef_.flatten()[0]
        pendiente *= -1
        return pendiente

    if 'year' in kwargs:
        year = kwargs['year']
    else:
        year = 1e5

    df = df.copy()
    df = df.assign(Year=df.FECHA_INICIO.dt.year)

    # Filtra el dataframe hasta el año indicado
    df = df[df['Year'] <= year]

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
    feature = df_feature.tendencia_no_publicacion_contratos.fillna(0)
    df_feature = df_feature.assign(
        tendencia_no_publicacion_contratos=feature
    )
    return df_feature


def pc_adjudicaciones_incompletas(df: DataFrame,
                                  **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos (adjudicaciones directas)
    con documentacion incompleta
    Indicador:
        Porcentaje de AD que no cumplen con contrato publicado
    """
    df_claves = pd.DataFrame(data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    tipos_validos = {'ADJUDICACION DIRECTA', }
    df = df.loc[df.TIPO_PROCEDIMIENTO.isin(tipos_validos)].copy()
    df = df.reset_index(drop=True)
    # Archivos
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


def pc_procs_sin_junta_aclaracion(df: DataFrame,
                                  tipos_validos=None,
                                  **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos sin archivo de
    junta de aclaraciones
    Indicador:
        Porcentaje de procedimientos sin junta de aclaraciones
    """
    if tipos_validos is None:
        # solo aplica para Licitaciones publicas
        tipos_validos = {
            'LICITACION PUBLICA',
            'LICITACION PUBLICA CON OSD'
        }
    df_claves = pd.DataFrame(
        data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_interes = 'archivo_junta'
    col_feature = 'pc_procs_sin_junta_aclaracion'
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


def pc_invitaciones_incompletas(df: DataFrame, **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos (inv a 3)
    con documentacion incompleta
    Indicador:
        Porcentaje de INV3 que no cumplen con convocatoria, la apertura de propuestase, el fallo y el contrato.
    """
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

    for i in range(len(archivos) + 1):
        if i not in df_feature.columns:
            # Nadie tuvo los archivos completos
            df_feature[i] = 0

    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    # Remueve la columna que equivale a tener toda la documentación
    df_feature = df_feature.assign(
        pc_invitaciones_incompletas=df_feature.drop(
            {len(archivos)}, axis=1).sum(axis=1)
    )
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', 'pc_invitaciones_incompletas']])
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


def pc_licitaciones_incompletas(df: DataFrame,
                                **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos (licitaciones publicas)
    con documentacion incompleta
    Indicador:
        Porcentaje de licitaciones que no cumplen con convocatoria, junta de aclaraciones, apertura de propuestas, fallo y contrato
    """
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
    # Remueve la columna que equivale a tener toda la documentación
    df_feature = df_feature.assign(
        pc_licitaciones_incompletas=df_feature.drop(
            {len(archivos)}, axis=1).sum(axis=1)
    )
    df_feature = (df_feature.reset_index()
                            .loc[:, ['CLAVEUC', 'pc_licitaciones_incompletas']])
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)
    return df_feature


# Tabla de participantes (y procedimientos)


def pc_inconsistencias_en_monto(df_proc: DataFrame,
                                df_part: DataFrame,
                                **kwargs) -> DataFrame:
    """
    Usa tabla de proc y participantes. Obtiene el porcentaje de
    procedimientos en donde el monto es diferente en participantes y
    procedimientos
    Indicador:
        Porcentaje de inconsistencias en los montos reportados entre base pública y Compranet IM
    """
    df_proc: DataFrame = df_proc.copy()
    df_part: DataFrame = df_part.copy()

    # Calcular el monto de los ganadores en participantes
    if 'ESTATUS_FALLO' in df_part.columns:
        df_ganadores = df_part.loc[df_part.ESTATUS_FALLO == 'GANADOR']
    else:
        # La nueva base conseguida del SIPOT no tiene ESTATUS_FALLO
        df_ganadores = df_part.loc[:, :]

    estatus = df_ganadores.ESTATUS_DE_PROPUESTA.mask(
        df_ganadores.ESTATUS_DE_PROPUESTA == 'SIN REPORTAR', 'GANADOR'
    )
    df_ganadores = df_ganadores.assign(ESTATUS_DE_PROPUESTA=estatus)
    del estatus
    df_ganadores = df_ganadores.loc[
        df_ganadores.ESTATUS_DE_PROPUESTA == 'GANADOR']
    monto_ganadores_procs = df_ganadores.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO'],
        as_index=False).PRECIO_TOTAL.sum()
    monto_ganadores_procs = monto_ganadores_procs.rename(
        columns={'PRECIO_TOTAL': 'monto_participantes'})
    # calcular el monto de procedimientos
    monto_procs = df_proc.groupby(
        ['CLAVEUC', 'NUMERO_PROCEDIMIENTO'], as_index=False
    ).IMPORTE_PESOS.sum()
    monto_procs = monto_procs.rename(
        columns={'IMPORTE_PESOS': 'monto_procedimientos'})

    df_final = pd.merge(monto_procs, monto_ganadores_procs,
                        on=['CLAVEUC', 'NUMERO_PROCEDIMIENTO'], how='left')
    # Se asigna el valor de procedimientos cuando no se tiene
    # valor de participantes
    monto_participantes = df_final.monto_participantes.mask(
        df_final.monto_participantes.isnull(), df_final.monto_procedimientos
    )
    df_final = df_final.assign(monto_participantes=monto_participantes)
    num_procs = (df_final.groupby('CLAVEUC', as_index=False)
                         .NUMERO_PROCEDIMIENTO.count()
                         .rename(columns={'NUMERO_PROCEDIMIENTO': 'num_procs'}))
    is_diff = (df_final.monto_participantes != df_final.monto_procedimientos)
    is_diff = is_diff.astype(int)
    df_final = df_final.assign(is_diff=is_diff)
    df_final = df_final.groupby('CLAVEUC', as_index=False).is_diff.sum()
    df_final = pd.merge(df_final, num_procs, on='CLAVEUC', how='inner')
    feature = df_final.is_diff.divide(df_final.num_procs)
    df_final = df_final.assign(pc_inconsistencias_en_monto=feature)
    df_featue = df_final.loc[:, ['CLAVEUC', 'pc_inconsistencias_en_monto']]
    return df_featue


def pc_procs_con_provs_faltantes(df_proc: DataFrame,
                                 df_part: DataFrame) -> DataFrame:
    """
    Usa tabla de proc y participantes. Obtiene el porcentaje de
    proveedores que aparecen en participantes pero no en
    procedimientos
    Indicador:
        Porcentaje de procedimientos en la base pública de contratos en donde no se reportan a todos los ganadores.
    """
    col_interes = [
        'CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'PROVEEDOR_CONTRATISTA']
    df_proc: DataFrame = (df_proc.copy().loc[:, col_interes])
    df_part: DataFrame = df_part.copy()

    # Sólo los ganadores
    # La nueva base conseguida del SIPOT no tiene ESTATUS_FALLO
    if 'ESTATUS_FALLO' in df_part.columns:
        df_part = df_part.loc[df_part.ESTATUS_FALLO == 'GANADOR']

    estatus = df_part.ESTATUS_DE_PROPUESTA.mask(
        df_part.ESTATUS_DE_PROPUESTA == 'SIN REPORTAR', 'GANADOR'
    )
    df_part = df_part.assign(ESTATUS_DE_PROPUESTA=estatus)
    df_part = df_part.loc[df_part.ESTATUS_DE_PROPUESTA == 'GANADOR']
    df_part: DataFrame = df_part.loc[:, col_interes]
    # conseguir conjuntos
    df_proveedores_proc = (df_proc.groupby(['CLAVEUC', 'NUMERO_PROCEDIMIENTO'])
                                  .agg({'PROVEEDOR_CONTRATISTA': lambda x: set(x)})
                                  .reset_index()
                                  .rename(columns={'PROVEEDOR_CONTRATISTA': 'proveedores_proc'}))
    df_proveedores_part = (df_part.groupby(['CLAVEUC', 'NUMERO_PROCEDIMIENTO'])
                                  .agg({'PROVEEDOR_CONTRATISTA': lambda x: set(x)})
                                  .reset_index()
                                  .rename(columns={'PROVEEDOR_CONTRATISTA': 'proveedores_part'}))

    # P. ej. en 2012 no hay OBRA PUBLICA en df_participantes
    if not df_part.empty:
        df_final = pd.merge(df_proveedores_proc, df_proveedores_part,
                            on=['CLAVEUC', 'NUMERO_PROCEDIMIENTO'], how='left')
    else:
        df_final = df_proveedores_proc
        df_final["proveedores_part"] = ""


    num_procs = (df_final.groupby('CLAVEUC', as_index=False)
                         .NUMERO_PROCEDIMIENTO.count()
                         .rename(columns={'NUMERO_PROCEDIMIENTO': 'num_procs'}))

    # TODO: llenar los proveedores que faltan en participantes con la de procedimientos
    proveedores_part = df_final.proveedores_part.mask(
        df_final.proveedores_part.isnull(), df_final.proveedores_proc
    )
    df_final = df_final.assign(proveedores_part=proveedores_part)
    is_diff = df_final.proveedores_proc != df_final.proveedores_part
    is_diff = is_diff.astype(int)
    df_final = df_final.assign(is_diff=is_diff)
    df_final = df_final.groupby('CLAVEUC', as_index=False).is_diff.sum()
    df_final = pd.merge(df_final, num_procs,
                        on='CLAVEUC', how='inner')
    feature = df_final.is_diff.divide(df_final.num_procs)
    df_final = df_final.assign(pc_procs_con_provs_faltantes=feature)
    df_feature = df_final.loc[:, ['CLAVEUC', 'pc_procs_con_provs_faltantes']]
    return df_feature


def promedio_datos_faltantes_por_contrato_pnt(df_procs: DataFrame,
                                              df_sipot: DataFrame) -> DataFrame:
    """
    Indicador compuesto de las siguientes variables que
    miden Falta de Transparencia en PNT:
        1. Adjudicación directa sin autorización del ejercicio de la opción (dictamen).
        2. Adjudicación directa sin cotización (posibles contratantes)
        3. Adjudicación directa sin contrato
        4. INV3 y/o LP sin convocatoria.
        5. INV3 y/o LP sin fallo de adjudicación.
        6. INV3 y/o LP sin contrato.
        7. INV3 y/o LP sin finiquito.
        8. Inconsistencias en el monto reportado entre la PNT y Compranet.
        9. Inconsistencias entre lo publicado en Compranet y en PNT

    Utiliza el subproducto falta_transparencia_pnt
    """
    # Usamos los procedimientos como base
    # Consigue las 9 variables y las suma en una nueva columna
    # Lista copiada de falta_transparencia_pnt
    fallas_columnas = [
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

    fallas = df_procs.merge(falta_transparencia_pnt(df_procs, df_sipot))
    fallas = fallas.assign(total_fallas=fallas.loc[:, fallas_columnas].sum(axis=1))

    # Sacamos el promedio por UC
    df_claves = pd.DataFrame(data=df_procs.CLAVEUC.unique(), columns=['CLAVEUC'])
    df_feature = (fallas.groupby('CLAVEUC', as_index=False)
                  .total_fallas.mean()
                  .rename(columns={'total_fallas': 'promedio_datos_faltantes_por_contrato_pnt'}))

    return df_feature


def pc_procs_con_testigo_social(df: DataFrame, **kwargs) -> DataFrame:
    """
    Usa tabla scraper.
    Calcula el porcentaje de procedimientos con testigo social.
    Indicador:
        Porcentaje de procedimientos que contaron con testimonio del Testigo Social
    """
    df_claves = pd.DataFrame(data=df.CLAVEUC.unique(), columns=['CLAVEUC'])
    col_interes = 'testigo_social'
    col_feature = 'pc_procs_con_testigo_social'
    df = df.copy()
    df_feature = (df.groupby(['CLAVEUC', col_interes],
                             as_index=False).CODIGO_EXPEDIENTE.count()
                    .pivot(index='CLAVEUC',
                           columns=col_interes,
                           values='CODIGO_EXPEDIENTE')
                    .fillna(0)
                    .rename(columns={1: col_feature}))

    columnas = list(df_feature.columns.values)
    if col_feature not in columnas:
        raise ValueError('Ningún procedimiento presento testigo')

    df_feature = (df_feature * 100).divide(df_feature.sum(axis=1), axis=0)
    df_feature = (df_feature.reset_index()
                  .loc[:, ['CLAVEUC', col_feature]])
    df_feature.columns.name = ''
    df_feature = pd.merge(df_claves, df_feature, on='CLAVEUC', how='left')
    df_feature = df_feature.fillna(0)

    return df_feature

