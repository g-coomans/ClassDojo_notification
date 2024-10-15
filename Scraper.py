import requests
from requests.exceptions import HTTPError, InvalidSchema
from requests.adapters import HTTPAdapter, Retry
import abc

class Scraper():
    def __init__(self, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                                "Accept-Language": "en-US,en;q=0.5",
                                "Accept-Encoding": "gzip, deflate",
                                "Connection": "keep-alive",
                                "Upgrade-Insecure-Requests": "1",
                                "Sec-Fetch-Dest": "document",
                                "Sec-Fetch-Mode": "navigate",
                                "Sec-Fetch-Site": "none",
                                "Sec-Fetch-User": "?1",
                                "Cache-Control": "max-age=0",
                                }, verify=True) -> None:
        self.conn = requests.Session()
        retries = Retry(total=5,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])

        self.conn.mount('http://', HTTPAdapter(max_retries=retries))
        self.conn.mount('https://', HTTPAdapter(max_retries=retries))
        self.verify = verify
        self.conn.headers = headers        
            
    def _request_url(self, url):
        try:
            response = self.conn.get(url, verify=self.verify)
            response.raise_for_status()  # If the response was succesful, no Exception will be raised                
        except HTTPError as http_err:
            print(f'HTTP error occured : {http_err}')
#         except Exception as err:
#             print(f'Other error occured ("URL" try): {err}')
        
        return response
    
    def get_page(self, url):
        try:
            page = self._request_url(url)
            
            return page
        except InvalidSchema as err:
            with open(url,'r',encoding="utf8") as f:
                page = f.read()
                
            return page
        except Exception as err:
            print(f'Other error occured: {err}')
            return False

    @abc.abstractmethod
    def get_list_entries(self, url:str):
        """ Get a list of data which need to be scraped """
        raise NotImplementedError
    
    @abc.abstractmethod
    def extract_data(self, brut_data:str):
        """ Get data from a specific entry."""
        raise NotImplementedError
