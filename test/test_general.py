import pandas as pd

from features.general import (
    monto_total_por_tipo,
    numero_contratos_por_tipo
)


class TestGeneral:
    def get_test_procs(self):
        return pd.DataFrame(data=[
            ['ISSSTE', '0001', 'Empresa A', '001-AD-1001/2018', 1001, 'ADJUDICACION DIRECTA', 12000],
            ['ISSSTE', '0001', 'Empresa A', '001-AD-1002/2018', 1002, 'ADJUDICACION DIRECTA', 14000],
            ['ISSSTE', '0001', 'Empresa B', '001-LP-1003/2018', 1003, 'LICITACION PUBLICA', 114000],
            ['ISSSTE', '0002', 'Empresa C', '001-AD-1004/2018', 1004, 'ADJUDICACION DIRECTA', 4000],
            ['ISSSTE', '0002', 'Empresa C', '001-LP-1005/2018', 1005, 'LICITACION PUBLICA', 90000],
            ['ISSSTE', '0002', 'Empresa D', '001-LP-1006/2018', 1006, 'LICITACION PUBLICA', 80000],
            ['ISSSTE', '0002', 'Empresa E', '001-LP-1007/2018', 1007, 'LICITACION PUBLICA', 40000],
            ['ISSSTE', '0003', 'Empresa A', '001-LP-1008/2018', 1008, 'INVITACION A CUANDO MENOS TRES', 70000],
            ['ISSSTE', '0003', 'Empresa A', '001-LP-1009/2018', 1009, 'OTRO', 20000]
        ], columns=[
            'DEPENDENCIA', 'CLAVEUC', 'PROVEEDOR_CONTRATISTA',
            'NUMERO_PROCEDIMIENTO', 'CODIGO_CONTRATO', 'TIPO_PROCEDIMIENTO',
            'IMPORTE_PESOS'
        ])

    def test_monto_total_por_tipo(self):
        df_test_procs = self.get_test_procs()
        df_expected = pd.DataFrame(data=[
            ['0001', 26000.0, 0.0, 114000.0],
            ['0002', 4000.0, 0.0, 210000.0],
            ['0003', 0.0, 70000.0, 0.0]
        ], columns=[
            'CLAVEUC',
            'monto_AD', 'monto_INV3', 'monto_LP'
        ])

        res = monto_total_por_tipo(df_test_procs)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_numero_contratos_por_tipo(self):
        df_test_procs = self.get_test_procs()
        df_expected = pd.DataFrame(data=[
            ['0001', 2.0, 0.0, 1.0],
            ['0002', 1.0, 0.0, 3.0],
            ['0003', 0.0, 1.0, 0.0]
        ], columns=[
            'CLAVEUC',
            'numero_contratos_AD', 'numero_contratos_INV3', 'numero_contratos_LP'
        ])

        res = numero_contratos_por_tipo(df_test_procs)
        pd.testing.assert_frame_equal(res, df_expected)
