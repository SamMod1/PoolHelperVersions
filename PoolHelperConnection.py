import requests
from pandas import read_csv
from io import StringIO



class PoolHelperConnection:
    def __init__(self, username, password, pool_helper_url):
        self.username = username
        self.password = password
        self.url = pool_helper_url
        
        if not self.url[-1] == '/':
            self.url += '/'
        
        self.login_url = self.url + 'accounts/login/'
        self.query_url = self.url + 'Pool-Helper/db-api/'
        
        self.client = None
        self.csrftoken = None
        
        self.login(username, password)
        
    
    def login(self, username, password):
        self.username = username
        self.password = password
        self.client = requests.session()
        self.client.get(self.login_url)
        self.csrftoken = self.client.cookies['csrftoken']
        login_info = {'username': username, 'password': password, 'csrfmiddlewaretoken': self.csrftoken}
        self.client.post(self.login_url, data=login_info)
        self.csrftoken = self.client.cookies['csrftoken']
        
    def query(self, query):
        query = {'query': query, 'csrfmiddlewaretoken': self.csrftoken}
        response = self.client.post(self.query_url, data=query)
        self.csrftoken = self.client.cookies['csrftoken']
        return response.text
    
    def pd_query(self, query, colnames = None):
        response = self.query(query)[1:-1]
        response = response.replace(')(', '\n')
        df = read_csv(StringIO(response), usecols=colnames)
        return df
