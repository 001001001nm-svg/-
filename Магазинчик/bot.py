import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Твой токен
TOKEN = "8963845436:AAEX8346I6DEZGnDKCdqIcXBW6STyGlBxeo"

# Временная база данных
categories = ["Кофе", "Сладости", "Снеки", "Напитки", "Рамен"]
products = [
    {"id": 1, "name": "Кока-Кола 1.5л", "price": 150, "category": "Напитки"}
]
ads = [
    {"id": 1, "title": "Скидки до 30% на соки!", "photo": None}
]

# Состояния для пошагового добавления рекламы
class AdStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_title = State()

# Главное меню администратора
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Каталог"), KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="➕ Добавить товар"), KeyboardButton(text="🗑 Снять товар")],
            [KeyboardButton(text="🏷 Сделать скидку"), KeyboardButton(text="📋 Список товаров")],
            [KeyboardButton(text="👑 Панель Владельца")]
        ],
        resize_keyboard=True
    )

# Меню Панели Владельца
def get_owner_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Поставить рекламу"), KeyboardButton(text="🗑 Убрать рекламу")],
            [KeyboardButton(text="📂 Удалить каталог"), KeyboardButton(text="❌ Убрать все товары")],
            [KeyboardButton(text="🔙 Назад в главное меню")]
        ],
        resize_keyboard=True
    )

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "Привет! Бот полностью перезапущен и готов к работе.",
            reply_markup=get_main_keyboard()
        )

    @dp.message(F.text == "🔙 Назад в главное меню")
    async def back_to_main(message: types.Message, state: FSMContext):
        await state.clear()
        await message.answer("Главное меню:", reply_markup=get_main_keyboard())

    @dp.message(F.text == "👑 Панель Владельца")
    async def owner_panel(message: types.Message):
        await message.answer("Панель управления рекламой и каталогом:", reply_markup=get_owner_keyboard())

    # --- ОБРАБОТЧИКИ КНОПОК ГЛАВНОГО МЕНЮ ---
    @dp.message(F.text == "🛍 Каталог")
    async def menu_catalog(message: types.Message):
        cats_text = ", ".join(categories)
        await message.answer(f"📂 Текущие категории в каталоге:\n{cats_text}")

    @dp.message(F.text == "👤 Мой профиль")
    async def menu_profile(message: types.Message):
        await message.answer(f"👤 Вы вошли как Администратор магазина.\n🆔 Telegram ID: {message.from_user.id}")

    @dp.message(F.text == "➕ Добавить товар")
    async def menu_add_product(message: types.Message):
        await message.answer("Эта функция добавления товаров через бота будет подключена к базе данных на следующем этапе!")

    @dp.message(F.text == "🗑 Снять товар")
    async def menu_remove_product(message: types.Message):
        await message.answer("Функция удаления отдельного товара в разработке.")

    @dp.message(F.text == "🏷 Сделать скидку")
    async def menu_make_discount(message: types.Message):
        await message.answer("Функция установки скидок на товары в разработке.")

    # --- УПРАВЛЕНИЕ ТОВАРАМИ И КАТАЛОГАМИ (Владелец) ---
    @dp.message(F.text == "❌ Убрать все товары")
    async def clear_all_products(message: types.Message):
        products.clear()
        await message.answer("✅ Все товары успешно удалены из базы!", reply_markup=get_owner_keyboard())

    @dp.message(F.text == "📂 Удалить каталог")
    async def delete_catalog_menu(message: types.Message):
        if not categories:
            await message.answer("Каталогов больше нет.")
            return
        buttons = [[InlineKeyboardButton(text=f"❌ Удалить: {cat}", callback_data=f"del_cat_{cat}")] for cat in categories]
        await message.answer("Выберите каталог для удаления:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    @dp.callback_query(F.data.startswith("del_cat_"))
    async def process_delete_category(callback: types.CallbackQuery):
        cat = callback.data.replace("del_cat_", "")
        if cat in categories:
            categories.remove(cat)
            await callback.message.edit_text(f"✅ Каталог '{cat}' успешно удален.")

    # --- УПРАВЛЕНИЕ РЕКЛАМОЙ (Владелец) ---
    @dp.message(F.text == "📢 Поставить рекламу")
    async def start_add_ad(message: types.Message, state: FSMContext):
        await message.answer("Отправьте **фотографию** для рекламного баннера:")
        await state.set_state(AdStates.waiting_for_photo)

    @dp.message(AdStates.waiting_for_photo, F.photo)
    async def ad_received_photo(message: types.Message, state: FSMContext):
        photo_id = message.photo[-1].file_id
        await state.update_data(photo=photo_id)
        await message.answer("Отлично! Теперь введите **название и текст** рекламы:")
        await state.set_state(AdStates.waiting_for_title)

    @dp.message(AdStates.waiting_for_photo)
    async def ad_wrong_photo(message: types.Message):
        await message.answer("⚠️ Пожалуйста, отправьте именно фотографию (картинку).")

    @dp.message(AdStates.waiting_for_title, F.text)
    async def ad_received_title(message: types.Message, state: FSMContext):
        data = await state.get_data()
        photo_id = data.get("photo")
        ad_text = message.text

        ads.append({"id": len(ads) + 1, "title": ad_text, "photo": photo_id})
        await state.clear()
        await message.answer("🎉 Рекламный баннер успешно добавлен!", reply_markup=get_owner_keyboard())

    @dp.message(F.text == "🗑 Убрать рекламу")
    async def remove_ad_menu(message: types.Message):
        if not ads:
            await message.answer("Активной рекламы нет.")
            return
        buttons = [[InlineKeyboardButton(text=f"❌ Удалить: {ad['title'][:20]}...", callback_data=f"del_ad_{ad['id']}")] for ad in ads]
        await message.answer("Выберите рекламу для удаления:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

    @dp.callback_query(F.data.startswith("del_ad_"))
    async def process_delete_ad(callback: types.CallbackQuery):
        ad_id = int(callback.data.replace("del_ad_", ""))
        global ads
        ads = [ad for ad in ads if ad["id"] != ad_id]
        await callback.message.edit_text("✅ Реклама успешно удалена.")

    @dp.message(F.text == "📋 Список товаров")
    async def list_products(message: types.Message):
        if not products:
            await message.answer("Список товаров пуст.")
            return
        text = "\n".join([f"- {p['name']} ({p['price']} ₽)" for p in products])
        await message.answer(f"Товары в базе:\n{text}")

    print("Бот успешно запущен и готов отвечать на все кнопки...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())