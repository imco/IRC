package main

import (
	"log"
	"os"
	"strings"

	"github.com/headzoo/surf/browser"

	"fmt"

	"strconv"

	_ "net/http/pprof"
	"net/url"

	"flag"

	"net/http"

	"crypto/tls"

	"github.com/PuerkitoBio/goquery"
	"github.com/headzoo/surf/agent"
	"github.com/headzoo/surf/jar"
	"github.com/jbowtie/gokogiri"
	xx "github.com/jbowtie/gokogiri/xml"
	"gopkg.in/headzoo/surf.v1"
)

const (
	sourceTabla   = "formTabla:tabla:0:atenderBtn"
	sourceRender  = "formTabla:tabla consulta:pnlBuscar consulta:growl"
	sourceBtn     = "formTabla:tabla:0:atenderBtn"
	renderDialog  = "formTabla:rupcDialogId"
	atenderHeader = "formTabla:tabla:0:atenderBtn"
	formTabla     = "formTabla"
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

func openFile(name string) *os.File {
	file, err := os.OpenFile(name, os.O_WRONLY|os.O_APPEND|os.O_CREATE, 0644)
	if err != nil {
		log.Fatalf("could not open file: %v", err)
	}
	return file
}

type CustomBrowser struct {
	Browser *browser.Browser
}

func CreateBrowser(url string) (*CustomBrowser, error) {
	// var c *CustomBrowser
	b, err := getNewBrowserWithSession(url)
	if err != nil {
		return nil, err
	}
	c := new(CustomBrowser)
	c.Browser = b
	return c, nil
}

func getDefaultHeaderVals(source, render string) url.Values {
	u := make(url.Values)
	u.Set("javax.faces.partial.ajax", "true")
	u.Set("javax.faces.source", source)
	u.Set("javax.faces.partial.execute", "@all")
	u.Set("javax.faces.partial.render", render)
	return u

}

func (c *CustomBrowser) MakePost(session string, pURL string, urlValues url.Values) (*xx.XmlDocument, string, error) {
	idSession := session
	if session == "" {
		c.Browser.Find("[name=\"javax.faces.ViewState\"]").Each(func(i int, s *goquery.Selection) {
			// fmt.Println(s.Attr("value"))
			idSession, _ = s.Attr("value")
		})
	}
	urlValues.Set("javax.faces.ViewState", idSession)
	urlValues.Encode()
	cookie := c.Browser.SiteCookies()
	// fmt.Println("JSESSIONID=" + cookie[0].Value)
	// browser.AddRequestHeader("Cookie", "JSESSIONID="+cookie[0].Value)
	headers := http.Header{}
	headers.Set("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
	headers.Set("Cache-Control", "no-cache")
	headers.Set("Cookie", "JSESSIONID="+cookie[0].Value)
	headers.Set("Connection", "keep-alive")
	headers.Set("Faces-Request", "partial/ajax")
	headers.Set("Referer", "https://cnet.hacienda.gob.mx/servicios/consultaRUPC.jsf")
	headers.Set("Host", "cnet.hacienda.gob.mx")
	headers.Set("Origin", "https://cnet.hacienda.gob.mx")
	headers.Set("Accept", "application/xml, text/xml, */*; q=0.01")
	headers.Set("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36")
	c.Browser.SetHeadersJar(headers)

	err := c.Browser.PostForm(pURL, urlValues)
	if err != nil {
		return nil, "", err
	}

	xml := c.Browser.Body()
	xml = "<?xml version='1.0' encoding='UTF-8'?>" + xml
	doc, err := gokogiri.ParseXml([]byte(xml))
	if err != nil {
		return nil, "", err
	}
	return doc, idSession, nil

}

func getHtmlFromXml(doc *xx.XmlDocument, query string) (html *goquery.Document, err error) {
	d, err := doc.Search(query)
	if err != nil {
		return nil, err
	}
	for c := d[0].FirstChild(); c != nil; c = c.NextSibling() {

		x, _ := c.Search("//table")
		if len(x) > 0 {
			html, err = goquery.NewDocumentFromReader(strings.NewReader(x[0].String()))
			if err != nil {
				fmt.Println("error" + err.Error())
			}
			break
		}
	}
	return html, nil
}

func main() {
	const CompranetURL = "https://cnet.hacienda.gob.mx/servicios/consultaRUPC.jsf"
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

	browser, err := CreateBrowser(CompranetURL)
	if err != nil {
		log.Panic(err)
		// fmt.Println("HOLA TODO EXPLOTOO")
	}
	urlValues := getDefaultHeaderVals(sourceTabla, sourceRender)
	urlValues.Set("consulta:btnBuscar", "consulta:btnBuscar")
	urlValues.Set("consulta:rfc", "MAN9209143V1")
	urlValues.Set("consulta", "consulta")
	urlValues.Set("consulta:tipoSol_input", "1")
	doc, session, err := browser.MakePost("", CompranetURL, urlValues)
	defer doc.Free()
	if err != nil {
		fmt.Println()
	}

	urlValues = getDefaultHeaderVals(sourceBtn, renderDialog)
	urlValues.Set(atenderHeader, atenderHeader)
	urlValues.Set(formTabla, formTabla)
	doc, session, err = browser.MakePost(session, CompranetURL, urlValues)
	defer doc.Free()

	html, _ := getHtmlFromXml(doc, "//update[@id='formTabla:rupcDialogId']")

	fmt.Println(html.Html())
}

func writeLastToLog(file *os.File, last int) {
	s := strconv.Itoa(last)
	file.WriteString(s + "\n")
}

// getNewBrowserWithSession returns a new surf Browser object, a new cookie jar and
// Firefox as the default userAgent
func getNewBrowserWithSession(url string) (bow *browser.Browser, err error) {

	bow = surf.NewBrowser()
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	}
	bow.SetTransport(tr)
	bow.SetCookieJar(jar.NewMemoryCookies())
	err = bow.Open(url)
	if err != nil {
		return nil, err
	}
	bow.SetUserAgent(agent.Firefox())
	return bow, nil
}
