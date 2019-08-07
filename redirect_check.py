import requests
import csv
import urllib3
import sys
import urllib.parse as urlparse
import argparse
import logging
import os
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAX_REDIRECTS = 10

def check_redirect(req_session, source_url, target_url, logger, auth=None):
  result = []
  redirect_chain = []
  if target_url[-1] == '/':
    target_url = target_url[:-1]

  # processing the query string in order to reattach it to the target_url
  # source_parsed = urlparse.urlparse(source_url)
  # source_query_string = source_parsed.query
  # target_parsed = urlparse.urlparse(source_url)
  # target_query_string = target_parsed.query
  # if source_query_string and target_query_string:
  #   target_url = target_url + '?' + query_string

  # print(target_url)
  try:
    req = req_session.get(source_url, allow_redirects=True, verify=False, auth=auth)

    if len(req.history) != 0:
      for res in req.history:
        Location = res.headers['Location']
        # print(Location)
        redirect_chain.append(Location)
        if Location == target_url:
          result.append(res.status_code)
          result.append('yes')
          # print('Redirect matches the list.')
          # print(f'Redirect status code: {res.status_code}')
      if not result:
        result = ['n/a', 'no']
      result.append(redirect_chain)
    else:
      result = [req.status_code, 'no', [f'No redirects found']]
  except (requests.exceptions.TooManyRedirects) as e:
    # print(f'Error while processing source url: {source_url}. Error details: {e}')
    logger.error(f'Error while processing source url: {source_url}', exc_info=True)
    result = ['n/a', 'no', [f'Exeeded {MAX_REDIRECTS} redirects']]
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
  with open(file_name, newline='') as input_csvfile:
    reader = csv.reader(input_csvfile, delimiter=',', quotechar='"')
    with open(output_file, 'w', newline='') as output_csvfile:
      writer = csv.writer(output_csvfile, delimiter=',', 
                          quotechar='"', quoting=csv.QUOTE_MINIMAL)
      writer.writerow(['Source Url', 'Target Url', 'Redirect Code', 
                      'Redirect Ok', 'Redirect Chain'])
      for idx, row in enumerate(reader):
        if not args.no_header:
          if idx == 0:
            continue
        # print(f'Checking: {row[0]}')
        result = check_redirect(s, row[0], row[1], logger, auth)
        # print(f'status_code: {result[0]}, matches: {result[1]}, chain: {"|".join(result[2])}')
        logger.info(f'status_code: {result[0]}, matches: {result[1]}, source_url: "{row[0]}", chain: {"|".join(result[2])}')
        writer.writerow([row[0], row[1], result[0], result[1], '|'.join(result[2])])


if __name__ == '__main__':
    main()