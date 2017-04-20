package main

import (
	"log"
	"os"

	"github.com/headzoo/surf/browser"

	"fmt"

	"io/ioutil"

	"github.com/headzoo/surf/jar"
	"gopkg.in/headzoo/surf.v1"
)

func getExpedienteData(id int, expURL string, browser *browser.Browser) error {
	if err := browser.Open(expURL); err != nil {
		return fmt.Errorf("could not open %s, error: %v", expURL, err)
	}
	qnaRaw := browser.Find("#cntDetail .form_container ul li")
	exp := GetNewExpediente(qnaRaw)
	exp.URL = expURL
	exp.Print(os.Stdout)
	ioutil.WriteFile("output.json", exp.ToJson(), 0644)
	return nil
}

func main() {

	browser, err := getNewBrowserWithSession("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
	if err != nil {
		log.Fatalln(err.Error())
	}
	expedienteURL := fmt.Sprintf("https://compranet.funcionpublica.gob.mx/esop/toolkit/opportunity/opportunityDetail.do?opportunityId=%d&oppList=PAST", 1)
	if err := getExpedienteData(0, expedienteURL, browser); err != nil {
		fmt.Println(err)
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
