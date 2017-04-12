package main

import (
	"fmt"
	"log"
	"math/rand"
	"os"
	"regexp"
	"strconv"
	"strings"

	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/headzoo/surf/jar"
	"gopkg.in/headzoo/surf.v1"
)

func main() {
	idFile, err := os.OpenFile("ids", os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0666)
	if err != nil {
		panic(err)
	}

	defer idFile.Close()

	bow := surf.NewBrowser()
	bow.SetCookieJar(jar.NewMemoryCookies())
	ferr := bow.Open("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
	if ferr != nil {
		panic(ferr)
	}
	fmt.Println(bow.Title())
	// fmt.Printf("%+v", bow.Dom())
	// bow.Dom().Each(func(i int, s *goquery.Selection) {
	// 	fmt.Println(s.Text())
	// })
	// TODO: revisar REGEXP
	idRegexp, _ := regexp.Compile("([0-9]+)', ")
	totalPaginasRegexp, _ := regexp.Compile("([0-9]+)")
	totalCountRaw := strings.TrimSpace(bow.Find("div#allButtons_nav1").Text())
	log.SetOutput(os.Stdout)
	// fmt.Println(totalPaginasRegexp.MatchString(totalPaginas))
	// fmt.Println(totalPaginasRegexp.FindAllString(totalPaginas, -1))
	totalCount, err := strconv.Atoi(totalPaginasRegexp.FindAllString(totalCountRaw, -1)[0])
	if err != nil {
		log.Println(err)
	}
	fmt.Printf("TOTAL DOCS: %d\n", totalCount)

	for currentPage := 1; currentPage < 53558; currentPage++ {
		log.Printf("PAGINA %d", currentPage)

		bow.Dom().Find("td.col__fixed_ a").Each(func(i int, s *goquery.Selection) {
			// fmt.Println(s.Attr("onclick"))
			idText, _ := s.Attr("onclick") // JS attr con el ID
			id := idRegexp.FindStringSubmatch(idText)
			log.Println(id[1]) //TODO: fix regexp == finds the ID to navigate
			if _, err = idFile.WriteString(id[1] + "\n"); err != nil {
				log.Printf("could not print: %v", err)
			}
		})
		frm, err := bow.Form("#cntList form") //encuentra la forma de la tabla
		if err != nil {
			log.Fatalf("could not find the form: %v", err)
		}
		currentPage++

		frm.Input("listManager.pagerComponent.page", strconv.Itoa(currentPage))
		sleepTimer := randomTimer()
		log.Printf("durmiendo por: %d segundos", sleepTimer)
		time.Sleep(time.Duration(sleepTimer) * time.Second)
		if frm.Submit() != nil {
			panic(err)
		}

	}

}

func randomTimer() int {
	rand.Seed(time.Now().Unix())
	return rand.Intn(6-1) + 1
}
