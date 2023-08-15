package main

import (
	"encoding/xml"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/korovkin/limiter"
)

type Entry struct {
	ID        string `xml:"id"`
	Updated   string `xml:"updated"`
	Published string `xml:"published"`
	Title     string `xml:"title"`
}

type Feed struct {
	XMLName xml.Name `xml:"feed"`
	Entry   []Entry  `xml:"entry"`
}

func downloadArxivEntry(id string) {
	resp, err := http.Get(arxivDownloadUrl + id)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	fileBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}

	if resp.Header.Get("Content-Type") == "application/x-eprint-tar" {
		id += ".tar"
	} else if resp.Header.Get("Content-Type") == "application/pdf" {
		id += ".pdf"
	} else if resp.Header.Get("Content-Type") == "application/x-eprint" {
		id += ".tex"
	}

	fileErr := os.WriteFile(id, fileBytes, 0644)
	if fileErr != nil {
		panic(fileErr)
	}
	fmt.Println("Downloaded", id)
}

func getArxivXmlResponse(query url.Values) ([]byte, error) {
	req, err := http.NewRequest(http.MethodGet, arxivApiUrl, nil)
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

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return []byte{}, err
	}

	return respBody, nil
}

func getArxivPapersFromOneFeed(xmlResp []byte, oldTime time.Time, downloadLimiter *limiter.ConcurrencyLimiter) (bool, error) {
	var feed Feed
	if downloadLimiter == nil {
		downloadLimiter = limiter.NewConcurrencyLimiter(maxGoroutines)
	}

	err := xml.Unmarshal(xmlResp, &feed)
	if err != nil {
		return false, err
	}

	for _, entry := range feed.Entry {
		updatedTime, err := time.Parse(time.RFC3339, entry.Updated)
		if err != nil {
			return false, err
		}
		if updatedTime.Before(oldTime) {
			return false, nil
		}

		Id := entry.ID
		downloadLimiter.Execute(func() {
			downloadArxivEntry(strings.Split(Id, "/")[4])
		})
	}

	return true, nil
}

func getArxivAllNewPapers(oldTime time.Time) {
	start := 0
	query := url.Values(map[string][]string{
		"search_query": {"cat:cs.ai"},
		"sortBy":       {"lastUpdatedDate"},
		"sortOrder":    {"descending"},
		"max_results":  {fmt.Sprint(maxResults)},
		"start":        {fmt.Sprint(start)},
	})
	downloadLimiter := limiter.NewConcurrencyLimiter(maxGoroutines)
	toContinue := true

	for toContinue {
		query.Set("start", fmt.Sprint(start))
		resp, err := getArxivXmlResponse(query)
		if err != nil {
			panic(err)
		}

		toContinue, err = getArxivPapersFromOneFeed(resp, oldTime, downloadLimiter)
		if err != nil {
			panic(err)
		}

		start += maxResults
	}

	downloadLimiter.WaitAndClose()
}

func main() {
	oldTime := time.Date(2023, 8, 10, 14, 0, 0, 0, time.UTC)

	getArxivAllNewPapers(oldTime)
}

const arxivApiUrl = "https://export.arxiv.org/api/query"
const arxivDownloadUrl = "https://export.arxiv.org/e-print/"
const maxGoroutines = 25
const maxResults = 5
