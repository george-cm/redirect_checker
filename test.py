import redirect_check
import logging
import requests

# preparing the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# adding logging to the terminal (stdout)
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)

s = requests.Session()
s.max_redirects = 10


url = "https://www.uvex.us/error.htm?aspxerrorpath=/products/general%20purpose%20eyewear/uvex-hypershock/lens%20coatings"
target = "https://industrialsafety.honeywell.com/en-us/brands/uvex"


print(redirect_check.check_redirect(s, url, target, logger, True))