
import re
import pandas as pd
from typing import Set, List

DataFrame = pd.DataFrame


REGEX_LIST = [
    # SA DE CV
    '[S]\s?[A]\s+[D]\s?[E]\s+[C]\s?[V]',
    # SAPI DE CV
    '[S]\s?[A]\s?[P]\s?[I]\s+[D]\s?[E]\s+[C]\s?[V]',
    # SAB DE CV
    '[S]\s?[A]\s?[B]\s+[D]\s?[E]\s+[C]\s?[V]',
    # S DE RL DE CV
    '[S]\s?[D]\s?[E]\s+[R]\s?[L]\s+[D]\s?[E]\s+[C]\s?[V]',
    # SC DE RL DE CV
    '[S]\s?[C]\s+[D]\s?[E]\s+[R]\s?[L]\s+[D]\s?[E]\s+[C]\s?[V]',
    # SCP DE RL DE CV
    '[S]\s?[C]\s?[P]\s+[D]\s?[E]\s+[R]\s?[L]\s+[D]\s?[E]\s+[C]\s?[V]',
    # SPR DE RL DE CV
    '[S]\s?[P]\s?[R]\s+[D]\s?[E]\s+[R]\s?[L]\s+[D]\s?[E]\s+[C]\s?[V]',
    # PR DE RL DE CV
    '[P]\s?[R]\s+[D]\s?[E]\s+[R]\s?[L]\s+[D]\s?[E]\s+[C]\s?[V]',
    # SC DE C DE RL DE CV
    '[S]\s?[C]\s+[D]\s?[E]\s+[C]\s+[D]\s?[E]\s+[R]\s?[L]\s+[D]\s?[E]\s+[C]\s?[V]',
]


def find_numbers(string):
    return re.findall('[-+]?\d+[\.]?\d*', string)


def remove_pattern(string, pattern):
    """Remover el patron de la cadena de texto"""
    if isinstance(string, str):
        return pattern.sub('', string)
    return string


def remove_double_white_space(name):
    """Remueve dobles espacios en blanco"""
    if isinstance(name, str):
        return " ".join(name.split())
    return name


def get_claveuc_proc(num_proc):
    """Se saca la clave de unidad compradora usando
    el numero de procedimiento.
    """
    if isinstance(num_proc, str):
        return num_proc.split('-')[1]
    return None


def get_claveuc_nombre(nombre_uc):
    """Se saca la clave de unidad compradora a partir
    del nombre de la uc, usualmente viene después del '#'
    """
    if isinstance(nombre_uc, str):
        nombre_uc = nombre_uc.split('#')
    else:
        return None
    if len(nombre_uc) > 1 and isinstance(nombre_uc, list):
        return nombre_uc[1]
    return None


def get_claveuc_real(df: DataFrame,
                     unidades_validas: Set[str]) -> DataFrame:
    """Obtiene la clave uc a partir del nombre, num de
    procedimiento y el directorio de UCs"""
    df: DataFrame = df.copy()
    cond1: pd.Series = (df.CLAVEUC == df.CLAVEUC_PROC)
    cond2: pd.Series = (df.CLAVEUC == df.CLAVEUC_NOM)
    cond3: pd.Series = (df.CLAVEUC_NOM == df.CLAVEUC_PROC)
    df_aux = df.assign(CLAVEUC_REAL='MISSING')
    # Set the value of clave if at least one condition is met
    df_aux.loc[cond1[cond1 == True].index, 'CLAVEUC_REAL'] = df_aux.loc[
        cond1[cond1 == True].index, 'CLAVEUC']
    df_aux.loc[cond2[cond2 == True].index, 'CLAVEUC_REAL'] = df_aux.loc[
        cond2[cond2 == True].index, 'CLAVEUC']
    df_aux.loc[cond3[cond3 == True].index, 'CLAVEUC_REAL'] = df_aux.loc[
        cond3[cond3 == True].index, 'CLAVEUC_PROC']

    df_test = df_aux.loc[df_aux.CLAVEUC_REAL == 'MISSING']
    cond_nom = df_test.CLAVEUC_NOM.map(lambda clave: clave in unidades_validas)
    cond_proc = df_test.CLAVEUC_PROC.map(lambda clave: clave in unidades_validas)
    cond_clave = df_test.CLAVEUC.map(lambda clave: clave in unidades_validas)

    df_aux.loc[
        cond_nom[cond_nom == True].index, 'CLAVEUC_REAL'
    ] = df_aux.loc[cond_nom[cond_nom == True].index].CLAVEUC_NOM

    df_aux.loc[
        cond_proc[cond_proc == True].index, 'CLAVEUC_REAL'
    ] = df_aux.loc[cond_proc[cond_proc == True].index].CLAVEUC_PROC

    df_aux.loc[
        cond_clave[cond_clave == True].index, 'CLAVEUC_REAL'
    ] = df_aux.loc[cond_clave[cond_clave == True].index].CLAVEUC
    return df_aux


def convert_to_mxn(converter, montos, monedas, fechas) -> List[float]:
    """Convertir la moneda a pesos"""
    monto_pesos = []
    for monto, moneda, fecha in zip(montos, monedas, fechas):
        if moneda in {'MXN', 'TEST', 'OTH'}:
            monto_pesos.append(monto)
        else:
            val = converter.convert(monto, moneda, 'MXN', date=fecha)
            monto_pesos.append(val)
    return monto_pesos


def procesar_archivo_procedimientos(file: str, year: int):
    df = pd.read_excel(file,
                       dtype={
                           'CLAVEUC': str, 'FOLIO_RUPC': str,
                           'CODIGO_CONTRATO': str,
                           'CODIGO_EXPEDIENTE': str,
                           'IMPORTE_CONTRATO': float,
                           'APORTACION_FEDERAL': float
                       })
    df = df.assign(
        PROC_F_PUBLICACION=pd.to_datetime(df.PROC_F_PUBLICACION,
                                          yearfirst=True),
        FECHA_APERTURA_PROPOSICIONES=pd.to_datetime(
            df.FECHA_APERTURA_PROPOSICIONES, yearfirst=True),
        EXP_F_FALLO=pd.to_datetime(df.EXP_F_FALLO, yearfirst=True),
        FECHA_CELEBRACION=pd.to_datetime(df.FECHA_CELEBRACION, yearfirst=True),
        FECHA_INICIO=pd.to_datetime(df.FECHA_INICIO, yearfirst=True),
        FECHA_FIN=pd.to_datetime(df.FECHA_FIN, yearfirst=True),
        FECHA_ARCHIVO=year
    )
    cols = [
        'SIGLAS', 'DEPENDENCIA', 'NOMBRE_DE_LA_UC', 'RESPONSABLE',
        'ESTRATIFICACION_MUC', 'PROVEEDOR_CONTRATISTA', 'ESTRATIFICACION_MPC',
        'ESTATUS_EMPRESA', 'GOBIERNO', 'TITULO_EXPEDIENTE', 'TITULO_CONTRATO',
        'TIPO_CONTRATACION', 'TIPO_PROCEDIMIENTO', 'ESTATUS_CONTRATO',
        'FORMA_PROCEDIMIENTO', 'CARACTER', 'PLANTILLA_EXPEDIENTE',
    ]
    # Remove non ascii chars
    for col in cols:
        df.loc[:, col] = (df[col].str.normalize('NFD')
                                 .str.encode('ascii', 'ignore')
                                 .str.decode('utf-8').str.upper()
                                 .str.replace('.', '')
                                 .str.replace(',', '')
                                 .str.strip())
    # Clean some extra details for PoC and double white spaces
    df.loc[:, 'PROVEEDOR_CONTRATISTA'] = (df.PROVEEDOR_CONTRATISTA
                                            .str.replace('"', '')
                                            .str.replace("'", '')
                                            .map(remove_double_white_space))
    # Remove common endigns
    for regex in REGEX_LIST:
        pattern = re.compile(regex)
        df = df.assign(
                PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(
                    lambda string: remove_pattern(string, pattern)
                )
        )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    df.loc[:, 'NUMERO_PROCEDIMIENTO'] = df.NUMERO_PROCEDIMIENTO.str.upper()
    return df


def clean_base_rfc(df_rfc: DataFrame) -> DataFrame:
    """Homologa los nombres de proveedores de la base de RFC"""
    df_rfc = df_rfc.rename(
        columns={'NOMBRE DEL CONTRIBUYENTE': 'PROVEEDOR_CONTRATISTA'})
    proveedor = (df_rfc.PROVEEDOR_CONTRATISTA
                       .str.normalize('NFD')
                       .str.encode('ascii', 'ignore')
                       .str.decode('utf-8')
                       .str.upper()
                       .str.replace('.', '')
                       .str.replace(',', '')
                       .str.strip()
                       .replace('"', '')
                       .str.replace("'", '')
                       .map(remove_double_white_space))
    df_rfc = df_rfc.assign(PROVEEDOR_CONTRATISTA=proveedor)
    for regex in REGEX_LIST:
        pattern = re.compile(regex)
        df_rfc = df_rfc.assign(
            PROVEEDOR_CONTRATISTA=df_rfc.PROVEEDOR_CONTRATISTA.map(
                lambda string: remove_pattern(string, pattern)
            )
        )
    df_rfc = df_rfc.assign(
        PROVEEDOR_CONTRATISTA=df_rfc.PROVEEDOR_CONTRATISTA.str.strip()
    )
    return df_rfc


def clean_base_sancionados(df: DataFrame) -> DataFrame:
    """Homologa los nombres de proveedores de la base de sancionados"""
    df = df.rename(
        columns={'Proveedor y Contratista ': 'PROVEEDOR_CONTRATISTA'})
    df = df.assign(Multa=df.Multa.str.replace(',', '').astype(float))
    proveedor = (df.PROVEEDOR_CONTRATISTA
                   .str.normalize('NFD')
                   .str.encode('ascii', 'ignore')
                   .str.decode('utf-8')
                   .str.upper()
                   .str.replace('.', '')
                   .str.replace(',', '')
                   .str.strip()
                   .replace('"', '')
                   .str.replace("'", '')
                   .map(remove_double_white_space))
    df = df.assign(PROVEEDOR_CONTRATISTA=proveedor)
    for regex in REGEX_LIST:
        pattern = re.compile(regex)
        df = df.assign(
            PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(
                lambda string: remove_pattern(string, pattern)
            )
        )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    return df
