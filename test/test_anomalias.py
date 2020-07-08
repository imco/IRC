import pandas as pd

from features.anomalias import (
    procs_con_incumplimiento_de_exclusividad_mipyme,
    pc_adj_directas_excedieron_monto_fraccionado
)


class TestAnomalias:
    def test_procs_con_incumplimiento_de_exclusividad_mipyme(self):
        df_test_procs = pd.DataFrame(data=[
            ['001', 1000, 'MICRO'],
            ['001', 1001, 'NO MIPYME'],
            ['001', 1002, 'NO MIPYME'],
            ['002', 1003, 'PEQUENA'],
            ['002', 1004, 'MEDIANA'],
            ['002', 1005, 'NO REPORTADA']
        ], columns=['CLAVEUC', 'CODIGO_EXPEDIENTE', 'ESTRATIFICACION_MPC'])

        df_test_scrap = pd.DataFrame(data=[
            [1000, 1],
            [1001, 1],
            [1002, 1],
            [1003, 1],
            [1004, 0],
            [1005, 0]
        ], columns=['CODIGO_EXPEDIENTE', 'exclusivo_mipymes'])

        res = procs_con_incumplimiento_de_exclusividad_mipyme(df_test_procs, df_test_scrap)

        assert(res.iloc[0].procs_con_incumplimiento_de_exclusividad_mipyme == 2)
        assert(res.iloc[1].procs_con_incumplimiento_de_exclusividad_mipyme == 0)

    def test_pc_adj_directas_excedieron_monto_fraccionado(self):
        df_test_procs = pd.DataFrame(data=[
            ['001', 'ADJUDICACION DIRECTA', 'SERVICIOS', '2018-01-01', 'Empresa A', '001-AD-0001/2018', 1000.0],
            ['001', 'ADJUDICACION DIRECTA', 'SERVICIOS', '2018-01-01', 'Evil corp', '001-AD-0002/2018', 500.0],
            ['001', 'ADJUDICACION DIRECTA', 'SERVICIOS', '2018-01-04', 'Evil corp', '001-AD-0003/2018', 600.0],
            ['001', 'LICITACION PUBLICA', 'SERVICIOS', '2018-01-01', 'Empresa A', '001-LP-0004/2018', 5000.0],
            ['001', 'ADJUDICACION DIRECTA', 'SERVICIOS', '2018-02-01', 'Empresa A', '001-AD-0005/2018', 1000.0],
            ['001', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', '2018-02-01', 'Empresa A', '001-AD-0006/2018', 2000.0],

            ['002', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', '2018-02-01', 'Empresa A', '002-AD-0001/2018', 200.0],
            ['002', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', '2018-02-01', 'Empresa A', '002-AD-0002/2018', 300.0],
            ['002', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', '2018-02-01', 'Empresa A', '002-AD-0003/2018', 400.0],
            ['002', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', '2018-07-02', 'Evil corp', '002-AD-0004/2018', 600.0],
            ['002', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', '2018-07-04', 'Evil corp', '002-AD-0005/2018', 1600.0],
            ['002', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', '2018-07-05', 'Evil corp', '002-AD-0006/2018', 200.0]
        ], columns=([
            'CLAVEUC', 'TIPO_PROCEDIMIENTO', 'TIPO_CONTRATACION', 'FECHA_INICIO',
            'PROVEEDOR_CONTRATISTA', 'NUMERO_PROCEDIMIENTO', 'IMPORTE_PESOS'
        ]))

        df_test_procs.FECHA_INICIO = pd.to_datetime(df_test_procs.FECHA_INICIO)

        df_maximos = pd.DataFrame(data=[
            [2018, 'ADQUISICIONES', 2000, 10000],
            [2018, 'SERVICIOS', 1000, 10000],
            [2019, 'ADQUISICIONES', 1100, 11000],
            [2019, 'SERVICIOS', 1100, 11000]
        ], columns=['Año', 'Tipo de contratación', 'Adjudicación directa', 'INV3'])

        df_expected = pd.DataFrame(data=[
            ['001', .40],
            ['002', .50]
        ], columns=['CLAVEUC', 'pc_adj_directas_excedieron_monto_fraccionado'])

        res = pc_adj_directas_excedieron_monto_fraccionado(df_test_procs, df_maximos, year=2018)
        pd.testing.assert_frame_equal(res, df_expected)
