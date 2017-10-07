# coding=utf-8

import re
from Queue import Queue

from bot_commands import commands_list, understand_text
# from storage import Storage
from settings import *
from secret_settings import BOT_TOKEN
from Telegram_requests import *
import threading
import json
import requests
from image_recognition import get_info_by_url

# Включение бота
reset_messages = raw_input('Reset messages? y/n\n')
if reset_messages == 'y':
    reset_messages = True
else:
    reset_messages = False

try:
    log_file = open('logs/logs.txt', 'a')
except Exception, err_exception:
    sys.stderr.write('error: {}'.format(err_exception))
    exit(1)
log_write(log_file, 'sys', '------------- Начало сеанса -------------')
bot = init_bot(BOT_TOKEN)
try:
    write_bot_name(log_file, bot)
    log_write(log_file, 'sys', 'Successfully started')
except FatalError as exc_txt:
    log_write(log_file, 'sys', exc_txt.txt)
    exit(1)
# storage = Storage()
offset = 0

# Пропускаем пропущенные сообщения
if reset_messages:
    updates = get_updates_for_bot(bot, offset)
    if updates:
        try:
            with open('logs/reset_file.txt', 'a') as reset_file:
                reset_file.write(str(updates))
        except Exception, err_exception:
            sys.stderr.write('error: {}'.format(err_exception))
            exit(1)

        offset = updates[-1].update_id + 1

log_write(log_file, 'sys', 'Successfully skipped messages')

print "bot started\n"  # Используется, чтобы из консоли можно было понять, что старт прошел успешно

def get_photo_url(photo):
    first_req = 'https://api.telegram.org/bot' + BOT_TOKEN + '/getFile?file_id=' + photo.file_id
    # print first_req
    res_req = requests.get(first_req).content
    x = json.loads(res_req)
    return 'https://api.telegram.org/file/bot' + BOT_TOKEN + '/' + x['result']['file_path']


def multi_thread_user_communication(user_id):
    print user_id
    try:
        personal_update = threads[user_id].get()

        # Получаем информацию о сообщении
        offset, user_id, chat_id, username, text, message_date, photo = extract_update_info(personal_update)

        da = get_info_by_url(user_id, get_photo_url(photo))
        for i in da:
            answer(log_file, bot, user_id, chat_id, i, reply_markup, del_msg=False)

    #     give_answer = False  # Готов ли ответ
    #
    #     # Если не текстовое сообщение
    #     if text is None:
    #         text = u'(Нет текста)'
    #         answer_text = NO_TEXT
    #         give_answer = True
    #
    #     # Логи
    #     try:
    #         log_write(log_file, 'usr', personal_update, username, user_id)
    #         log_write(log_file, 'usr', text.encode('utf-8'), username, user_id)
    #     except UnicodeError:
    #         log_write(log_file, 'usr', 'UnicodeError', username, user_id)
    #
    #     # Если получили комманду
    #     if text[0] == '/' and not give_answer:
    #         try:
    #             if '@food_rate_bot' in text:
    #                 text = re.sub(r'@food_rate_bot', '', text)  # Для групповых чатов
    #             if '/answer' in text:
    #                 text = re.sub(r'/answer ', '', text)
    #                 answer_text, reply_markup = commands_list['/answer'](
    #                     user_id in storage.data, storage,
    #                     user_id, username, text)
    #                 give_answer = True
    #
    #             if not give_answer:
    #                 answer_text, reply_markup = commands_list.get(text)(
    #                     user_id in storage.data, storage,
    #                     user_id, username)
    #
    #         except TypeError:
    #             if user_id not in storage.data:
    #                 storage.new_user(username, user_id)
    #             answer_text = NON_EXISTENT_COMMAND
    #         give_answer = True
    #
    #     # Если текстовый запрос, пытаемся понять его
    #     if not give_answer:
    #         answer_text, reply_markup = understand_text(user_id in storage.data,
    #                                                     storage,
    #                                                     user_id, username, text)
    #         give_answer = True
    #
    #     if storage.data[user_id]['question'] == 'answer_article_id' or \
    #                     storage.data[user_id]['state'] == 'waitForStart':
    #         del_msg = True
    #     else:
    #         del_msg = False
    #     answer(log_file, storage, bot, user_id, chat_id, answer_text,
    #            reply_markup, del_msg=False)
    #
    except ContinueError as exc_txt:
        answer(log_file, bot, user_id, chat_id, exc_txt.txt,
               reply_markup, del_msg=False)
    except EasyError as exc_txt:
        log_write(log_file, 'sys', exc_txt.txt)


threads = dict()
# Запуск прослушки Телеграма
try:
    answer_text = u'<Заготовка под ответ>'
    reply_markup = None  # Клавиатура
    while True:
        try:  # Отлавиваем только EasyError, остальное завершает работу
            updates = get_updates_for_bot(bot, offset)  # Если нет обновлений, вернет пустой список
            for update in updates:
                # Получаем информацию о сообщении
                offset, user_id, _, _, _, _, _ = extract_update_info(update)

                if user_id not in threads:
                    threads[user_id] = Queue()
                threads[user_id].put(update)

                t = threading.Thread(target=multi_thread_user_communication, args=[user_id])
                t.start()

                offset += 1  # id следующего обновления

            time.sleep(0.01)
        except Exception as e:
            offset += 1  # id следующего обновления
            print e.message

except KeyboardInterrupt:
    log_write(log_file, 'endl', '')
    log_write(log_file, 'sys', 'Бот остановлен.')
except FatalError as exc_txt:
    log_write(log_file, 'sys', exc_txt.txt)
except Exception, exc_txt:
    log_write(log_file, 'sys', 'Неизвестная ошибка: {}'.format(exc_txt), sys_time())
finally:
    log_write(log_file, 'sys', '------------- Конец сеанса --------------\n\n\n')
    log_file.close()
    # storage.close_db()
