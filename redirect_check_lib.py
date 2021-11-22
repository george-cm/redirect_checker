from typing import Callable, List, Tuple, Iterable
from requests_html import AsyncHTMLSession, HTMLResponse, requests
import logging

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
MAX_REDIRECTS = 10
SourceUrl = str
StatusCode = str
RedirectChain = str

def create_head_request(assession: AsyncHTMLSession, url: str, auth:Tuple[str, str]=None) -> Callable:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info(f'Adding request for {url}')
    async def head_request() -> Tuple[str, HTMLResponse]:
        logger.info(f"Making head request for {url}")
        try:
            r = await assession.head(url, verify=False, auth=auth, allow_redirects=True)
        except requests.exceptions.TooManyRedirects:
            return TooManyRedirectsResponse()
        except Exception as e:
            logger.exception(e)
            raise e
        else:
            logger.info(f"Returning response for {url}")
            return url, r
    return head_request

def request_head_urls(urls: Iterable[str]) -> List[Tuple[str, HTMLResponse]]:
    assession = AsyncHTMLSession()
    assession.max_redirects = MAX_REDIRECTS
    coros = [create_head_request(assession, url) for url in urls]
    responses = assession.run(*coros)
    return responses

def check_redirect(response: Tuple[str, HTMLResponse]) -> Tuple[SourceUrl, StatusCode, RedirectChain]:
    redirect_chain = []
    if len(response[1].history) != 0:
        for res in response[1].history:
            Location = res.headers['Location'].rstrip('/')
            redirect_chain.append(f"{res.status_code}::{Location}")
        if len(response[1].history) == 1:
            status_code = res.status_code
        else:
            status_code = 'multiple'
        result = (response[0], status_code, '|'.join(redirect_chain))
    else:
        result = (response[0], response[1].status_code, '')
    return result

class TooManyRedirectsResponse(requests.Response):

    def __init__(self):
        self.status_code = 'too many redirects'
        self.history = []

class EmptySourceUrlResponse(requests.Response):

    def __init__(self):
        self.status_code = 'source url is missing'
        self.history = []

def get_logger(log_file=None):
    if not log_file:
        log_file = f"{__file__}.log"
    # prepare the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    # checking if a log file was passed as argument
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # adding logging to the terminal (stdout)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(formatter)
    logger.addHandler(consoleHandler)
    logger.propagate = False
    return logger


def main():
    pass


logger = get_logger()

if __name__ == "__main__":
    main()