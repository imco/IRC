import pandas as pd

from features.anomalias import (
    procs_con_incumplimiento_de_exclusividad_mipyme
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
