"""Telegram AI-продавец на Gemini.
Консультация -> заказ -> реквизиты -> чек -> одобрение админом.
Запуск: python bot.py   (все секреты только в переменных окружения / .env)
"""
import asyncio, json, logging, os, re
from collections import defaultdict

import aiosqlite, httpx
from aiohttp import web
from dotenv import load_dotenv
from aiogram import BaseMiddleware, Bot, Dispatcher, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter, Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Kb,
                           KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove)

load_dotenv()
TG_TOKEN = os.environ["TG_TOKEN"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)   # 0 = владельцем станет первый, кто напишет боту
DB = os.getenv("DB_PATH", "shop.db")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("shop")
bot = Bot(TG_TOKEN)
http = httpx.AsyncClient(timeout=60)

# ───────────────────────── НАСТРОЙКИ АССИСТЕНТА ─────────────────────────
# ключ: (название, значение по умолчанию, тип)  тип: "text" | "toggle" | список вариантов | "hidden"
SET = {
    "business_name": ("🏪 Название бизнеса", "Мой магазин", "text"),
    "greeting": ("👋 Приветствие (/start)", "Здравствуйте! Я ассистент магазина. Помогу выбрать товар и оформить заказ 🙂", "text"),
    "system_prompt": ("🧠 Инструкция для ИИ", "Ты опытный консультант-продавец. Помогай выбрать товар, отвечай по делу, "
                      "не дави на клиента. Цены и наличие бери ТОЛЬКО из search_catalog, ничего не выдумывай.", "text"),
    "tone": ("🎭 Стиль общения", "дружелюбный", ["дружелюбный", "деловой", "краткий", "энергичный с эмодзи"]),
    "upsell": ("🛍 Допродажи (предлагать сопутствующее)", "1", "toggle"),
    "need_phone": ("📞 Запрашивать телефон", "1", "toggle"),
    "need_address": ("📍 Запрашивать адрес доставки", "1", "toggle"),
    "min_order": ("💰 Мин. сумма заказа (0 — нет)", "0", "text"),
    "delivery_info": ("🚚 Условия доставки", "Доставка 1–2 дня. Самовывоз бесплатно.", "text"),
    "work_hours": ("🕒 Режим работы", "", "text"),
    "requisites": ("💳 Реквизиты для оплаты", "", "text"),
    "payment_note": ("📝 Подсказка после реквизитов", "После оплаты отправьте сюда фото или файл чека 🧾", "text"),
    "handoff_text": ("🙋 Текст при вызове менеджера", "Передал диалог менеджеру, он скоро ответит 🙌", "text"),
    "disabled_text": ("⏸ Ответ при выключенном боте", "Сейчас бот отключён. Загляните позже 🙏", "text"),
    "currency": ("💱 Валюта", "₽", "text"),
    "model": ("🤖 Модель Gemini", "gemini-2.5-flash", "text"),
    "temperature": ("🌡 Температура (0–2)", "0.4", "text"),
    "bot_enabled": ("", "1", "hidden"),
}
ST = {"awaiting_payment": "⏳ Ждёт оплаты", "checking": "🔎 Чек на проверке", "paid": "💳 Оплачен",
      "shipped": "🚚 Отправлен", "done": "✅ Выполнен", "cancelled": "❌ Отменён"}
ICON = {"owner": "👑", "admin": "🛡", "customer": "👤", "banned": "🚫"}
B_CAT, B_ORD, B_HUM = "🛍 Каталог", "📦 Мои заказы", "🙋 Менеджер"
B_SET, B_ADM, B_OWN = "⚙️ Настройки", "🛠 Админ-панель", "👑 Панель владельца"


# ───────────────────────── БАЗА ─────────────────────────
async def q(sql, args=(), commit=False):
    async with aiosqlite.connect(DB, timeout=30) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(sql, args)
        rows = [dict(r) for r in await cur.fetchall()]
        if commit:
            await db.commit()
            return cur.lastrowid
        return rows


async def q1(sql, args=()):
    r = await q(sql, args)
    return r[0] if r else None


async def qrc(sql, args=()):
    """Выполнить и вернуть число затронутых строк (для атомарных проверок)."""
    async with aiosqlite.connect(DB, timeout=30) as db:
        cur = await db.execute(sql, args)
        await db.commit()
        return cur.rowcount


async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS users(tg_id INTEGER PRIMARY KEY, username TEXT DEFAULT '', name TEXT DEFAULT '',
            role TEXT DEFAULT 'customer', handoff INTEGER DEFAULT 0, ts TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY, v TEXT);
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL,
            stock INTEGER DEFAULT 0, description TEXT DEFAULT '', active INTEGER DEFAULT 1);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, name TEXT, phone TEXT,
            address TEXT, comment TEXT, items TEXT, total REAL, status TEXT DEFAULT 'awaiting_payment', ts TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, uid INTEGER,
            file_id TEXT, kind TEXT, status TEXT DEFAULT 'pending', by_admin INTEGER, ts TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS receipt_msgs(receipt_id INTEGER, chat_id INTEGER, message_id INTEGER);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, role TEXT, text TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        await db.commit()


async def S(key):
    r = await q1("SELECT v FROM settings WHERE k=?", (key,))
    return r["v"] if r else SET[key][1]


async def set_S(key, val):
    await q("INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (key, val), commit=True)


def kb(*rows):
    return Kb(inline_keyboard=[[Btn(text=t, callback_data=d) for t, d in r] for r in rows])


def reply_kb(role):
    rows = [[KeyboardButton(text=B_CAT), KeyboardButton(text=B_ORD)], [KeyboardButton(text=B_HUM)]]
    if role in ("admin", "owner"):
        rows.append([KeyboardButton(text=B_SET), KeyboardButton(text=B_ADM)])
    if role == "owner":
        rows.append([KeyboardButton(text=B_OWN)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def staff_ids():
    return [u["tg_id"] for u in await q("SELECT tg_id FROM users WHERE role IN ('owner','admin')")]


async def notify(text, markup=None):
    for uid in await staff_ids():
        try:
            await bot.send_message(uid, text[:4000], reply_markup=markup)
        except Exception as e:
            log.warning("notify %s: %s", uid, e)


async def safe_send(uid, text, markup=None):
    try:
        await bot.send_message(uid, text[:4000], reply_markup=markup)
    except Exception as e:
        log.warning("send %s: %s", uid, e)


def fmt_items(items):
    return "\n".join(f"• {i['name']} × {i['qty']} = {i['price'] * i['qty']:g}" for i in items)


# ───────────────────────── GEMINI ─────────────────────────
TOOLS = [{"functionDeclarations": [
    {"name": "search_catalog", "description": "Поиск товаров (цена, наличие, описание). Пустой query — весь каталог.",
     "parameters": {"type": "OBJECT", "properties": {"query": {"type": "STRING"}}}},
    {"name": "create_order",
     "description": "Оформить заказ. ТОЛЬКО после явного подтверждения клиентом состава, суммы и данных.",
     "parameters": {"type": "OBJECT", "properties": {
         "items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
             "product_id": {"type": "INTEGER"}, "qty": {"type": "INTEGER"}}, "required": ["product_id", "qty"]}},
         "name": {"type": "STRING"}, "phone": {"type": "STRING"},
         "address": {"type": "STRING", "description": "адрес или 'самовывоз'"},
         "comment": {"type": "STRING"},
         "customer_confirmed": {"type": "BOOLEAN", "description": "true только если клиент ответил 'да' на итоговое подтверждение"}},
         "required": ["items", "customer_confirmed"]}},
    {"name": "call_human", "description": "Позвать живого менеджера: жалоба, нестандартный вопрос, просьба клиента.",
     "parameters": {"type": "OBJECT", "properties": {"reason": {"type": "STRING"}}, "required": ["reason"]}},
]}]


async def build_system(u):
    s = {k: await S(k) for k in SET}
    steps = ["1. Выясни, что нужно клиенту; проверь товары и наличие через search_catalog."]
    need = []
    if s["need_phone"] == "1": need.append("телефон")
    if s["need_address"] == "1": need.append("адрес доставки (или «самовывоз»)")
    steps.append("2. Собери: " + (", ".join(need) if need else "ничего дополнительно не требуется") + ".")
    steps.append("3. Перескажи заказ: позиции, итоговую сумму"
                 + (", контакты" if need else "") + " — и спроси «Подтверждаете заказ?».")
    steps.append("4. Только после явного «да» вызови create_order с customer_confirmed=true.")
    steps.append("5. После создания заказа бот САМ отдельным сообщением пришлёт клиенту реквизиты и кнопку отправки чека. "
                 "Реквизиты сам не пиши. Коротко скажи, что заказ создан, назови номер и сумму, и что после оплаты нужно отправить чек (фото или файл) в этот чат.")
    return f"""{s['system_prompt']}

Бизнес: {s['business_name']}. Валюта: {s['currency']}.
Стиль общения: {s['tone']}.
Доставка: {s['delivery_info'] or 'уточняй у менеджера'}. Режим работы: {s['work_hours'] or 'не указан'}.
Мин. сумма заказа: {s['min_order']}.
{'Когда уместно, мягко предлагай сопутствующие товары из каталога.' if s['upsell'] == '1' else 'Не предлагай допродажи.'}
Клиент: {u['name']} (@{u['username'] or 'нет'}).

ФОРМАТ: пиши простым текстом без markdown (без **, #, таблиц). Коротко.

ПОРЯДОК ОФОРМЛЕНИЯ:
""" + "\n".join(steps) + """

Никогда не выдумывай цены, скидки, сроки и наличие. Если не уверен — вызови call_human."""


async def gemini_chat(uid, u):
    hist = await q("SELECT role,text FROM messages WHERE uid=? ORDER BY id DESC LIMIT 24", (uid,))
    contents = [{"role": h["role"], "parts": [{"text": h["text"]}]} for h in reversed(hist)]
    while contents and contents[0]["role"] != "user":
        contents.pop(0)
    try:
        temp = float((await S("temperature")).replace(",", "."))
    except ValueError:
        temp = 0.4
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{await S('model')}:generateContent"
    system = await build_system(u)
    for _ in range(6):
        body = {"system_instruction": {"parts": [{"text": system}]}, "contents": contents,
                "tools": TOOLS, "generationConfig": {"temperature": temp}}
        data = {}
        for _try in range(2):
            r = await http.post(url, headers={"x-goog-api-key": GEMINI_KEY}, json=body)
            data = r.json()
            if "candidates" in data:
                break
            log.error("Gemini: %s", str(data)[:500])
            await asyncio.sleep(2)
        if "candidates" not in data:
            return None
        content = data["candidates"][0].get("content") or {}
        parts = content.get("parts", [])
        calls = [p["functionCall"] for p in parts if "functionCall" in p]
        if not calls:
            return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip() or None
        contents.append(content)
        resp = []
        for c in calls:
            try:
                res = await run_tool(c["name"], c.get("args", {}), uid, u)
            except Exception as e:
                log.exception("tool")
                res = {"error": str(e)}
            resp.append({"functionResponse": {"name": c["name"], "response": {"result": res}}})
        contents.append({"role": "user", "parts": resp})
    return None


async def restore_stock(items):
    for i in items:
        await q("UPDATE products SET stock=stock+? WHERE id=?", (i["qty"], i["id"]), commit=True)


async def do_handoff(uid, reason):
    await q("UPDATE users SET handoff=1 WHERE tg_id=?", (uid,), commit=True)
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    await notify(f"🙋 Нужен человек: {u['name']} @{u['username'] or '—'} uid:{uid}\nПричина: {reason}\n\n"
                 "↩️ Отвечайте реплаем на сообщения клиента — я перешлю ему.", kb([("🤖 Вернуть боту", f"cr:{uid}")]))


async def run_tool(name, a, uid, u):
    cur = await S("currency")
    if name == "search_catalog":
        words = (a.get("query") or "").lower().split()
        allp = await q("SELECT * FROM products WHERE active=1")
        hit = [p for p in allp if any(w in (p["name"] + " " + p["description"]).lower() for w in words)] if words else allp
        hit = hit or allp
        return {"currency": cur, "products": [{"product_id": p["id"], "name": p["name"], "price": p["price"],
                                               "in_stock": p["stock"], "description": p["description"]} for p in hit[:30]]}
    if name == "call_human":
        await do_handoff(uid, a.get("reason", "—"))
        return {"ok": True, "instruction": "Скажи клиенту, что передал диалог менеджеру и тот скоро ответит."}
    if name == "create_order":
        if not a.get("customer_confirmed"):
            return {"error": "Нет явного подтверждения. Перескажи заказ и спроси подтверждение."}
        phone, address = (a.get("phone") or "").strip(), (a.get("address") or "").strip()
        if await S("need_phone") == "1" and not phone:
            return {"error": "Нужен телефон клиента."}
        if await S("need_address") == "1" and not address:
            return {"error": "Нужен адрес доставки или слово «самовывоз»."}
        items, total, reserved = [], 0.0, []

        async def rollback():
            for pid, qty in reserved:
                await q("UPDATE products SET stock=stock+? WHERE id=?", (qty, pid), commit=True)
        for it in a.get("items") or []:
            try:
                pid, qty = int(it.get("product_id")), int(it.get("qty"))
            except (TypeError, ValueError):
                await rollback(); return {"error": "Неверные позиции заказа"}
            p = await q1("SELECT * FROM products WHERE id=? AND active=1", (pid,))
            if not p or qty < 1:
                await rollback(); return {"error": f"Товар {pid} не найден или неверное количество"}
            if not await qrc("UPDATE products SET stock=stock-? WHERE id=? AND stock>=?", (qty, pid, qty)):
                await rollback(); return {"error": f"Недостаточно «{p['name']}»: в наличии {p['stock']}"}
            reserved.append((pid, qty))
            items.append({"id": pid, "name": p["name"], "qty": qty, "price": p["price"]})
            total += p["price"] * qty
        if not items:
            return {"error": "Пустой заказ"}
        try:
            mn = float((await S("min_order")).replace(",", ".") or 0)
        except ValueError:
            mn = 0
        if total < mn:
            await rollback(); return {"error": f"Минимальная сумма заказа {mn:g} {cur}, сейчас {total:g}"}
        oid = await q("INSERT INTO orders(uid,name,phone,address,comment,items,total) VALUES(?,?,?,?,?,?,?)",
                      (uid, a.get("name") or u["name"], phone, address, a.get("comment", ""),
                       json.dumps(items, ensure_ascii=False), total), commit=True)
        await send_requisites(uid, oid, items, total)
        await notify(f"🛒 Новый заказ #{oid} от {u['name']} @{u['username'] or '—'}\n{fmt_items(items)}\nИтого: {total:g} {cur}\n"
                     f"📞 {phone or '—'}  📍 {address or '—'}\nСтатус: ждёт оплаты", kb([("Открыть", f"o:{oid}")]))
        return {"order_id": oid, "total": total, "currency": cur,
                "note": "Реквизиты и кнопка чека уже отправлены клиенту отдельным сообщением."}
    return {"error": "unknown tool"}


async def send_requisites(uid, oid, items, total):
    cur, req, note = await S("currency"), await S("requisites"), await S("payment_note")
    if req:
        text = f"🧾 Заказ #{oid}\n{fmt_items(items)}\n\nК оплате: {total:g} {cur}\n\n💳 Реквизиты:\n{req}\n\n{note}"
    else:
        text = f"🧾 Заказ #{oid}\nК оплате: {total:g} {cur}\n\nМенеджер скоро пришлёт реквизиты."
        await notify(f"⚠️ В заказе #{oid} нет реквизитов: заполните их в ⚙️ Настройки → 💳 Реквизиты и отправьте клиенту.")
    await safe_send(uid, text, kb([("🧾 Отправить чек", f"rcpt:{oid}")], [("❌ Отменить заказ", f"cancel:{oid}")]))


locks = defaultdict(asyncio.Lock)


async def chat_with_ai(uid, text):
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    if u["handoff"]:
        await q("INSERT INTO messages(uid,role,text) VALUES(?,?,?)", (uid, "user", text), commit=True)
        await notify(f"💬 {u['name']} @{u['username'] or '—'} uid:{uid}:\n{text}", kb([("🤖 Вернуть боту", f"cr:{uid}")]))
        return
    if await S("bot_enabled") != "1":
        if t := await S("disabled_text"):
            await safe_send(uid, t)
        return
    await q("INSERT INTO messages(uid,role,text) VALUES(?,?,?)", (uid, "user", text), commit=True)
    try:
        await bot.send_chat_action(uid, "typing")
    except Exception:
        pass
    async with locks[uid]:
        reply = await gemini_chat(uid, u)
    if reply is None:
        await do_handoff(uid, "Сбой ИИ")
        reply = await S("handoff_text")
    await q("INSERT INTO messages(uid,role,text) VALUES(?,?,?)", (uid, "model", reply), commit=True)
    await safe_send(uid, reply)


# ───────────────────────── Роли, фильтры, middleware ─────────────────────────
async def touch_user(u):
    row = await q1("SELECT role FROM users WHERE tg_id=?", (u.id,))
    uname = (u.username or "").lower()
    if row:
        await q("UPDATE users SET username=?, name=? WHERE tg_id=?", (uname, u.full_name, u.id), commit=True)
        role = row["role"]
        if role == "customer" and OWNER_ID == u.id and not await q1("SELECT 1 AS x FROM users WHERE role='owner'"):
            role = "owner"
            await q("UPDATE users SET role='owner' WHERE tg_id=?", (u.id,), commit=True)
        return role
    has_owner = await q1("SELECT 1 AS x FROM users WHERE role='owner'")
    role = "owner" if (not has_owner and OWNER_ID in (0, u.id)) else "customer"
    await q("INSERT INTO users(tg_id,username,name,role) VALUES(?,?,?,?)", (u.id, uname, u.full_name, role), commit=True)
    return role


class Gate(BaseMiddleware):
    async def __call__(self, handler, event, data):
        u = event.from_user
        chat = event.chat if isinstance(event, Message) else (event.message.chat if event.message else None)
        if u is None or u.is_bot or (chat and chat.type != "private"):
            return
        role = await touch_user(u)
        data["role"] = role
        if role == "banned":
            if isinstance(event, CallbackQuery):
                await event.answer("🚫 Доступ закрыт", show_alert=True)
            else:
                await event.answer("🚫 Доступ закрыт.", reply_markup=ReplyKeyboardRemove())
            return
        return await handler(event, data)


class IsAdmin(BaseFilter):
    async def __call__(self, event, role: str = "customer"):
        return role in ("admin", "owner")


class IsOwner(BaseFilter):
    async def __call__(self, event, role: str = "customer"):
        return role == "owner"


class ReplyToClient(BaseFilter):
    async def __call__(self, m: Message):
        rm = m.reply_to_message
        mm = re.search(r"uid:(\d+)", (rm.text or rm.caption or "")) if rm else None
        return {"cuid": int(mm.group(1))} if mm else False


class St(StatesGroup):
    cat_name = State(); cat_price = State(); cat_stock = State(); cat_desc = State()
    prod_edit = State(); set_val = State(); own_target = State(); bcast = State(); receipt = State()


nav, own, adm, cust = Router(), Router(), Router(), Router()
own.message.filter(IsOwner()); own.callback_query.filter(IsOwner())
adm.message.filter(IsAdmin()); adm.callback_query.filter(IsAdmin())


async def show(cb: CallbackQuery, text, markup=None):
    try:
        await cb.message.edit_text(text[:4000], reply_markup=markup)
    except TelegramBadRequest:
        pass
    await cb.answer()


# ───────────────────────── Навигация (кнопки меню) ─────────────────────────
@nav.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext, role: str):
    await state.clear()
    text = await S("greeting")
    if role in ("admin", "owner"):
        text += f"\n\nВы вошли как {ICON[role]} {'владелец' if role == 'owner' else 'админ'}. Кнопки управления — внизу."
    await m.answer(text, reply_markup=reply_kb(role))


@nav.message(Command("id"))
async def cmd_id(m: Message):
    await m.answer(f"Ваш id: {m.from_user.id}")


@nav.message(Command("cancel"))
async def cmd_cancel(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Отменено.")


@nav.message(Command("reset"))
async def cmd_reset(m: Message, state: FSMContext):
    await state.clear()
    await q("DELETE FROM messages WHERE uid=?", (m.from_user.id,), commit=True)
    await q("UPDATE users SET handoff=0 WHERE tg_id=?", (m.from_user.id,), commit=True)
    await m.answer("🔄 Диалог сброшен. Чем помочь?")


@nav.message(F.text == B_CAT)
async def customer_catalog(m: Message, state: FSMContext):
    await state.clear()
    cur = await S("currency")
    ps = await q("SELECT * FROM products WHERE active=1 AND stock>0 ORDER BY id")
    if not ps:
        return await m.answer("Каталог пока пуст 🙈")
    lines = "\n".join(f"• {p['name']} — {p['price']:g} {cur}" + (f"\n  {p['description']}" if p["description"] else "") for p in ps[:30])
    await m.answer(("🛍 Каталог\n\n" + lines)[:3900] + "\n\nНажмите на товар, чтобы заказать 👇",
                   reply_markup=kb(*[[(f"🛒 {p['name']} — {p['price']:g}{cur}", f"buy:{p['id']}")] for p in ps[:20]]))


@nav.message(F.text == B_ORD)
async def my_orders(m: Message, state: FSMContext):
    await state.clear()
    orders = await q("SELECT * FROM orders WHERE uid=? ORDER BY id DESC LIMIT 8", (m.from_user.id,))
    if not orders:
        return await m.answer("Заказов пока нет. Нажмите «🛍 Каталог» или просто напишите, что хотите 🙂")
    cur, text, rows = await S("currency"), "", []
    for o in orders:
        its = ", ".join(f"{i['name']}×{i['qty']}" for i in json.loads(o["items"]))
        text += f"#{o['id']} · {ST[o['status']]} · {o['total']:g} {cur}\n{its}\n\n"
        if o["status"] == "awaiting_payment":
            rows.append([(f"🧾 Чек по #{o['id']}", f"rcpt:{o['id']}"), (f"❌ Отмена #{o['id']}", f"cancel:{o['id']}")])
    await m.answer(text[:4000], reply_markup=kb(*rows) if rows else None)


@nav.message(F.text == B_HUM)
async def human_btn(m: Message, state: FSMContext):
    await state.clear()
    await do_handoff(m.from_user.id, "Клиент нажал «Менеджер»")
    await m.answer(await S("handoff_text"), reply_markup=kb([("🤖 Вернуться к ассистенту", "back2bot")]))


@nav.message(F.text == B_SET, IsAdmin())
async def open_settings(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("⚙️ Настройки ассистента", reply_markup=await settings_markup())


@nav.message(F.text == B_ADM, IsAdmin())
async def open_panel(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🛠 Админ-панель", reply_markup=await panel_markup())


@nav.message(F.text == B_OWN, IsOwner())
async def open_owner(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("👑 Панель владельца", reply_markup=await owner_markup())


# ───────────────────────── Клиент: инлайн-кнопки, чеки, ИИ ─────────────────────────
@cust.callback_query(F.data == "back2bot")
async def cb_back(cb: CallbackQuery):
    await q("UPDATE users SET handoff=0 WHERE tg_id=?", (cb.from_user.id,), commit=True)
    await cb.answer("🤖 Ассистент снова с вами")
    await safe_send(cb.from_user.id, "Я снова на связи! Чем помочь?")


@cust.callback_query(F.data.startswith("buy:"))
async def cb_buy(cb: CallbackQuery):
    p = await q1("SELECT * FROM products WHERE id=?", (int(cb.data[4:]),))
    await cb.answer()
    if p:
        await chat_with_ai(cb.from_user.id, f"Хочу заказать: {p['name']}")


@cust.callback_query(F.data.startswith("cancel:"))
async def cb_cancel_order(cb: CallbackQuery):
    o = await q1("SELECT * FROM orders WHERE id=? AND uid=?", (int(cb.data[7:]), cb.from_user.id))
    if not o or o["status"] != "awaiting_payment":
        return await cb.answer("Этот заказ уже нельзя отменить", show_alert=True)
    if await qrc("UPDATE orders SET status='cancelled' WHERE id=? AND status='awaiting_payment'", (o["id"],)):
        await restore_stock(json.loads(o["items"]))
        await notify(f"❌ Клиент {cb.from_user.full_name} отменил заказ #{o['id']}")
    await show(cb, f"❌ Заказ #{o['id']} отменён.")


@cust.callback_query(F.data.startswith("rcpt:"))
async def cb_receipt(cb: CallbackQuery, state: FSMContext):
    o = await q1("SELECT * FROM orders WHERE id=? AND uid=?", (int(cb.data[5:]), cb.from_user.id))
    if not o:
        return await cb.answer("Заказ не найден", show_alert=True)
    if o["status"] == "checking":
        return await cb.answer("Чек уже на проверке 🔎", show_alert=True)
    if o["status"] != "awaiting_payment":
        return await cb.answer("По этому заказу оплата не требуется", show_alert=True)
    await state.set_state(St.receipt)
    await state.update_data(rcpt_order=o["id"])
    await cb.answer()
    await safe_send(cb.from_user.id, f"Отправьте фото или файл чека по заказу #{o['id']} (/cancel — отмена).")


@cust.message(StateFilter(None, St.receipt), F.photo | F.document)
async def got_receipt(m: Message, state: FSMContext):
    uid = m.from_user.id
    oid = (await state.get_data()).get("rcpt_order")
    o = await q1("SELECT * FROM orders WHERE id=? AND uid=?", (oid, uid)) if oid else None
    if not o or o["status"] != "awaiting_payment":
        o = await q1("SELECT * FROM orders WHERE uid=? AND status='awaiting_payment' ORDER BY id DESC LIMIT 1", (uid,))
    await state.clear()
    if not o:
        return await m.answer("Не нашёл заказов, ожидающих оплаты. Если нужна помощь, нажмите «🙋 Менеджер».")
    file_id, kind = (m.photo[-1].file_id, "photo") if m.photo else (m.document.file_id, "doc")
    rid = await q("INSERT INTO receipts(order_id,uid,file_id,kind) VALUES(?,?,?,?)", (o["id"], uid, file_id, kind), commit=True)
    await q("UPDATE orders SET status='checking' WHERE id=?", (o["id"],), commit=True)
    await m.answer(f"✅ Чек по заказу #{o['id']} получен и передан на проверку. Мы сообщим результат здесь.")
    await push_receipt(rid, await staff_ids())


@cust.message(St.receipt, F.text)
async def receipt_text(m: Message):
    await m.answer("Пришлите чек фото или файлом. Для отмены — /cancel.")


@cust.message(StateFilter(None), F.text)
async def talk(m: Message):
    await chat_with_ai(m.from_user.id, m.text)


# ───────────────────────── Чеки: отправка админам и решение ─────────────────────────
async def receipt_caption(rid):
    r = await q1("SELECT * FROM receipts WHERE id=?", (rid,))
    o = await q1("SELECT * FROM orders WHERE id=?", (r["order_id"],))
    u = await q1("SELECT * FROM users WHERE tg_id=?", (r["uid"],))
    cur = await S("currency")
    return (f"🧾 Чек #{rid} · заказ #{o['id']}\n👤 {u['name']} @{u['username'] or '—'}\n"
            f"Сумма: {o['total']:g} {cur}\n{', '.join(i['name'] + '×' + str(i['qty']) for i in json.loads(o['items']))}")[:900]


async def push_receipt(rid, targets):
    r = await q1("SELECT * FROM receipts WHERE id=?", (rid,))
    cap, mk = await receipt_caption(rid), kb([("✅ Одобрить", f"rok:{rid}"), ("❌ Отклонить", f"rno:{rid}")])
    for chat in targets:
        try:
            send = bot.send_photo if r["kind"] == "photo" else bot.send_document
            msg = await send(chat, r["file_id"], caption=cap, reply_markup=mk)
            await q("INSERT INTO receipt_msgs VALUES(?,?,?)", (rid, chat, msg.message_id), commit=True)
        except Exception as e:
            log.warning("receipt -> %s: %s", chat, e)


async def close_receipt_msgs(rid, suffix):
    cap = await receipt_caption(rid)
    for r in await q("SELECT * FROM receipt_msgs WHERE receipt_id=?", (rid,)):
        try:
            await bot.edit_message_caption(chat_id=r["chat_id"], message_id=r["message_id"], caption=cap + suffix, reply_markup=None)
        except Exception:
            pass
    await q("DELETE FROM receipt_msgs WHERE receipt_id=?", (rid,), commit=True)


@adm.callback_query(F.data.startswith("rok:"))
async def cb_receipt_ok(cb: CallbackQuery):
    rid = int(cb.data[4:])
    if not await qrc("UPDATE receipts SET status='approved', by_admin=? WHERE id=? AND status='pending'", (cb.from_user.id, rid)):
        return await cb.answer("Уже обработан другим админом", show_alert=True)
    r = await q1("SELECT * FROM receipts WHERE id=?", (rid,))
    await qrc("UPDATE orders SET status='paid' WHERE id=? AND status IN ('checking','awaiting_payment')", (r["order_id"],))
    await safe_send(r["uid"], f"✅ Оплата по заказу #{r['order_id']} подтверждена! Заказ принят в работу. Спасибо 🙌")
    await cb.answer("Одобрено")
    await close_receipt_msgs(rid, f"\n\n✅ Одобрил: {cb.from_user.full_name}")


@adm.callback_query(F.data.startswith("rno:"))
async def cb_receipt_no(cb: CallbackQuery):
    rid = int(cb.data[4:])
    if not await qrc("UPDATE receipts SET status='rejected', by_admin=? WHERE id=? AND status='pending'", (cb.from_user.id, rid)):
        return await cb.answer("Уже обработан другим админом", show_alert=True)
    r = await q1("SELECT * FROM receipts WHERE id=?", (rid,))
    await qrc("UPDATE orders SET status='awaiting_payment' WHERE id=? AND status='checking'", (r["order_id"],))
    await safe_send(r["uid"], f"❌ Чек по заказу #{r['order_id']} не принят. Проверьте оплату и отправьте чек ещё раз.",
                    kb([("🧾 Отправить чек снова", f"rcpt:{r['order_id']}")], [("🙋 Позвать менеджера", "need_human")]))
    await cb.answer("Отклонено")
    await close_receipt_msgs(rid, f"\n\n❌ Отклонил: {cb.from_user.full_name}")


@cust.callback_query(F.data == "need_human")
async def cb_need_human(cb: CallbackQuery):
    await do_handoff(cb.from_user.id, "Вопрос по отклонённому чеку")
    await cb.answer()
    await safe_send(cb.from_user.id, await S("handoff_text"), kb([("🤖 Вернуться к ассистенту", "back2bot")]))


@adm.callback_query(F.data == "rlist")
async def cb_rlist(cb: CallbackQuery):
    rs = await q("SELECT * FROM receipts WHERE status='pending' ORDER BY id")
    await show(cb, "🧾 Чеки на проверке" if rs else "Чеков на проверке нет 🎉",
               kb(*[[(f"Чек #{r['id']} · заказ #{r['order_id']}", f"rv:{r['id']}")] for r in rs[:20]], [("⬅️ Панель", "panel")]))


@adm.callback_query(F.data.startswith("rv:"))
async def cb_rview(cb: CallbackQuery):
    rid = int(cb.data[3:])
    r = await q1("SELECT * FROM receipts WHERE id=? AND status='pending'", (rid,))
    if not r:
        return await cb.answer("Уже обработан", show_alert=True)
    await cb.answer()
    await push_receipt(rid, [cb.from_user.id])


# ───────────────────────── Админ-панель ─────────────────────────
async def panel_markup():
    n = (await q1("SELECT COUNT(*) n FROM receipts WHERE status='pending'"))["n"]
    return kb([("📋 Заказы", "orders"), (f"🧾 Чеки ({n})", "rlist")], [("🛍 Каталог", "cat"), ("⚙️ Настройки", "set")],
              [("📊 Статистика", "stats"), ("📣 Рассылка", "bcast")])


@adm.callback_query(F.data == "panel")
async def cb_panel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await show(cb, "🛠 Админ-панель", await panel_markup())


@adm.callback_query(F.data == "stats")
async def cb_stats(cb: CallbackQuery):
    rows = await q("SELECT status, COUNT(*) n, COALESCE(SUM(total),0) s FROM orders GROUP BY status")
    cur = await S("currency")
    lines = [f"{ST[r['status']]}: {r['n']} шт. / {r['s']:g} {cur}" for r in rows] or ["Заказов пока нет"]
    rev = sum(r["s"] for r in rows if r["status"] in ("paid", "shipped", "done"))
    users = (await q1("SELECT COUNT(*) n FROM users"))["n"]
    pend = (await q1("SELECT COUNT(*) n FROM receipts WHERE status='pending'"))["n"]
    await show(cb, "📊 Статистика\n\n" + "\n".join(lines) + f"\n\n💰 Выручка: {rev:g} {cur}\n👥 Пользователей: {users}\n🧾 Чеков на проверке: {pend}",
               kb([("⬅️ Панель", "panel")]))


# Заказы
@adm.callback_query(F.data == "orders")
async def cb_orders(cb: CallbackQuery):
    rows = await q("SELECT * FROM orders ORDER BY id DESC LIMIT 15")
    cur = await S("currency")
    await show(cb, "📋 Последние заказы" if rows else "Заказов пока нет",
               kb(*[[(f"#{o['id']} {ST[o['status']][:2]} {o['total']:g}{cur} {o['name']}", f"o:{o['id']}")] for o in rows], [("⬅️ Панель", "panel")]))


@adm.callback_query(F.data.startswith("o:"))
async def cb_order(cb: CallbackQuery):
    o = await q1("SELECT * FROM orders WHERE id=?", (int(cb.data[2:]),))
    if not o:
        return await cb.answer("Не найден")
    cur = await S("currency")
    st = [[(v, f"os:{o['id']}:{k}")] for k, v in ST.items() if k != o["status"]]
    await show(cb, f"Заказ #{o['id']} — {ST[o['status']]}\n{o['ts']}\n\n{fmt_items(json.loads(o['items']))}\nИтого: {o['total']:g} {cur}\n"
                   f"👤 {o['name']}  📞 {o['phone'] or '—'}\n📍 {o['address'] or '—'}\n💬 {o['comment'] or '—'}\nuid:{o['uid']}",
               kb(*st, [("⬅️ К заказам", "orders")]))


@adm.callback_query(F.data.startswith("os:"))
async def cb_order_status(cb: CallbackQuery):
    _, oid, st = cb.data.split(":")
    o = await q1("SELECT * FROM orders WHERE id=?", (int(oid),))
    if not o or st not in ST:
        return await cb.answer("Ошибка")
    if st == "cancelled" and o["status"] != "cancelled":
        await restore_stock(json.loads(o["items"]))
    await q("UPDATE orders SET status=? WHERE id=?", (st, oid), commit=True)
    await safe_send(o["uid"], f"Статус заказа #{oid}: {ST[st]}")
    cb.data = f"o:{oid}"
    await cb_order(cb)


# Каталог
@adm.callback_query(F.data == "cat")
async def cb_cat(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    cur = await S("currency")
    ps = await q("SELECT * FROM products ORDER BY id")
    await show(cb, "🛍 Каталог" if ps else "Каталог пуст. Добавьте первый товар 👇",
               kb(*[[(f"{p['name']} — {p['price']:g}{cur} ({p['stock']} шт.)", f"p:{p['id']}")] for p in ps],
                  [("➕ Добавить товар", "cat_add")], [("⬅️ Панель", "panel")]))


@adm.callback_query(F.data.startswith("p:"))
async def cb_prod(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    pid = int(cb.data[2:])
    p = await q1("SELECT * FROM products WHERE id=?", (pid,))
    if not p:
        return await cb.answer("Не найден")
    cur = await S("currency")
    await show(cb, f"{p['name']}\nЦена: {p['price']:g} {cur}\nОстаток: {p['stock']}\nОписание: {p['description'] or '—'}",
               kb([("✏️ Название", f"pe:{pid}:name"), ("💰 Цена", f"pe:{pid}:price")],
                  [("📦 Остаток", f"pe:{pid}:stock"), ("📝 Описание", f"pe:{pid}:description")],
                  [("🗑 Удалить", f"pd:{pid}")], [("⬅️ Каталог", "cat")]))


@adm.callback_query(F.data.startswith("pd:"))
async def cb_prod_del(cb: CallbackQuery):
    await q("DELETE FROM products WHERE id=?", (int(cb.data[3:]),), commit=True)
    await show(cb, "🗑 Удалено", kb([("⬅️ Каталог", "cat")]))


@adm.callback_query(F.data.startswith("pe:"))
async def cb_prod_edit(cb: CallbackQuery, state: FSMContext):
    _, pid, field = cb.data.split(":")
    await state.set_state(St.prod_edit)
    await state.update_data(pid=int(pid), field=field)
    await show(cb, "Отправьте новое значение (/cancel — отмена):")


@adm.message(St.prod_edit, F.text)
async def prod_edit_val(m: Message, state: FSMContext):
    d = await state.get_data()
    field, val = d["field"], m.text.strip()
    try:
        if field == "price": val = float(val.replace(",", "."))
        elif field == "stock": val = int(val)
        elif field not in ("name", "description"): return
    except ValueError:
        return await m.answer("Нужно число. Ещё раз или /cancel")
    await q(f"UPDATE products SET {field}=? WHERE id=?", (val, d["pid"]), commit=True)  # field — из белого списка
    await state.clear()
    await m.answer("✅ Сохранено", reply_markup=kb([("⬅️ К товару", f"p:{d['pid']}")]))


@adm.callback_query(F.data == "cat_add")
async def cb_cat_add(cb: CallbackQuery, state: FSMContext):
    await state.set_state(St.cat_name)
    await show(cb, "Название товара? (/cancel — отмена)")


@adm.message(St.cat_name, F.text)
async def add_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text.strip())
    await state.set_state(St.cat_price)
    await m.answer("Цена (числом)?")


@adm.message(St.cat_price, F.text)
async def add_price(m: Message, state: FSMContext):
    try:
        price = float(m.text.replace(",", ".").strip())
    except ValueError:
        return await m.answer("Нужно число")
    await state.update_data(price=price)
    await state.set_state(St.cat_stock)
    await m.answer("Остаток (целое число)?")


@adm.message(St.cat_stock, F.text)
async def add_stock(m: Message, state: FSMContext):
    if not m.text.strip().isdigit():
        return await m.answer("Нужно целое число")
    await state.update_data(stock=int(m.text))
    await state.set_state(St.cat_desc)
    await m.answer("Описание (или «-» пропустить)?")


@adm.message(St.cat_desc, F.text)
async def add_desc(m: Message, state: FSMContext):
    d = await state.get_data()
    desc = "" if m.text.strip() == "-" else m.text.strip()
    await q("INSERT INTO products(name,price,stock,description) VALUES(?,?,?,?)", (d["name"], d["price"], d["stock"], desc), commit=True)
    await state.clear()
    await m.answer(f"✅ Добавлено: {d['name']}", reply_markup=kb([("➕ Ещё", "cat_add")], [("⬅️ Каталог", "cat")]))


# Настройки ассистента
async def settings_markup():
    rows = []
    for k, (label, _d, t) in SET.items():
        if t == "hidden":
            continue
        v = await S(k)
        pv = ("✅" if v == "1" else "⛔") if t == "toggle" else (v if isinstance(t, list) else ("✓" if v else "—"))
        rows.append([(f"{label}: {pv}"[:60], f"s:{k}")])
    rows.append([("⬅️ Панель", "panel")])
    return kb(*rows)


@adm.callback_query(F.data == "set")
async def cb_set(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await show(cb, "⚙️ Настройки ассистента", await settings_markup())


@adm.callback_query(F.data.startswith("s:"))
async def cb_set_one(cb: CallbackQuery, state: FSMContext):
    key = cb.data[2:]
    if key not in SET or SET[key][2] == "hidden":
        return await cb.answer()
    label, default, t = SET[key]
    if t == "toggle":
        await set_S(key, "0" if await S(key) == "1" else "1")
        return await show(cb, "⚙️ Настройки ассистента", await settings_markup())
    if isinstance(t, list):
        return await show(cb, f"{label}\nСейчас: {await S(key)}",
                          kb(*[[(o, f"sc:{key}:{i}")] for i, o in enumerate(t)], [("⬅️ Назад", "set")]))
    await state.set_state(St.set_val)
    await state.update_data(key=key)
    await show(cb, f"{label}\n\nСейчас:\n{(await S(key))[:3000] or '—'}\n\nОтправьте новое значение («-» очистить, /cancel — отмена)",
               kb([("↩️ По умолчанию", f"sr:{key}")], [("⬅️ Назад", "set")]))


@adm.callback_query(F.data.startswith("sc:"))
async def cb_set_choice(cb: CallbackQuery):
    _, key, i = cb.data.split(":")
    await set_S(key, SET[key][2][int(i)])
    await show(cb, "⚙️ Настройки ассистента", await settings_markup())


@adm.callback_query(F.data.startswith("sr:"))
async def cb_set_reset(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await set_S(cb.data[3:], SET[cb.data[3:]][1])
    await show(cb, "✅ Сброшено", await settings_markup())


@adm.message(St.set_val, F.text)
async def set_val(m: Message, state: FSMContext):
    key, val = (await state.get_data())["key"], m.text.strip()
    if val == "-":
        val = ""
    if key in ("temperature", "min_order") and val:
        try:
            x = float(val.replace(",", "."))
            assert 0 <= x <= (2 if key == "temperature" else 10 ** 9)
            val = val.replace(",", ".")
        except Exception:
            return await m.answer("Нужно число (для температуры 0–2)")
    await set_S(key, val)
    await state.clear()
    await m.answer("✅ Сохранено", reply_markup=await settings_markup())


# Рассылка
@adm.callback_query(F.data == "bcast")
async def cb_bcast(cb: CallbackQuery, state: FSMContext):
    await state.set_state(St.bcast)
    await show(cb, "📣 Пришлите текст рассылки для всех пользователей (/cancel — отмена)")


@adm.message(St.bcast, F.text)
async def bcast_text(m: Message, state: FSMContext):
    await state.update_data(text=m.text)
    n = (await q1("SELECT COUNT(*) n FROM users WHERE role!='banned'"))["n"]
    await m.answer(f"Отправить {n} получателям?\n\n{m.text[:1500]}", reply_markup=kb([("✅ Отправить", "bc_go")], [("Отмена", "panel")]))


@adm.callback_query(F.data == "bc_go")
async def bcast_go(cb: CallbackQuery, state: FSMContext):
    text = (await state.get_data()).get("text")
    await state.clear()
    if not text:
        return await cb.answer("Нет текста", show_alert=True)
    await cb.answer("Отправляю…")
    ok = 0
    for u in await q("SELECT tg_id FROM users WHERE role!='banned'"):
        try:
            await bot.send_message(u["tg_id"], text)
            ok += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)
    await safe_send(cb.from_user.id, f"✅ Доставлено: {ok}")


# Ответ клиенту реплаем + возврат боту
@adm.message(StateFilter(None), F.text, ReplyToClient())
async def reply_to_client(m: Message, cuid: int):
    await q("INSERT INTO messages(uid,role,text) VALUES(?,?,?)", (cuid, "model", m.text), commit=True)
    await safe_send(cuid, m.text)
    await m.answer("✅ Отправлено клиенту")


@adm.callback_query(F.data.startswith("cr:"))
async def cb_release(cb: CallbackQuery):
    uid = int(cb.data[3:])
    await q("UPDATE users SET handoff=0 WHERE tg_id=?", (uid,), commit=True)
    await cb.answer("🤖 Диалог возвращён боту", show_alert=True)
    await safe_send(uid, "Я снова на связи! Чем помочь?")


# ───────────────────────── Панель владельца ─────────────────────────
async def owner_markup():
    on = await S("bot_enabled") == "1"
    return kb([("🛡 Назначить админа", "oa:admin"), ("👥 Админы", "olist:admin")],
              [("🚫 Забанить", "oa:ban"), ("♻️ Забаненные", "olist:banned")],
              [("👤 Пользователи", "olist:customer"), ("👑 Передать права", "oa:transfer")],
              [("🔴 Выключить бота" if on else "🟢 Включить бота", "otoggle")])


async def find_user(text):
    t = text.strip().lstrip("@").lower()
    return await q1("SELECT * FROM users WHERE tg_id=?", (int(t),)) if t.isdigit() else await q1("SELECT * FROM users WHERE username=?", (t,))


async def apply_role(target, role):
    await q("UPDATE users SET role=?, handoff=0 WHERE tg_id=?", (role, target), commit=True)
    msg = {"admin": "🛡 Вам назначена роль администратора! Кнопки управления появились внизу.",
           "customer": "Ваша роль изменена: теперь вы обычный пользователь.", "banned": "🚫 Доступ закрыт."}[role]
    await safe_send(target, msg, ReplyKeyboardRemove() if role == "banned" else reply_kb(role))


@own.callback_query(F.data == "otoggle")
async def cb_otoggle(cb: CallbackQuery):
    await set_S("bot_enabled", "0" if await S("bot_enabled") == "1" else "1")
    await show(cb, "👑 Панель владельца", await owner_markup())


@own.callback_query(F.data.startswith("oa:"))
async def cb_oa(cb: CallbackQuery, state: FSMContext):
    action = cb.data[3:]
    await state.set_state(St.own_target)
    await state.update_data(action=action)
    what = {"admin": "назначить админом", "ban": "забанить", "transfer": "передать права владельца"}[action]
    await show(cb, f"Отправьте @username или id пользователя, которого нужно {what}.\n"
                   "Он должен хотя бы раз написать боту. (/cancel — отмена)")


@own.message(St.own_target, F.text)
async def own_target(m: Message, state: FSMContext):
    action = (await state.get_data())["action"]
    u = await find_user(m.text)
    if not u:
        return await m.answer("Не нашёл. Пусть он сначала напишет боту /start. Ещё раз или /cancel")
    if u["tg_id"] == m.from_user.id:
        return await m.answer("Это вы 🙂 Укажите другого пользователя.")
    await state.clear()
    if action == "transfer":
        return await m.answer(f"⚠️ Передать права владельца: {u['name']} @{u['username'] or '—'}?\nВы станете админом.",
                              reply_markup=kb([("✅ Да, передать", f"otc:{u['tg_id']}")], [("Отмена", "ohome")]))
    await apply_role(u["tg_id"], "admin" if action == "admin" else "banned")
    await m.answer(f"✅ {u['name']}: {'назначен админом' if action == 'admin' else 'забанен'}", reply_markup=kb([("⬅️ Панель владельца", "ohome")]))


@own.callback_query(F.data == "ohome")
async def cb_ohome(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await show(cb, "👑 Панель владельца", await owner_markup())


@own.callback_query(F.data.startswith("olist:"))
async def cb_olist(cb: CallbackQuery):
    role = cb.data[6:]
    us = await q("SELECT * FROM users WHERE role=? ORDER BY ts DESC LIMIT 20", (role,))
    title = {"admin": "👥 Админы", "banned": "♻️ Забаненные", "customer": "👤 Пользователи (последние 20)"}[role]
    await show(cb, title if us else title + "\n\nСписок пуст",
               kb(*[[(f"{u['name']} @{u['username'] or '—'}", f"ou:{u['tg_id']}")] for u in us], [("⬅️ Назад", "ohome")]))


@own.callback_query(F.data.startswith("ou:"))
async def cb_ouser(cb: CallbackQuery):
    uid = int(cb.data[3:])
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    if not u:
        return await cb.answer()
    rows = []
    if u["role"] != "owner":
        if u["role"] == "customer": rows.append([("🛡 Назначить админом", f"orole:{uid}:admin")])
        if u["role"] == "admin": rows.append([("⬇️ Снять с админа", f"orole:{uid}:customer")])
        if u["role"] == "banned": rows.append([("♻️ Разбанить", f"orole:{uid}:customer")])
        else: rows.append([("🚫 Забанить", f"orole:{uid}:banned")])
        rows.append([("👑 Передать права", f"ot:{uid}")])
    await show(cb, f"{ICON[u['role']]} {u['name']} @{u['username'] or '—'}\nid {uid}\nРоль: {u['role']}", kb(*rows, [("⬅️ Назад", "ohome")]))


@own.callback_query(F.data.startswith("orole:"))
async def cb_orole(cb: CallbackQuery):
    _, uid, role = cb.data.split(":")
    uid = int(uid)
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    if uid == cb.from_user.id or not u or u["role"] == "owner" or role not in ("admin", "customer", "banned"):
        return await cb.answer("Нельзя", show_alert=True)
    await apply_role(uid, role)
    await show(cb, f"✅ {u['name']}: роль → {role}", kb([("⬅️ Панель владельца", "ohome")]))


@own.callback_query(F.data.startswith("ot:"))
async def cb_ot(cb: CallbackQuery):
    uid = int(cb.data[3:])
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    await show(cb, f"⚠️ Передать права владельца: {u['name']} @{u['username'] or '—'}?\nВы станете админом.",
               kb([("✅ Да, передать", f"otc:{uid}")], [("Отмена", "ohome")]))


@own.callback_query(F.data.startswith("otc:"))
async def cb_otc(cb: CallbackQuery):
    new = int(cb.data[4:])
    if new == cb.from_user.id or not await q1("SELECT 1 AS x FROM users WHERE tg_id=?", (new,)):
        return await cb.answer("Нельзя", show_alert=True)
    await q("UPDATE users SET role='admin' WHERE tg_id=?", (cb.from_user.id,), commit=True)
    await q("UPDATE users SET role='owner', handoff=0 WHERE tg_id=?", (new,), commit=True)
    await safe_send(new, "👑 Вам переданы права владельца бота!", reply_kb("owner"))
    await safe_send(cb.from_user.id, "Теперь вы администратор.", reply_kb("admin"))
    await show(cb, "✅ Права владельца переданы.")


# ───────────────────────── ЗАПУСК ─────────────────────────
async def health_server():
    """Мини-веб-сервер: Render (тип Web Service) требует открытый порт."""
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="ok"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "10000"))).start()


async def keepalive():
    """Раз в 10 минут пингует свой URL, чтобы бесплатный Render не засыпал."""
    url = os.getenv("RENDER_EXTERNAL_URL")
    while url:
        await asyncio.sleep(600)
        try:
            await http.get(url)
        except Exception:
            pass


async def main():
    await init_db()
    await health_server()
    asyncio.create_task(keepalive())
    dp = Dispatcher()
    dp.message.outer_middleware(Gate())
    dp.callback_query.outer_middleware(Gate())
    dp.include_routers(nav, own, adm, cust)
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
