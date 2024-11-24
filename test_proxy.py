from logic import read_proxy
import requests

r = requests.get('https://www.instagram.com', proxies=read_proxy(0))
print(r.status_code)
