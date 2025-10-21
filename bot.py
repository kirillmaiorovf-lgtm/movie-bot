import os
import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Загружаем переменные из .env (если запускаешь локально или в Replit)
from dotenv import load_dotenv
load_dotenv()

# Токены из .env или напрямую (на случай, если .env не подхватился)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8306127980:AAHGXcF1rA-Sg0ACbvG6j3i5diOBUDCQBjI"
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY") or "FB86TF8-K4V4FTQ-NQ8J2SY-7P6WV49"

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# ✅ Только официальные жанры, поддерживаемые Kinopoisk.dev
GENRES = [
    "аниме", "биография", "боевик", "вестерн", "военный", "детектив", "детский",
    "документальный", "драма", "игра", "история", "комедия", "короткометражка",
    "криминал", "мелодрама", "мистика", "мультфильм", "мюзикл", "новости",
    "приключения", "реальное ТВ", "семейный", "спорт", "триллер", "ужасы",
    "фантастика", "фэнтези", "церемония"
]

def get_genre_keyboard():
    buttons = []
    for genre in GENRES:
        buttons.append(InlineKeyboardButton(text=genre.capitalize(), callback_data=f"genre:{genre}"))
    keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def fetch_movies_by_genre(genre: str):
    url = "https://api.kinopoisk.dev/v1/movie"
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    params = {
        "genres.name": genre,
        "page": 1,
        "limit": 20,
        "rating.kp": "4.5-10"  # как ты просил
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"🔍 Запрос: жанр={genre}")
        print(f"📡 Статус: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            movies = data.get("docs", [])
            print(f"✅ Фильмов получено: {len(movies)}")
            return movies
        else:
            print(f"❌ API ошибка: {response.text}")
            return []
    except Exception as e:
        print(f"💥 Исключение при запросе: {e}")
        return []

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.answer(
        "🎬 Привет! Я помогу тебе найти крутые фильмы.\n\n"
        "Нажми на жанр ниже, и я покажу тебе лучшие фильмы с рейтингом от 4.5+!",
        reply_markup=get_genre_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("genre:"))
async def process_genre_callback(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    genre = callback_query.data.split(":", 1)[1]
    movies = fetch_movies_by_genre(genre)
    if movies:
        for movie in movies[:3]:  # Показываем первые 3
            title = movie.get("name") or movie.get("alternativeName") or "Без названия"
            year = movie.get("year", "—")
            rating = movie.get("rating", {}).get("kp", "—")
            # Формируем сообщение
            msg = f"🎥 <b>{title}</b> ({year})\n⭐ Рейтинг: {rating}"
            await bot.send_message(callback_query.from_user.id, msg, parse_mode="HTML")
    else:
        await bot.send_message(
            callback_query.from_user.id,
            f"К сожалению, по жанру «{genre}» сейчас нет фильмов с рейтингом ≥4.5.\n"
            "Попробуй другой жанр!",
            reply_markup=get_genre_keyboard()
        )

if __name__ == "__main__":
    print("🚀 Бот запускается...")
    print(f"🔑 Telegram Token (частично): ...{TELEGRAM_TOKEN[-5:]}")
    print(f"🔑 Kinopoisk API Key (частично): ...{KINOPOISK_API_KEY[-5:]}")
    executor.start_polling(dp, skip_updates=True)
