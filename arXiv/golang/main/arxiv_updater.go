package main

import (
	"encoding/xml"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/korovkin/limiter"
)

type Feed struct {
	XMLName xml.Name `xml:"feed"`
	Entry   []Entry  `xml:"entry"`
}

type Entry struct {
	ID        string `xml:"id"`
	Updated   string `xml:"updated"`
	Published string `xml:"published"`
	Title     string `xml:"title"`
}

func downloadArxivEntry(id string) {
	resp, err := http.Get("https://export.arxiv.org/e-print/" + id)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	fileBytes, err := ioutil.ReadAll(resp.Body)

	file := os.WriteFile(id, fileBytes, 0644)
	if file != nil {
		panic(file)
	}
	fmt.Println("Downloaded", id)
}

func getXMLResponse(query url.Values) ([]byte, error) {
	req, err := http.NewRequest(http.MethodGet, arxivURL, nil)
	if err != nil {
		return []byte{}, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.URL.RawQuery = query.Encode()

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return []byte{}, err
	}
	defer resp.Body.Close()

	respBody, err := ioutil.ReadAll(resp.Body)
	return respBody, nil
}

func main() {
	query := url.Values(map[string][]string{
		"search_query": {"cat:cs.ai"},
		"sortBy":       {"lastUpdatedDate"},
		"sortOrder":    {"descending"},
		"max_results":  {"200"},
		"start":        {"0"},
	})
	timeNow := time.Date(2023, 8, 1, 10, 0, 0, 0, time.UTC)

	resp, err := getXMLResponse(query)
	if err != nil {
		panic(err)
	}
	var feed Feed
	err = xml.Unmarshal(resp, &feed)
	if err != nil {
		panic(err)
	}
	for ind, entry := range feed.Entry {
		updatedTime, err := time.Parse(time.RFC3339, entry.Updated)
		if err != nil {
			panic(err)
		}
		if updatedTime.Before(timeNow) {
			fmt.Println("Updated before timeNow", ind)
			break
		}
	}

	limiter := limiter.NewConcurrencyLimiter(maxGoroutines)

	for _, entry := range feed.Entry[0:193] {
		entry := entry
		limiter.Execute(func() {
			downloadArxivEntry(strings.Split(entry.ID, "/")[4])
		})
	}
	limiter.WaitAndClose()
}

const arxivURL = "https://export.arxiv.org/api/query"
const maxGoroutines = 25
