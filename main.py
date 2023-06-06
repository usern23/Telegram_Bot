import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
import pickle
import asyncio
from datetime import datetime, time, timedelta, date

logging.basicConfig(level=logging.INFO)

bot = Bot(token='6178490851:AAFLnjDjg4WP75oHyE227AjsB5VGZfqUWcY')
dp = Dispatcher(bot, storage=MemoryStorage())

class NewsStates(StatesGroup):
    waiting_for_news = State()
    waiting_for_topic = State()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("Привет! Я новостной бот. Напиши /menu, чтобы подписаться на интересующий тебя раздел новостей.")

@dp.message_handler(commands=['news'])
async def news_command(message: types.Message):
    await message.reply("Введите тему новостей, которые вы хотите получить:")

    await NewsStates.waiting_for_news.set()



@dp.message_handler(commands=['menu'])
async def menu_command(message: types.Message):
    # Создаем инлайн-клавиатуру
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton('Добавить новую тему', callback_data='newSection'),
        InlineKeyboardButton('Мои темы', callback_data='mySections'),
        InlineKeyboardButton('Удалить тему', callback_data='deleteSection')
    )

    await message.answer('Меню\n\nВы можете добавить интересующую вас тему, по которой вы бы хотели получать новости.\n\nВ "Мои темы" Вы сможете просматривать свежие новости по каждому добавленному разделу новостей.', reply_markup=keyboard)




async def add_topic_to_csv(user_id, topic):
    filename = 'geekyfile'

    allSections = []
    listik = []
    bb = []

    with open(filename, 'rb') as geeky_file:
        bb = pickle.load(geeky_file)

    async with aiohttp.ClientSession() as session:
        yesterday = date.today() - timedelta(days=1)
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        async with session.get(
                f'https://newsapi.org/v2/everything?q={topic}&from={yesterday_str}&to={yesterday_str}&apiKey=08c5f8a2ff964a04a2a052cc475c2e24') as resp:
            data = await resp.json()
            bb[user_id].append(data)

    if user_id in bb:
        allSections = bb[user_id][0]
        allSections.append(topic)
        bb[user_id][0] = allSections
    else:
        allSections.append(topic)
        listik.append(allSections)
        bb[user_id] = listik

    with open('geekyfile', 'wb') as geeky_file:
        pickle.dump(bb, geeky_file)





@dp.callback_query_handler(lambda query: query.data == 'newSection')
async def handle_button1(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await bot.send_message(callback_query.from_user.id, "Введите название темы:")
    await NewsStates.waiting_for_topic.set()




@dp.callback_query_handler(lambda query: query.data == 'deleteSection')
async def handle_button1(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    filename = 'geekyfile'
    bb = []
    with open(filename, 'rb') as geeky_file:
        bb = pickle.load(geeky_file)

    listik = []

    if callback_query.from_user.id in bb:
        listik = bb[callback_query.from_user.id][0]


    for i in range(0,len(listik)):
        button_data = f'del_button:{listik[i]}'
        keyboard.add(InlineKeyboardButton(listik[i], callback_data=button_data))
    keyboard.add(InlineKeyboardButton('Назад', callback_data='backFromDelete'))

    await callback_query.message.answer('Выберите тему, которую хотите удалить:', reply_markup=keyboard)




@dp.callback_query_handler(lambda c: c.data.startswith('news_button:'))
async def handle_button_press(callback_query: types.CallbackQuery):
    button_data = callback_query.data
    button_label = button_data.split(':')[-1]
    filename = 'geekyfile'
    bb = []
    with open(filename, 'rb') as geeky_file:
        bb = pickle.load(geeky_file)
    listik = bb[callback_query.from_user.id][0]
    index = listik.index(button_label) + 1

    data = bb[callback_query.from_user.id][index]
    if data['totalResults'] > 0:
        for article in data['articles']:
            await callback_query.message.answer(
                f"<b>{article['title']}</b>\n\n{article['description']}\n<a href='{article['url']}'>Читать далее</a>",
                parse_mode=ParseMode.HTML)
    else:
        await callback_query.message.answer('Нет свежих новостей по теме ' + button_label)


@dp.callback_query_handler(lambda c: c.data.startswith('del_button:'))
async def handle_button_press(callback_query: types.CallbackQuery):
    button_data = callback_query.data
    # Обработка кнопки, используя переданные данные
    button_label = button_data.split(':')[-1]
    filename = 'geekyfile'
    bb = []
    with open(filename, 'rb') as geeky_file:
        bb = pickle.load(geeky_file)

    listik = []

    listik = bb[callback_query.from_user.id][0]

    index = listik.index(button_label) + 1

    listik.remove(button_label)
    bb[callback_query.from_user.id].pop(index)

    bb[callback_query.from_user.id][0] = listik
    with open('geekyfile', 'wb') as geeky_file:
        pickle.dump(bb, geeky_file)

    await callback_query.message.answer('Тема "' + button_label + '" удалена!')

@dp.callback_query_handler(lambda query: query.data == 'backFromDelete')
async def handle_button1(callback_query: types.CallbackQuery):
    message = types.Message(
        message_id=1,
        chat=types.Chat(id=callback_query.message.chat.id, type='private'),
        from_user=types.User(id=callback_query.from_user.id, is_bot=False),
        date=1234567890,
        text='/menu'
    )
    await menu_command(message)


@dp.message_handler(state=NewsStates.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    topic = message.text


    await add_topic_to_csv(user_id, topic)
    await message.answer(f'Тема "{topic}" добавлена в список ваших тем.')

    await state.finish()
    message = types.Message(
        message_id=1,
        chat=types.Chat(id=message.chat.id, type='private'),
        from_user=types.User(id=message.from_user.id, is_bot=False),
        date=1234567890,
        text='/menu'
    )
    await menu_command(message)




@dp.callback_query_handler(lambda query: query.data == 'mySections')
async def handle_button2(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    filename = 'geekyfile'
    bb = []
    with open(filename, 'rb') as geeky_file:
        bb = pickle.load(geeky_file)
    listik = []
    listik = bb[callback_query.from_user.id][0]
    yesterday = datetime.now().date() - timedelta(days=1)
    formatted_date = yesterday.strftime("%d.%m.%Y")

    for i in range(0, len(listik)):
        button_data = f'news_button:{listik[i]}'
        data = bb[callback_query.from_user.id][i+1]
        number = data['totalResults']

        keyboard.add(InlineKeyboardButton(listik[i] + '(' + str(number) + ' новых за ' + str(formatted_date) + ')', callback_data=button_data))
    keyboard.add(InlineKeyboardButton('Назад', callback_data='backFromDelete'))

    await callback_query.message.answer("Смотреть свежие новости на тему:", reply_markup=keyboard)


@dp.message_handler(state=NewsStates.waiting_for_news)
async def process_news_topic(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://newsapi.org/v2/everything?q={message.text}&apiKey=08c5f8a2ff964a04a2a052cc475c2e24%27') as resp:
            data = await resp.json()

            if data['totalResults'] > 0:
                for article in data['articles']:
                    await message.answer(f"<b>{article['title']}</b>\n\n{article['description']}\n<a href='{article['url']}'>Читать далее</a>", parse_mode=ParseMode.HTML)

            else:
                await message.answer("К сожалению, новости по этой теме не найдены.")

    await state.finish()

async def scheduled_function():
    while True:
        current_time = datetime.now().time()
        target_time = time(hour=12, minute=0)

        if current_time >= target_time:

            filename = 'geekyfile'
            bb = []
            with open(filename, 'rb') as geeky_file:
                bb = pickle.load(geeky_file)
            listik = []
            for userid in bb:
                sections = bb[userid][0]
                cursec = 1

                for section in sections:
                    async with aiohttp.ClientSession() as session:
                        yesterday = date.today() - timedelta(days=1)
                        yesterday_str = yesterday.strftime('%Y-%m-%d')
                        async with session.get(f'https://newsapi.org/v2/everything?q={section}&from={yesterday_str}&to={yesterday_str}&apiKey=08c5f8a2ff964a04a2a052cc475c2e24') as resp:
                            data = await resp.json()
                            bb[userid][cursec] = data
                    cursec += 1

            with open('geekyfile', 'wb') as geeky_file:
                pickle.dump(bb, geeky_file)

            tomorrow = datetime.now().date() + timedelta(days=1)
            target_datetime = datetime.combine(tomorrow, target_time)
            time_to_wait = (target_datetime - datetime.now()).total_seconds()
            await asyncio.sleep(time_to_wait)

        await asyncio.sleep(10)

def run_scheduled_task():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_function())

run_scheduled_task()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)