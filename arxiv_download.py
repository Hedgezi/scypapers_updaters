"""
This script downloads all papers from the arXiv API from a given date to the present.

:author: Mykola Vorontsov
:date: 20 July 2023
"""

import time
import feedparser
import requests
from concurrent.futures import ThreadPoolExecutor

from arxiv_vars import *


def download_paper(url: str, file_name: str):
    """
    Download a paper from the arXiv API.

    :param url: URL of the paper
    :param file_name: Name of the file to save the paper to
    """
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Error: {response.status_code}')
        return

    with open(file_name, 'wb') as f:
        f.write(response.content)

    print(f'Downloaded {file_name}!')


def download_all_entries_from_feed(feed: feedparser.FeedParserDict, previous_date: time.struct_time,
                                   max_parallel_downloads: int = 10) -> list:
    """
    Download all papers from a given feed.

    :param feed: Feed to download papers from
    :param previous_date: Date, when DB was last updated
    :param max_parallel_downloads: Maximum number of parallel downloads
    :return: List of futures of the downloads
    """
    download_futures = []

    for entry in feed.entries:
        if entry.updated_parsed < previous_date:
            return download_futures

        with ThreadPoolExecutor(max_workers=max_parallel_downloads) as executor:
            cur_paper_id: str = entry.id.split('/')[-1]
            download_futures.append(executor.submit(download_paper,
                                                    "https://arxiv.org/e-print/{0}".format(cur_paper_id),
                                                    cur_paper_id))

    return download_futures


def get_all_previous_papers_from_api(previous_date: time.struct_time, category: str, max_results: int = 100,
                                     max_parallel_downloads: int = 10):
    """
    Get all papers from the arXiv API from a given date to the present.

    :param previous_date: Date, when DB was last updated
    :param category: Category to search in
    :param max_results: Maximum number of results per request
    :param max_parallel_downloads: Maximum number of parallel downloads
    """
    download_futures = []
    request_iter = 0

    while True:
        response = requests.get(CATCHUP_URL, params={
            'search_query': f'cat:{category}',
            'sortBy': 'lastUpdatedDate',
            'sortOrder': 'descending',
            'max_results': str(max_results),
            'start': request_iter*max_results
        })
        if response.status_code != 200:
            print(f'Error: {response.status_code}')
            return

        new_download_futures = download_all_entries_from_feed(feedparser.parse(response.text), previous_date,
                                                              max_parallel_downloads)
        download_futures.extend(new_download_futures)
        if len(new_download_futures) < max_results:
            break

        request_iter += 1

    for future in download_futures:
        future.result()


if __name__ == '__main__':
    time_to_test = (2023, 7, 18, 17, 30, 0, 0, 199, 0)
    get_all_previous_papers_from_api(time.struct_time(time_to_test), 'cs.CV', MAX_ENTRIES_PER_REQUEST,
                                     MAX_PARALLEL_DOWNLOADS)
