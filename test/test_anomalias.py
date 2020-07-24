import pandas as pd

from features.anomalias import (
    pc_inconsistencias_convenios_pnt_compranet,
    procs_con_incumplimiento_de_exclusividad_mipyme,
    pc_adj_directas_excedieron_monto,
    pc_adj_directas_excedieron_monto_fraccionado
)


class TestAnomalias:
    def test_pc_inconsistencias_convenios_pnt_compranet(self):
        common = ['NUMERO_PROCEDIMIENTO', 'TIPO_PROCEDIMIENTO', 'TIPO_CONTRATACION', 'PROVEEDOR_CONTRATISTA']
        df_test_scrap = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '001', 0],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '001', 1],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa V', '001', 1],
            ['001-AD-0004/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa V', '001', 2],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '002', 0],
            # Ignorado porque no está en el sipot
            ['002-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '002', 0]
        ], columns=common + ['CLAVEUC', 'numero_convenios'])

        df_test_sipot = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', 0],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', 2],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa V', 2],
            ['001-AD-0004/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa V', 2],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', 1]
        ], columns=common + ['LIGA_CONVENIO'])

        df_expected = pd.DataFrame(data=[
            ['001', 0.50], # (2.00) / 4
            ['002', 1.00]  # (1.00) / 1
        ], columns=['CLAVEUC', 'pc_inconsistencias_convenios_pnt_compranet'])

        res = pc_inconsistencias_convenios_pnt_compranet(df_test_scrap, df_test_sipot)
        pd.testing.assert_frame_equal(res, df_expected)

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

    def test_pc_adj_directas_excedieron_monto(self):
        df_test_procs = pd.DataFrame(data=[
            ['006A2O001', 'ADJUDICACION DIRECTA', 'ARRENDAMIENTOS', 'AA-006A2O001-E65-2017', 1692235, '2018-01-01', 'SINTEG EN MEXICO', 263362.22],
            ['006A2O001', 'ADJUDICACION DIRECTA', 'ARRENDAMIENTOS', 'AA-006A2O001-E65-2017', 1692246, '2018-01-01', 'IT SERVICES AND SOLUTIONS', 167555.37],
            ['006A2O001', 'ADJUDICACION DIRECTA', 'ARRENDAMIENTOS', 'AA-006A2O001-E65-2017', 1692222, '2018-01-01', 'BENITO ARTEAGA SILVA', 268293.30],
            ['006A2O001', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', 'AA-006A2O001-E59-2018', 1988018, '2018-12-12', 'ECO FALH', 1109000.00],
            ['006A2O001', 'ADJUDICACION DIRECTA', 'ADQUISICIONES', 'AA-006A2O001-E59-2018', 1988014, '2018-12-12', 'SISTEMAS PHOENIX S DE RL', 474328.00]
        ], columns=([
            'CLAVEUC',
            'TIPO_PROCEDIMIENTO',
            'TIPO_CONTRATACION',
            'NUMERO_PROCEDIMIENTO',
            'CODIGO_CONTRATO',
            'FECHA_INICIO',
            'PROVEEDOR_CONTRATISTA',
            'IMPORTE_PESOS'
        ]))

        df_test_procs.FECHA_INICIO = pd.to_datetime(df_test_procs.FECHA_INICIO)

        df_maximos = pd.DataFrame(data=[
            [2018, 'ADQUISICIONES',     583480.0, 1e7],
            [2018, 'SERVICIOS',         583480.0, 1e7],
            [2018, 'ARRENDAMIENTOS',    583480.0, 1e7]
        ], columns=['Año', 'Tipo de contratación', 'Adjudicación directa', 'INV3'])

        df_expected = pd.DataFrame(data=[
            ['006A2O001', 'ADQUISICIONES',   50.0],
            ['006A2O001', 'SERVICIOS',        0.0],
            ['006A2O001', 'ARRENDAMIENTOS',   0.0],
        ], columns=['CLAVEUC', 'TIPO_PROCEDIMIENTO', 'pc_adj_directas_excedieron_monto'])

        acc = []
        for t in ['ADQUISICIONES', 'SERVICIOS', 'ARRENDAMIENTOS']:
            res = pc_adj_directas_excedieron_monto(df_test_procs, df_maximos, tipo_contratacion=t, year=2018)
            if res.empty == False:
                res.insert(1, 'TIPO_PROCEDIMIENTO', t)
                acc.append(res)

        res = pd.concat(acc).reset_index().drop('index', axis=1)
        pd.testing.assert_frame_equal(res, df_expected)
        return None

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
