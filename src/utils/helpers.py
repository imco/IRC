"""
Helpers utilizados por src.features.productos
"""

import pandas as pd

DataFrame = pd.DataFrame


def agrupa_participaciones(df_parts: DataFrame) -> DataFrame:
    """
    A pesar de que CODIGO_CONTRATO es único en la tabla de procedimientos,
    la tabla de participantes no tiene este identificador.
    Usar sólo NUMERO_PROCEDIMIENTO genera alrededor de 25% de duplicados.
    Usando una llave compuesta reducimos los duplicados a menos del 1%.

    No podemos usar REF_PARTICIPANTES porque existen
    miles de entradas con esto en 0 ya que fueron procesos sin participantes.

    Este método sirve para estandarizar la agrupación de participaciones
    requerida por varios productos que utilizan esta tabla.
    """
    return df_parts.groupby([
        'NUMERO_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        'TIPO_CONTRATACION',
        'FECHA_INICIO',
        'CLAVEUC'
    ])


def une_participantes_con_procedimientos(df_procs: DataFrame,
                                         df_parts: DataFrame) -> DataFrame:
    """
    Éste método estandariza la manera en la que conectamos tablas
    de procedimientos y participantes.

    Como vimos en el método agrupa_participaciones, la tabla de participantes
    no tiene identificador único, por lo que tenemos que formar una llave
    compuesta.
    """
    # Agregando el PROVEEDOR (el ganador en df_parts) y el importe,
    # mejoramos los matches en procedimientos.
    # Dejando sólo 1,012 de ~351,000 con uno que otro duplicado.
    keys = [
        'NUMERO_PROCEDIMIENTO',
        'TIPO_PROCEDIMIENTO',
        'TIPO_CONTRATACION',
        'FECHA_INICIO',
        'CLAVEUC',
        'PROVEEDOR_CONTRATISTA',
        'IMPORTE_PESOS'
    ]

    # Siempre con LEFT JOIN porque la tabla de procedimientos es nuestro
    # punto de referencia siempre.
    parts = df_parts.rename(columns={'PRECIO_TOTAL': 'IMPORTE_PESOS'})
    return df_procs.merge(parts, on=keys, how='left')


def da_participaciones_unicas(df_parts: DataFrame,
                              gr_parts: DataFrame) -> DataFrame:
    """
    Una vez que aplicamos operaciones a una agrupación de participaciones
    Vamos a conectarla con los ganadores, para así no tener duplicados entre ganadores
    y perdedores.

    De paso renombramos PRECIO_TOTAL para poder ligar con procedimientos.
    """
    ganadores = df_parts[df_parts.ESTATUS_DE_PROPUESTA == 'GANADOR']
    return (pd.merge(ganadores, gr_parts)
            .drop('ESTATUS_DE_PROPUESTA', axis=1))
