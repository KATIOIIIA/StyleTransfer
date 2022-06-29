from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

'''
Кнопки в чате
'''
btn_km = InlineKeyboardMarkup()
btn_km.add(InlineKeyboardButton('Кто ты?', callback_data='btn_about'))
btn_km.add(InlineKeyboardButton('Статус', callback_data='btn_status'))
btn_km.add(InlineKeyboardButton('Справка', callback_data='btn_help'))

'''
Кнопки скрываемые в поле ввода текста
'''
button_about = KeyboardButton('Кто ты?')
button_status = KeyboardButton('Статус')
button_help = KeyboardButton('Справка')

markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).row(
    button_about, button_status, button_help)

'''
Кнопки, отправляющие контакт и локацию
'''
markup_request = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton('Отправить свой контакт ☎️', request_contact=True)
).add(
    KeyboardButton('Отправить свою локацию 🗺️', request_location=True)
)
