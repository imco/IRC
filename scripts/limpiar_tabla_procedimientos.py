import pandas as pd
from typing import List
from utils.clean_data import ensamblar_procedimientos

if __name__ == '__main__':
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
    base_path = '../data/bases'
    df_procs = ensamblar_procedimientos(files, years, base_path)

    # TODO: crear parquet, feather y csv
    # Save as psv, parquet and feather
    df_procs.to_csv(f'{output_path}/procedimientos.psv',
                    sep='|', encoding='utf-8',
                    index=False, quoting=1)
    df_procs.to_parquet(f'{output_path}/procedimientos.parquet',
                        engine='pyarrow')
    # feather.write_dataframe(df_procs,
    #                         f'{output_path}/procedimientos.feather')

