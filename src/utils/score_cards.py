
import json
import pandas as pd
import pdfkit
import numpy as np
from typing import Tuple, List, Any, Dict, Iterator, Iterable
from pathlib import Path
from collections import defaultdict
from jinja2 import Environment, select_autoescape, FileSystemLoader
from sklearn.preprocessing import MinMaxScaler


DataFrame = pd.DataFrame


def chunks(l: List[Any], n: int):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def escalar_features(df: DataFrame,
                     cols,
                     rango: Tuple[int, int]) -> DataFrame:
    """Se escalan los features de 0 a 100"""
    for col in cols:
        x = df[col].values
        data_min = np.nanmin(x)
        data_max = np.nanmax(x)
        data_range = data_max - data_min
        scaled_value = (x - data_min) / data_range
        scaled_value = scaled_value * 100
        df.loc[:, col] = pd.Series(data=scaled_value.flatten(),
                                   index=df.index)
    return df


def normaliza_columnas(df: DataFrame,
                       cols,
                       rango=(0, 100)) -> DataFrame:
    """
    Utiliza sklearn.preprocessing.MinMaxScaler para
    normalizar una serie de columnas de un DataFrame.
    Por default el rango es de 0 a 100.
    Regresa una copia del dataframe con las columnas actualizadas.
    """
    scaler = MinMaxScaler(rango)
    scaled = df.copy()

    for c in cols:
        # Necesitamos hacer los valores un vector para fit
        X = scaled[c].values.reshape(-1, 1)
        scaled[c] = pd.Series(scaler.fit_transform(X).flatten(),
                              index=scaled.index)
    return scaled


def invierte_relacion_de_columnas(df: DataFrame,
                                  cols,
                                  max=100) -> DataFrame:
    """
    Despues de normalizar algunos indicadores deben invertirse
    con respecto al rango normalizado.

    Esto para poder representar relaciones negativas, p. ej.
    Un alto % de procedimientos con un solo licitante debe pasar
    de un valor cerca de 100 a uno cerca de 0, ya que es una
    característica a penalizar.

    IMPORTANTE que este método se utilice después de normaliza_columnas.

    Regresa copia de todo el dataframe con las columnas actualizadas.
    """
    updated = df.copy()
    for c in cols:
        updated[c] = max - updated[c]

    return updated


def calcular_scores_dependencia(scores: Dict[str, DataFrame],
                                weight_by: str) -> Dict[str, DataFrame]:
    if weight_by not in {'monto_total', 'conteo_procedimientos'}:
        raise ValueError('weight_by solo puede tomar valores '
                         'monto_total y conteo_procedimientos')
    tipos_contratacion = (
        'SERVICIOS',
        'ARRENDAMIENTOS',
        'ADQUISICIONES',
        'OBRA PUBLICA',
        'SERVICIOS RELACIONADOS CON LA OP'
    )
    cols_interes = [
        'CLAVEUC', 'dependencia', 'competencia',
        'transparencia', 'anomalias', 'monto_total',
        'conteo_procedimientos'
    ]
    scores_out = {}
    for tipo in tipos_contratacion:
        df_aux: DataFrame = scores[tipo].copy()
        df_aux = df_aux.reset_index()
        df_aux = df_aux.loc[:, cols_interes]
        # TODO: esta parte hacerla por monto o num procs
        weight = df_aux[weight_by]
        df_aux = df_aux.assign(
            competencia=df_aux.competencia * weight,
            transparencia=df_aux.transparencia * weight,
            anomalias=df_aux.anomalias * weight,
        )
        df_dep = df_aux.groupby('dependencia', as_index=False).sum()
        weight_dependencia = df_dep[weight_by]
        df_dep = df_dep.assign(
            competencia=df_dep.competencia.divide(weight_dependencia),
            transparencia=df_dep.transparencia.divide(weight_dependencia),
            anomalias=df_dep.anomalias.divide(weight_dependencia),
        )
        scores_out[tipo] = df_dep.set_index('dependencia')
    return scores_out


def calcular_riesgo(scores: Dict[str, DataFrame],
                    weight_by: str) -> DataFrame:
    """Se calcula el riesgo ponderado por monto"""
    if weight_by not in {'monto_total', 'conteo_procedimientos'}:
        raise ValueError('weight_by solo puede tomar valores '
                         'monto_total y conteo_procedimientos')

    tipos_contratacion = ('SERVICIOS',
                          'ARRENDAMIENTOS',
                          'ADQUISICIONES',
                          'OBRA PUBLICA',
                          'SERVICIOS RELACIONADOS CON LA OP')
    # se sacan los montos/num_procs por tipo de contratacion
    df_weights = []
    for tipo in tipos_contratacion:
        df_test: DataFrame = scores[tipo].copy()
        df_test = df_test[[weight_by]]
        df_test = df_test.rename(
            columns={weight_by: f'{weight_by}_{tipo}'})
        df_weights.append(df_test)
    df_weights = pd.concat(df_weights, axis=1)
    # Se suman todos los tipos de montos/num_procs
    df_weights = df_weights.sum(axis=1)
    # se saca el weith total de los tipos
    total_column = f'{weight_by}_total'
    df_weights.name = total_column
    # df_weights.name = weight_by.upper()
    df_weights = df_weights.to_frame()
    #
    ponderados = {}
    cols_interes = [
        'competencia', 'transparencia', 'anomalias', weight_by
    ]
    conceptos = ['competencia', 'transparencia', 'anomalias']
    for tipo in tipos_contratacion:
        df_test: DataFrame = scores[tipo].copy()
        df_test = df_test.loc[:, cols_interes]
        # Se divide cada tipo de contratacion por el total
        df_test = df_test.join(df_weights, how='inner')
        pc_weight = df_test[weight_by].divide(df_test[total_column])
        df_test = df_test.drop([weight_by, total_column], axis=1)
        # cada concepto se multiplica por porcentaje de cada tipo
        for concepto in conceptos:
            df_test.loc[:, concepto] = df_test.loc[:, concepto] * pc_weight
        ponderados[tipo] = df_test

    df_concepto_ponderado = []
    for concepto in conceptos:
        df_valor = pd.concat(
            [ponderados[tipo][concepto] for tipo in tipos_contratacion],
            axis=1).sum(axis=1)
        df_valor.name = concepto
        df_valor = df_valor.to_frame()
        df_concepto_ponderado.append(df_valor)
    #
    df_concepto_ponderado = pd.concat(df_concepto_ponderado, axis=1)
    riesgo = df_concepto_ponderado.mean(axis=1)
    riesgo.name = f'Riesgo_{weight_by}'
    riesgo = riesgo.to_frame()
    return riesgo


def extraer_informacion(identidicador,
                        df: DataFrame,
                        palette: List[str]):
    try:
        serie = df.loc[identidicador]
        valores = [
            f'{serie.competencia:.0f}',
            f'{serie.transparencia:.0f}',
            f'{serie.anomalias:.0f}',
            # '50',
            f'${serie.monto_total:,.02f}',
            f'{serie.conteo_procedimientos:}',
        ]
        colores = [
            palette[int(serie.competencia)],
            palette[int(serie.transparencia)],
            palette[int(serie.anomalias)],
            # '#FFFFFF',
            '#FFFFFF',
            '#FFFFFF'
        ]
    except KeyError:
        valores = [''] * 5
        colores = ['#BDBDBD'] * 5
    return valores, colores


def create_score_card_dep_dict(scores: Dict[str, DataFrame],
                               elementos: Iterable[str],
                               tipos: Iterator[str],
                               palette: List[str]):
    templates = {}
    for identificador in elementos:
        template = {
            'dependencia': identificador,
            'riesgo': 'XX.',
            'datos': {
                'columnas': [
                    'Falta de competencia',
                    'Falta de transparencia',
                    'Anomalías',
                    # 'Percentil',
                    'Monto',
                    'Total de procedimientos',
                ],
                'valores': list(),
                'colores': list(),
            }

        }
        valores = []
        colores = []
        riesgo = None
        riesgo_color = None
        for tipo in tipos:
            df_aux: DataFrame = scores[tipo].copy()
            riesgo_column = [c for c in df_aux.columns if 'Riesgo' in c][0]
            # TODO: en algun punto cambiar esta parte porque esta fea
            if riesgo is None:
                try:
                    df_riesgo = df_aux.loc[identificador]
                    riesgo = str(int(df_riesgo[riesgo_column]))
                    riesgo_color = palette[int(df_riesgo[riesgo_column])]
                except KeyError:
                    pass
            vals, cols = extraer_informacion(identificador, df_aux, palette)
            valores.append(vals)
            colores.append(cols)
        template['datos']['valores'] = valores
        template['datos']['colores'] = colores
        template['riesgo'] = {'valor': riesgo, 'color': riesgo_color}
        templates[identificador] = template
    return templates


def create_score_card_uc_dict(scores: Dict[str, DataFrame],
                              elementos: Iterable[str],
                              uc_to_name: Dict[str, str],
                              uc_to_dep: Dict[str, str],
                              tipos: Iterator[str],
                              palette: List[str]):
    templates = {}
    for identificador in elementos:
        template = {
            'uc': uc_to_name[identificador],
            'dependencia': uc_to_dep[identificador],
            'riesgo': 'XX.',
            'datos': {
                'columnas': [
                    'Falta de competencia',
                    'Falta de transparencia',
                    'Anomalías',
                    # 'Percentil',
                    'Monto',
                    'Total de procedimientos',
                ],
                'valores': list(),
                'colores': list(),
            }

        }
        valores = []
        colores = []
        riesgo = None
        riesgo_color = None
        for tipo in tipos:
            df_aux: DataFrame = scores[tipo].copy()
            riesgo_column = [c for c in df_aux.columns if 'Riesgo' in c][0]
            # TODO: en algun punto cambiar esta parte porque esta fea
            if riesgo is None:
                try:
                    df_riesgo = df_aux.loc[identificador]
                    riesgo = str(int(df_riesgo[riesgo_column]))
                    # riesgo = f'{int(df_riesgo.Riesgo)}',
                    riesgo_color = palette[int(df_riesgo[riesgo_column])]
                except KeyError:
                    pass
            vals, cols = extraer_informacion(identificador, df_aux, palette)
            valores.append(vals)
            colores.append(cols)
        template['datos']['valores'] = valores
        template['datos']['colores'] = colores
        template['riesgo'] = {'valor': riesgo, 'color': riesgo_color}
        templates[identificador] = template
    return templates


def create_score_card_html(input_dir: str,
                           path_templates: str,
                           row_names: Iterator[str],
                           output_dir: str) -> None:
    """Lee los arhivos json con scores y los convierte en html"""
    file_loader = FileSystemLoader(path_templates)
    jinja_env = Environment(
        loader=file_loader,
        autoescape=select_autoescape(['html', 'xml'])
    )
    # titulos_rows = [
    #     'Servicios', 'Arrendamiento', 'Adquisiciones',
    #     'Obra Pública', 'Servicios relacionado con la OP'
    # ]
    json_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    for file_path in json_path.glob('*.json'):
        template_jinja = jinja_env.get_template('table.html')
        with open(file_path, 'r') as file:
            json_test = json.load(file)
        datos = zip(json_test['datos']['valores'],
                    json_test['datos']['colores'],
                    row_names)
        valores_rows = []
        for valores, colores, titulo in datos:
            row = [titulo]
            for valor, color in zip(valores, colores):
                row.append((valor, color))
            valores_rows.append(row)
        with open(output_path / f'{file_path.stem}.html', 'w+') as file_html:
            span = len(json_test['datos']['columnas'])
            uc = json_test.get('uc', None)
            table_data = {
                "span": span,
                "dependencia": json_test['dependencia'],
                "riesgo": json_test['riesgo'],
                'datos': {
                    'columnas': json_test['datos']['columnas'],
                    'valores': valores_rows
                }
            }
            # when uc is None is because is a dependencia
            if uc:
                table_data['uc'] = uc
            file_html.write(template_jinja.render(table_data))


def _groupby_dep(collection,
                 mapper: Dict[str, str]) -> Dict[str, str]:
    """ Group elements in collection using the mapper.
    http://matthewrocklin.com/blog/work/2013/05/21/GroupBy"""
    d = dict()
    for item in collection:
        name = item.stem
        key = mapper[name]
        if key not in d:
            d[key] = []
        d[key].append(item.as_posix())
    return d


def convert_html_to_pdf(input_dir: str,
                        output_dir: str,
                        mapper=None) -> None:
    """ Se pasan los paths de los html para convertilos a pdf"""
    html_path = Path(input_dir).resolve()
    pdf_path = Path(output_dir).resolve()
    files_html = html_path.glob('*.html')
    if mapper is None:
        grupos = defaultdict(list)
        for i, file in enumerate(files_html):
            grupos[f'salida_{i % 5}'].append(file.as_posix())
        grupos = dict(grupos)
    else:
        grupos = _groupby_dep(files_html, mapper)
    for dep, unidades in grupos.items():
        file_name = dep.replace('/', '-')
        pdfkit.from_file(unidades, pdf_path / f'{file_name}.pdf')


if __name__ == '__main__':
    # pruebas para el template
    path_of_templates = '../resources/templates/'
    path_entrada = '../data/score_cards/input_unidades/'
    path_salida = '../data/score_cards/output_unidades/'
    path_to_pdf = '../data/score_cards/pdf_unidades/'
    create_score_card_html(path_entrada, path_of_templates, path_salida)
    convert_html_to_pdf(path_salida, path_to_pdf)



