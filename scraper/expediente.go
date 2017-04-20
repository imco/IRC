package main

import (
	"encoding/json"
	"html/template"
	"io"
	"strings"

	"fmt"

	"github.com/PuerkitoBio/goquery"
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
	TablasA            []tablaA   `json:"tabla_a"`
	TablaProc          tablaProc  `json:"tabla_proc"`
	TablaAnexo         tablaAnexo `json:"tabla_anexo"`
	URL                string     `json:"url"`
	IDCompranet        int        `json:"id_compranet"`
}

type tablaA struct {
	Header string
	Rows   []rowTablaA
}

type tablaProc struct {
	Rows []rowTablaProc
}

type tablaAnexo struct {
	Rows []rowTablaAnexo
}

type rowTablaAnexo struct {
	Fila               int
	NombreArchivo      string
	UrlArchivo         string
	DescripcionArchivo string
	Comentarios        string
	FechaMod           string
}

type rowTablaProc struct {
	Fila        int
	Status      string
	Titulo      string
	FechaLimite string
}

type rowTablaA struct {
	Visible     string
	Etiqueta    string
	Descripcion string
	Valor       string
	UrlArchivo  string
	DescArchivo string
}

type answer struct {
	question string
	value    string
}

// const (
// 	Codigo =
// 	Descripcion =
// 	Referencia =
// 	Tipo =
// 	Categorias =
// 	DescripcionAnuncio =
// 	Notas =
// 	TipoContratacion =
// 	Entidad =
// 	FechaPublicacion =
// 	FechaUltima =
// 	PlazoParticipacion =
// 	FechaInicio =
// 	Duracion =
// 	FechaConcl =
// 	UC =
// 	NombreOperador =
// 	Email =
// 	Web =
// )
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

func (e *Expediente) Print(writer io.Writer) {
	report := template.Must(template.New("expediente").Parse(expedienteTemplate))
	report.Execute(writer, e)
}

func (e *Expediente) ToJson() []byte {
	jsonExp, _ := json.Marshal(e)
	return jsonExp
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
