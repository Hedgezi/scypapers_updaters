"""
This script downloads all papers from the arXiv API from a given date to the present.

:author: Mykola Vorontsov
:date: 20 July 2023
"""

import time
import feedparser
import requests
import logging
from concurrent.futures import ThreadPoolExecutor, Future

from arxiv_config import *


def download_paper(url: str, file_name: str):
    """
    Download a paper from the arXiv API.

    :param url: URL of the paper
    :param file_name: Name of the file to save the paper to
    """
    response = requests.get(url)
    if response.status_code != 200:
        logging.critical(f'Error: {response.status_code} on file {file_name}.')
        return

    # Determine file extension, because it is not always present in file header
    if response.headers['Content-Type'] == 'application/x-eprint-tar':
        file_name = file_name + '.tar'
    elif response.headers['Content-Type'] == 'application/pdf':
        file_name = file_name + '.pdf'
    elif response.headers['Content-Type'] == 'application/x-eprint':
        file_name = file_name + '.tex'

    with open(file_name, 'wb') as f:
        f.write(response.content)

    response.close()

    logging.info(f'File {file_name} downloaded.')


def download_all_entries_from_feed(feed: feedparser.FeedParserDict, previous_date: time.struct_time,
                                   thread_pool_executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=10)
                                   ) -> list[Future]:
    """
    Download all papers from a given feed.

    :param feed: Feed to download papers from
    :param previous_date: Date, when DB was last updated
    :param thread_pool_executor: ThreadPoolExecutor for querying new downloads
    :return: List of downloads futures
    """
    download_futures = []

    for entry in feed.entries:
        if entry.updated_parsed < previous_date:
            break

        link_split: list[str] = entry.id.split('/')
        cur_paper_link: str = link_split[-1]  # link to paper
        for segment in link_split[-2::-1]:
            # legacy arXiv links contains name of category before ID; for example http://arxiv.org/abs/astro-ph/0701212
            if segment == 'abs':
                break
            cur_paper_link = segment + '/' + cur_paper_link

        download_futures.append(thread_pool_executor.submit(download_paper,
                                                            "https://arxiv.org/e-print/{0}".format(cur_paper_link),
                                                            cur_paper_link.replace('/', '')))

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
    thread_pool_executor = ThreadPoolExecutor(max_workers=max_parallel_downloads)
    download_futures = []
    request_iter = 0

    while True:
        response = requests.get(CATCHUP_URL, params={
            'search_query': f'cat:{category}',
            'sortBy': 'lastUpdatedDate',
            'sortOrder': 'descending',
            'max_results': str(max_results),
            'start': request_iter * max_results
        })
        if response.status_code != 200:
            print(f'Error: {response.status_code}')
            return

        new_download_futures = download_all_entries_from_feed(feedparser.parse(response.text), previous_date,
                                                              thread_pool_executor)
        download_futures.extend(new_download_futures)
        # if there are fewer results than max_results, then we collected every paper after our update date
        if len(new_download_futures) < max_results:
            break

        request_iter += 1

    for future in download_futures:
        future.result()
    thread_pool_executor.shutdown()


if __name__ == '__main__':
    time_to_test = (2023, 8, 14, 17, 0, 0, 0, 226, 0)
    logging.basicConfig(level=logging.INFO)
    get_all_previous_papers_from_api(time.struct_time(time_to_test), 'cs.AI', MAX_ENTRIES_PER_REQUEST,
                                     MAX_PARALLEL_DOWNLOADS)
