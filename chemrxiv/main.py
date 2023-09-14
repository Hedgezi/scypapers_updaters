''' Download all papers from the chemrXiv API.

'''
import json
import logging
import sys
from datetime import datetime

import requests

API_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items"

LAST_LAUNCH = datetime(2023, 9, 10)
PER_PAGE = 2


def download_paper(url: str, filename: str):
    """
    Download a paper from the chemrXiv API.

    :param url: URL of the paper
    :param file_name: Name of the file to save the paper to
    """
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, "wb") as f:
        f.write(response.content)

    response.close()

    logging.info("File %s downloaded.", filename)


def download_one_page(json_page: dict):
    """
    Download all papers from one page of the chemrXiv API.
    """
    for item in json_page:
        item = item["item"]
        if datetime.strptime(item["statusDate"], "%Y-%m-%dT%H:%M:%S.%fZ") < LAST_LAUNCH:
            sys.exit(0)
        download_paper(item["asset"]["original"]["url"], item["asset"]["fileName"])


def download_all_pages():
    """
    Download all papers from the chemrXiv API.
    """
    i = 0
    while True:
        response = requests.get(
            API_URL,
            timeout=60,
            params={
                "sort": "PUBLISHED_DATE_DESC",
                "limit": PER_PAGE,
                "skip": PER_PAGE*i,
            },
        )
        response.raise_for_status()

        download_one_page(json.loads(response.content)["itemHits"])
        i += PER_PAGE


if __name__ == "__main__":
    download_all_pages()
