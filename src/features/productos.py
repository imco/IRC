#!/usr/bin/env python

import pandas as pd
import numpy as np

DataFrame = pd.DataFrame


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
    id_cols = [
        'NUMERO_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        'TIPO_CONTRATACION',
        'PROVEEDOR_CONTRATISTA'
    ]

    merged = df_procs.merge(df_sipot, on=id_cols, how='left', indicator=True)

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

    # Remueve columnas utilizadas para los cálculos
    merged.drop(ad_cols + lp_cols + ['PRECIO_TOTAL', '_merge'], axis=1, inplace=True)

    df_feature = pd.concat([merged, fallas], axis=1)

    return df_feature
