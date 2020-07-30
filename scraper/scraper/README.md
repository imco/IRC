# Scraper Compranet

## Instalación y uso

Descarga de los releases el ejecutable correspondiente a tu plataforma y ejecuta:

```bash
./scraper -inicio x -fin y
```

donde `x` es el ID interno de Compranet inicial y `y` es el ID final.

Si no introduces valores de inicio y final, el scraper iniciará en 1 y terminará hasta llegar al 1300000.

En el archivo `log.out` se almacenan los ids que se pudieron obtener correctamente. Dentro de `data.json` se almacenan los Expedientes extraidos en formato [JSON lines](http://jsonlines.org/). En la carpeta `html` se encuentra el html en crudo del expediente extraido, ordenado por ID interno de compranet.

Para trabajar una lista no secuencial de expedientes de Compranet,
utiliza el parámetro -ids para pasar el nombre de un archivo donde se
encuentre la lista de ids a scrapear; uno por línea.

```bash
(base) ➜  scraper git:(scrape-a-list) ✗ echo "105\n109\n110" >> algunos.txt
(base) ➜  scraper git:(scrape-a-list) ✗ ./scraper -ids algunos.txt
cargando lista de ids de archivo
2020/03/02 17:40:22 ended exp: 105
2020/03/02 17:40:22 getting new session
2020/03/02 17:40:43 ended exp: 109
2020/03/02 17:40:45 ended exp: 110
```

## Uso en modo desarrollo.

Primero [instala el lenguaje Go](https://golang.org/doc/install).

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

Para confirmar que se instaló y ver las opciones ejecuta:

```bash
./scraper -h
```

## Ejemplo de expediente en JSON

```json
{
   "codigo":"483",
   "descripcion":"DK040-003-2010 \"18164159-014-10 REPOTENCIACION LMX-4012 ZONA TUXTLA\"",
   "referencia":"ZONA TUXTLA 9400059354",
   "tipo":"sub110525_16. Licitación Pública Nacional LOPSRM",
   "categorias":"",
   "descripcion_anuncio":"Repotenciación de la Línea de Distribución de Energía Eléctrica del Circuito LMX-4012 de la Zona de Distribución Tuxtla, en el Estado de Chiapas",
   "notas":"Paredes Aquino Jose Carlos",
   "tipo_contratacion":"No especificado por la UC",
   "entidad":"No especificado por la UC",
   "fecha_publicacion":"",
   "fecha_ultima_actualizacion":"",
   "plazo_participacion":"07/01/2011 12:00 AM",
   "fecha_inicio_contrato":"28/02/2011",
   "duracion_contrato":"120 DIAS NATURALES",
   "fecha_conclusion":"2487186.93",
   "unidad_compradora":"CFE-Subdirección de Distribución División Sureste Zona Tuxtla",
   "nombre_operador":"Paredes Aquino Jose Carlos",
   "email":"jose.paredes02@cfe.gob.mx",
   "web":"",
   "tabla_datos":{
      "rows":null
   },
   "tabla_procedimientos":{
      "rows":null
   },
   "tabla_anexos":{
      "rows":[
         {
            "num":0,
            "archivo":"",
            "url":"",
            "descripcion":"",
            "comentarios":"",
            "fecha_modificacion":""
         },
         {
            "num":1,
            "archivo":"ACTA DE APERTURA N15.pdf  (797 KB) ",
            "url":"/esop/toolkit/DownloadProxy/798162?verify=15\u0026oid=185271\u0026fileId=77793",
            "descripcion":"ACTA DE APERTURA",
            "comentarios":"",
            "fecha_modificacion":"09/03/2011 02:38 PM"
         },
         {
            "num":2,
            "archivo":"ACTA DE FALLO.pdf  (815 KB) ",
            "url":"/esop/toolkit/DownloadProxy/736255?verify=15\u0026oid=171535\u0026fileId=71077",
            "descripcion":"ACTA DE FALLO",
            "comentarios":"",
            "fecha_modificacion":"07/03/2011 03:23 PM"
         },
         {
            "num":3,
            "archivo":"AT01410.zip  (1,485 KB) ",
            "url":"/esop/toolkit/DownloadProxy/63216?verify=15\u0026oid=28833\u0026fileId=7169",
            "descripcion":"DOCUMENTACION TECNICA DE PROYECTO",
            "comentarios":"",
            "fecha_modificacion":"22/12/2010 08:55 AM"
         },
         {
            "num":4,
            "archivo":"AX01410.zip  (2,964 KB) ",
            "url":"/esop/toolkit/DownloadProxy/63220?verify=15\u0026oid=28835\u0026fileId=7171",
            "descripcion":"ANEXOS Y GUIAS DE LLENADO PARA INTEGRACION DE PROPUESTA",
            "comentarios":"",
            "fecha_modificacion":"22/12/2010 08:56 AM"
         },
         {
            "num":5,
            "archivo":"BA01410.doc  (217 KB) ",
            "url":"/esop/toolkit/DownloadProxy/52413?verify=15\u0026oid=25677\u0026fileId=5859",
            "descripcion":"CONVOCATORIA DE LICITACION",
            "comentarios":"",
            "fecha_modificacion":"09/12/2010 09:06 PM"
         },
         {
            "num":6,
            "archivo":"convocatoria-modificada-10-12-10-compran...  (169 KB) ",
            "url":"/esop/toolkit/DownloadProxy/58875?verify=15\u0026oid=27484\u0026fileId=6590",
            "descripcion":"RESUMEN DE CONVOCATORIA COMPLETA",
            "comentarios":"",
            "fecha_modificacion":"15/12/2010 01:11 PM"
         },
         {
            "num":7,
            "archivo":"JUNTA 14.tif  (322 KB) ",
            "url":"/esop/toolkit/DownloadProxy/69343?verify=15\u0026oid=31069\u0026fileId=8277",
            "descripcion":"JUNTA DE ACLARACIONES",
            "comentarios":"",
            "fecha_modificacion":"29/12/2010 04:39 PM"
         },
         {
            "num":8,
            "archivo":"LO-018TOQ097-N15-2010.doc  (17 KB) ",
            "url":"/esop/toolkit/DownloadProxy/58881?verify=15\u0026oid=27486\u0026fileId=6592",
            "descripcion":"RESUMEN DE CONVOCATORIA COMPRANET",
            "comentarios":"",
            "fecha_modificacion":"15/12/2010 01:13 PM"
         },
         {
            "num":9,
            "archivo":"OFIC DIF N15.pdf  (191 KB) ",
            "url":"/esop/toolkit/DownloadProxy/119967?verify=15\u0026oid=42972\u0026fileId=12478",
            "descripcion":"OFICIO DE DIFERIMIENTO DE FALLO",
            "comentarios":"",
            "fecha_modificacion":"20/01/2011 08:45 PM"
         },
         {
            "num":10,
            "archivo":"VISITA 14.tif  (229 KB) ",
            "url":"/esop/toolkit/DownloadProxy/69341?verify=15\u0026oid=31068\u0026fileId=8276",
            "descripcion":"VISITA DE OBRA",
            "comentarios":"",
            "fecha_modificacion":"29/12/2010 04:39 PM"
         }
      ]
   },
   "url":"https://compranet.hacienda.gob.mx/esop/toolkit/opportunity/opportunityDetail.do?opportunityId=2\u0026oppList=PAST",
   "id_compranet":2,
   "timestamp":1492819628
}
```
