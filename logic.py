import json
import re

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import openpyxl
from openpyxl import load_workbook
from openpyxl.writer.excel import save_workbook


def get_work_accounts():
    names = os.listdir('cookies')
    accounts = []
    for name in names:
        with open(f'cookies/{name}', 'r', encoding='utf-8') as f:
            accounts.append(json.load(f))

    return accounts


def swap_account(account: dict):
    with open(f'cookies.json', 'w', encoding='utf-8') as f:
        json.dump(account, f)


def read_proxy(sequence_number: int):
    """Получение прокси из файла"""

    # Получаем содержимое файла
    with open('proxy.json', 'r') as f:
        proxi = json.load(f)

    return proxi[sequence_number]['proxy']


def clean_out_excel():
    """Если есть выходной файл Excel удаляет его и создает новый"""
    if os.path.exists('Reels.xlsx') is True:
        os.remove('Reels.xlsx')

def read_setup() -> tuple:
    """Получает данные для парсинга"""
    with open('users_to_pars.txt', 'r', encoding='utf-8') as file:
        users = file.read().split('\n')

    view = int(users[0])
    users = users[1:]
    return view, users


def creat_out_excel():
    """Создает новый выходной Excel файл"""
    file_name = 'Reels.xlsx'
    wb = openpyxl.Workbook()
    wb.remove(wb['Sheet'])
    ws = wb.create_sheet('reels')
    ws.cell(row=1, column=1).value = 'ссылка'
    ws.cell(row=1, column=2).value = 'просмотров:'
    ws.cell(row=1, column=3).value = 'лайков:'
    ws.cell(row=1, column=4).value = 'комментов:'
    save_workbook(wb, file_name)


def wright_in_excel(reels, cur):
    """Записывает данные рилсов одного аккаунта"""
    wb = load_workbook('Reels.xlsx')
    ws = wb['reels']
    for reel in reels:
        ws.cell(row=cur, column=1).value = reel['url']
        ws.cell(row=cur, column=2).value = reel['play_count']
        ws.cell(row=cur, column=3).value = reel['like_count']
        ws.cell(row=cur, column=4).value = reel['comment_count']
        cur += 1
    save_workbook(wb, 'Reels.xlsx')
    return cur


def load_cookies() -> dict:
    """Загружает куки"""
    with open('cookies.json', 'r', encoding='utf-8') as f:
        cookies = json.load(f)

    return {item['name']: item['value'] for item in cookies}


def load_patterns():
    """Загружает потерны"""
    with open('patterns.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def param_from_html(html: str) -> dict:
    """Получаем аргументы из html"""
    args = {
        'x_bloks_version_id': r'."versioningID":"(.*?)"',
        'lsd': r'"LSD",.*?,."token":"(.*?)"',
        'app_id': r',"APP_ID":"(.*?)"',
        'av': r'actorID":"(.*?)"',
        'rev': r'"rev":(.*?).,',
        '__hsi': r',"hsi":"(.*?)"',
        'fb_dtsg': r'."DTSGInitialData",..,."token":"(.*?)"',
        'jazoest': r'&jazoest=(.*?)"',
        '__spin_r': r'"__spin_r":(.*?),',
        '__spin_b': r',"__spin_b":"(.*?)",',
        '__spin_t': r',"__spin_t":(.*?),',
        'target_id': r'"target_id":"(.*?)"'
    }

    try:
        for parm in args:
            new = re.search(args[parm], html, flags=re.DOTALL | re.MULTILINE).group(1)
            args[parm] = new

        return {'ok': True, 'args': args}
    except Exception as e:
        return {'ok': False, 'msg': str(e)}


def insert_params_in_headers(parameters: dict, referer) -> dict:
    """Вставляем аргументы в headers запроса"""
    patterns = load_patterns()
    cookies = load_cookies()
    headers_for_reels = patterns['headers_for_reels']
    headers_for_reels['referer'] = referer
    headers_for_reels['x-bloks-version-id'] = parameters['x_bloks_version_id']
    headers_for_reels['x-csrftoken'] = cookies['csrftoken']
    headers_for_reels['x-fb-lsd'] = parameters['lsd']
    headers_for_reels['x-ig-app-id'] = parameters['app_id']
    return headers_for_reels


def insert_params_in_data(parameters: dict):
    """Вставляем аргументы в data запроса"""
    patterns = load_patterns()
    data = patterns['data_for_reels']
    for p in ['av', 'rev', '__hsi', 'fb_dtsg', 'jazoest', 'lsd', '__spin_r', '__spin_b', '__spin_t']:
        data[p] = parameters[p]

    data['variables'] = data['variables'].replace('userID', parameters['target_id'])

    return data


def insert_cur(data: dict, cur: str, user_id) -> dict:
    """обновляем курсор бд"""
    data['variables'] = (f'{{"after":"{cur}","before":null,"data":{{"include_feed_video":true,'
                         f'"page_size":12,"target_user_id":"{user_id}"}},"first":4,"last":null}}')
    return data


def data_headers(res, q_count):
    """Обработчик данных рилсов из ответа"""

    raw_data = res.json()['data']['xdt_api__v1__clips__user__connection_v2']['edges']
    valid_reels = []

    for n, video in enumerate(raw_data):
        video = video['node']['media']
        if video['play_count'] is not None:
            play_count = video['play_count']
        elif video['view_count'] is not None:
            play_count = video['view_count']
        else:
            play_count = 1

        if play_count >= q_count:
            reels = {'url': f'https://www.instagram.com/reel/{video['code']}',
                     'play_count': play_count}
            if 'like_count' in video:
                reels['like_count'] = video['like_count']
            if 'comment_count' in video:
                reels['comment_count'] = video['comment_count']
            valid_reels.append(reels)

    return valid_reels


def check_end(res):
    """Проверяет последний ли это срез"""
    res = res.json()['data']['xdt_api__v1__clips__user__connection_v2']['page_info']['has_next_page']
    if res:
        return False
    else:
        return True


def pars_account(account_name: str, q_count: int):
    """Прасинг всех видео с аккаунта"""

    # получаем все заголовки для запроса
    cookies = load_cookies()
    patterns = load_patterns()
    headers = patterns['headers_for_html']
    headers['referer'] = headers['referer'].replace('name', account_name)

    # сохраняем прокси
    proxies = read_proxy(0)

    # запрашиваем базовый html
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    response = session.get(f'https://www.instagram.com/{account_name}/reels/',
                           cookies=cookies, headers=headers, proxies=proxies)

    # проверяем статус ответа
    if response.status_code == 200:
        print('base html - ok', end='\r')
    if response.status_code in [560, 572]:
        return {'ok': False}

    # Если все ОК сохраняем страницу в переменной html
    html = response.text

    # Пробуем получить доп параметры для запроса рилсов
    parameters = param_from_html(html)
    if parameters['ok']:
        parameters = parameters['args']
    else:
        return {'ok': False, 'error': 'account'}
    headers = insert_params_in_headers(parameters, headers['referer'])
    data = insert_params_in_data(parameters)

    # создаем список для хранения валидных видео со страницы
    reels = []

    #Делаем запрос к api для получения первых 12ти видео
    response = session.post(
        'https://www.instagram.com/graphql/query',
        cookies=cookies, headers=headers, data=data, proxies=proxies)

    n = 1

    # Проверяем статус запроса
    if response.status_code == 200:
        print(f'Получено: {n*12} видео', end='\r')
    elif response.status_code in [560, 572]:
        return {'ok': False}
    else:
        return {'ok': False, 'error': response.status_code}

    try:
        response.json()
    except requests.exceptions.JSONDecodeError:
        return {'ok': False, 'error': 'json'}

    # Сохраняем валидные видео
    videos = data_headers(response, q_count)
    reels.extend(videos)

    # Проверяем конец-ли это
    if check_end(response):
        print(f'всего получено: {n * 12} видео, валидных: {len(reels)}')
        return {'ok': True, 'data': reels}

    while True:
        # Получаем курсор для следующего запроса
        cur = response.json()['data']['xdt_api__v1__clips__user__connection_v2']['page_info']['end_cursor']
        data = insert_cur(data, cur, parameters['target_id'])

        # Делаем запрос для получения следующих 12ти видео
        response = session.post(
            'https://www.instagram.com/graphql/query',
            cookies=cookies, headers=headers, data=data, proxies=proxies)


        # Проверяем статус запроса
        if response.status_code == 200:
            try:
                response.json()
            except requests.exceptions.JSONDecodeError:
                print(f'всего получено: {n * 12} видео, валидных: {len(reels)}')
                return {'ok': True, 'data': reels}
            n += 1
            print(f'Получено: {n * 12} видео')
        else:
            return {'ok': False, 'error': response.status_code}

        if 'errors' in response.json():
            print(f'всего получено: {n*12} видео, валидных: {len(reels)}')
            return {'ok': True, 'data': reels}

        elif 'data' in response.json():
            videos = data_headers(response, q_count)
            reels.extend(videos)
            if check_end(response):
                print(f'всего получено: {n * 12} видео, валидных: {len(reels)}')
                return {'ok': True, 'data': reels}


def update_setup(users, q_count):
    text = f'{q_count}\n'
    for name in users:
        text += f'{name}\n'
    with open('users_to_pars.txt', 'w', encoding='utf-8') as f:
        f.write(text)
