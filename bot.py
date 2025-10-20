import asyncio
import httpx
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from dotenv import load_dotenv
import os
from session import set_session, get_session, add_to_history

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
KINOPOISK_API_KEY = "FB86TF8-K4V4FTQ-NQ8J2SY-7P6WV49"
KINOPOISK_URL = "https://api.kinopoisk.dev/v1.4/movie"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

GENRES = {
    "Боевик": "боевик",
    "Драма": "драма",
    "Комедия": "комедия",
    "Фантастика": "фантастика",
    "Триллер": "триллер",
    "Детектив": "детектив",
    "Приключения": "приключения",
}

async def fetch_movies(genre: str, page: int = 1):
    params = {
        "genres.name": genre,
        "rating.kp": "4.5-10",          # ✅ ПОНИЖЕН ПОРОГ до 4.5!
        "type": "movie",
        "movieLength": "60-300",        # от 1 часа
        "votes.kp": "1000-",            # минимум 1000 голосов (чтобы не мусор)
        "limit": 10,
        "page": page
    }
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    async with httpx.AsyncClient() as client:
        r = await client.get(KINOPOISK_URL, params=params, headers=headers)
        return r.json() if r.status_code == 200 else {"docs": [], "pages": 0}

@router.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Выбрать жанр", callback_data="genres")],
        [InlineKeyboardButton(text="🕒 История", callback_data="history")]
    ])
    await message.answer("🎬 Привет! Выбери жанр или посмотри историю.", reply_markup=kb)

@router.callback_query(F.data == "genres")
async def show_genres(callback: CallbackQuery):
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"genre_{eng}")] for name, eng in GENRES.items()]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    await callback.message.edit_text("Выбери жанр:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(F.data.startswith("genre_"))
async def handle_genre(callback: CallbackQuery):
    genre = callback.data.split("_", 1)[1]
    await callback.message.answer(f"🔍 Ищу фильмы в жанре «{genre}» с рейтингом от 4.5...")

    data = await fetch_movies(genre, page=1)
    movies = data.get("docs", [])

    if not movies:
        await callback.message.answer("❌ Ничего не найдено даже с рейтингом от 4.5. Возможно, API временно недоступно.")
        return

    set_session(callback.from_user.id, {"genre": genre, "page": 1})
    await send_movie_list(callback.message, movies, 1)

async def send_movie_list(message_or_callback, movies, page):
    text = f"🔍 Страница {page}\n\n"
    buttons = []
    for i, m in enumerate(movies, 1):
        year = m.get("year", "?")
        rating = m.get("rating", {}).get("kp", 0)
        name = m.get("name", "Без названия")
        text += f"{i}. 🎬 *{name}* ({year}) — ⭐{rating}\n"
        buttons.append([InlineKeyboardButton(text=f"👁️ {i}", callback_data=f"detail_{m['id']}")])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⏮️ Назад", callback_data="prev_page"))
    nav_buttons.append(InlineKeyboardButton(text="⏭️ Другие варианты", callback_data="next_page"))
    buttons.append(nav_buttons)

    if hasattr(message_or_callback, 'message'):
        await message_or_callback.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        await message_or_callback.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data == "next_page")
async def next_page(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    if not session:
        await callback.answer("Сессия устарела. Начни с /start.")
        return
    new_page = session["page"] + 1
    data = await fetch_movies(session["genre"], page=new_page)
    movies = data.get("docs", [])
    if not movies:
        await callback.answer("Больше фильмов нет.", show_alert=True)
        return
    set_session(callback.from_user.id, {"genre": session["genre"], "page": new_page})
    await send_movie_list(callback, movies, new_page)

@router.callback_query(F.data == "prev_page")
async def prev_page(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    if not session or session["page"] <= 1:
        await callback.answer("Это первая страница.")
        return
    new_page = session["page"] - 1
    data = await fetch_movies(session["genre"], page=new_page)
    movies = data.get("docs", [])
    set_session(callback.from_user.id, {"genre": session["genre"], "page": new_page})
    await send_movie_list(callback, movies, new_page)

@router.callback_query(F.data.startswith("detail_"))
async def show_detail(callback: CallbackQuery):
    movie_id = callback.data.split("_", 1)[1]
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.kinopoisk.dev/v1.4/movie/{movie_id}", headers=headers)  # ✅ Без пробелов!
        movie = r.json() if r.status_code == 200 else None

    if not movie:
        await callback.answer("Фильм не найден.")
        return

    add_to_history(callback.from_user.id, movie)

    name = movie.get("name", "—")
    year = movie.get("year", "?")
    rating = movie.get("rating", {}).get("kp", 0)
    runtime = movie.get("movieLength", "?")
    genres = ", ".join([g["name"] for g in movie.get("genres", [])])
    desc = movie.get("description") or movie.get("shortDescription", "Описание отсутствует.")
    poster = movie.get("poster", {}).get("url")

    platforms = "Кинопоиск HD, IVI, Okko"
    awards = "Нет данных"

    caption = f"""🎬 *{name}* • {year}
⭐ {rating} | ⏳ {runtime} мин | 🎯 {genres}

📌 {desc}

🏆 Награды: {awards}
🌐 Где смотреть: {platforms}
"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Это он", callback_data="selected")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_list")]
    ])

    if poster:
        await callback.message.answer_photo(photo=poster, caption=caption, parse_mode="Markdown", reply_markup=kb)
    else:
        await callback.message.answer(caption, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data == "selected")
async def selected(callback: CallbackQuery):
    await callback.message.answer("✅ Отличный выбор! Фильм сохранён в историю.")

@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery):
    from session import user_history
    history = user_history.get(callback.from_user.id, [])
    if not history:
        await callback.message.answer("🕗 История пуста.")
        return
    text = "🕗 Твоя история:\n\n"
    for m in history[-5:]:
        text += f"• 🎬 {m['name']} ({m.get('year', '?')})\n"
    await callback.message.answer(text)

dp.include_router(router)

if __name__ == "__main__":
    print("🚀 Бот запущен!")
    asyncio.run(dp.start_polling(bot))
