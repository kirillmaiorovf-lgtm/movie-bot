import os
import json
from pathlib import Path
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx

# === Загрузка переменных ===
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8306127980:AAHGXcF1rA-Sg0ACbvG6j3i5diOBUDCQBjI"
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY") or "E6XED3B-W1V4X10-K70S8ZP-42YE6YS"  # ← замени на свой, если нужно

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# === Хранилище сессий и истории ===
SESSIONS_FILE = Path("sessions.json")
HISTORY_FILE = Path("history.json")

def load_json(file: Path):
    if file.exists():
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file: Path, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === Жанры (только официальные) ===
GENRES = [
    "аниме", "биография", "боевик", "вестерн", "военный", "детектив", "детский",
    "документальный", "драма", "игра", "история", "комедия", "короткометражка",
    "криминал", "мелодрама", "мистика", "мультфильм", "мюзикл", "новости",
    "приключения", "реальное ТВ", "семейный", "спорт", "триллер", "ужасы",
    "фантастика", "фэнтези", "церемония"
]

# === Клавиатура жанров ===
def get_genre_keyboard():
    buttons = []
    for genre in GENRES:
        buttons.append(InlineKeyboardButton(text=genre.capitalize(), callback_data=f"genre_{genre}"))
    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# === Сессии ===
def get_session(user_id):
    sessions = load_json(SESSIONS_FILE)
    return sessions.get(str(user_id))

def set_session(user_id, data):
    sessions = load_json(SESSIONS_FILE)
    sessions[str(user_id)] = data
    save_json(SESSIONS_FILE, sessions)

def add_to_history(user_id, movie):
    history = load_json(HISTORY_FILE)
    user_key = str(user_id)
    if user_key not in history:
        history[user_key] = []
    entry = {
        "id": movie.get("id"),
        "name": movie.get("name"),
        "year": movie.get("year"),
        "rating": movie.get("rating", {}).get("kp"),
        "poster": movie.get("poster", {}).get("url")
    }
    if entry not in history[user_key]:
        history[user_key].append(entry)
    save_json(HISTORY_FILE, history)

# === Запрос к API ===
async def fetch_movies(genre: str, page: int = 1):
    url = "https://api.kinopoisk.dev/v2.2/movie"
    headers = {
        "X-API-KEY": KINOPOISK_API_KEY,
        "User-Agent": "MovieBot/1.0 (Telegram Bot)"
    }
    params = {
        "genres.name": genre,
        "page": page,
        "limit": 20,
        "rating.kp": "4.5-10"
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers, params=params)
        print(f"🔍 Запрос: жанр={genre}, страница={page} → Статус: {r.status_code}")
        try:
            return r.json() if r.status_code == 200 else {"docs": []}
        except Exception as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"📡 Ответ: {r.text[:200]}")
            return {"docs": []}

async def send_movie_list(message, movies, page, start_index=1):
    if not movies:
        await message.answer("❌ Ничего не найдено.")
        return

    text = f"🔍 Страница {page}\n\n"
    buttons = []
    for i, m in enumerate(movies, start=start_index):
        name = m.get("name", "—")
        year = m.get("year", "?")
        rating = m.get("rating", {}).get("kp", "—")
        text += f"{i}. 🎬 <b>{name}</b> ({year}) — ⭐{rating}\n"
        buttons.append([InlineKeyboardButton(text=f"👁️ {i}", callback_data=f"detail_{m['id']}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⏮️ Назад", callback_data="prev_page"))
    nav.append(InlineKeyboardButton(text="⏭️ Другие варианты", callback_data="next_page"))
    buttons.append(nav)

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

# === Обработчики ===
@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 <b>Добро пожаловать в MovieBot!</b>\n\n"
        "Что я умею:\n"
        "• Подбирать фильмы по жанрам\n"
        "• Показывать постеры, рейтинг, описание\n"
        "• Давать ссылки на платформы для просмотра\n"
        "• Запоминать историю ваших запросов\n\n"
        "Выберите жанр ниже 👇",
        parse_mode="HTML",
        reply_markup=get_genre_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("genre_"))
async def handle_genre(callback: types.CallbackQuery):
    await callback.answer()
    genre = callback.data.split("_", 1)[1]
    await callback.message.answer(f"🔍 Ищу фильмы в жанре «{genre}» с рейтингом от 4.5...")

    data = await fetch_movies(genre, page=1)
    movies = data.get("docs", [])

    if not movies:
        await callback.message.answer("❌ Ничего не найдено даже с рейтингом от 4.5.")
        return

    set_session(callback.from_user.id, {"genre": genre, "page": 1})
    await send_movie_list(callback.message, movies, 1, start_index=1)

@dp.callback_query_handler(lambda c: c.data == "next_page")
async def next_page(callback: types.CallbackQuery):
    await callback.answer()
    session = get_session(callback.from_user.id)
    if not session:
        await callback.message.answer("Сессия устарела. Начните с /start.")
        return

    new_page = session["page"] + 1
    data = await fetch_movies(session["genre"], page=new_page)
    movies = data.get("docs", [])
    if not movies:
        await callback.answer("Больше фильмов нет.", show_alert=True)
        return

    set_session(callback.from_user.id, {"genre": session["genre"], "page": new_page})
    start_index = (new_page - 1) * 20 + 1
    await send_movie_list(callback.message, movies, new_page, start_index)

@dp.callback_query_handler(lambda c: c.data == "prev_page")
async def prev_page(callback: types.CallbackQuery):
    await callback.answer()
    session = get_session(callback.from_user.id)
    if not session or session["page"] <= 1:
        await callback.answer("Это первая страница.")
        return

    new_page = session["page"] - 1
    data = await fetch_movies(session["genre"], page=new_page)
    movies = data.get("docs", [])
    set_session(callback.from_user.id, {"genre": session["genre"], "page": new_page})
    start_index = (new_page - 1) * 20 + 1
    await send_movie_list(callback.message, movies, new_page, start_index)

@dp.callback_query_handler(lambda c: c.data.startswith("detail_"))
async def show_detail(callback: types.CallbackQuery):
    await callback.answer()
    movie_id = callback.data.split("_", 1)[1]
    headers = {
        "X-API-KEY": KINOPOISK_API_KEY,
        "User-Agent": "MovieBot/1.0 (Telegram Bot)"
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.kinopoisk.dev/v2.2/movie/{movie_id}", headers=headers)
        try:
            movie = r.json() if r.status_code == 200 else None
        except:
            movie = None

    if not movie:
        await callback.message.answer("Фильм не найден.")
        return

    add_to_history(callback.from_user.id, movie)

    name = movie.get("name", "—")
    year = movie.get("year", "?")
    rating = movie.get("rating", {}).get("kp", "—")
    runtime = movie.get("movieLength", "?")
    genres = ", ".join([g["name"] for g in movie.get("genres", [])])
    desc = (movie.get("description") or movie.get("shortDescription") or "Описание отсутствует.")[:400] + "..."
    poster = movie.get("poster", {}).get("url") or "https://via.placeholder.com/300x450?text=No+Poster"

    kp_id = movie.get("id", "")
    kinopoisk_url = f"https://www.kinopoisk.ru/film/{kp_id}/"
    ivi_url = f"https://www.ivi.ru/search/?q={name.replace(' ', '+')}"
    okko_url = f"https://okko.tv/search?text={name.replace(' ', '+')}"

    caption = (
        f"🎬 <b>{name}</b> • {year}\n"
        f"⭐ Рейтинг: {rating} | ⏱️ {runtime} мин\n"
        f"🎭 Жанры: {genres}\n\n"
        f"📝 {desc}\n\n"
        f"🔗 Где смотреть:\n"
        f"• <a href='{kinopoisk_url}'>Кинопоиск</a>\n"
        f"• <a href='{ivi_url}'>IVI</a>\n"
        f"• <a href='{okko_url}'>Okko</a>"
    )

    await bot.send_photo(
        chat_id=callback.from_user.id,
        photo=poster,
        caption=caption,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🌐 Открыть на Кинопоиске", url=kinopoisk_url)
        )
    )

# === Запуск ===
if __name__ == "__main__":
    print("🚀 Бот запускается...")
    print(f"🔑 Telegram Token (частично): ...{TELEGRAM_TOKEN[-5:]}")
    print(f"🔑 Kinopoisk API Key (частично): ...{KINOPOISK_API_KEY[-5:]}")
    executor.start_polling(dp, skip_updates=True)
