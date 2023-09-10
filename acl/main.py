"""
This script downloads the ACL Anthology corpus


"""
import gzip

import requests

ACL_ANTHOLOGY_URL = "https://aclanthology.org/anthology.bib.gz"


def get_all_acl_entries() -> list[str]:
    """This function returns all the urls of the ACL Anthology corpus
    from the ACL Anthology BibTex file

    Returns:
        list[str]: list of urls from the ACL Anthology corpus
    """
    r = requests.get(ACL_ANTHOLOGY_URL, timeout=60)
    r.raise_for_status()
    bibtex_file = gzip.decompress(r.content).decode("utf-8").split("\n")
    bibtex_file_iter = iter(bibtex_file)
    urls = []

    for line in bibtex_file_iter:
        if line.startswith("@inproceedings"):
            while True:
                line_strip = next(bibtex_file_iter).strip()
                if line_strip.startswith("}"):
                    break
                if line_strip.startswith("url"):
                    urls.append(
                        line_strip[line_strip.find('"') + 1 : line_strip.rfind('"')]
                    )
        else:
            continue

    return urls


if __name__ == "__main__":
    get_all_acl_entries()
