import pytest
from redirect_check_lib import (
    request_head_urls,
    check_redirect,
    HTMLResponse,
    AsyncHTMLSession,
    requests,
    MAX_REDIRECTS,
)


@pytest.fixture(autouse=True, scope="session")
def disable_https_warnings():
    requests.packages.urllib3.disable_warnings(category=requests.packages.urllib3.exceptions.InsecureRequestWarning)  # type: ignore


request_head_urls_parameters = [
    ("https://httpbin.org/absolute-redirect/1", 302, "http://httpbin.org/get")
]
request_head_urls_parameters_many = [
    (
        ("https://httpbin.org/absolute-redirect/1", 302, "http://httpbin.org/get", 1),
        ("https://httpbin.org/absolute-redirect/2", 302, "http://httpbin.org/get", 2),
        ("https://httpbin.org/absolute-redirect/3", 302, "http://httpbin.org/get", 3),
        ("https://httpbin.org/absolute-redirect/4", 302, "http://httpbin.org/get", 4),
        ("https://httpbin.org/absolute-redirect/5", 302, "http://httpbin.org/get", 5),
        ("https://httpbin.org/absolute-redirect/6", 302, "http://httpbin.org/get", 6),
    )
]


class TestRequest_head_urls:
    def test_request_head_urls_0_redirects(self):
        url = "https://httpbin.org/get"
        status_code = 200
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == status_code
        assert len(result[1].history) == 0

    def test_request_head_urls_1_redirect(self):
        url = "https://httpbin.org/absolute-redirect/1"
        status_code = 302
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == 200
        assert len(result[1].history) == 1
        assert result[1].history[0].status_code == status_code
        assert result[1].history[0].headers["location"] == "http://httpbin.org/get"

    def test_request_head_urls_2_redirect(self):
        url = "https://httpbin.org/absolute-redirect/2"
        status_code = 302
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == 200
        assert len(result[1].history) == 2
        assert result[1].history[0].status_code == status_code
        assert (
            result[1].history[0].headers["location"]
            == "http://httpbin.org/absolute-redirect/1"
        )
        assert result[1].history[1].status_code == status_code
        assert result[1].history[1].headers["location"] == "http://httpbin.org/get"

    def test_request_head_urls_over_max_redirect(self):
        url = "https://httpbin.org/absolute-redirect/" + str(MAX_REDIRECTS + 1)
        status_code = "too many redirects"
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == status_code
        assert len(result[1].history) == 0


class TestCheckRedirect:
    def test_check_redirect_0_redirects(self):
        url = "https://httpbin.org/get"
        status_code = 200
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == status_code
        assert len(result[1].history) == 0
        checked_result = check_redirect(result)
        assert checked_result[0] == url
        assert checked_result[1] == 200
        assert checked_result[2] == ""

    def test_check_redirect_1_redirects(self):
        url = "https://httpbin.org/absolute-redirect/1"
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == 200
        assert len(result[1].history) == 1
        checked_result = check_redirect(result)
        assert checked_result[0] == url
        assert checked_result[1] == 302
        assert checked_result[2] == "302::http://httpbin.org/get"

    def test_check_redirect_2_redirects(self):
        url = "https://httpbin.org/absolute-redirect/2"
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == 200
        assert len(result[1].history) == 2
        checked_result = check_redirect(result)
        assert checked_result[0] == url
        assert checked_result[1] == "multiple"
        assert (
            checked_result[2]
            == "302::http://httpbin.org/absolute-redirect/1|302::http://httpbin.org/get"
        )

    def test_check_redirect_404(self):
        url = "https://httpbin.org/this-should-be-404"
        results = request_head_urls([url])
        assert len(results) == 1
        result = results[0]
        assert result[0] == url
        assert result[1].status_code == 404
        assert len(result[1].history) == 0
        checked_result = check_redirect(result)
        assert checked_result[0] == url
        assert checked_result[1] == 404
        assert checked_result[2] == ""
