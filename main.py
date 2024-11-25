from logic import ParsAccountReels, read_setup
from logic import clean_out_excel, creat_out_excel, wright_in_excel
import time
import asyncio

# Читаем входные данные
q_view, users_for_pars = read_setup()
users_len = len(users_for_pars)
print(f'Загружено {45} рабочих акков')


# Обновляем старый выходной файл
clean_out_excel()
creat_out_excel()
excel_row = 2


def check(reels):
    global excel_row
    if reels['ok']:
        time.sleep(2)
        excel_row = wright_in_excel(reels['data'], excel_row)
        return True
    else:
        if 'error' in reels:
            if reels['error'] == 'account':
                print('Аккаунт закрытый или удален !')
            else:
                print(f'Непредвиденная ошибка, код: {reels['error']}')
                return 'exit'

async def main():
    try:
        for i in range(0, users_len, 2):
            parser1 = ParsAccountReels(users_for_pars[i], q_view)
            parser2 = ParsAccountReels(users_for_pars[i+1], q_view)
            task1 = asyncio.create_task(parser1.pars())
            task2 = asyncio.create_task(parser2.pars())

            valid = await task1
            check(valid)
            if valid == 'exit':
                break
            valid1 = await task2
            check(valid1)
            if valid1 == 'exit':
                break
    except KeyboardInterrupt:
        print('программа была закрыта')
