package main

import (
	"fmt"

	"github.com/PuerkitoBio/goquery"
	"github.com/headzoo/surf/jar"
	"gopkg.in/headzoo/surf.v1"
)

func main() {
	// doc, err := goquery.NewDocument("https://compranet.funcionpublica.gob.mx/esop/toolkit/opportunity/opportunityList.do")

	// if err != nil {
	// 	log.Fatal(err)
	// }

	// doc.Find("body").Each(func(index int, item *goquery.Selection) {

	// 	fmt.Printf("item %s", item.Text())
	// })

	bow := surf.NewBrowser()
	bow.SetCookieJar(jar.NewMemoryCookies())
	err := bow.Open("https://compranet.funcionpublica.gob.mx/esop/guest/go/public/opportunity/past?locale=es_MX")
	if err != nil {
		panic(err)
	}
	fmt.Println(bow.Title())
	// fmt.Printf("%+v", bow.Dom())
	bow.Dom().Each(func(i int, s *goquery.Selection) {
		fmt.Println(s.Text())
	})

}
