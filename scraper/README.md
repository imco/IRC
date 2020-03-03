En la carpeta `scraper` encontrarás el scraper de COMPRANET.

En la carpeta `etl` scripts de limpieza y verificación de los datos
descargados por el scraper.

## Uso

Para obtener ids de compranet que no se descargaron.

```sh
~/IRC/scraper/etl/missing log.out 1300000 1400000 | tee missing.txt
```

Para obtener ids de compranets con expedientes vacíos

```sh
~/IRC/scraper/etl/empty data.json | tee empty.txt
```

Para filtrar documentos sin una propiedad (i.e. supuestamente
inválidos), p. ej. sin descripción.

```sh
~/IRC/scraper/etl/valid data.json > valid.json
```

Mezclar la lista de ids de faltantes y vacíos (sin duplicados).

```sh
sort missing.txt empty.txt | uniq > todo.txt
```
