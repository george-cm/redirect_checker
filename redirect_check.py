import requests
import csv
import urllib3
import sys
import urllib.parse as urlparse
import argparse
import logging
import os
from datetime import datetime
import chardet

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAX_REDIRECTS = 10

def detect_encoding(fname):
    import chardet
    rawdata = open(fname, 'rb').read()
    result = chardet.detect(rawdata)
    charenc = result['encoding']
    return charenc

def check_redirect(req_session, source_url, target_url, logger, auth=None, retries=30):
  result = []
  redirect_chain = []
  target_url = target_url.rstrip('/')
  # if target_url[-1] == '/':
  #   target_url = target_url[:-1]
  # processing the query string in order to reattach it to the target_url
  # source_parsed = urlparse.urlparse(source_url)
  # source_query_string = source_parsed.query
  # target_parsed = urlparse.urlparse(source_url)
  # target_query_string = target_parsed.query
  # if source_query_string and target_query_string:
  #   target_url = target_url + '?' + query_string

  # print(target_url)
  for retry in range(retries):
    try:
      # import pdb; pdb.set_trace()
      req = req_session.get(source_url, allow_redirects=True, verify=False, auth=auth)
      if len(req.history) != 0:
        for res in req.history:
          Location = res.headers['Location'].rstrip('/')
          redirect_chain.append(f"{res.status_code}::{Location}")
        if len(req.history) == 1:
          if req.history[-1].headers['Location'].rstrip('/') == target_url:
            result.append(res.status_code)
            result.append('yes')
          else:
            result.append(res.status_code)
            result.append('no')
        else:
          if req.history[-1].headers['Location'].rstrip('/') == target_url:
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
        result = [req.status_code, 'no', [f'No redirects found']]
    except (requests.exceptions.TooManyRedirects) as e:
      # print(f'Error while processing source url: {source_url}. Error details: {e}')
      logger.error(f'Error while processing source url: {source_url}', exc_info=True)
      result = ['n/a', 'no', [f'Exeeded {MAX_REDIRECTS} redirects']]
    except (requests.exceptions.ConnectionError) as e:
      if retry < (retries - 1):
        logger.warning(f'Connection Error while processing source url: {source_url}, retrying ({retry + 1})')
        continue
      else:
        logger.error(f'Connection Error while processing source url: {source_url}, retrying ({retry + 1})', exc_info=True)
        raise
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

  s = requests.Session()
  s.max_redirects = MAX_REDIRECTS

  auth = (args.username, args.password)

  output_file = file_name[:-4] + '_' + '{:%Y%m%d%H%M%S}'.format(datetime.now()) + '.csv'
  # for csv_file in csv_files:
  
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
      
      if not args.no_header:
        header = next(reader)
      for idx, row in enumerate(reader):
        # if not args.no_header:
        #   if idx == 0:
        #     continue
        # print(f'Checking: {row[0]}')
        result = check_redirect(s, row[0], row[1], logger, auth, 200)
        # print(f'status_code: {result[0]}, matches: {result[1]}, chain: {"|".join(result[2])}')
        logger.info(f'{idx+1}/{total_lines} status_code: {result[0]}, matches: {result[1]}, source_url: "{row[0]}", chain: {"|".join(result[2])}')
        writer.writerow([row[0], row[1], result[0], result[1], '|'.join(result[2])])
  # print(enc)


if __name__ == '__main__':
    main()