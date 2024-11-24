import asyncio
import requests
import time
import json

def read_proxy() -> str:
    with open('proxy.json', 'r') as f:
        return json.load(f)[0]['proxy']


def creat_requests(set_proxy: bool=None):
    if set_proxy:
        set_proxy = read_proxy()

    request = requests.get('https://api.ipify.org', proxies=set_proxy)
    return f"{'proxy' if set_proxy else 'clear'} -> " + request.text


async def requests_with_proxy():
    await asyncio.sleep(3)
    return creat_requests(True)


async def requests_with_out_proxy():
    return creat_requests()


print(time.strftime('%X'))

loop = asyncio.get_event_loop()
tasks = []
task1 = loop.create_task(requests_with_proxy())
task2 = loop.create_task(requests_with_out_proxy())
tasks.append(task1)
tasks.append(task2)

loop.run_until_complete(asyncio.wait(tasks))

print(time.strftime('%X'))
