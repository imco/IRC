import pandas as pd
import numpy as np

from features.productos import (
    colusion,
    contratos_fraccionados,
    convenios_entre_entes_publicos,
    falta_transparencia_pnt,
    favoritismo,
    ganador_mas_barato,
    plazos_cortos,
    tajada_por_empresa
)

# Columnas comunes para cruces entre bases
common = ['NUMERO_PROCEDIMIENTO', 'TIPO_PROCEDIMIENTO', 'TIPO_CONTRATACION', 'PROVEEDOR_CONTRATISTA']

# Mock de tabla de procedimientos
df_test_procs = pd.DataFrame(data=[
    ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '2019/01/01', '001', 1000],
    ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2019/02/01', '001', 2000],
    ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2019/03/01', '001', 2000],
    ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2019/04/01', '001', 9000],
    ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', '2019/05/01', '001', 5000],
    ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2019/06/01', '002', 3000],
    # No reportadas en PNT
    ['002-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa F', '2019/07/01', '002', 3000],
    ['002-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa G', '2019/07/01', '002', 4000],
    # Otras Licitaciones Públicas
    ['001-LP-0006/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2019/08/01', '002', 450000],
    ['001-LP-0007/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2019/08/01', '002', 350000]
], columns=common + ['FECHA_INICIO', 'CLAVEUC', 'IMPORTE_PESOS'])

df_test_procs['FECHA_INICIO'] = pd.to_datetime(df_test_procs['FECHA_INICIO'])

# Mock de tabla de participantes
df_test_parts = pd.DataFrame(data=[
    # Adjudicación con 3 participantes
    ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '2018/02/01', '001', 1200, 'GANADOR', 320000],
    ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa C', '2018/02/01', '001', 1000, 'PERDEDOR', 320000],
    ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa D', '2018/02/01', '001', 1000, 'PERDEDOR', 320000],
    # Adjudicación con un solo participante
    ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/03/01', '001', 2000, 'GANADOR', 320001],
    # Adjudicación con 2 participantes
    ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/04/01', '001', 2000, 'GANADOR', 320002],
    ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa C', '2018/04/01', '001', 2000, 'GANADOR', 320002],
    # Licitación pública con un solo participante
    ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2018/05/01', '001', 9000, 'GANADOR', 320003],
    # Licitación pública con tres participantes
    ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', '2018/06/01', '001', 5000, 'GANADOR', 320004],
    ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2018/06/01', '001', 5000, 'PERDEDOR', 320004],
    ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa B', '2018/06/01', '001', 5000, 'PERDEDOR', 320004],
    # Adjudicación directa con un solo participante
    ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/07/01', '002', 3000, 'GANADOR', 320005],
    # Otras Licitaciones Públicas
    ['001-LP-0006/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2018/05/01', '002', 9500, 'GANADOR', 320006],
    ['001-LP-0006/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa B', '2018/05/01', '002', 9000, 'PERDEDOR', 320006],
    ['001-LP-0007/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2018/05/09', '002', 8000, 'GANADOR', 320007],
    ['001-LP-0007/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa B', '2018/05/09', '002', 8010, 'PERDEDOR', 320007],
    ['001-LP-0007/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', '2018/05/09', '002', 8020, 'PERDEDOR', 320007]
], columns=common + ['FECHA_INICIO', 'CLAVEUC', 'PRECIO_TOTAL', 'ESTATUS_DE_PROPUESTA', 'REF_PARTICIPANTES'])

df_test_parts.FECHA_INICIO = pd.to_datetime(df_test_parts.FECHA_INICIO)


class TestProductos:
    def test_favoritismo(self):
        sth = 1 / 6 * 100
        trd = 1 / 3 * 100
        fir = 1420 * .40 + sth * .20 + 100 * .40
        flp = 800000 * .40 + trd * .20 + 100 * .40
        fav007 = fir * .35
        variables = pd.DataFrame(data=[
            # Ganadores para UC 001: A, B, B, C, D
            [1, 0, 0, 20.0,   0.0,   0.0, 1000.0,    0.0,     0.0,     0.0,    0.0, np.nan, np.nan,  666.6,    0.0,    0.0,    333.3],
            [2, 0, 0, 40.0,   0.0,   0.0, 4000.0,    0.0,     0.0,     0.0,    1.0, np.nan, np.nan, 2653.2,    0.0,    0.0,   1326.6],
            [2, 0, 0, 40.0,   0.0,   0.0, 4000.0,    0.0,     0.0,     0.0,    1.0, np.nan, np.nan, 2653.2,    0.0,    0.0,   1326.6],
            [0, 0, 1,  0.0,   0.0,  20.0,    0.0,    0.0,  9000.0,     0.0,    2.0, np.nan,   50.0,    0.0,    0.0, 3624.0,    543.6],
            [0, 0, 1,  0.0,   0.0,  20.0,    0.0,    0.0,  5000.0,     0.0,    1.0, np.nan,  100.0,    0.0,    0.0, 2044.0,    306.6],
            # Ganadores para UC 002: B, F, G, C, C, D
            [1, 0, 0,  sth,   0.0,   0.0, 3000.0,    0.0,      0.0,    0.0,    2.0, np.nan, np.nan, 1985.5,    0.0,    0.0,   992.75],
            [1, 0, 0,  sth,   0.0,   0.0, 3000.0,    0.0,      0.0, np.nan, np.nan, np.nan, np.nan, 1985.5,    0.0,    0.0,   992.75],
            [1, 0, 0,  sth,   0.0,   0.0, 4000.0,    0.0,      0.0, np.nan, np.nan, np.nan, np.nan, 2645.5,    0.0,    0.0,  1322.75],
            [0, 0, 2,  0.0,   0.0,   trd,    0.0,    0.0, 800000.0,    0.0,    2.0, np.nan,  100.0,    0.0,    0.0,    flp, 48007.00],
            [0, 0, 2,  0.0,   0.0,   trd,    0.0,    0.0, 800000.0,    0.0,    2.0, np.nan,  100.0,    0.0,    0.0,    flp, 48007.00],
            [0, 1, 0,  0.0,   sth,  00.0,    0.0, 1420.0,      0.0,    1.0,    1.0,  100.0,    0.0,    0.0,    fir,    0.0,   fav007]
        ], columns=[
            'num_ganados_ad', 'num_ganados_ir', 'num_ganados_lp',
            'frec_ganados_ad', 'frec_ganados_ir', 'frec_ganados_lp',
            'monto_ganado_ad', 'monto_ganado_ir', 'monto_ganado_lp',
            'num_propuestas_ir', 'num_propuestas_lp',
            'pc_exito_ir', 'pc_exito_lp',
            'favorita_ad', 'favorita_ir', 'favorita_lp', 'favoritismo'
        ])

        procs = df_test_procs.append(pd.DataFrame(data=[
            ['002-IR-0008/2018', 'INVITACION A CUANDO MENOS TRES', 'SERVICIOS', 'Empresa D', '2018/05/15', '002', 1420]
        ], columns=common + ['FECHA_INICIO', 'CLAVEUC', 'IMPORTE_PESOS']), ignore_index=True)

        parts = df_test_parts.append(pd.DataFrame(data=[
            ['002-IR-0008/2018', 'INVITACION A CUANDO MENOS TRES', 'SERVICIOS', 'Empresa D', '2018/05/15', '002', 1420, 'GANADOR', 320008]
        ], columns=common + ['FECHA_INICIO', 'CLAVEUC', 'PRECIO_TOTAL', 'ESTATUS_DE_PROPUESTA', 'REF_PARTICIPANTES']), ignore_index=True)

        df_expected = pd.concat([procs, variables], axis=1)

        procs_before = procs.copy()
        parts_before = parts.copy()

        res = favoritismo(procs, parts)
        pd.testing.assert_frame_equal(res, df_expected)

        # Inmutabilidad
        pd.testing.assert_frame_equal(procs_before, procs)
        pd.testing.assert_frame_equal(parts_before, parts)

    def test_tajada_por_empresa(self):
        variables = pd.DataFrame(data=[
            [  1000,    1000/19000],
            [  4000,    4000/19000],
            [  4000,    4000/19000],
            [  9000,    9000/19000],
            [  5000,    5000/19000],
            [  3000,   3000/810000],
            [  3000,   3000/810000],
            [  4000,   4000/810000],
            [800000, 800000/810000],
            [800000, 800000/810000]
        ], columns=['monto_por_empresa', 'share_por_empresa'])

        df_expected = pd.concat([df_test_procs, variables], axis=1)
        res = tajada_por_empresa(df_test_procs)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_contratos_fraccionados(self):
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

        variables = pd.DataFrame(data=[
            [1, 1000, 1000, 1000, 1, 1, False],
            # Evil corp se excede con la UC 001 en la primera semana
            [1, 1000, 500, 1100, 2, 1, True],
            [1, 1000, 600, 1100, 2, 1, True],
            # Ignoramos las Licitaciones
            [None, None, None, None, None, None, None],
            # La empresa A en Servicios no se excede
            [5, 1000, 1000, 1000, 1, 1, False],
            # tampoco en Adquisiciones porque lo contratan otras UC
            [5, 2000, 2000, 2000, 1, 1, False],

            [5, 2000, 900, 900, 3, 3, False],
            [5, 2000, 900, 900, 3, 3, False],
            [5, 2000, 900, 900, 3, 3, False],
            # La empresa Evil Corp excedió en Adquisiciones semanales con la UC 002
            [27, 2000, 600, 2400, 3, 1, True],
            [27, 2000, 1600, 2400, 3, 1, True],
            [27, 2000, 200, 2400, 3, 1, True]
        ], columns=[
            'semana', 'maximo_permitido', 'monto_diario_empresa', 'monto_semanal_empresa',
            'contratos_semanales_empresa', 'contratos_diarios_empresa', 'fraccionado'
        ])

        df_expected = pd.concat([df_test_procs, variables], axis=1)
        res = contratos_fraccionados(df_test_procs, df_maximos, year=2018)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_convenios_entre_entes_publicos(self):
        df_test_sipot = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', 'LEY DE ADQUI Y ARRENDAMIENTOS', 1000, '2019/01/01'],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 'LEY DE PETROLEOS',              2000, '2019/02/01'],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 'LAASSP',                        2000, '2019/03/01'],
            ['001-LP-0004/2018', 'LICITACION PUBLICA',   'SERVICIOS', 'Empresa C', '',                              9000, '2019/04/01'],
            ['001-LP-0005/2018', 'LICITACION PUBLICA',   'SERVICIOS', 'Empresa D', '',                              9000, '2019/05/01'],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 'Artículo 43 de LOPSRM',         3000, '2019/06/01'],
        ], columns=common + ['MOTIVOS_ADJUDICACION', 'PRECIO_TOTAL', 'FECHA_INICIO'])

        df_test_sipot.FECHA_INICIO = pd.to_datetime(df_test_sipot.FECHA_INICIO)

        variables = pd.DataFrame(data=[
            [1, 0],
            [0, 0],
            [1, 0],
            [None, None],
            [None, None],
            [0, 1]
        ], columns=['LAASSP', 'LOPSRM'])

        df_expected = pd.concat([df_test_procs, variables], axis=1)
        res = convenios_entre_entes_publicos(df_test_procs, df_test_sipot)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_falta_transparencia_pnt(self):
        sipot_cols = (['LIGA_AUTORIZACION', 'REF_COTIZACIONES', 'LIGA_CONTRATO'] +
                      ['LIGA_CONVOCATORIA', 'LIGA_FALLO', 'LIGA_FINIQUITO'])

        df_test_sipot = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', 1, 1, 1, None, None, None, 1000, 201000100, '2019/01/01'],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 1, 1, 1, None, None, None, 2000, 201000101, '2019/02/01'],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', None, None, None, None, None, None, 3000, 201000102, '2019/03/01'],
            ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', None, None, 1, 1, 1, 1, 9000, 201000103, '2019/04/01'],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', None, None, None, None, 1, 1, 9000, 201000104, '2019/05/01'],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', None, None, 1, None, None, None, 3000, 201000105, '2019/06/01'],
        ], columns=common + sipot_cols + ['PRECIO_TOTAL', 'SIPOT_ID', 'FECHA_INICIO'])

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
            # Estas últimas no estan en SIPOT
            [0, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 1],
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

        df_expected = pd.concat([df_test_procs, df_fallas], axis=1)

        res = falta_transparencia_pnt(df_test_procs, df_test_sipot)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_colusion(self):
        df_test_fantasma = pd.DataFrame(data={
            'RFC': ['D000'],
            'PROVEEDOR_CONTRATISTA': ['Empresa D'],
            'Publicación página SAT definitivos': ['25/05/2018']
        })

        _jaccard = lambda a, b, c: c / (a + b - c) * 100
        _colusion = lambda j, N: (sum(j) / (N - 1)) * 100

        # Sólo hubo 3 LP con más de un licitante
        df_variables = pd.DataFrame(data=[
            [],
            [],
            [],
            [],
            # La empresa ganadora D aparece 2 veces en la base
            # Ganándole a B y C
            [50, 2, _colusion([_jaccard(2, 3, 1) + _jaccard(2, 3, 1)], 3),  2, 2, 1],
            # Otra Adjudicación ignorada
            [],
            # Dos procesos que no estan en la PNT
            [],
            [],
            # La empresa ganadora C aparece 3 veces en la base
            # y le ha ganado a B dos veces y perdido contra D una
            [50, 1, _colusion([_jaccard(3, 3, 2)], 2),                      3, 2, None],
            [75, 2, _colusion([_jaccard(3, 3, 2) + _jaccard(3, 2, 1)], 3),  3, 3, 1]
        ], columns=[
            'suma_jaccard',
            'perdedores_por_proceso',
            'colusion',
            'participaciones_totales_empresa',
            'num_participaciones_en_conjunto',
            'propuestas_artificiales'
        ])

        df_expected = pd.concat([df_test_procs, df_variables], axis=1)
        res = colusion(df_test_procs, df_test_parts, df_test_fantasma)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_ganador_mas_barato(self):
        df_test_procs = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', 1200, '2018/02/01', '001'],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 2000, '2018/03/01', '001'],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 2000, '2018/04/01', '001'],
            ['001-LP-0004/2018', 'LICITACION PUBLICA',   'SERVICIOS', 'Empresa C', 9000, '2018/05/01', '001'],
            ['001-LP-0005/2018', 'LICITACION PUBLICA',   'SERVICIOS', 'Empresa D', 5000, '2018/06/01', '001'],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', 3000, '2018/07/01', '002'],
            # No reportadas en PNT
            ['002-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa F', 3000, '2018/05/01', '002'],
            ['002-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa G', 4000, '2018/05/01', '002'],
            # Otras Licitaciones Públicas
            ['001-LP-0006/2018', 'LICITACION PUBLICA',   'SERVICIOS', 'Empresa C', 9500, '2018/05/01', '002'],
            ['001-LP-0007/2018', 'LICITACION PUBLICA',   'SERVICIOS', 'Empresa C', 8000, '2018/05/09', '002']
        ], columns=common + ['IMPORTE_PESOS', 'FECHA_INICIO' , 'CLAVEUC'])

        df_variables = pd.DataFrame(data=[
            [1000, 0],
            [2000, 1],
            [2000, 1],
            [9000, 1],
            [5000, 1],
            [3000, 1],
            [],
            [],
            [9000, 0],
            [8000, 1]
        ], columns=[
            'PRECIO_MAS_BAJO', 'mas_barato'
        ])

        df_test_procs['FECHA_INICIO'] = pd.to_datetime(df_test_procs['FECHA_INICIO'])

        df_expected = pd.concat([df_test_procs, df_variables], axis=1)
        res = ganador_mas_barato(df_test_procs, df_test_parts)
        pd.testing.assert_frame_equal(res, df_expected)

    def test_plazos_cortos(self):
        df_test_procs = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '2018/02/01', '2018/01/01', '2018/01/04', 1200, '001'],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/03/01', '2018/02/01', '2018/02/28', 2000, '001'],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/04/01', '2018/03/01', '2018/03/04', 2000, '001'],
            ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C',   '2018/05/01', '2018/04/01', '2018/04/09', 9000, '001'],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D',   '2018/06/01', '2018/04/01', '2018/05/30', 5000, '001'],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/07/01', '2018/06/01', '2018/06/09', 3000, '002'],
            # No reportadas en PNT
            ['002-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa F', '2018/08/01', '2018/07/01', '2018/07/04', 3000, '002'],
            ['002-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa G', '2018/08/01', '2018/06/01', '2018/07/30', 3000, '002']
        ], columns=common + ['FECHA_INICIO', 'PROC_F_PUBLICACION', 'FECHA_APERTURA_PROPOSICIONES', 'IMPORTE_PESOS', 'CLAVEUC'])

        # Transforma columnas de fechas
        for c in ['FECHA_INICIO', 'PROC_F_PUBLICACION', 'FECHA_APERTURA_PROPOSICIONES']:
            df_test_procs[c] = pd.to_datetime(df_test_procs[c])

        # Calcula variables
        res = plazos_cortos(df_test_procs, df_test_parts)

        df_expected = df_test_procs.copy()
        df_variables = pd.DataFrame(data=[
            # Esta adjudicación tuvo plazos muy cortos
            [ 3, 3, 3, 3, 3],
            # Esta adjudicación cumple el plazo nacional e internacional
            [27, 1, 0, 0, 1],
            [ 3, 2, 2, 2, 2],
            [ 8, 1, 1, 1, 1],
            # Una licitación con suficiente tiempo para participar
            [59, 3, 0, 0, 0],
            [ 8, 1, 1, 1, 1],
            # A pesar de que 002-AD-0002/2018 no esta en participantes, sabemos que hubo un ganador
            [ 3, 1, 1, 1, 1],
            # Igual, una no reportada en PNT pero con buen plazo
            [59, 1, 0, 0, 0]
        ], columns=[
            'diff_anuncio_apertura',
            'num_propuestas',
            'plazos_cortos_nacionales',
            'plazos_cortos_internacionales',
            'plazos_cortos_internacionales_bajo_tratados'
        ])

        df_expected = pd.concat([df_expected, df_variables], axis=1)
        pd.testing.assert_frame_equal(res, df_expected)

