package catchup_html_test

import (
	"fmt"
	"net/http"
	"net/url"

	"golang.org/x/net/html"
)

func getAllDownloadTagsFromHTML(htmlNode *html.Node, tag, class string, foundTags *[]*html.Node) bool {
	if htmlNode.Type == html.ElementNode && htmlNode.Data == tag {
		for _, attr := range htmlNode.Attr {
			if attr.Key == "class" && attr.Val == class {
				*foundTags = append(*foundTags, htmlNode)
				return false
			}
		}
	}
	for child := htmlNode.FirstChild; child != nil; child = child.NextSibling {
		getAllDownloadTagsFromHTML(child, tag, class, foundTags)
	}

	if len(*foundTags) == 0 {
		return false
	}
	return true
}

func getAllDownloadURLs(query url.Values) string {
	resp, err := http.PostForm(arxivURL, query) // post request
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close() // close connection

	body, err := html.Parse(resp.Body)
	if err != nil {
		panic(err)
	}

	if body.Type != html.ElementNode || body.Data != "html" {
		for child := body.FirstChild; child != nil; child = child.NextSibling {
			if child.Type == html.ElementNode && child.Data == "html" {
				body = child
				break
			}
		}
	}

	var spanTags []*html.Node
	getAllDownloadTagsFromHTML(body, "span", "list-identifier", &spanTags)

	for _, spanTag := range spanTags {
		fmt.Println(spanTag.FirstChild.FirstChild.Data)
	}
	return ""
}

// func main() {
// 	query := map[string][]string{
// 		"archive": {"hep-th"},
// 		"sday":    {"09"},
// 		"smonth":  {"07"},
// 		"syear":   {"2023"},
// 		"method":  {"without"},
// 	}
// 	getAllDownloadURLs(query)
// }

const arxivURL = "http://export.arxiv.org/catchup"
