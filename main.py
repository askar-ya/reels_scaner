from logic import ParsAccountReels, read_setup, get_work_accounts, swap_account
from logic import clean_out_excel, creat_out_excel, wright_in_excel
import time


# Читаем входные данные
q_view, users_for_pars = read_setup()
users_len = len(users_for_pars)
accounts = get_work_accounts()
accounts_len = len(accounts)
print(f'Загружено {accounts_len} рабочих акков')
current_account = 0
swap_account(accounts[current_account])

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

try:
    # Проходимся по аккаунтам
    for n, user in enumerate(users_for_pars, 1):
        print(f'Получаем видео с аккаунта -> {user}({n}/{users_len})')
        parser = ParsAccountReels(user, q_view)
        valid = check(parser.pars())
        if valid == 'exit':
            break
except KeyboardInterrupt:
    print('программа была закрыта')