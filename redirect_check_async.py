import requests
import csv
# import urllib3
import sys
import urllib.parse as urlparse
import argparse
import logging
import os
from datetime import datetime
import chardet
from requests_html import AsyncHTMLSession
from pprint import pprint

# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

MAX_REDIRECTS = 10


class TooManyRedirectsResponse(requests.Response):
    
    def __init__(self):
      self.status_code = 'too many redirects'
      self.history = []

too_many_redirects_reponse = TooManyRedirectsResponse()

def detect_encoding(fname):
    import chardet
    rawdata = open(fname, 'rb').read()
    result = chardet.detect(rawdata)
    charenc = result['encoding']
    return charenc

def check_redirect(response, source_url, target_url):
  result = []
  redirect_chain = []
  target_url = target_url.rstrip('/')
  if len(response.history) != 0:
    for res in response.history:
      Location = res.headers['Location'].rstrip('/')
      redirect_chain.append(f"{res.status_code}::{Location}")
    if len(response.history) == 1:
      if response.history[-1].headers['Location'].rstrip('/') == target_url:
        result.append(res.status_code)
        result.append('yes')
      else:
        result.append(res.status_code)
        result.append('no')
    else:
      if response.history[-1].headers['Location'].rstrip('/') == target_url:
        result.append('multiple')
        result.append('yes')
      else:
        result.append('multiple')
        result.append('no')

      # print(Location)
        # print('Redirect matches the list.')
        # print(f'Redirect status code: {res.status_code}')
    # if not result:
    #   result = ['n/a', 'no', []]
    result.append(redirect_chain)
  else:
    result = [response.status_code, 'no', [f'No redirects found']]  
  return result

def main():
  parser = argparse.ArgumentParser(description="""Check a list of redirects mapped from a source url to a target url.
The input must be a CSV file containing two colums: source url and target url.
The output file will be saved in the same directory as the input file and the
output file name will be <input_filename>_YYYYMMDDhhmmss.csv""",
epilog="""""", formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument("file_name", help="name of the CSV file to be processed")
  parser.add_argument("-H", "--no-header-row", help="use when the input CSV file doesn't contain a header row", action='store_true', dest='no_header')  
  parser.add_argument("-l", "--log-file", help="name of the log file", default='', dest='log_file')
  parser.add_argument("-u", "--username", help="username for simple HTTP authentication", dest='username')
  parser.add_argument("-p", "--password", help="password for simple HTTP authentication", dest='password')
  args = parser.parse_args()
  
  if args.file_name is not None and args.file_name[-3:] == "csv":    
    file_name = args.file_name
  else:
    print('You need to provide a CSV file containing two columns: frist the source url, second the target url')
    sys.exit(1)
  if not os.path.isfile(file_name):
    print('File does not exist')
    sys.exit(1)

  # preparing the logger
  logger = logging.getLogger(__name__)
  logger.setLevel(logging.INFO)

  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

  # checking if a log file was passed as argument
  if args.log_file != '':
    log_file = args.log_file
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

  # adding logging to the terminal (stdout)
  consoleHandler = logging.StreamHandler()
  consoleHandler.setLevel(logging.INFO)
  consoleHandler.setFormatter(formatter)
  logger.addHandler(consoleHandler)

  # s = requests.Session()
  asession = AsyncHTMLSession()
  asession.max_redirects = MAX_REDIRECTS

  # async def one():
  #   r = await asession.get('https://safety.honeywell.com/en-us/products/by-category/gas-and-flame-detection/high-tech-and-government-systems/transportable-analyzers/chemkey-tld-toxic-gas-detector')
  #   return r

  # async def two():
  #   r = await asession.get('https://safety.honeywell.com/en-us/products/by-brand/honeywell/cf7000-series-abrasive-blast-respirator')
  #   return r
  # async def three():
  #   r = await asession.get('https://safety.honeywell.com/en-us/products/by-brand/honeywell/cf2000-series-supplied-air-for-tight-fitting-facepieces')
  #   return r

  # results = asession.run(one, two, three)
  # print(results)
  # sys.exit(1)
  auth = (args.username, args.password)

  output_file = file_name[:-4] + '_' + '{:%Y%m%d%H%M%S}'.format(datetime.now()) + '.csv'
  # for csv_file in csv_files:
  
  concurrent_requests = 100

  enc = detect_encoding(file_name)
  with open(file_name, encoding=enc) as input_csvfile:
    total_lines = sum(1 for line in input_csvfile)
    if not args.no_header:
      total_lines -=1

  with open(file_name, encoding=enc) as input_csvfile:
    reader = csv.reader(input_csvfile, delimiter=',', quotechar='"')
    with open(output_file, 'w', encoding=enc, newline='') as output_csvfile:
      writer = csv.writer(output_csvfile, delimiter=',', 
                          quotechar='"', quoting=csv.QUOTE_MINIMAL)
      writer.writerow(['Source Url', 'Target Url', 'Redirect Code', 
                      'Redirect Ok', 'Redirect Chain'])
      
      get_next_batch = get_next_n(concurrent_requests)
      
      if not args.no_header:
        header = next(reader)
      for n_elements in get_next_batch(reader):
        req_pool = []
        for row in n_elements:
          req_pool.append(create_request(asession, row[0], row[1]))
        # print(req_pool)
        responses = asession.run(*req_pool)
        for response in responses:
          result = check_redirect(*response)
          # print(f'status_code: {result[0]}, matches: {result[1]}, chain: {"|".join(result[2])}')
          logger.info(f'status_code: {result[0]}, matches: {result[1]}, source_url: "{response[1]}", chain: {"|".join(result[2])}')
          writer.writerow([response[1], response[2], result[0], result[1], '|'.join(result[2])])
          # if result:
          #   logger.info(f"{result[0]}::{result[1].status_code}::{result[1].url}")
          # else:
          #   logger.error(f"Error occured")
  # print(enc)

def get_next_n(n):
  def _getnext_n(reader):
    while True:
      n_elements = []
      for i in range(n):
        try:
          el = next(reader)
        except StopIteration:
          if n_elements:
            yield n_elements
            return
          else:
            return
        n_elements.append(el)
      yield n_elements
  return _getnext_n


def create_request(asession, source_url, target_url):
  async def _req():
    try:
      r = await asession.get(source_url, verify=False)
      return r, source_url, target_url
    except requests.exceptions.TooManyRedirects:
      return too_many_redirects_reponse, source_url, target_url
  return _req

if __name__ == "__main__":
  import timeit
  from datetime import timedelta
  print(str(timedelta(seconds=timeit.timeit(main, number=1))))