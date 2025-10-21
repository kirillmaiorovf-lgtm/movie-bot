import asyncio
import httpx
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from dotenv import load_dotenv
import os
from session import set_session, get_session, add_to_history

# Загружаем переменные окружения из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")
KINOPOISK_URL = "https://api.kinopoisk.dev/v1.4/movie"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# ✅ Расширенный список жанров (все основные жанры Kinopoisk)
GENRES = {
    "Боевик": "боевик",
    "Драма": "драма",
    "Комедия": "комедия",
    "Фантастика": "фантастика",
    "Триллер": "триллер",
    "Детектив": "детектив",
    "Приключения": "приключения",
    "Ужасы": "ужасы",
    "Мелодрама": "мелодрама",
    "Исторический": "история",
    "Военный": "военный",
    "Семейный": "семейный",
    "Фэнтези": "фэнтези",
    "Криминал": "криминал",
    "Биография": "биография",
    "Документальный": "документальный",
    "Музыкальный": "музыкальный",
    "Спорт": "спорт",
    "Зарубежный": "зарубежный",
    "Российский": "российский",
    "Анимация": "анимация",
    "Короткометражка": "короткометражка",
    "ТВ-шоу": "тв-шоу",
    "Мини-сериал": "мини-сериал",
    "Сериал": "сериал",
    "Реалити": "реалити",
    "Концерт": "концерт",
    "Игра": "игра",
    "Квест": "квест",
    "Подростковый": "подростковый",
    "ЛГБТ": "лгбт",
    "Эротика": "эротика",
    "Нуар": "нуар",
    "Вестерн": "вестерн",
    "Сказка": "сказка",
    "Пародия": "пародия",
    "Чёрная комедия": "чёрная комедия",
    "Политический": "политический",
    "Психологический": "психологический",
    "Религиозный": "религиозный",
    "Супергерой": "супергерой",
    "Триллер-драма": "триллер-драма",
    "Фантастика-драма": "фантастика-драма",
    "Фантастика-боевик": "фантастика-боевик",
    "Фантастика-триллер": "фантастика-триллер",
    "Фантастика-ужасы": "фантастика-ужасы",
    "Фантастика-комедия": "фантастика-комедия",
    "Фантастика-фэнтези": "фантастика-фэнтези",
    "Фантастика-мелодрама": "фантастика-мелодрама",
    "Фантастика-история": "фантастика-история",
    "Фантастика-военный": "фантастика-военный",
    "Фантастика-семейный": "фантастика-семейный",
    "Фантастика-документальный": "фантастика-документальный",
    "Фантастика-музыкальный": "фантастика-музыкальный",
    "Фантастика-спорт": "фантастика-спорт",
    "Фантастика-зарубежный": "фантастика-зарубежный",
    "Фантастика-российский": "фантастика-российский",
    "Фантастика-анимация": "фантастика-анимация",
    "Фантастика-короткометражка": "фантастика-короткометражка",
    "Фантастика-тв-шоу": "фантастика-тв-шоу",
    "Фантастика-мини-сериал": "фантастика-мини-сериал",
    "Фантастика-сериал": "фантастика-сериал",
    "Фантастика-реалити": "фантастика-реалити",
    "Фантастика-концерт": "фантастика-концерт",
    "Фантастика-игра": "фантастика-игра",
    "Фантастика-квест": "фантастика-квест",
    "Фантастика-подростковый": "фантастика-подростковый",
    "Фантастика-лгбт": "фантастика-лгбт",
    "Фантастика-эротика": "фантастика-эротика",
    "Фантастика-нуар": "фантастика-нуар",
    "Фантастика-вестерн": "фантастика-вестерн",
    "Фантастика-сказка": "фантастика-сказка",
    "Фантастика-пародия": "фантастика-пародия",
    "Фантастика-чёрная комедия": "фантастика-чёрная комедия",
    "Фантастика-политический": "фантастика-политический",
    "Фантастика-психологический": "фантастика-психологический",
    "Фантастика-религиозный": "фантастика-религиозный",
    "Фантастика-супергерой": "фантастика-супергерой",
}

async def fetch_movies(genre: str, page: int = 1):
    params = {
        "genres.name": genre,
        "rating.kp": "4.0-10",
        "type": "movie",
        "movieLength": "60-300",
        "limit": 20,
        "page": page
    }
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    
    print(f"🔍 Запрос к API: жанр={genre}, страница={page}")
    
    async with httpx.AsyncClient() as client:
        r = await client.get(KINOPOISK_URL, params=params, headers=headers)
        print(f"📡 Статус ответа: {r.status_code}")
        
        if r.status_code != 200:
            print(f"❌ Ошибка API: {r.text}")
            return {"docs": [], "pages": 0}
        
        try:
            data = r.json()
            print(f"✅ Получено фильмов: {len(data.get('docs', []))}")
            return data
        except Exception as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return {"docs": [], "pages": 0}

@router.message(Command("start"))
async def start(message: Message):
    text = """🎬 *MyMovieRecBot* — твой личный помощник в мире кино!

📌 Что я умею:
- 🎯 Выбирать фильмы по жанру (более 50 жанров!)
- 📺 Показывать подробную информацию о фильме (рейтинг, описание, где смотреть)
- 🔁 Листать списки фильмов (до 20 штук на страницу)
- 📚 Сохранять историю просмотров
- 🔗 Открывать ссылки на платформы (Иви, Okko, Kinopoisk HD и др.)
- 🆓 Находить бесплатные сайты для просмотра

👉 Начни с выбора жанра или посмотри историю.

Список команд:
/start — перезапустить бота
/history — посмотреть историю просмотров"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Выбрать жанр", callback_data="genres")],
        [InlineKeyboardButton(text="🕒 История", callback_data="history")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=kb)

@router.callback_query(F.data == "genres")
async def show_genres(callback: CallbackQuery):
    buttons = [InlineKeyboardButton(text=name, callback_data=f"genre_{eng}") for name, eng in GENRES.items()]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    await callback.message.edit_text("Выбери жанр:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(F.data.startswith("genre_"))
async def handle_genre(callback: CallbackQuery):
    genre = callback.data.split("_", 1)[1]
    await callback.message.answer(f"🔍 Ищу фильмы в жанре «{genre}» с рейтингом от 4.0...")

    data = await fetch_movies(genre, page=1)
    movies = data.get("docs", [])

    if not movies:
        await callback.message.answer("❌ Ничего не найдено даже с рейтингом от 4.0.")
        return

    # ✅ Сохраняем начальную страницу и общее количество фильмов
    set_session(callback.from_user.id, {
        "genre": genre,
        "page": 1,
        "total_movies": len(movies),
        "start_index": 0  # Индекс первого фильма на текущей странице
    })
    await send_movie_list(callback.message, movies, 1, 0)  # Передаём start_index=0

async def send_movie_list(message_or_callback, movies, page, start_index):
    text = f"🔍 Страница {page}\n\n"
    buttons = []
    for i, m in enumerate(movies, 1):
        year = m.get("year", "?")
        rating = m.get("rating", {}).get("kp", 0)
        name = m.get("name", "Без названия")
        # ✅ Нумерация сквозная: start_index + i
        # ✅ Кнопка содержит номер и название фильма
        text += f"{start_index + i}. 🎬 *{name}* ({year}) — ⭐{rating}\n"
        buttons.append([InlineKeyboardButton(text=f"👁️ {start_index + i}. {name}", callback_data=f"detail_{m['id']}")])

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
    # ✅ Обновляем индекс начала списка
    start_index = session.get("start_index", 0) + 20
    set_session(callback.from_user.id, {
        "genre": session["genre"],
        "page": new_page,
        "total_movies": len(movies),
        "start_index": start_index
    })
    await send_movie_list(callback, movies, new_page, start_index)

@router.callback_query(F.data == "prev_page")
async def prev_page(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    if not session or session["page"] <= 1:
        await callback.answer("Это первая страница.")
        return
    new_page = session["page"] - 1
    data = await fetch_movies(session["genre"], page=new_page)
    movies = data.get("docs", [])
    # ✅ Уменьшаем индекс начала списка
    start_index = session.get("start_index", 0) - 20
    set_session(callback.from_user.id, {
        "genre": session["genre"],
        "page": new_page,
        "total_movies": len(movies),
        "start_index": start_index
    })
    await send_movie_list(callback, movies, new_page, start_index)

@router.callback_query(F.data.startswith("detail_"))
async def show_detail(callback: CallbackQuery):
    movie_id = callback.data.split("_", 1)[1]
    headers = {"X-API-KEY": KINOPOISK_API_KEY}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"https://api.kinopoisk.dev/v1.4/movie/{movie_id}", headers=headers)
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

    # ✅ Собираем ссылки на платформы
    platforms = ""
    watchability = movie.get("watchability", {})
    if watchability and "items" in watchability:
        for item in watchability["items"]:
            name = item.get("name", "")
            url = item.get("url", "")
            if name and url:
                platforms += f"[{name}]({url})\n"

    # ✅ Добавляем ссылки на бесплатные сайты (если есть)
    free_sites = ""
    # Пример: можно добавить свои ссылки или использовать API для поиска
    # Для примера добавим несколько популярных
    free_sites += "[🌐 Бесплатный просмотр на Filmix](https://filmix.co/search/?q={name})\n"
    free_sites += "[🌐 Бесплатный просмотр на Kinopoisk](https://www.kinopoisk.ru/film/{movie_id}/)\n"
    free_sites += "[🌐 Бесплатный просмотр на OnlineCinema](https://onlinecinema.net/search?q={name})\n"

    # ✅ Ссылка на фильм на Kinopoisk
    kp_url = f"https://www.kinopoisk.ru/film/{movie_id}/"

    caption = f"""🎬 *{name}* • {year}
⭐ {rating} | ⏳ {runtime} мин | 🎯 {genres}

📌 {desc}

🏆 Награды: Нет данных
🌐 Где смотреть:
{platforms}
🔗 [Смотреть на Kinopoisk]({kp_url})

🆓 Бесплатные сайты:
{free_sites}
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

@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery):
    session = get_session(callback.from_user.id)
    if not session:
        await callback.answer("Сессия устарела. Начни с /start.")
        return
    genre = session["genre"]
    page = session["page"]
    start_index = session.get("start_index", 0)
    data = await fetch_movies(genre, page=page)
    movies = data.get("docs", [])
    await send_movie_list(callback.message, movies, page, start_index)

@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery):
    from session import user_history
    history = user_history.get(callback.from_user.id, [])
    if not history:
        await callback.message.answer("ugh Твоя история пуста.")
        return
    text = "ugh Твоя история:\n\n"
    for m in history[-5:]:
        text += f"• 🎬 {m['name']} ({m.get('year', '?')})\n"
    await callback.message.answer(text)

dp.include_router(router)

if __name__ == "__main__":
    print("🚀 Бот запущен!")
    asyncio.run(dp.start_polling(bot))
