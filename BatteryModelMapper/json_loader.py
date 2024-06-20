import requests

class JSONLoader:
    @staticmethod
    def load(json_url):
        response = requests.get(json_url)
        response.raise_for_status()
        return response.json()
