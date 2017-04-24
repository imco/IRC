# Scraper Compranet

## Instalación y uso

Descarga de los releases el ejecutable correspondiente a tu plataforma y ejecuta:

```bash
./scraper -inicio x -fin y
```

donde `x` es el ID interno de Compranet inicial y `y` es el ID final.

Si no introduces valores de inicio y final, el scraper iniciará en 1 y terminará hasta llegar al 1300000.

En el archivo `log.out` se almacenan los ids que se pudieron obtener correctamente. Dentro de `data.json` se almacenan los Expedientes extraidos en formato [JSON lines](http://jsonlines.org/). En la carpeta `html` se encuentra el html en crudo del expediente extraido, ordenado por ID interno de compranet.

## Uso en modo desarrollo.

Clona el repo dentro de tu `GOHOME` en la carpeta:

```bash
git clone https://github.com/opintel/compranet.git ~/$GOHOME/src/github.com/opintel/compranet
```

Este scraper se encuentra dentro de la carpeta `scraper`

Posteriormente instala las dependencias y construye:

```bash
go get
go build
```