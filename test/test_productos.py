import pandas as pd

from features.productos import (
    falta_transparencia_pnt,
    plazos_cortos
)


class TestProductos:
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

    def test_plazos_cortos(self):
        common = [
            'NUMERO_PROCEDIMIENTO',
            'TIPO_PROCEDIMIENTO',
            'TIPO_CONTRATACION',
            'PROVEEDOR_CONTRATISTA',
            'FECHA_INICIO'
        ]

        df_test_procs = pd.DataFrame(data=[
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '2018/02/01', '2018/01/01', '2018/01/04', 1000],
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/03/01', '2018/02/01', '2018/02/28', 2000],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/04/01', '2018/03/01', '2018/03/04', 2000],
            ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C',   '2018/05/01', '2018/04/01', '2018/04/09', 9000],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D',   '2018/06/01', '2018/04/01', '2018/05/30', 5000],
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/07/01', '2018/06/01', '2018/06/09', 3000],
            # No reportadas en PNT
            ['002-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa F', '2018/08/01', '2018/07/01', '2018/07/04', 3000],
            ['002-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa G', '2018/08/01', '2018/06/01', '2018/07/30', 3000]
        ], columns=common + ['PROC_F_PUBLICACION', 'FECHA_APERTURA_PROPOSICIONES', 'IMPORTE_PESOS'])

        df_test_parts = pd.DataFrame(data=[
            # Adjudicación con 3 participantes
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa A', '2018/02/01', 1000, 'GANADOR', 320000],
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa C', '2018/02/01', 1000, 'PERDEDOR', 320000],
            ['001-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa D', '2018/02/01', 1000, 'PERDEDOR', 320000],
            # Adjudicación con un solo participante
            ['001-AD-0002/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/03/01', 2000, 'GANADOR', 320001],
            # Adjudicación con 2 participantes
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/04/01', 2000, 'GANADOR', 320002],
            ['001-AD-0003/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa C', '2018/04/01', 2000, 'GANADOR', 320002],
            # Licitación pública con un solo participante
            ['001-LP-0004/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2018/05/01', 9000, 'GANADOR', 320003],
            # Licitación pública con tres participantes
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa D', '2018/06/01', 5000, 'GANADOR', 320004],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa C', '2018/06/01', 5000, 'PERDEDOR', 320004],
            ['001-LP-0005/2018', 'LICITACION PUBLICA', 'SERVICIOS', 'Empresa B', '2018/06/01', 5000, 'PERDEDOR', 320004],
            # Adjudicación directa con un solo participante
            ['002-AD-0001/2018', 'ADJUDICACION DIRECTA', 'SERVICIOS', 'Empresa B', '2018/07/01', 3000, 'GANADOR', 320005]
        ], columns=common + ['PRECIO_TOTAL', 'ESTATUS_DE_PROPUESTA', 'REF_PARTICIPANTES'])

        # Transforma columnas de fechas
        for c in ['FECHA_INICIO', 'PROC_F_PUBLICACION', 'FECHA_APERTURA_PROPOSICIONES']:
            df_test_procs[c] = pd.to_datetime(df_test_procs[c])
        df_test_parts.FECHA_INICIO = pd.to_datetime(df_test_parts.FECHA_INICIO)

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

