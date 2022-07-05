# StyleTransfer
Перенос стиля с одного изображения на другое в асинхронном телеграм-боте. 

Данный бот является учебным в рамках курса Deep Learning School ФПМИ МФТИ.

## Стек:
- pytorch
- aiogram

## Параметры сети
- Модель: сверточная нейронная сеть VGG19
- Количество эпох: 400
- Выходное изобржаение: 256*256

Данные настройки сети указаны в файле config.py

## Работа телеграмм бота

Бот асинхронный. 

В нем предусмотрены следующие inline кнопки меня:
- "Кто ты?" - описание бота
- "Статус" - текущее состояние бота. Показывает сколько изображений сейчас в обработке, а сколько в буфере стека.
- "Справка" - описание 

Прикрепленные пользователем изображения попадают в стек. Как только изображений становится 2 и более запускается процедура переноса стиля. Причем первое добавленное изображение становится стилем, а второе - обрабатываемым.

Алгоритм медленный. Поэтому обработка занимает значительное время. 

По завершению обработки выходит сообщение "Стиль перенесен" с прикрепленным результатом работы.

## Примеры работы бота
Стиль                      |  Обрабатываемое изображение       |  Результат работы
:-------------------------:|:---------------------------------:|:-------------------------:
<img src="https://github.com/KATIOIIIA/StyleTransfer/blob/00d1bffe35231548e728e30459fa6014b52a36e3/images/style.jpg" height="250" width="250">  |  <img src="https://github.com/KATIOIIIA/StyleTransfer/blob/00d1bffe35231548e728e30459fa6014b52a36e3/images/IMG.jpg" height="250" width="250">  |  <img src="https://github.com/KATIOIIIA/StyleTransfer/blob/00d1bffe35231548e728e30459fa6014b52a36e3/images/result.jpg" height="250" width="250"> 
||
<img src="https://github.com/KATIOIIIA/StyleTransfer/blob/00d1bffe35231548e728e30459fa6014b52a36e3/images/style3.jpeg" height="250" width="250">  |  <img src="https://github.com/KATIOIIIA/StyleTransfer/blob/00d1bffe35231548e728e30459fa6014b52a36e3/images/images3.jpeg" height="250" width="250">  |  <img src="https://github.com/KATIOIIIA/StyleTransfer/blob/00d1bffe35231548e728e30459fa6014b52a36e3/images/result3.jpg" height="250" width="250"> 

## Как работает бот можно посмотреть по ссылк: 

https://github.com/KATIOIIIA/StyleTransfer/blob/00d1bffe35231548e728e30459fa6014b52a36e3/images/bot_w.avi
