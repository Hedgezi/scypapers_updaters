import requests
import gzip
import bibtexparser


ACL_ANTHOLOGY_URL = "https://aclanthology.org/anthology.bib.gz"


def get_acl_anthology():
    mid = bibtexparser.bibdatabase.Middlewares()
    r = requests.get(ACL_ANTHOLOGY_URL)
    r.raise_for_status()
    # print('\n'.join(gzip.decompress(r.content).decode("utf-8").split("\n")[646730:646755]))
    acl_bibtex = bibtexparser.parse_string(gzip.decompress(r.content).decode("utf-8"))
    # print(acl_bibtex.entries)

if __name__ == "__main__":
    get_acl_anthology()
