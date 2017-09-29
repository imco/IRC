#!/usr/bin/env python

# Created by Raul Peralta-Lozada (29/09/17)
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


def remove_pattern(string, pattern):
    if isinstance(string, str):
        return pattern.sub('', string)
    return string


def clean_procedimientos_file(name):
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
        FECHA_APERTURA_PROPOSICIONES=pd.to_datetime(df.FECHA_APERTURA_PROPOSICIONES,
                                                    yearfirst=True),
        EXP_F_FALLO=pd.to_datetime(df.EXP_F_FALLO, yearfirst=True),
        FECHA_CELEBRACION=pd.to_datetime(df.FECHA_CELEBRACION, yearfirst=True),
        FECHA_INICIO=pd.to_datetime(df.FECHA_INICIO, yearfirst=True),
        FECHA_FIN=pd.to_datetime(df.FECHA_FIN, yearfirst=True)
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
    # All upper case
    df.loc[:, 'NUMERO_PROCEDIMIENTO'] = df.NUMERO_PROCEDIMIENTO.str.upper()
    return df


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
