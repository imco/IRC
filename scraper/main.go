package main

import (
	"log"
	"os"

	"github.com/headzoo/surf/browser"

	"fmt"

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

func main() {

	browser, err := getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
	if err != nil {
		log.Fatalln(err.Error())
	}

	outputFile := openOutputFile("data.json")
	defer outputFile.Close()

	rawHTMLFolder := "htmls"
	os.Mkdir(rawHTMLFolder, 0777)

	for idCompranet := 0; idCompranet < 1; idCompranet++ {
		expedienteURL := fmt.Sprintf("https://compranet.funcionpublica.gob.mx/esop/toolkit/opportunity/opportunityDetail.do?opportunityId=%d&oppList=PAST", 900585)
		// if err := getExpedienteData(idCompranet, expedienteURL, browser); err != nil {
		// 	fmt.Println(err)
		// }
		exp, err := getExpedienteData(900585, expedienteURL, browser)
		if err != nil {
			log.Printf("error: %v", err)
		} else {
			// exp.Print(os.Stdout)
			tables := browser.Find("table")
			exp.AddTables(tables)
			jstring := string(exp.ToJson())
			outputFile.WriteString(jstring + "\n")
			err := exp.SaveRawHTML(browser, rawHTMLFolder)
			if err != nil {
				log.Fatal(err)
			}
		}

		// ioutil.WriteFile("output.json", exp.ToJson(), 0644)

	}

	// fmt.Printf("EXPEDIENTE == %v", exp)
	// var node []*html.Node

	// browser.
	// fmt.Println("--------------------------")
	// // fmt.Println(browser.Find("table").Length())
	// browser.Find("table").Each(func(i int, t *goquery.Selection) {
	// 	fmt.Printf("TABLA: %d\n", i)
	// 	section := 0
	// 	t.Find("tr").Each(func(j int, tr *goquery.Selection) {
	// 		section++
	// 		if tr.Children().First().Is("th") && tr.Children().Length() == 1 {
	// 			fmt.Println(tr.Text())
	// 		}
	// 	})
	// })
	// browser.Find("table tbody tr td").Each(func(i int, s *goquery.Selection) {
	// 	fmt.Printf("%d -----> %s\n", i, strings.TrimSpace(s.Text()))

	// })
	// //Save the full HTML body
	// fmt.Println(browser.Body())
	// fmt.Println(browser.Url())

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
	log.Printf("page title: %s", bow.Title())
	return bow, nil
}
