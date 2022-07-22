"""Helper module"""
import requests

# fake headers
fake_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0)"
    " Gecko/20100101 Firefox/97.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_file_size(link: str, session: requests.Session = None) -> int:
    """Gets file size

    Args:
        link (str): downloadable file

    Returns:
        int: size of file
    """
    if not session:
        session = requests
    if link:
        r = session.head(
            url=link,
            headers=fake_headers,
            allow_redirects=True,
        )
        if r.ok and (size := r.headers.get("Content-Length", None)):
            return int(size)
    return 0
