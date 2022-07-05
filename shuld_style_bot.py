import logging
from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.utils.emoji import emojize
from aiogram.dispatcher import Dispatcher
from aiogram.types.message import ContentType
from aiogram.utils.markdown import text, italic, code, pre
from aiogram.types import ParseMode
from aiogram.utils.executor import start_webhook

from StyleTransferModel import StyleTransferModel
from config import TOKEN

from PIL import Image
from io import BytesIO

import numpy as np
import keyboards as kb
import os

logging.basicConfig(format=u'%(filename)s [ LINE:%(lineno)+3s ]#%(levelname)+8s [%(asctime)s]  %(message)s',
                    level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    await bot.delete_webhook()

# Хранит изображения, полученные от пользователей
images_buf = []

# Флаг обработки
images_run_buf = []

'''
Класс, хранит изображения, полученные от пользователя
'''


class ImagesInfo:
    def __init__(self, id_photo, path, photo):
        self.id = id_photo
        self.photo = photo
        self.path = path


def send_help():
    msg = text(emojize('Я могу работать со следующими командами:\n'),
               '/about', '- расскажу о себе\n',
               '/status', '- статус работы\n',
               '/help', '- справка по командам.\n')
    return msg


def send_about():
    msg = f"Меня зовут StyleBot, я могу переносить стиль с одной фотографии на другую. \n" \
          + f"Хочешь попробовать? Добавь изображения!\n" \
          + f"Первое изображение будет стилем, второе - контентом."
    return msg


def send_status():
    message_text = ''
    if len(images_run_buf) == 0:
        message_text = 'В обработке изображений нет.'
    else:
        message_text = 'В обработке '+str(len(images_run_buf))+f" шт."
    msg_buf = '\nВ буфере '
    if len(images_buf) == 0:
        msg_buf = msg_buf + 'файлов нет.'
    else:
        msg_buf = msg_buf+str(len(images_buf))+f" шт."
    return message_text+msg_buf


def getBytesIOimg(img_data):
    output = np.rollaxis(img_data.cpu().detach().numpy()[0], 0, 3)
    output = Image.fromarray(np.uint8(output * 255))
    bio = BytesIO()
    bio.name = 'result.jpeg'
    output.save(bio, 'JPEG')
    bio.seek(0)
    return bio


async def style_transfer(style_img, content_img):
    st = StyleTransferModel(style_img.photo, content_img.photo)
    images_run_buf.append(style_img.path)
    images_run_buf.append(content_img.path)
    output = await st.run_style_transfer()
    images_run_buf.pop(0)
    images_run_buf.pop(0)
    return getBytesIOimg(output)


'''
@dp.callback_query_handler(lambda c: c.data == 'button_about')
async def process_callback_button1(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id,send_about())
'''


@dp.message_handler(text="Кто ты?")
async def bot_message(message: types.Message):
    await bot.send_message(message.chat.id, send_about())


@dp.message_handler(text="Справка")
async def bot_message(message: types.Message):
    await bot.send_message(message.chat.id, send_help())


@dp.message_handler(text="Статус")
async def bot_message(message: types.Message):
    await bot.send_message(message.chat.id, send_status())


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!", reply_markup=kb.markup)


@dp.message_handler(commands=['help'])
async def process_start_command(message: types.Message):
    await bot.send_message(message.chat.id, send_help())


@dp.message_handler(commands=['about'])
async def process_start_command(message: types.Message):
    await bot.send_message(message.chat.id, send_about())


@dp.message_handler(content_types=['photo', 'document'])
async def get_image(message):
    # Если файл добавили с сжатием,
    # то придет 'photo'.
    # Иначе - 'document'
    if message.content_type == 'photo':
        img = message.photo[-1]
    else:
        img = message.document
        if img.mime_type[:5] != 'image':
            await bot.send_message(message.chat.id,
                                   "Загрузи изображение")
            return

    image_id = message.photo[len(message.photo) - 1].file_id

    file_info = await bot.get_file(img.file_id)
    photo = await bot.download_file(file_info.file_path)
    images_buf.append(ImagesInfo(image_id, file_info.file_path, photo))
    if len(images_buf) > 1:
        await bot.send_message(message.chat.id,
                               f"Сеть начала переность стиль. Работа может занять продолжительное время. Пожалуйста, подождите...")
        style_img = images_buf.pop(0)
        content_img = images_buf.pop(0)
        output = await style_transfer(style_img, content_img)
        await bot.send_message(message.chat.id, f"Стиль перенесен!")
        #await bot.send_document(message.chat.id, deepcopy(output))
        await bot.send_photo(message.chat.id, output)


@dp.message_handler(commands=['status'])
async def process_photo_command(message: types.Message):
    await bot.send_message(message.chat.id, send_status())


@dp.message_handler(content_types=ContentType.ANY)
async def unknown_message(msg: types.Message):
    message_text = text(emojize('Я не знаю, что с этим делать :astonished:'),
                        italic('\nЯ просто напомню,'), 'что есть',
                        code('команда'), '/help')
    await msg.reply(message_text, parse_mode=ParseMode.MARKDOWN)

if __name__ == '__main__':
    #executor.start_polling(dp)
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
