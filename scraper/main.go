package main

import (
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

// startScrapping extrae los expedientes de compranet. Requiere como parametros el id de expediente inicial, el
// expediente final, el directorio de salida de los archivos HTML, un surf browser, y archivos de salida y de logeo.
// En caso de error al regenerar una nueva sesión, regresa un error y el último expediente extraido
func startScrapping(startExp, endExp int, htmlDir string, browser *browser.Browser, outFile *os.File, logFile *os.File) (int, error) {
	if endExp < startExp {
		return 0, fmt.Errorf("el valor de inicio debe ser menor al del final")
	}
	newSession := false
	// loop principal de scraping
	for idCompranet := startExp; idCompranet <= endExp; idCompranet++ {
		expedienteURL := fmt.Sprintf("https://compranet.funcionpublica.gob.mx/esop/toolkit/opportunity/opportunityDetail.do?opportunityId=%d&oppList=PAST", idCompranet)
		exp, err := getExpedienteData(idCompranet, expedienteURL, browser)
		if err != nil { //En caso que falle compranet por algun motivo
			if _, ok := err.(*ScrapErr); ok { //revisar que el tipo del error sea uno nuestro
				// log.Printf("remote error: %v", sc)
				return idCompranet, err
			}
			newSession = true
			log.Printf("error: %v", err) //No se obtuvieron datos para ese id
			// return idCompranet, err
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
		// reiniciar browser despues de 100 requests
		if idCompranet%100 == 0 || newSession {
			log.Println("getting new session")
			time.Sleep(10 * time.Second)
			browser, err = getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
			if err != nil {
				return idCompranet, fmt.Errorf("no puedo abrir la pagina: %v", err)
			}
			newSession = false

		}

	}

	return endExp, nil
}

func main() {

	//TODO: utlizar urfave/cli para manejar flag y línea de comandos

	//definicion de flags y de valores iniciales
	var startVal int
	var endVal int
	flag.IntVar(&startVal, "inicio", 1, "valor de expediente inicial")
	flag.IntVar(&endVal, "fin", 1209999, "valor de expediente final")
	flag.Parse()

	//
	outputFile := openFile("data.json")
	defer outputFile.Close()

	logFile := openFile("log.out")
	defer logFile.Close()

	rawHTMLFolder := "htmls"
	os.Mkdir(rawHTMLFolder, 0777)

	browser, err := getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
	if err != nil {
		log.Fatalf("no puedo abrir la pagina: %v", err)
	}
	lastRead := startVal

	//Loop infinito de scrapeo
	for {
		lastRead, err = startScrapping(startVal, endVal, rawHTMLFolder, browser, outputFile, logFile)
		if err != nil { //En caso de error, dormir 120 segundos y reintentar
			log.Printf("could not continue scraping, %v, sleeping for 120 seconds", err)
			time.Sleep(120 * time.Second)
			browser, _ = getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
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
