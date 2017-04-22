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

func getExpedienteData(id int, expURL string, browser *browser.Browser) (*Expediente, error) {
	if err := browser.Open(expURL); err != nil {
		return nil, fmt.Errorf("could not open %s, error: %v", expURL, err)
	}
	qnaRaw := browser.Find("#cntDetail .form_container ul li")
	exp, err := GetNewExpediente(qnaRaw)
	if err != nil {
		return nil, fmt.Errorf("no data for %d", id)
	}
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

func startScrapping(startExp, endExp int, htmlDir string, browser *browser.Browser, outFile *os.File, logFile *os.File) (int, error) {
	if endExp < startExp {
		return 0, fmt.Errorf("el valor de inicio debe ser menor al del final")
	}

	for idCompranet := startExp; idCompranet <= endExp; idCompranet++ {
		expedienteURL := fmt.Sprintf("https://compranet.funcionpublica.gob.mx/esop/toolkit/opportunity/opportunityDetail.do?opportunityId=%d&oppList=PAST", idCompranet)
		exp, err := getExpedienteData(idCompranet, expedienteURL, browser)
		if err != nil {
			log.Printf("error: %v", err) //No se obtuvieron datos
		} else {
			tables := browser.Find("table")
			exp.AddTables(tables)
			exp.FechaScrap = time.Now().Unix()
			jstring := string(exp.ToJson())
			outFile.WriteString(jstring + "\n")
			err := exp.SaveRawHTML(browser, htmlDir)
			if err != nil {
				log.Printf("no puedo escribir el archivo HTML: %v", err)
			}
			writeLastToLog(logFile, idCompranet)
			time.Sleep(2 * time.Second)
			log.Printf("ended exp: %d", idCompranet)
		}

		// reiniciar browser despues de 100 requests
		if idCompranet%100 == 0 {
			log.Println("getting new session")
			browser, err = getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
			if err != nil {
				return idCompranet, fmt.Errorf("no puedo abrir la pagina: %v", err)
			}

		}

		// browser, _ = getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
		// if err != nil {
		// 	log.Fatalf("no puedo abrir la pagina: %v", err)
		// }

	}

	return endExp, nil
}

func main() {

	// app := cli.NewApp()

	// app.Flags = []cli.Flag {
	// 	cli.StringFlag{
	// 		Name: "outfile"
	// 	}
	// }

	// app.Name = "compranet expedientes scraper"
	// app.Usage = "obtiene los expedientes de compranet"
	// app.Action = func(c *cli.Context) error {
	// 	fmt.Println("running from CLI")
	// 	return nil
	// }

	// app.Run(os.Args)
	var startVal int
	var endVal int
	flag.IntVar(&startVal, "inicio", 1, "valor de expediente inicial")
	flag.IntVar(&endVal, "fin", 1209999, "valor de expediente final")
	flag.Parse()

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

	for {
		lastRead, err := startScrapping(lastRead, endVal, rawHTMLFolder, browser, outputFile, logFile)
		if err != nil {
			log.Printf("could not continue scraping, %v, sleeping for 60 seconds", err)
			time.Sleep(60 * time.Second)
			browser, _ = getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
			log.Printf("restarting from %d", lastRead)
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
