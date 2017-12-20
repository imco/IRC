import os
import json
import pandas as pd
import matplotlib.colors
import seaborn as sns
from itertools import chain
from sklearn.preprocessing import MinMaxScaler
from utils.score_cards import escalar_features
from utils.score_cards import calcular_scores_dependencia
from utils.score_cards import calcular_riesgo
from utils.score_cards import create_score_card_uc_dict
from utils.score_cards import create_score_card_dep_dict
from utils.score_cards import create_score_card_html
from utils.score_cards import convert_html_to_pdf


tipos_contratacion = (
    'ADQUISICIONES',
    'SERVICIOS',
    'OBRA PUBLICA',
    'ARRENDAMIENTOS',
    'SERVICIOS RELACIONADOS CON LA OP'
)

thresholds = {
    'ADQUISICIONES': 6,
    'SERVICIOS': 10,
    'OBRA PUBLICA': 4,
    'ARRENDAMIENTOS': 2,
    'SERVICIOS RELACIONADOS CON LA OP': 2
}


conceptos = ['competencia', 'transparencia', 'anomalias']


if __name__ == '__main__':
    # Variables de configuracion
    conceptos_path: str = './data/conceptos/'
    procedimientos_path = './data/bases/procedimientos.parquet'
    path_json_unidades = './data/score_cards/input_unidades/'
    path_json_dependencias = './data/score_cards/input_dependencias/'
    directorio_uc_path = './data/bases/nombres_unidades_compradoras.csv'
    # Variable de ponderacion
    # 'conteo_procedimientos', 'monto_total'
    COLUMN_WEIGHT: str = 'monto_total'
    # -------------------------------------------------------------
    # Se cargan los nombres de las UCs y Dependencias
    df_directorio = pd.read_csv(directorio_uc_path, dtype={'CLAVEUC': str})
    nombres_dep = {row.CLAVEUC: row.DEPENDENCIA
                   for row in df_directorio.itertuples()}
    nombres_uc = {row.CLAVEUC: row.NOMBRE_UC
                  for row in df_directorio.itertuples()}
    del df_directorio

    # -----------------------------------------------------------
    # Se cargan los dataframes y se obtiene los datos generales por tipo
    dfs_general = {}
    for tipo in tipos_contratacion:
        path_general = os.path.join(conceptos_path, 'general',
                                    tipo, 'features.csv')
        df_general = pd.read_csv(path_general, dtype={'CLAVEUC': str})
        # quitar las UCs que no tengan los valores minimos de contratos
        df_general = df_general.loc[df_general.numero_contratos > thresholds[tipo]]
        dfs_general[tipo] = df_general

    features = {}
    for concepto in conceptos:
        for tipo in tipos_contratacion:
            path_feat = os.path.join(conceptos_path, concepto,
                                     tipo, 'features.csv')
            df_features = pd.read_csv(path_feat, dtype={'CLAVEUC': str})
            # join para quitar UCs con pocas observaciones
            df_features = pd.merge(dfs_general[tipo].loc[:, ['CLAVEUC']],
                                   df_features,
                                   on='CLAVEUC', how='inner')
            df_features = df_features.set_index('CLAVEUC')
            df_features = escalar_features(df_features,
                                           df_features.columns,
                                           (0, 100))
            features[tipo, concepto] = df_features

    # ------------------------------------------------------------------
    # Se promedian los features de cada concepto,
    # se agrega el nombre y,
    # Se agrega los datos generales.
    scores_tipo = {}
    for tipo in tipos_contratacion:
        dfs = []
        for concepto in conceptos:
            df_aux = features[tipo, concepto].mean(axis=1)
            # Escalar de 0 a 100
            scaler = MinMaxScaler((0, 100))
            df_aux = pd.Series(
                scaler.fit_transform(df_aux.values.reshape(-1, 1)).flatten(),
                index=df_aux.index
            )
            df_aux.name = concepto
            dfs.append(df_aux)
        # Se concatenan conceptos
        df_conceptos = pd.concat(dfs, axis=1, join='inner')
        df_conceptos = df_conceptos.reset_index()
        df_conceptos = pd.merge(df_conceptos, dfs_general[tipo],
                                on='CLAVEUC', how='inner')
        dependencia = df_conceptos.CLAVEUC.map(nombres_dep)
        unidad_compradora = df_conceptos.CLAVEUC.map(nombres_uc)
        df_conceptos = (df_conceptos.assign(dependencia=dependencia,
                                            unidad_compradora=unidad_compradora)
                                    .set_index('CLAVEUC'))
        scores_tipo[tipo] = df_conceptos
    # ------------------------------------------------------------
    # Calcular el riesgo de cada UC
    riesgo_uc = calcular_riesgo(scores_tipo, weight_by=COLUMN_WEIGHT)
    scores_tipo_con_riesgo = {}
    for tipo in tipos_contratacion:
        df_aux = scores_tipo[tipo]
        # Asignar riesgo
        df_aux = df_aux.join(riesgo_uc, how='inner')
        # guardar
        scores_tipo_con_riesgo[tipo] = df_aux

    # -----------------------------------------------------------
    # scores de las dependencias
    scores_dep = calcular_scores_dependencia(scores_tipo,
                                             weight_by=COLUMN_WEIGHT)
    # riesgo de la dependencia
    riesgo_dep = calcular_riesgo(scores_dep, weight_by=COLUMN_WEIGHT)
    scores_dep_con_riesgo = {}
    for tipo in tipos_contratacion:
        df_aux = scores_dep[tipo]
        # Asignar riesgo
        df_aux = df_aux.join(riesgo_dep, how='inner')
        scores_dep_con_riesgo[tipo] = df_aux
    # TODO: hacer diagrama de como calcular el riesgo

    # ----------------------------------------------------------
    # Generar archivos json
    palette_colores = [matplotlib.colors.to_hex(c)
                       for c in sns.color_palette("Spectral", 101)]
    palette_colores.reverse()
    # Generar todas las UCs
    unidades_compradoras = set(
        chain.from_iterable(
            [list(df.index.unique()) for df in scores_tipo.values()]
        )
    )
    dependencias = set(
        chain.from_iterable(
            [list(df.index.unique()) for df in scores_dep_con_riesgo.values()]
        )
    )
    # TODO: buscar una mejor manera de hacerlo
    templates_uc = create_score_card_uc_dict(scores_tipo_con_riesgo,
                                             unidades_compradoras,
                                             nombres_uc,
                                             nombres_dep,
                                             tipos_contratacion,
                                             palette_colores)

    templates_dep = create_score_card_dep_dict(scores_dep_con_riesgo,
                                               dependencias,
                                               tipos_contratacion,
                                               palette_colores)

    # guardar templates de uc
    for k, template in templates_uc.items():
        # para evitar "/" en el path
        k = k.replace('/', '-')
        path = os.path.join(path_json_unidades, f'{k}.json')
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(template, file, ensure_ascii=False)
    # guardar templates de dependencias
    for k, template in templates_dep.items():
        # para evitar "/" en el path
        k = k.replace('/', '-')
        path = os.path.join(path_json_dependencias, f'{k}.json')
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(template, file, ensure_ascii=False)

    # TODO Agregar aqui la parte de guardar a html y a pdf
    path_of_templates = './resources/templates/'

    # Crear pdfs para unidades
    path_entrada = './data/score_cards/input_unidades/'
    path_salida = './data/score_cards/output_unidades/'
    path_to_pdf = './data/score_cards/pdf_unidades/'
    create_score_card_html(path_entrada, path_of_templates,
                           tipos_contratacion, path_salida)
    convert_html_to_pdf(path_salida, path_to_pdf, nombres_dep)

    # crear pdfs para dependencias
    path_entrada = './data/score_cards/input_dependencias/'
    path_salida = './data/score_cards/output_dependencias/'
    path_to_pdf = './data/score_cards/pdf_dependencias/'
    create_score_card_html(path_entrada, path_of_templates,
                           tipos_contratacion, path_salida)
    convert_html_to_pdf(path_salida, path_to_pdf)

    # # Save dependencias values
    # path_tablas_max = f'./data/tablas_max/{COLUMN_WEIGHT}/'
    # for k, df in scores_dep_con_riesgo.items():
    #     df.index.name = 'Dependencia'
    #     df.to_csv(f'{path_tablas_max}{k}.csv',
    #               encoding='utf-8', index=True, quoting=1)
