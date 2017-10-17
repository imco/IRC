#!/usr/bin/env python

# Created by Raul Peralta-Lozada (29/09/17)
import re
import unicodedata
import pandas as pd

endings_regex_list = [
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
    if isinstance(string, str):
        return pattern.sub('', string)
    return string


def convert_to_mxn(converter, montos, monedas, fechas):
    monto_pesos = []
    for monto, moneda, fecha in zip(montos, monedas, fechas):
        if moneda in {'MXN', 'TEST', 'OTH'}:
            monto_pesos.append(monto)
        else:
            val = converter.convert(monto, moneda, 'MXN', date=fecha)
            monto_pesos.append(val)
    return monto_pesos


def get_claveuc_proc(num_proc):
    if isinstance(num_proc, str):
        return num_proc.split('-')[1]
    return None


def remove_double_white_space(name):
    if isinstance(name, str):
        return " ".join(name.split())
    return name


def get_claveuc_nombre(nombre_uc):
    if isinstance(nombre_uc, str):
        nombre_uc = nombre_uc.split('#')
    else:
        return None
    if len(nombre_uc) > 1 and isinstance(nombre_uc, list):
        return nombre_uc[1]
    return None


def get_claveuc_real(df, unidades_validas):
    cond1 = (df.CLAVEUC == df.CLAVEUC_PROC)
    cond2 = (df.CLAVEUC == df.CLAVEUC_NOM)
    cond3 = (df.CLAVEUC_NOM == df.CLAVEUC_PROC)
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


def clean_procedimientos_file(name, year):
    df = pd.read_excel(
        '{0}'.format(name),
        dtype={
            'FOLIO_RUPC': str, 'CLAVEUC': str, 'CODIGO_CONTRATO': str,
            'CODIGO_EXPEDIENTE': str, 'FOLIO_RUPC': str,
            'IMPORTE_CONTRATO': float, 'APORTACION_FEDERAL': float
        }
    )
    df = df.assign(
        PROC_F_PUBLICACION=pd.to_datetime(df.PROC_F_PUBLICACION, yearfirst=True),
        FECHA_APERTURA_PROPOSICIONES=pd.to_datetime(
            df.FECHA_APERTURA_PROPOSICIONES, yearfirst=True),
        EXP_F_FALLO=pd.to_datetime(df.EXP_F_FALLO, yearfirst=True),
        FECHA_CELEBRACION=pd.to_datetime(df.FECHA_CELEBRACION, yearfirst=True),
        FECHA_INICIO=pd.to_datetime(df.FECHA_INICIO, yearfirst=True),
        FECHA_FIN=pd.to_datetime(df.FECHA_FIN, yearfirst=True),
        FECHA_ARCHIVO=year
    )
    cols = [
        'SIGLAS', 'DEPENDENCIA', 'NOMBRE_DE_LA_UC', 'RESPONSABLE', 'ESTRATIFICACION_MUC',
        'PROVEEDOR_CONTRATISTA', 'ESTRATIFICACION_MPC', 'ESTATUS_EMPRESA', 'GOBIERNO',
        'TITULO_EXPEDIENTE', 'TITULO_CONTRATO', 'TIPO_CONTRATACION', 'TIPO_PROCEDIMIENTO',
        'ESTATUS_CONTRATO', 'FORMA_PROCEDIMIENTO', 'CARACTER', 'PLANTILLA_EXPEDIENTE',
    ]
    # Remove non ascii chars
    for col in cols:
        df.loc[:, col] = df[col].str.normalize('NFD').str.encode('ascii', 'ignore').str.decode(
            'utf-8').str.upper()
        df.loc[:, col] = df[col].str.replace('.', '')
        df.loc[:, col] = df[col].str.replace(',', '')
        df.loc[:, col] = df[col].str.strip()
    # Clean some extra details for PoC and double white spaces
    df.loc[:, 'PROVEEDOR_CONTRATISTA'] = df.PROVEEDOR_CONTRATISTA.str.replace('"', '')
    df.loc[:, 'PROVEEDOR_CONTRATISTA'] = df.PROVEEDOR_CONTRATISTA.str.replace("'", '')
    df.loc[:, 'PROVEEDOR_CONTRATISTA'] = df.PROVEEDOR_CONTRATISTA.map(remove_double_white_space)
    for regex in endings_regex_list:
        pattern = re.compile(regex)
        df = df.assign(
                PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(
                    lambda string: remove_pattern(string, pattern)
                )
        )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    # All upper case
    df.loc[:, 'NUMERO_PROCEDIMIENTO'] = df.NUMERO_PROCEDIMIENTO.str.upper()
    return df


def clean_participantes_file(path: str):
    df = pd.read_csv(path, encoding='iso-8859-1', dtype={'Expediente': str})
    # Add the period according to the file name
    periodo = path.split('.csv')[0]
    periodo = '-'.join(find_numbers(periodo))
    df = df.assign(periodo=periodo)
    # Normalize column names
    df = df.rename(
        columns={
            'Dependencia/Entidad': 'DEPENDENCIA',
            'Nº de Procedimiento': 'NUMERO_PROCEDIMIENTO',
            'Unidad Compradora': 'NOMBRE_DE_LA_UC',
            'Forma del procedimiento': 'FORMA_PROCEDIMIENTO',
            'Nombre de Licitante': 'PROVEEDOR_CONTRATISTA',
            'Expediente': 'CODIGO_EXPEDIENTE'
        }
    )
    new_columns = {
        col: unicodedata.normalize('NFD', col).encode('ascii', 'ignore').decode('utf-8')
        for col in df.columns
    }
    new_columns = {
        k: '_'.join(v.split(' ')).upper()
        for k, v in new_columns.items()
    }
    df = df.rename(columns=new_columns)

    # Normalize string column values
    cols = {k for k, v in df.dtypes.to_dict().items() if str(v) == 'object'}
    for col in cols:
        df.loc[:, col] = df[col].str.normalize('NFD').str.encode('ascii', 'ignore').str.decode(
            'utf-8').str.upper()
        df.loc[:, col] = df[col].str.replace('.', '')
        df.loc[:, col] = df[col].str.replace(',', '')
        df.loc[:, col] = df[col].str.strip()

    # Extract clave from UC's names
    CLAVEUC = df.NOMBRE_DE_LA_UC.map(get_claveuc_nombre)
    df = df.assign(CLAVEUC=CLAVEUC)
    # Save as category to reduce memory usage
    cols = (
        'TIPO_PROCEDIMIENTO', 'TIPO_CONTRATACION', 'FORMA_PROCEDIMIENTO', 'PERIODO',
        'ESTATUS_PARTIDA', 'ESTATUS_FALLO', 'ESTATUS_DE_PROPUESTA', 'DEPENDENCIA',
        'CLAVEUC', 'PERIODO'
    )
    for col in cols:
        df.loc[:, col] = df[col].astype('category')

    # Remove common endings
    for regex in endings_regex_list:
        pattern = re.compile(regex)
        df = df.assign(
            PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(
                lambda string: remove_pattern(string, pattern))
        )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    return df


def clean_rfc_fantasma(df_rfc_fantasma):
    df_rfc_fantasma = df_rfc_fantasma.rename(
        columns={'NOMBRE DEL CONTRIBUYENTE': 'PROVEEDOR_CONTRATISTA'})
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=(
            df_rfc_fantasma.PROVEEDOR_CONTRATISTA.str.normalize('NFD').str.encode(
                'ascii', 'ignore'
            ).str.decode('utf-8').str.upper()
        )
    )
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.str.replace('.', '')
    )
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.str.replace(',', '')
    )
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.str.strip()
    )
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.str.replace('"', '')
    )
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.str.replace("'", '')
    )
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.map(remove_double_white_space)
    )
    for regex in endings_regex_list:
        pattern = re.compile(regex)
        df_rfc_fantasma = df_rfc_fantasma.assign(
            PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.map(
                lambda string: remove_pattern(string, pattern)
            )
        )
    df_rfc_fantasma = df_rfc_fantasma.assign(
        PROVEEDOR_CONTRATISTA=df_rfc_fantasma.PROVEEDOR_CONTRATISTA.str.strip()
    )
    return df_rfc_fantasma


def clean_sancionados(df):
    df = df.rename(columns={'Proveedor y Contratista ': 'PROVEEDOR_CONTRATISTA'})
    df = df.assign(Multa=df.Multa.str.replace(',', '').astype(float))
    df = df.assign(
        PROVEEDOR_CONTRATISTA=(
            df.PROVEEDOR_CONTRATISTA.str.normalize('NFD').str.encode(
                'ascii', 'ignore'
            ).str.decode('utf-8').str.upper()
        )
    )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace('.', ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace(',', ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace('"', ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace("'", ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(remove_double_white_space))
    for regex in endings_regex_list:
        pattern = re.compile(regex)
        df = df.assign(
            PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(
                lambda string: remove_pattern(string, pattern)
            )
        )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    return df


def clean_rupc(df):
    df = df.rename(columns={'NOMBRE_EMPRESA': 'PROVEEDOR_CONTRATISTA'})
    df = df.assign(
        FECHA_INSCRIPCION_RUPC=pd.to_datetime(df.FECHA_INSCRIPCION_RUPC, dayfirst=True)
    )
    df = df.assign(
        PROVEEDOR_CONTRATISTA=(
            df.PROVEEDOR_CONTRATISTA.str.normalize('NFD').str.encode(
                'ascii', 'ignore'
            ).str.decode('utf-8').str.upper()
        )
    )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace('.', ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace(',', ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace('"', ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.replace("'", ''))
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(remove_double_white_space))
    for regex in endings_regex_list:
        pattern = re.compile(regex)
        df = df.assign(
            PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(
                lambda string: remove_pattern(string, pattern)
            )
        )
    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    return df


def write_file(df, file_name: str, sep='|', file_format='.psv'):
    df.to_csv(file_name + file_format, index=False, quoting=1, encoding='utf-8', sep=sep)
