# csv_to_parquet.py <csv_file>
# adaptado de https://stackoverflow.com/questions/26124417/how-to-convert-a-csv-file-to-parquet

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
                         sep='|',
                         quoting=1,
                         chunksize=chunksize,
                         low_memory=False)

for i, chunk in enumerate(csv_stream):
    print("Chunk", i)
    if i == 0:
        # Guess the schema of the CSV file from the first chunk
        chunk = chunk.astype({"IDENTIFICADOR_CM": str})
        parquet_schema = pa.Table.from_pandas(df=chunk).schema
        print('SCHEMA')
        print(parquet_schema)
        print('------')
        # Open a Parquet file for writing
        parquet_writer = pq.ParquetWriter(parquet_file, parquet_schema, compression='snappy')
    # Write CSV chunk to the parquet file
    try:
        table = pa.Table.from_pandas(chunk, schema=parquet_schema)
        parquet_writer.write_table(table)
    except:
        print('FAILURE\n', chunk)
        raise

parquet_writer.close()
