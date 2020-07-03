import os
import re
import pandas as pd
import numpy as np
from currency_converter import CurrencyConverter
from joblib import Parallel, delayed
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


# Mapping de columnas 2018 a 2012
# Las comentadas son columnas no encontradas en la versión previa (2012-2017)
COLUMN_MAPPING = {
    'Orden de gobierno': 'GOBIERNO',
    'Siglas de la Institución': 'SIGLAS',
    'Institución': 'DEPENDENCIA',
    'Clave de la UC': 'CLAVEUC',
    'Nombre de la UC': 'NOMBRE_DE_LA_UC',
    'Responsable de la UC': 'RESPONSABLE',
    'Código del expediente': 'CODIGO_EXPEDIENTE',
    # 'Referencia del expediente': '',
    # 'Clave CUCOP': '',
    'Título del expediente': 'TITULO_EXPEDIENTE',
    'Plantilla del expediente': 'PLANTILLA_EXPEDIENTE',
    # 'Fundamento legal': '',
    'Número del procedimiento': 'NUMERO_PROCEDIMIENTO',
    'Fecha de fallo': 'EXP_F_FALLO',
    'Fecha de publicación': 'PROC_F_PUBLICACION',
    'Fecha de apertura': 'FECHA_APERTURA_PROPOSICIONES',
    'Carácter del procedimiento': 'CARACTER',
    'Tipo de contratación': 'TIPO_CONTRATACION',
    'Tipo de procedimiento': 'TIPO_PROCEDIMIENTO',
    'Forma de participación': 'FORMA_PROCEDIMIENTO',
    'Código del contrato': 'CODIGO_CONTRATO',
    # 'Núm. de control del contrato': '',
    'Título del contrato': 'TITULO_CONTRATO',
    'Fecha de inicio del contrato': 'FECHA_INICIO',
    'Fecha de fin del contrato': 'FECHA_FIN',
    'Importe del contrato': 'IMPORTE_CONTRATO',
    'Moneda del contrato': 'MONEDA',
    'Estatus del contrato': 'ESTATUS_CONTRATO',
    'Convenio modificatorio': 'CONVENIO_MODIFICATORIO',
    'Clave del programa federal': 'CLAVE_PROGRAMA',
    'Fecha de firma del contrato': 'FECHA_CELEBRACION',
    'Contrato marco': 'IDENTIFICADOR_CM',
    'Compra consolidada': 'COMPRA_CONSOLIDADA',
    'Contrato plurianual': 'PLURIANUAL',
    'Clave de cartera SHCP': 'CLAVE_CARTERA_SHCP',
    'Folio en el RUPC': 'FOLIO_RUPC',
    # 'RFC': '',
    'Proveedor o contratista': 'PROVEEDOR_CONTRATISTA',
    'Estratificación de la empresa': 'ESTRATIFICACION_MPC',
    'Clave del país de la empresa': 'SIGLAS_PAIS',
    # 'RFC verificado en el SAT': '',
    'Crédito externo': 'C_EXTERNO',
    'Organismo financiero': 'ORGANISMO',
    'Dirección del anuncio': 'ANUNCIO'
}


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
    df = pd.read_excel(file, dtype=str)

    if year >= 2018:
        # Para procesar archivos de nueva generación
        # vamos a renombrar las columnas para que
        # correspondan a la versión anterior.
        # Hay algunas columnas que tendremos que rellenar
        # dado que no existen en formatos recientes
        # de Compranet.
        df.rename(columns=COLUMN_MAPPING, inplace=True)
        df['APORTACION_FEDERAL'] = np.nan
        df['ARCHIVADO'] = -1
        df['CONTRATO_MARCO'] = df['IDENTIFICADOR_CM'].astype(bool)
        df['CUENTA_ADMINISTRADA_POR'] = 'N/A'
        df['ESTATUS_EMPRESA'] = 'N/A'
        df['ESTRATIFICACION_MUC'] = df['ESTRATIFICACION_MPC']
        df['RAMO'] = ''

    df['IMPORTE_CONTRATO'] = df['IMPORTE_CONTRATO'].astype(float)
    df['APORTACION_FEDERAL'] = df['APORTACION_FEDERAL'].astype(float)

    # Las bases del 2019 traen algunas fechas como un espacio, i.e. ' '.
    # Tenemos que usar 'coerce' para permitir a pandas convertirlas en NaT
    df = df.assign(
        PROC_F_PUBLICACION=pd.to_datetime(df.PROC_F_PUBLICACION, yearfirst=True, errors='coerce'),
        FECHA_APERTURA_PROPOSICIONES=pd.to_datetime(df.FECHA_APERTURA_PROPOSICIONES, yearfirst=True, errors='coerce'),
        EXP_F_FALLO=pd.to_datetime(df.EXP_F_FALLO, yearfirst=True, errors='coerce'),
        FECHA_CELEBRACION=pd.to_datetime(df.FECHA_CELEBRACION, yearfirst=True, errors='coerce'),
        FECHA_INICIO=pd.to_datetime(df.FECHA_INICIO, yearfirst=True, errors='coerce'),
        FECHA_FIN=pd.to_datetime(df.FECHA_FIN, yearfirst=True, errors='coerce'),
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


def procesar_dataframe_sipot(df: DataFrame, type: str) -> DataFrame:
    """
    Rutinas de limpieza de archivos obtenidos de imco/sipot
    - Renombra las columnas
    - Pasa varios campos a mayúscula
    - Remueve acentos
    - Normaliza razones sociales
    """
    # Elimina espacios alrededor de los nombres de columna
    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)

    col_mapping = None
    if type == 'adjudicaciones':
        col_mapping = {
            'ID': 'SIPOT_ID',
            'Ejercicio': 'EJERCICIO',
            'Fecha de Inicio Del Periodo Que Se Informa': 'FECHA_INICIO',
            'Tipo de Procedimiento (catálogo)': 'TIPO_PROCEDIMIENTO',
            'Materia (catálogo)': 'TIPO_CONTRATACION',
            'Número de Expediente, Folio O Nomenclatura Que Lo Identifique': 'NUMERO_PROCEDIMIENTO',
            'Motivos Y Fundamentos Legales Aplicados para Realizar La Adjudicación Directa': 'MOTIVOS_ADJUDICACION',
            'Hipervínculo a La Autorización Del Ejercicio de La Opción': 'LIGA_AUTORIZACION',
            'Nombre Completo O Razón Social de Las Cotizaciones Consideradas Y Monto de Las Mismas (Tabla_334271)': 'REF_COTIZACIONES',
            'Razón Social Del Adjudicado': 'PROVEEDOR_CONTRATISTA',
            'Registro Federal de Contribuyentes (rfc) de La Persona Física O Moral Adjudicada': 'RFC_PROVEEDOR_CONTRATISTA',
            'Número Que Identifique Al Contrato': 'CODIGO_EXPEDIENTE',
            'Monto Total Del Contrato con Impuestos Incluidos (expresado en Pesos Mexicanos)': 'PRECIO_TOTAL',
            'Hipervínculo Al Documento Del Contrato Y Anexos, Versión Pública Si Así Corresponde': 'LIGA_CONTRATO',
            'Se Realizaron Convenios Modificatorios (catálogo)': 'CONVENIOS_MODIFICATORIOS',
            'Datos de Los Convenios Modificatorios de La Contratación (Tabla_334268)': 'REF_CONVENIOS_MODIFICATORIOS'
        }
    elif type == 'licitaciones':
        col_mapping = {
            'ID': 'SIPOT_ID',
            'Ejercicio': 'EJERCICIO',
            'Fecha de Inicio Del Periodo Que Se Informa': 'FECHA_INICIO',
            'Tipo de Procedimiento (catálogo)': 'TIPO_PROCEDIMIENTO',
            'Materia (catálogo)': 'TIPO_CONTRATACION',
            'Posibles Contratantes (Tabla_334277)': 'REF_CANDIDATOS',
            'Número de Expediente, Folio O Nomenclatura': 'NUMERO_PROCEDIMIENTO',
            'Hipervínculo a La Convocatoria O Invitaciones Emitidas': 'LIGA_CONVOCATORIA',
            'Personas Físicas O Morales con Proposición U Oferta (Tabla_334306)': 'REF_OFERTAS',
            'Hipervínculo Al Fallo de La Junta de Aclaraciones O Al Documento Correspondiente': 'LIGA_FALLO',
            'Razón Social Del Contratista O Proveedor': 'PROVEEDOR_CONTRATISTA',
            'Rfc de La Persona Física O Moral Contratista O Proveedor': 'RFC_PROVEEDOR_CONTRATISTA',
            'Número Que Identifique Al Contrato': 'CODIGO_EXPEDIENTE',
            'Monto Total Del Contrato con Impuestos Incluidos (mxn)': 'PRECIO_TOTAL',
            'Hipervínculo Al Documento Del Contrato Y Anexos, en Versión Pública, en su Caso': 'LIGA_CONTRATO',
            'Se Realizaron Convenios Modificatorios (catálogo)': 'CONVENIOS_MODIFICATORIOS',
            'Convenios Modificatorios (Tabla_334310)': 'REF_CONVENIOS_MODIFICATORIOS',
            'Hipervínculo Al Finiquito, en su  Caso': 'LIGA_FINIQUITO'
        }

    # Renombra las columnas, y reduce el dataframe a ese conjunto de datos
    if col_mapping != None:
        df.rename(columns=col_mapping, inplace=True)
        df = df[col_mapping.values()]

    cols = [
        'PROVEEDOR_CONTRATISTA',
        'TIPO_CONTRATACION',
        'TIPO_PROCEDIMIENTO'
    ]

    # Elimina caracteres no ascii
    for col in cols:
        df.loc[:, col] = (df[col]
                          .str.normalize('NFD')
                          .str.encode('ascii', 'ignore')
                          .str.decode('utf-8')
                          .str.upper()
                          .str.replace('.', '')
                          .str.replace(',', '')
                          .str.strip())

    # Estandariza TIPO_CONTRATACION
    old_key = 'SERVICIOS RELACIONADOS CON OBRA PUBLICA'
    new_key = 'SERVICIOS RELACIONADOS CON LA OP'
    df.loc[:, 'TIPO_CONTRATACION'] = (df['TIPO_CONTRATACION']
                                      .str.replace(old_key, new_key))
    # Estandariza TIPO_PROCEDIMIENTO
    old_key = 'INVITACION A CUANDO MENOS TRES PERSONAS'
    new_key = 'INVITACION A CUANDO MENOS TRES'
    df.loc[:, 'TIPO_PROCEDIMIENTO'] = (df['TIPO_PROCEDIMIENTO']
                                       .str.replace(old_key, new_key))


    df.loc[:, 'PROVEEDOR_CONTRATISTA'] = (df.PROVEEDOR_CONTRATISTA
                                            .str.replace('"', '')
                                            .str.replace("'", '')
                                            .map(remove_double_white_space))

    # Limpia sufijos comunes de razones sociales
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


def clean_columna_proveedor(df: DataFrame) -> DataFrame:
    """
    Limpia PROVEEDOR_CONTRATISTA para facilitar cruces de info
    - Remueve caracteres especiales
    - Remueve terminaciones de razones sociales
    """
    df.loc[:, 'PROVEEDOR_CONTRATISTA'] = (df.PROVEEDOR_CONTRATISTA
                                          .str.replace('"', '')
                                          .str.replace("'", '')
                                          .map(remove_double_white_space))

    # Limpia sufijos comunes de razones sociales
    for regex in REGEX_LIST:
        pattern = re.compile(regex)
        df = df.assign(
            PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.map(
                lambda string: remove_pattern(string, pattern)
            )
        )

    df = df.assign(PROVEEDOR_CONTRATISTA=df.PROVEEDOR_CONTRATISTA.str.strip())
    return df


def clean_base_sancionados(df: DataFrame) -> DataFrame:
    """Homologa los nombres de proveedores de la base de sancionados"""
    df = df.rename(
        columns={'Proveedor y Contratista ': 'PROVEEDOR_CONTRATISTA'})

    if 'Multa' in df.columns:
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


def ensamblar_procedimientos(files: List[str],
                             years: List[int],
                             base_path: str = '.') -> DataFrame:
    """
    Toma una lista de procedimientos de contratación de Compranet
    y los convierte en un DataFrame, aplicando varias transformaciones.
    """
    columnas_procs: List[str] = [
        'GOBIERNO',
        # Dependencia/unidad/responsable
        'DEPENDENCIA',
        'SIGLAS',
        'NOMBRE_DE_LA_UC',
        'CLAVEUC',
        'RESPONSABLE',
        'ESTRATIFICACION_MUC',
        # proveedor
        'FOLIO_RUPC',
        'PROVEEDOR_CONTRATISTA',
        'ESTATUS_EMPRESA',
        'ESTRATIFICACION_MPC',
        'CLAVE_CARTERA_SHCP',
        # montos
        'IMPORTE_CONTRATO',
        'APORTACION_FEDERAL',
        'MONEDA',
        # datos procedimiento
        'NUMERO_PROCEDIMIENTO',
        'FORMA_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        # datos contrato
        'CODIGO_CONTRATO',
        'TITULO_CONTRATO',
        'IDENTIFICADOR_CM',
        'TIPO_CONTRATACION',
        'ESTATUS_CONTRATO',
        'COMPRA_CONSOLIDADA',
        'PLURIANUAL',
        'CARACTER',
        'CONTRATO_MARCO',
        'CONVENIO_MODIFICATORIO',
        # Fechas ordenadas
        'PROC_F_PUBLICACION',
        'FECHA_APERTURA_PROPOSICIONES',
        'EXP_F_FALLO',
        'FECHA_CELEBRACION',
        'FECHA_INICIO',
        'FECHA_FIN',
        # expediente
        'CODIGO_EXPEDIENTE',
        'TITULO_EXPEDIENTE',
        'PLANTILLA_EXPEDIENTE',
        'CLAVE_PROGRAMA',
        'CUENTA_ADMINISTRADA_POR',
        'ANUNCIO',
        'ARCHIVADO',
        'SIGLAS_PAIS',
        'RAMO',
        'ORGANISMO',
        'C_EXTERNO',
        'FECHA_ARCHIVO',
    ]

    converter_pesos = CurrencyConverter(fallback_on_missing_rate=True,
                                        verbose=False,
                                        fallback_on_wrong_date=True)

    directorio_unidades_path = os.path.join(base_path, 'directorio_UC.xlsx')
    exped_repeditos_path = os.path.join(base_path, 'codigos_expediente_repetidos.csv')

    dfs = Parallel(n_jobs=-1, batch_size=1)(
        delayed(procesar_archivo_procedimientos)(os.path.join(base_path, file), year)
        for file, year in zip(files, years)
    )
    df_procs: DataFrame = pd.concat(dfs, axis=0, ignore_index=True)
    print(df_procs.shape)
    df_procs = df_procs.loc[:, columnas_procs]
    print(df_procs.shape)
    # solo procedimientos de 2012 en adelante
    df_procs = df_procs.loc[(df_procs.FECHA_INICIO.dt.year > 2011), :]
    # Se reemplazan los valores de algunas dependencias
    dependencias_repetidas = {
        'HOSPITAL GENERAL DE MEXICO "DR. EDUARDO LICEAGA"': 'HOSPITAL GENERAL DE MEXICO',
        'INSTITUTO NACIONAL DE REHABILITACION LUIS GUILLERMO IBARRA IBARRA': 'INSTITUTO NACIONAL DE REHABILITACION',
        'CENTRO DE INVESTIGACION EN GEOGRAFIA Y GEOMATICA, "ING. JORGE L. TAMAYO", A.C.': 'CENTRO DE INVESTIGACION EN GEOGRAFIA Y GEOMATICA "ING. JORGE L. TAMAYO", A.C.',
        'TRIBUNAL FEDERAL DE JUSTICIA FISCAL Y ADMINISTRATIVA': 'TRIBUNAL FEDERAL DE JUSTICIA ADMINISTRATIVA',
        'INSTITUTO DE INVESTIGACIONES ELECTRICAS': 'INSTITUTO NACIONAL DE ELECTRICIDAD Y ENERGIAS LIMPIAS'
    }
    for k, v in dependencias_repetidas.items():
        df_procs.loc[df_procs.DEPENDENCIA == k, 'DEPENDENCIA'] = v
    del dependencias_repetidas
    # Se intenta rescatar las claves de uc de los nombres y los nums de proc
    df_procs = df_procs.assign(
        CLAVEUC_PROC=df_procs.NUMERO_PROCEDIMIENTO.map(get_claveuc_proc),
        CLAVEUC_NOM=df_procs.NOMBRE_DE_LA_UC.map(get_claveuc_nombre)
    )
    # Se completan algunas CLAVEUC
    claves_con_pad = df_procs.CLAVEUC.str.pad(9, fillchar='0')
    df_procs.loc[df_procs.CLAVEUC.str.len() == 8, 'CLAVEUC'] = claves_con_pad
    df_procs.loc[df_procs.CLAVEUC.str.len() == 7, 'CLAVEUC'] = claves_con_pad

    # Leer uc oficiales
    directorio_unidades_compradoras = pd.read_excel(
        directorio_unidades_path, dtype={'CLAVE_UC': str})
    directorio_unidades_compradoras = set(
        directorio_unidades_compradoras.CLAVE_UC.unique())

    df_procs = get_claveuc_real(df_procs, directorio_unidades_compradoras)
    df_procs = (df_procs.assign(CLAVEUC=df_procs.CLAVEUC_REAL)
                        .drop('CLAVEUC_REAL', axis=1))
    # convertir import en pesos mexicanos
    # Transform to mexican pesos
    monto_en_pesos = convert_to_mxn(
        converter_pesos, df_procs.IMPORTE_CONTRATO.values,
        df_procs.MONEDA.values, df_procs.FECHA_INICIO
    )

    df_procs = df_procs.assign(IMPORTE_PESOS=monto_en_pesos)
    # Llenar el valor de convenio cuando sea Nan con 'No reportado'
    # llenar convenio modificatorio
    df_procs = df_procs.assign(
        CONVENIO_MODIFICATORIO=df_procs.CONVENIO_MODIFICATORIO.astype(str)
    )
    df_procs.loc[
        df_procs.CONVENIO_MODIFICATORIO == '0.0', 'CONVENIO_MODIFICATORIO'
    ] = 'NO'
    df_procs.loc[
        df_procs.CONVENIO_MODIFICATORIO == '1.0', 'CONVENIO_MODIFICATORIO'
    ] = 'SI'
    df_procs.loc[
        df_procs.CONVENIO_MODIFICATORIO == 'nan', 'CONVENIO_MODIFICATORIO'
    ] = 'NO REPORTADO'

    # se reemplaza el valor del tipo de procedimiento para que sea
    #  consistente con el resto de las tablas
    df_procs.loc[
        df_procs.TIPO_PROCEDIMIENTO == 'INVITACION A CUANDO MENOS 3 PERSONAS',
        'TIPO_PROCEDIMIENTO'
    ] = 'INVITACION A CUANDO MENOS TRES'
    df_procs.loc[
        df_procs.TIPO_PROCEDIMIENTO == 'ADJUDICACION DIRECTA FEDERAL',
        'TIPO_PROCEDIMIENTO'
    ] = 'ADJUDICACION DIRECTA'

    # Remover codigos de expedientes que se repiten
    codigos_exped_repeditos = pd.read_csv(
        exped_repeditos_path, dtype=str,
        usecols=['CODIGO_EXPEDIENTE']
    )
    codigos_exped_repeditos = codigos_exped_repeditos.CODIGO_EXPEDIENTE.unique()
    codigos_exped_repeditos = set(codigos_exped_repeditos)
    df_procs = df_procs.assign(codigos_repetidos=0)
    df_procs.loc[
        df_procs.CODIGO_EXPEDIENTE.isin(codigos_exped_repeditos),
        'codigos_repetidos'] = 1
    cols = [
        'CLAVEUC', 'NUMERO_PROCEDIMIENTO', 'CODIGO_EXPEDIENTE',
        'CODIGO_CONTRATO', 'codigos_repetidos', 'PROVEEDOR_CONTRATISTA']
    # Se remueven cerca de 550 registros
    df_procs = df_procs.drop_duplicates(subset=cols)
    df_procs = df_procs.drop('codigos_repetidos', axis=1)

    # Se quita a pemex del analisis
    pemex_cond = df_procs.DEPENDENCIA.str.contains('PEMEX')
    df_procs = df_procs.loc[~pemex_cond]
    pemex_cond = df_procs.DEPENDENCIA.str.contains('PETROLEOS MEXICANOS')
    df_procs = df_procs.loc[~pemex_cond]
    # guardar el dataframe
    drop_cols = ['CLAVE_CARTERA_SHCP', 'CLAVEUC_PROC', 'CLAVEUC_NOM']
    df_procs = df_procs.drop(drop_cols, axis=1)
    df_procs = df_procs.reset_index(drop=True)

    return df_procs
