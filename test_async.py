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


async def check(reels):
    global excel_row
    if reels['ok']:
        return True
    else:
        if 'error' in reels:
            if reels['error'] == 'account':
                print('Аккаунт закрытый или удален !')
            else:
                print(f'Непредвиденная ошибка, код: {reels['error']}')
                return 'exit'


async def pars(user_name: str):
    parser = ParsAccountReels(user_name, q_view)
    valid = await check(await parser.pars())
    if valid == 'exit':
        return 'exit'

async def main():
    try:
        for i in range(0, users_len, 2):
            task1 = asyncio.create_task(pars(users_for_pars[i]))
            task2 = asyncio.create_task(pars(users_for_pars[i+1]))

            await task1
            await task2

    except KeyboardInterrupt:
        print('программа была закрыта')

asyncio.run(main())
