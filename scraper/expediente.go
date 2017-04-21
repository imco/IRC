package main

import (
	"encoding/json"
	"html/template"
	"io"
	"strings"

	"fmt"

	"strconv"

	"os"

	"github.com/PuerkitoBio/goquery"
	"github.com/headzoo/surf/browser"
)

type Expediente struct {
	Codigo             string     `json:"codigo"`
	Descripcion        string     `json:"descripcion"`
	Referencia         string     `json:"referencia"`
	Tipo               string     `json:"tipo"`
	Categorias         string     `json:"categorias"`
	DescripcionAnuncio string     `json:"descripcion_anuncio"`
	Notas              string     `json:"notas"`
	TipoContratacion   string     `json:"tipo_contratacion"`
	Entidad            string     `json:"entidad"`
	FechaPublicacion   string     `json:"fecha_publicacion"`
	FechaUltima        string     `json:"fecha_ultima_actualizacion"`
	PlazoParticipacion string     `json:"plazo_participacion"`
	FechaInicio        string     `json:"fecha_inicio_contrato"`
	Duracion           string     `json:"duracion_contrato"`
	FechaConcl         string     `json:"fecha_conclusion"`
	UC                 string     `json:"unidad_compradora"`
	NombreOperador     string     `json:"nombre_operador"`
	Email              string     `json:"email"`
	Web                string     `json:"web"`
	TablasA            tablaA     `json:"tabla_datos"`
	TablaProc          tablaProc  `json:"tabla_procedimientos"`
	TablaAnexo         tablaAnexo `json:"tabla_anexos"`
	URL                string     `json:"url"`
	IDCompranet        int        `json:"id_compranet"`
	FechaScrap         int64      `json:"timestamp"`
}

type tablaA struct {
	Rows []rowTablaA `json:"rows"`
}

type tablaProc struct {
	Rows []rowTablaProc `json:"rows"`
}

type tablaAnexo struct {
	Rows []rowTablaAnexo `json:"rows"`
}

type rowTablaAnexo struct {
	Fila               int    `json:"num"`
	NombreArchivo      string `json:"archivo"`
	UrlArchivo         string `json:"url"`
	DescripcionArchivo string `json:"descripcion"`
	Comentarios        string `json:"comentarios"`
	FechaMod           string `json:"fecha_modificacion"`
}

const (
	tablaAnexoFila = iota
	tablaAnexoArchivo
	tablaAnexoDescripcion
	tablaAnexoComentarios
	tablaAnexoFechaMod
)

type rowTablaProc struct {
	Fila        int    `json:"num"`
	Status      string `json:"status"`
	Titulo      string `json:"titulo"`
	FechaLimite string `json:"fecha_limite"`
}

const (
	tablaProcFila = iota
	tablaProcStatus
	tablaProcTitulo
	tablaProcFecha
)

type rowTablaA struct {
	Visible     string `json:"visible"`
	Etiqueta    string `json:"etiqueta"`
	Descripcion string `json:"descripcion"`
	Valor       string `json:"valor"`
	UrlArchivo  string `json:"url"`
	DescArchivo string `json:"archivo"`
}

const (
	tablaAVisible = iota
	tablaAEtiqueta
	tablaADescripcion
	tablaAValor
)

type answer struct {
	question string
	value    string
}

const (
	Codigo             = "Código del Expediente"
	Descripcion        = "Descripción del Expediente"
	Referencia         = "Referencia del Expediente"
	Tipo               = "Tipo de Expediente"
	Categorias         = "Categorias del Expediente"
	DescripcionAnuncio = "Descripción del Anuncio"
	Notas              = "Notas"
	TipoContratacion   = "Tipo de Contratación"
	Entidad            = "Entidad Federativa"
	FechaPublicacion   = "Fecha de publicación del anuncio (Convocatoria / Invitación / Adjudicación / Proyecto de Convocatoria)"
	FechaUltima        = "Fecha de la última publicación del Anuncio:"
	PlazoParticipacion = "Plazo de participación o vigencia del anuncio"
	FechaInicio        = "Fecha de Inicio del Contrato"
	Duracion           = "Duración del Contrato"
	FechaConcl         = "Fecha estimada de conclusión del contrato"
	UC                 = "Nombre de la Unidad Compradora (UC)"
	NombreOperador     = "Nombre del Operador en la UC"
	Email              = "Correo Electrónico del Operador en la UC"
	Web                = "Enlace Web"
)

type QuestionAndAnswer map[string]answer

const expedienteTemplate = `{{define "expediente"}}
	Codigo: 		{{.Codigo}}
	Descripcion:  		{{.Descripcion}}
	Referencia: 		{{.Referencia}}
	Tipo: 			{{.Tipo}}
	Categorias: 		{{.Categorias}}
	-----------
	DescAnuncio: 		{{.DescripcionAnuncio}}
	Notas: 			{{.Notas}}
	Tipo Contratacion: 	{{.TipoContratacion}}
	Entidad: 		{{.Entidad}}
	Fecha Publicacion:	{{.FechaPublicacion}}
	Fecha Ultima: 		{{.FechaUltima}}
	Plazo: 			{{.PlazoParticipacion}}
	Fecha Inicio: 		{{.FechaInicio}}
	Duracion Contrato: 	{{.Duracion}}
	Fecha Conclusion: 	{{.FechaConcl}}
	-----------
	Unidad Compradora: 	{{.UC}}
	Operador: 		{{.NombreOperador}}
	Email: 			{{.Email}}
	Web: 			{{.Web}}
	-----------
	URL:			{{.URL}}
	{{end}}
	`

func GetNewExpediente(rawqn *goquery.Selection) (*Expediente, error) {
	answers, err := joinQA(rawqn)
	if err != nil {
		return nil, fmt.Errorf("no data for ID")
	}
	exp := Expediente{
		Codigo:             answers[Codigo].value,
		Descripcion:        answers[Descripcion].value,
		Referencia:         answers[Referencia].value,
		Tipo:               answers[Tipo].value,
		Categorias:         answers[Categorias].value,
		DescripcionAnuncio: answers[DescripcionAnuncio].value,
		Notas:              answers[NombreOperador].value,
		TipoContratacion:   answers[TipoContratacion].value,
		Entidad:            answers[Entidad].value,
		FechaPublicacion:   answers[FechaPublicacion].value,
		FechaUltima:        answers[FechaUltima].value,
		PlazoParticipacion: answers[PlazoParticipacion].value,
		FechaInicio:        answers[FechaInicio].value,
		Duracion:           answers[Duracion].value,
		FechaConcl:         answers[FechaConcl].value,
		UC:                 answers[UC].value,
		NombreOperador:     answers[NombreOperador].value,
		Email:              answers[Email].value,
		Web:                answers[Web].value,
	}
	return &exp, nil
}

func joinQA(s *goquery.Selection) (map[string]answer, error) {
	// qamap := make(map[string]string)
	if s.Size() == 0 {
		fmt.Println("EMPTY DATA")
		return nil, fmt.Errorf("no data for that id")
	}
	qna := getNewQnA()
	s.Each(func(i int, a *goquery.Selection) {
		question := strings.TrimSpace(a.Find(".form_question").Text())
		answer := a.Find(".form_answer").Text()

		tempA := qna[question]
		tempA.value = strings.TrimSpace(answer)
		qna[question] = tempA

	})
	return qna, nil
}

func (e *Expediente) AddTables(tables *goquery.Selection) {
	// fmt.Println(tables.Size())
	// var tabla1 *goquery.Selection
	tables.Each(func(i int, t *goquery.Selection) {
		switch t.Children().First().Text() {
		case "Lista de Información Adicional de la Oportunidad":
			var tA tablaA
			// tA.Header = "Lista de Información Adicional de la Oportunidad"
			t.Find("tr").Each(func(j int, tr *goquery.Selection) {
				var row rowTablaA
				tr.Find("td").Each(func(k int, td *goquery.Selection) {
					switch k {
					case tablaAVisible:
						attrText, _ := td.Find("img").Attr("title")
						row.Visible = attrText
					case tablaAEtiqueta:
						row.Etiqueta = td.Text()
					case tablaADescripcion:
						row.Descripcion = td.Text()
					case tablaAValor:
						row.Valor = td.Text()
						file, hasFile := td.Find("a").Attr("href")
						if hasFile {
							row.UrlArchivo = file
						}
					}
				})
				tA.Rows = append(tA.Rows, row)
			})
			e.TablasA = tA
		case "Procedimiento":
			var tProc tablaProc
			t.Find("tr").Each(func(j int, tr *goquery.Selection) {
				var row rowTablaProc
				tr.Find("td").Each(func(k int, td *goquery.Selection) {
					switch k {
					case tablaProcFila:
						row.Fila, _ = strconv.Atoi(td.Text())
					case tablaProcStatus:
						row.Status, _ = td.Find("img").Attr("title")
					case tablaProcTitulo:
						row.Titulo = td.Text()
					case tablaProcFecha:
						row.FechaLimite = strings.TrimSpace(td.Text())
					}
				})
				tProc.Rows = append(tProc.Rows, row)

			})
			e.TablaProc = tProc
		case "Anexos":
			var tAnexo tablaAnexo
			t.Find("tr").Each(func(j int, tr *goquery.Selection) {
				var row rowTablaAnexo
				tr.Find("td").Each(func(z int, td *goquery.Selection) {
					switch z {
					case tablaAnexoFila:
						row.Fila, _ = strconv.Atoi(td.Text())
					case tablaAnexoArchivo:
						file, hasFile := td.Find("a").Attr("href")
						if hasFile {
							row.UrlArchivo = file
						}
						row.NombreArchivo = td.Text()
					case tablaAnexoDescripcion:
						row.DescripcionArchivo = td.Text()
					case tablaAnexoComentarios:
						row.Comentarios = td.Text()
					case tablaAnexoFechaMod:
						row.FechaMod = td.Text()
					}
				})
				tAnexo.Rows = append(tAnexo.Rows, row)
			})
			e.TablaAnexo = tAnexo
		}

	})
}

func (e *Expediente) Print(writer io.Writer) {
	report := template.Must(template.New("expediente").Parse(expedienteTemplate))
	report.Execute(writer, e)
}

func (e *Expediente) ToJson() []byte {
	jsonExp, _ := json.Marshal(e)
	return jsonExp
}

func (e *Expediente) SaveRawHTML(browser *browser.Browser, dir string) error {
	html := browser.Body()
	// e.Print(os.Stdout)
	id := strconv.Itoa(e.IDCompranet)
	file, err := os.OpenFile(dir+"/"+id+".html", os.O_CREATE|os.O_WRONLY, 0644)
	defer file.Close()
	if err != nil {
		return fmt.Errorf("could not create file: %v", err)
	}
	file.WriteString(html)
	return nil
}

func getNewQnA() map[string]answer {
	var qna = map[string]answer{
		Codigo:             answer{Codigo, ""},
		Descripcion:        answer{Descripcion, ""},
		Referencia:         answer{Referencia, ""},
		Tipo:               answer{Tipo, ""},
		Categorias:         answer{Categorias, ""},
		DescripcionAnuncio: answer{DescripcionAnuncio, ""},
		Notas:              answer{Notas, ""},
		TipoContratacion:   answer{TipoContratacion, ""},
		Entidad:            answer{Entidad, ""},
		FechaPublicacion:   answer{FechaPublicacion, ""},
		FechaUltima:        answer{FechaUltima, ""},
		PlazoParticipacion: answer{PlazoParticipacion, ""},
		FechaInicio:        answer{FechaInicio, ""},
		Duracion:           answer{Duracion, ""},
		FechaConcl:         answer{FechaConcl, ""},
		UC:                 answer{UC, ""},
		NombreOperador:     answer{NombreOperador, ""},
		Email:              answer{Email, ""},
		Web:                answer{Web, ""},
	}
	return qna
}
