
import os
# import feather
import pandas as pd
from joblib import Parallel, delayed
from currency_converter import CurrencyConverter
from typing import List
from utils.clean_data import procesar_archivo_procedimientos
from utils.clean_data import convert_to_mxn
from utils.clean_data import (get_claveuc_nombre,
                              get_claveuc_real,
                              get_claveuc_proc)
DataFrame = pd.DataFrame

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


if __name__ == '__main__':
    converter_pesos = CurrencyConverter(fallback_on_missing_rate=True,
                                        verbose=False,
                                        fallback_on_wrong_date=True)

    procs_path = './data/bases/procedimientos/'
    directorio_unidades_path = './data/bases/directorio_UC.xlsx'
    exped_repeditos_path = './data/bases/codigos_expediente_repetidos.csv'
    output_path = './data/bases/'

    files: List[str] = [
        'procedimientos_contratacion_2010-2012.xlsx',
        'procedimientos_contratacion_2013.xlsx',
        'procedimientos_contratacion_2014.xlsx',
        'procedimientos_contratacion_2015.xlsx',
        'procedimientos_contratacion_2016.xlsx',
        'procedimientos_contratacion_2017.xlsx',
    ]
    years: List[int] = [2012, 2013, 2014, 2015, 2016, 2017]
    dfs = Parallel(n_jobs=-1, batch_size=1)(
        delayed(procesar_archivo_procedimientos)(os.path.join(procs_path, file), year)
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
    # TODO: crear parquet, feather y csv
    # Save as psv, parquet and feather
    df_procs.to_csv(f'{output_path}/procedimientos.psv',
                    sep='|', encoding='utf-8',
                    index=False, quoting=1)
    df_procs.to_parquet(f'{output_path}/procedimientos.parquet',
                        engine='pyarrow')
    # feather.write_dataframe(df_procs,
    #                         f'{output_path}/procedimientos.feather')



