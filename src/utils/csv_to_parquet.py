# csv_to_parquet.py <csv_file>
# adaptado de https://stackoverflow.com/questions/26124417/how-to-convert-a-csv-file-to-parquet

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import sys

csv_file = sys.argv[1]
parquet_file = csv_file + ".parquet"
print("Reading", csv_file)
print("Writing", parquet_file)

chunksize = 100_000

csv_stream = pd.read_csv(csv_file,
                         dtype={
                             "CANTIDAD": float,
                             "CODIGO_EXPEDIENTE": float,
                             "PRECIO_TOTAL": float,
                             "PRECIO_UNITARIO": float
                         },
                         sep='|',
                         chunksize=chunksize,
                         low_memory=False)

for i, chunk in enumerate(csv_stream):
    print("Chunk", i)

    # Cast CODIGO_EXPEDIENTE as integer
    # We had to use float at the beginning so we could parse nan's
    chunk["CODIGO_EXPEDIENTE"] = chunk["CODIGO_EXPEDIENTE"].fillna(-1)
    chunk["CODIGO_EXPEDIENTE"] = chunk["CODIGO_EXPEDIENTE"].apply(pd.to_numeric, downcast='integer')

    if i == 0:
        # Guess the schema of the CSV file from the first chunk
        # To make it work for procedimientos.psv
        # chunk = chunk.astype({"IDENTIFICADOR_CM": str})
        print('SCHEMA chunk')
        print(chunk.dtypes)
        print('------')

        parquet_schema = pa.Table.from_pandas(df=chunk).schema
        print('SCHEMA parquet')
        print(parquet_schema)
        print('------')

        # Open a Parquet file for writing
        parquet_writer = pq.ParquetWriter(parquet_file, parquet_schema, compression='snappy')
    # Write CSV chunk to the parquet file
    try:
        table = pa.Table.from_pandas(chunk, schema=parquet_schema)
        parquet_writer.write_table(table)
    except:
        failed_column = 'CANTIDAD'
        print('FAILURE\n', chunk[failed_column])
        raise

parquet_writer.close()
