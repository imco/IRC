import pandas as pd
import numpy as np

from utils.score_cards import (
    escalar_features,
    normaliza_columnas,
    invierte_relacion_de_columnas
)


class TestUtils:
    def test_escalar_features(self):
        co = ['pc_procs_con_un_licitante', 'procs_con_contrato']
        df = pd.DataFrame(data=[
            ['001', 0.80, 1000],
            ['002', 0.60, 7200],
            ['003', 0.50, 5000],
            ['004', 0.40, 9000],
            ['005', 0.20, 8200],
            ['006', 0.00, 2000],
            ['007', None, 2000]
        ], columns=['CLAVEUC'] + co)

        ex = pd.DataFrame(data=[
            ['001', 100.0,    0.0],
            ['002',  75.0,   77.5],
            ['003',  62.5,   50.0],
            ['004',  50.0,  100.0],
            ['005',  25.0,   90.0],
            ['006',  00.0,   12.5],
            ['007',  np.nan, 12.5]
        ], columns=['CLAVEUC'] + co)

        res = escalar_features(df, co, (0, 100))
        pd.testing.assert_frame_equal(res, ex)

    def test_normaliza_columnas(self):
        co = ['pc_procs_con_un_licitante', 'procs_con_contrato']
        df = pd.DataFrame(data=[
            ['001', 0.80, 1000],
            ['002', 0.60, 7200],
            ['003', 0.50, 5000],
            ['004', 0.40, 9000],
            ['005', 0.20, 8200],
            ['006', 0.00, 2000]
        ], columns=['CLAVEUC'] + co)

        ex = pd.DataFrame(data=[
            ['001', 100.0,   0.0],
            ['002',  75.0,  77.5],
            ['003',  62.5,  50.0],
            ['004',  50.0, 100.0],
            ['005',  25.0,  90.0],
            ['006',  00.0,  12.5]
        ], columns=['CLAVEUC'] + co)

        res = normaliza_columnas(df, co)
        pd.testing.assert_frame_equal(res, ex)

    def test_invierte_relacion_de_columnas(self):
        co = ['pc_procs_con_un_licitante', 'procs_con_contrato']
        df = pd.DataFrame(data=[
            ['001', 100.0,   0.0],
            ['002',  75.0,  77.5],
            ['003',  62.5,  50.0],
            ['004',  50.0, 100.0],
            ['005',  25.0,  90.0],
            ['006',  00.0,  12.5]
        ], columns=['CLAVEUC'] + co)

        ex = pd.DataFrame(data=[
            ['001',  00.0,   0.0],
            ['002',  25.0,  77.5],
            ['003',  37.5,  50.0],
            ['004',  50.0, 100.0],
            ['005',  75.0,  90.0],
            ['006', 100.0,  12.5]
        ], columns=['CLAVEUC'] + co)

        res = invierte_relacion_de_columnas(df, ['pc_procs_con_un_licitante'])
        pd.testing.assert_frame_equal(res, ex)

