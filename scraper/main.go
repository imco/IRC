package main

import (
	"log"
	"os"

	"github.com/headzoo/surf/browser"

	"fmt"

	"time"

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

func openOutputFile(name string) *os.File {
	file, err := os.OpenFile(name, os.O_WRONLY|os.O_APPEND|os.O_CREATE, 0644)
	if err != nil {
		log.Fatalf("could not open file: %v", err)
	}
	return file
}

func startScrapping(startExp, endExp int, outFile *os.File, htmlDir string, browser *browser.Browser) error {
	if endExp < startExp {
		return fmt.Errorf("el valor de inicio debe ser menor al del final")
	}

	for idCompranet := startExp; idCompranet < endExp; idCompranet++ {
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
		}

		// browser, _ = getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
		// if err != nil {
		// 	log.Fatalf("no puedo abrir la pagina: %v", err)
		// }

	}

	return nil
}

func main() {
	outputFile := openOutputFile("data.json")
	defer outputFile.Close()

	rawHTMLFolder := "htmls"
	os.Mkdir(rawHTMLFolder, 0777)

	browser, err := getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
	if err != nil {
		log.Fatalf("no puedo abrir la pagina: %v", err)
	}

	startScrapping(1, 5, outputFile, rawHTMLFolder, browser)

}

func openFile(fileName string) *os.File {
	file, err := os.Open(fileName)
	if err != nil {
		log.Fatalf("could not open file: %s", err.Error())
	}
	return file
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
