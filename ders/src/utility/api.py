import requests
import json

class API:
    def __init__(self, base_url, headers=None, auth=None, cookies=None):
        self.base_url = base_url
        self.headers = headers
        self.auth = auth
        self.cookies = cookies

    def get(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, headers=self.headers, auth=self.auth, cookies=self.cookies)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, json=data, headers=self.headers, auth=self.auth, cookies=self.cookies)
        response.raise_for_status()
        return response.json()
    def __repr__(self):
        return f"<baseUrl={self.base_url}, headers={self.headers}, auth={self.auth}, cookies={self.cookies}>"