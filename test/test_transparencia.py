import pandas as pd

from features.transparencia import (
    pc_procs_con_testigo_social
)


class TestTransparencia:
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
