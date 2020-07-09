import pandas as pd

from features.transparencia import (
    promedio_datos_faltantes_por_contrato_pnt,
    pc_procs_con_testigo_social
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
            # Una AD sin las 3 LIGAS requeridas y mal monto
            # Una LP sin CONTRATO ni CONVOCATORIA, y con mal monto
            ['001', (4 + 3) / 5],
            # Una empresa sin AUTORIZACION ni FALLO,
            # un procedimiento no registrado en SIPOT es penalizado por 3 fallos de AD + la ausencia
            ['002', (2 + 1) / 2]
        ], columns=['CLAVEUC', 'promedio_datos_faltantes_por_contrato_pnt'])

        res = promedio_datos_faltantes_por_contrato_pnt(df_test_procs, df_test_sipot)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_pc_procs_con_testigo_social(self):
        df_test = pd.DataFrame(data=[
            ['001', 1000, 1],
            ['001', 1001, 1],
            ['001', 1002, 0],
            ['002', 1003, 0],
            ['002', 1004, 0],
            ['002', 1005, 0]
        ], columns=['CLAVEUC', 'CODIGO_EXPEDIENTE', 'testigo_social'])

        res = pc_procs_con_testigo_social(df_test)
        assert(res.iloc[0].pc_procs_con_testigo_social > 66.6)
        assert(res.iloc[1].pc_procs_con_testigo_social == 0)
