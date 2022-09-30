# from curses.ascii import HT
from http.client import TOO_MANY_REQUESTS
from typing import Callable, List, Optional, Tuple, Iterable, Union
from unittest import removeResult
from requests_html import AsyncHTMLSession, HTMLResponse, requests
import logging
from dataclasses import dataclass, field

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=requests.packages.urllib3.exceptions.InsecureRequestWarning)  # type: ignore
MAX_REDIRECTS = 10
SourceUrl = str
StatusCode = Union[str, int]
RedirectChain = str

@dataclass()
class TooManyRedirectsResponse(HTMLResponse):
    status_code = 'too many redirects' # type: ignore
    history: Optional[list[HTMLResponse]] = field(default_factory=list)

@dataclass()
class EmptySourceUrlResponse(HTMLResponse):
    status_code = 'source url is missing' # type: ignore
    history: Optional[list[HTMLResponse]] = field(default_factory=list)

@dataclass()
class ConnectionErrorResponse(HTMLResponse):
    status_code = 'connection error' # type: ignore
    history: Optional[list[HTMLResponse]] = field(default_factory=list)

def create_head_request(assession: AsyncHTMLSession, url: str, auth:Optional[Tuple[str, str]]=None) -> Callable:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.info(f'Adding request for {url}')
    async def head_request() -> Tuple[str, HTMLResponse]:
        logger.info(f"Making head request for {url}")
        try:
            r = await assession.head(url, verify=False, auth=auth, allow_redirects=True)  # type: ignore
        except requests.exceptions.TooManyRedirects as e:
            logger.exception(e)
            return url, TooManyRedirectsResponse()
        except requests.exceptions.ConnectionError as e:
            logger.exception(e)
            return url, ConnectionErrorResponse()
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
            redirect_chain.append(f"{res.status_code}::{res.url}")
        if len(response[1].history) == 1:
            # status_code = response[1].status_code
            status_code = response[1].history[0].status_code
        else:
            status_code = 'multiple'
        redirect_chain.append(f"{response[1].status_code}::{response[1].url}")
        result = (response[0], status_code, '|'.join(redirect_chain))
    else:
        result = (response[0], response[1].status_code, '')
    return result


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