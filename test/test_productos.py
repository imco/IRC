import pandas as pd

from features.productos import (
    falta_transparencia_pnt
)


class TestTransparencia:
    def test_promedio_datos_faltantes_por_contrato_pnt(self):
        common = ['NUMERO_PROCEDIMIENTO', 'TIPO_PROCEDIMIENTO', 'TIPO_CONTRATACION', 'PROVEEDOR_CONTRATISTA']
        sipot_cols = (['LIGA_AUTORIZACION', 'REF_COTIZACIONES', 'LIGA_CONTRATO'] +
                      ['LIGA_CONVOCATORIA', 'LIGA_FALLO', 'LIGA_FINIQUITO'])

        df_test_procs = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '001', 1000],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '001', 2000],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '001', 2000],
            ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '001', 9000],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', '001', 5000],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '002', 3000],
            ['002-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa F', '002', 3000]
        ], columns=common + ['CLAVEUC', 'IMPORTE_PESOS'])

        df_test_sipot = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', 1, 1, 1, None, None, None, 1000],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 1, 1, 1, None, None, None, 2000],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', None, None, None, None, None, None, 3000],
            ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', None, None, 1, 1, 1, 1, 9000],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', None, None, None, None, 1, 1, 9000],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', None, None, 1, None, None, None, 3000],
        ], columns=common + sipot_cols + ['PRECIO_TOTAL'])

        df_expected = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '001', 1000],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '001', 2000],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '001', 2000],
            ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '001', 9000],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', '001', 5000],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '002', 3000],
            ['002-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa F', '002', 3000]
        ], columns=common + ['CLAVEUC', 'IMPORTE_PESOS'])

        df_fallas = pd.DataFrame(data=[
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            # Esta AD para la Empresa B no tiene las 3 ligas requeridas y presenta mal monto
            [1, 1, 1, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0],
            # Una LP para Empresa D sin contrato ni convocatoria y presenta mal monto
            [0, 0, 0, 1, 0, 1, 0, 1, 0],
            # Esta AD para Empresa B le faltó autorización y cotizaciones
            [1, 1, 0, 0, 0, 0, 0, 0, 0],
            # Esta última no esta en SIPOT
            [0, 0, 0, 0, 0, 0, 0, 0, 1]
        ], columns=[
            'ad_sin_autorizacion',
            'ad_sin_cotizacion',
            'ad_sin_contrato',
            'inv3_lp_sin_convocatoria',
            'inv3_lp_sin_fallo',
            'inv3_lp_sin_contrato',
            'inv3_lp_sin_finiquito',
            'inconsistencias_monto_pnt_compranet',
            'inconsistencias_publicacion_pnt_compranet'
        ])

        df_expected = pd.concat([df_expected, df_fallas], axis=1)

        res = falta_transparencia_pnt(df_test_procs, df_test_sipot)
        pd.testing.assert_frame_equal(res, df_expected)

