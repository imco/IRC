# Repositorio de datos abierto “¿Cómo identificar focos rojos en contrataciones públicas?”

Este repositorio de datos abiertos contiene las bases de datos y el código necesario para replicar los resultados presentados en el reporte “Riesgos de eficiencia y corrupción en las contrataciones públicas en México”. Este reporte tiene como objetivo evaluar el desempeño, tanto en el nivel de eficiencia, como en la mitigación de corrupción, de la unidades compradoras que forman parte del sistema de compras públicas en México.
Por su naturaleza, todos los documentos incluidos en el repositorio pueden ser utilizados y distribuidos libremente, sujeto a que declaren la autoría correspondiente.

Dentro del repositorio se encuentran tres apartados:
1. notebooks: Todos los scripts necesarios para limpiar, procesar y analizar las bases de datos
2. scraper: Documentación metodológica de cómo se llevó a cabo el web scraping de los procedimientos publicados en Compranet
(https://compranet.funcionpublica.gob.mx/web/login.html) 
3. Datos procesados: Conjunto de bases de datos que se utilizaron para la obtención de resultados

Por un lado, los apartados uno y dos se componen completamente de código almacenado en la plataforma GitHub. Esta plataforma permite descargar o clonar todo el código en tu computadora, subir o crear nuevos archivos, proponer mejoras o correcciones al proceso, entre otros. Por otro lado, el conjunto de datos procesados se conservan en un servicio de almacenamiento en la nube provisto por Amazon.

Actualmente, un repositorio abierto es la mejor herramienta para publicar los resultados de un proyecto de esta índole debido a los siguientes beneficios:

**Replicabilidad**: Cualquier persona tienen acceso a todos los documentos que fueron utilizados para el proyecto, esto asegura máxima transparencia en la obtención de resultados

**Cooperación**: Github es una comunidad de programadores, en donde más de 20 millones de usuarios participan activamente ayudándose unos a otros. De esta forma, el código está expuesto a ser mejorado por cualquier persona de la comunidad, fomentando la colaboración y la transmisión de conocimiento entre usuarios

**Fácil Acceso**: Toda persona en cualquier parte del mundo puede acceder a los archivos en el repositorio. Por lo tanto, podrá ser empleado para fines de investigación por todos aquellos interesados en analizar el proceso de contrataciones públicas en México

**Disponibilidad**: La información está disponible en cualquier momento y en cualquier lugar, sin riesgo a que exista pérdida de información y que ya no pueda ser recuperada

Esta serie de beneficios permite expandir el alcance del proyecto a prácticamente todo el mundo, lo cual genera beneficios en materia de rendición de cuentas y transparencia en los procesos de contrataciones públicas en México. Asimismo, es un primer paso para impulsar el análisis continuo de estos procesos, elemento esencial para mitigar los riesgos de corrupción en el uso del presupuesto público.


## Datos procesados
* [Procedimientos y contrataciones 2012-2017](https://s3-us-west-2.amazonaws.com/opi-compranet/public/data/procedimientos_all_2017_09_25.psv)
* [Participantes 2010 - 2017](https://s3-us-west-2.amazonaws.com/opi-compranet/public/data/participantes_2017_09_25.zip)
