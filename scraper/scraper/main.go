package main

import (
	"bufio"
	"log"
	"os"

	"github.com/headzoo/surf/browser"

	"fmt"

	"time"

	"strconv"

	_ "net/http/pprof"

	"flag"

	"github.com/headzoo/surf/agent"
	"github.com/headzoo/surf/jar"
	"gopkg.in/headzoo/surf.v1"
)

// ScrapErr es un wrapper de error para controlar casos donde
// Compranet esté abajo y no funcione
type ScrapErr struct {
	remoteError bool
	msg         string
}

func (s *ScrapErr) Error() string {
	return fmt.Sprintf("scrap: %s; remoteError: %t", s.msg, s.remoteError)
}

// getExpedienteData accede a la URL del expediente dentro de CompraNet. Regresa un Expediente
// con todos los elementos de la página que no son tablas
func getExpedienteData(id int, expURL string, browser *browser.Browser) (*Expediente, error) {
	if err := browser.Open(expURL); err != nil { //intentar abrir la URL del expediente, regresar custom error
		errMsg := fmt.Sprintf("could not open %s, error: %v", expURL, err)
		return nil, &ScrapErr{true, errMsg}
	}
	qnaRaw := browser.Find("#cntDetail .form_container ul li") //Elementos que NO son tablas
	exp, err := GetNewExpediente(qnaRaw)                       //Intenta obtener los datos del expediente
	if err != nil {
		return nil, fmt.Errorf("no data for %d", id)
	}
	//Asignar al exp la url actual
	exp.URL = expURL
	exp.IDCompranet = id
	return exp, nil
}

func openFile(name string) *os.File {
	file, err := os.OpenFile(name, os.O_WRONLY|os.O_APPEND|os.O_CREATE, 0644)
	if err != nil {
		log.Fatalf("could not open file: %v", err)
	}
	return file
}

func scrape(idCompranet int, htmlDir string, browser *browser.Browser, outFile *os.File, logFile *os.File) (int, error) {
	expedienteURL := fmt.Sprintf("https://compranet.hacienda.gob.mx/esop/toolkit/opportunity/opportunityDetail.do?opportunityId=%d&oppList=PAST", idCompranet)
	exp, err := getExpedienteData(idCompranet, expedienteURL, browser)
	if err != nil {
		return idCompranet, err
	} else {
		// toca obtener las tablas y datos faltantes
		tables := browser.Find("table")
		exp.AddTables(tables)
		exp.FechaScrap = time.Now().Unix() //timestamp para saber el momento exacto de extracción
		jstring := string(exp.ToJson())    //construye el JSON que se va a guardar en el outFile
		outFile.WriteString(jstring + "\n")
		err = exp.SaveRawHTML(browser, htmlDir) //almacenamos el HTML sin procesar
		if err != nil {
			log.Printf("no puedo escribir el archivo HTML: %v", err)
		}
		writeLastToLog(logFile, idCompranet) //y llevamos registro de lo último que se pudo guardar
		time.Sleep(2 * time.Second)          //TODO: encontrar intervalo random para que compranet no explote
		log.Printf("ended exp: %d", idCompranet)
	}

	return idCompranet, nil
}

// startScrapping extrae los expedientes de compranet. Requiere como parametros el id de expediente inicial, el
// expediente final, el directorio de salida de los archivos HTML, un surf browser, y archivos de salida y de logeo.
// En caso de error al regenerar una nueva sesión, regresa un error y el último expediente extraido
func startScrapping(ids []int, htmlDir string, browser *browser.Browser, outFile *os.File, logFile *os.File) (int, error) {
	var lastRead int
	var err error

	newSession := false
	// loop principal de scraping
	for i, idCompranet := range ids {
		lastRead, err = scrape(idCompranet, htmlDir, browser, outFile, logFile)
		if err != nil { //En caso que falle compranet por algun motivo
			if _, ok := err.(*ScrapErr); ok { //revisar que el tipo del error sea uno nuestro
				return lastRead, err
			}
			newSession = true
			log.Printf("error: %v", err) //No se obtuvieron datos para ese id
		}

		// reiniciar browser despues de 100 requests
		if i%100 == 0 || newSession {
			log.Println("getting new session")
			time.Sleep(10 * time.Second)
			browser, err = getNewBrowserWithSession("https://compranet.hacienda.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
			if err != nil {
				return lastRead, fmt.Errorf("no puedo abrir la pagina: %v", err)
			}
			newSession = false
		}
	}

	return lastRead, nil
}

func main() {

	//TODO: utlizar urfave/cli para manejar flag y línea de comandos

	//definicion de flags y de valores iniciales
	var startVal int
	var endVal int
	var ids []int
	flag.IntVar(&startVal, "inicio", 1, "valor de expediente inicial")
	flag.IntVar(&endVal, "fin", 1209999, "valor de expediente final")
	idsFilename := flag.String("ids", "undef", "archivo [opcional] con lista de ids")
	flag.Parse()

	// Construye lista para scrapear en base a un archivo
	// o a una secuencia de ids de startVal a endVal
	if *idsFilename != "undef" {
		fmt.Println("cargando lista de ids de archivo")
		f, err := os.Open(*idsFilename)
		if err != nil {
			log.Fatal(err)
		}

		s := bufio.NewScanner(f)
		for s.Scan() {
			val, err := strconv.Atoi(s.Text())
			if err != nil {
				log.Fatal(err)
			}

			ids = append(ids, val)
		}

		// Para que podamos romper el loop infinito
		// NOTA: Asume que no hay duplicados en la lista
		endVal = ids[len(ids)-1]
	} else if endVal < startVal {
		log.Fatal("el valor de inicio debe ser menor al del final")
	} else {
		// Rango inclusivo [startVal, endVal]
		ids = make([]int, endVal-startVal+1)
		for i := range ids {
			ids[i] = startVal + i
		}
	}

	outputFile := openFile("data.json")
	defer outputFile.Close()

	logFile := openFile("log.out")
	defer logFile.Close()

	rawHTMLFolder := "htmls"
	os.Mkdir(rawHTMLFolder, 0777)

	browser, err := getNewBrowserWithSession("https://compranet.hacienda.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
	if err != nil {
		log.Fatalf("no puedo abrir la pagina: %v", err)
	}
	lastRead := startVal

	//Loop infinito de scrapeo
	for {
		lastRead, err = startScrapping(ids, rawHTMLFolder, browser, outputFile, logFile)
		if err != nil { //En caso de error, dormir 120 segundos y reintentar
			log.Printf("could not continue scraping, %v, sleeping for 120 seconds", err)
			time.Sleep(120 * time.Second)
			browser, _ = getNewBrowserWithSession("https://compranet.hacienda.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
			log.Printf("restarting from %d", lastRead)
			startVal = lastRead
		}
		if lastRead == endVal {
			break
		}

	}

}

func writeLastToLog(file *os.File, last int) {
	s := strconv.Itoa(last)
	file.WriteString(s + "\n")
}

// getNewBrowserWithSession returns a new surf Browser object, a new cookie jar and
// Firefox as the default userAgent
func getNewBrowserWithSession(url string) (bow *browser.Browser, err error) {
	bow = surf.NewBrowser()
	bow.SetCookieJar(jar.NewMemoryCookies())
	err = bow.Open(url)
	if err != nil {
		return nil, err
	}
	bow.SetUserAgent(agent.Firefox())
	return bow, nil
}
