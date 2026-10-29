"""Telegram AI-продавец на Gemini.
Консультация -> заказ -> реквизиты (+QR) -> чек -> одобрение админом.
Запуск: python bot.py   (все секреты только в переменных окружения / .env)
"""
import asyncio, base64, io, json, logging, os, re
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
TEMP = 0.6                                        # температура ИИ зашита в коде (из настроек убрана)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("shop")
bot = Bot(TG_TOKEN)
http = httpx.AsyncClient(timeout=60)

# ───────────────────────── НАСТРОЙКИ АССИСТЕНТА ─────────────────────────
# ключ: (название, значение по умолчанию, тип)  тип: "text" | "toggle" | "photo" | список вариантов | "hidden"
SET = {
    "business_name": ("🏪 Название бизнеса", "Мой магазин", "text"),
    "greeting": ("👋 Приветствие (/start)", "Здравствуйте! Я ассистент магазина. Помогу выбрать товар и оформить заказ 🙂\n"
                 "Можно писать текстом, отправлять голосовые или фото товара 🎤📷", "text"),
    "system_prompt": ("🧠 Инструкция для ИИ", "Ты опытный консультант-продавец. Помогай выбрать товар, отвечай по делу. "
                      "Цены и наличие бери ТОЛЬКО из search_catalog, ничего не выдумывай.", "text"),
    "tone": ("🎭 Стиль общения", "дружелюбный", ["дружелюбный", "деловой", "краткий", "энергичный с эмодзи"]),
    "upsell": ("🛍 Допродажи (предлагать сопутствующее)", "1", "toggle"),
    "need_phone": ("📞 Запрашивать телефон", "1", "toggle"),
    "need_address": ("📍 Запрашивать адрес доставки", "1", "toggle"),
    "min_order": ("💰 Мин. сумма заказа (0 — нет)", "0", "text"),
    "delivery_info": ("🚚 Условия доставки", "Доставка 1–2 дня. Самовывоз бесплатно.", "text"),
    "work_hours": ("🕒 Режим работы", "", "text"),
    "requisites": ("💳 Реквизиты для оплаты (текст)", "", "text"),
    "requisites_photo": ("🖼 QR-код / фото к реквизитам", "", "photo"),
    "payment_note": ("📝 Подсказка после реквизитов",
                     "После оплаты нажмите «🧾 Отправить чек» в меню внизу и пришлите фото или файл чека 🙏", "text"),
    "handoff_text": ("🙋 Текст после вопроса менеджеру", "Передал ваш вопрос менеджеру, он скоро ответит 🙌", "text"),
    "disabled_text": ("⏸ Ответ при выключенном боте", "Сейчас бот отключён. Загляните позже 🙏", "text"),
    "currency": ("💱 Валюта", "₽", "text"),
    "model": ("🤖 Модель Gemini", "gemini-2.5-flash", "text"),
    "offer": ("", "", "hidden"),          # «Что предлагать покупателям» — отдельная кнопка у админа
    "bot_enabled": ("", "1", "hidden"),
}
ST = {"awaiting_payment": "⏳ Ждёт оплаты", "checking": "🔎 Чек на проверке", "paid": "💳 Оплачен",
      "shipped": "🚚 Отправлен", "done": "✅ Выполнен", "cancelled": "❌ Отменён"}
ICON = {"owner": "👑", "admin": "🛡", "customer": "👤", "banned": "🚫"}

# Кнопки нижнего меню
B_CAT, B_ORD, B_HUM = "🛍 Каталог", "📦 Мои заказы", "🙋 Менеджер"
B_RCPT, B_PICK, B_BACK = "🧾 Отправить чек", "🎯 Подобрать за меня", "🤖 Вернуться к ассистенту"
B_CANCEL, B_HOME = "❌ Отмена", "🏠 Главное меню"
B_SET, B_ADM, B_OWN, B_OFFER = "⚙️ Настройки", "🛠 Админ-панель", "👑 Панель владельца", "💡 Что предлагать"
B_AORD, B_ARCP, B_ACAT, B_AADD = "📋 Заказы", "🧾 Чеки на проверке", "🗂 Товары", "➕ Добавить товар"
B_ASTAT, B_ABC = "📊 Статистика", "📣 Рассылка"
B_OADM, B_OLADM, B_OBAN, B_OLBAN = "🛡 Назначить админа", "👥 Админы", "🚫 Забанить", "♻️ Забаненные"
B_OUSR, B_OTR, B_OOFF, B_OON = "👤 Пользователи", "👑 Передать права", "🔴 Выключить бота", "🟢 Включить бота"


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
            address TEXT, comment TEXT, items TEXT, total REAL, status TEXT DEFAULT 'awaiting_payment',
            ts TEXT DEFAULT CURRENT_TIMESTAMP, reminded INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, uid INTEGER,
            file_id TEXT, kind TEXT, status TEXT DEFAULT 'pending', by_admin INTEGER, ts TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS receipt_msgs(receipt_id INTEGER, chat_id INTEGER, message_id INTEGER);
        CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, uid INTEGER, role TEXT, text TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        try:  # миграция старой базы
            await db.execute("ALTER TABLE orders ADD COLUMN reminded INTEGER DEFAULT 0")
        except Exception:
            pass
        await db.commit()


async def S(key):
    r = await q1("SELECT v FROM settings WHERE k=?", (key,))
    return r["v"] if r else SET[key][1]


async def set_S(key, val):
    await q("INSERT INTO settings(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (key, val), commit=True)


def kb(*rows):
    """Инлайн-кнопки (только для действий, привязанных к конкретному сообщению)."""
    return Kb(inline_keyboard=[[Btn(text=t, callback_data=d) for t, d in r] for r in rows]) if rows else None


def rk(*rows, ph=None):
    """Кнопки нижнего меню."""
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=t) for t in r] for r in rows],
                               resize_keyboard=True, input_field_placeholder=ph)


def reply_kb(role, handoff=False):
    rows = [[B_CAT, B_ORD], [B_RCPT, B_PICK], [B_BACK if handoff else B_HUM]]
    if role in ("admin", "owner"):
        rows.append([B_ADM, B_SET])
        rows.append([B_OFFER] + ([B_OWN] if role == "owner" else []))
    return rk(*rows, ph="Напишите, что ищете…")


def cancel_kb():
    return rk([B_CANCEL])


def panel_kb():
    return rk([B_AORD, B_ARCP], [B_ACAT, B_AADD], [B_ASTAT, B_ABC], [B_HOME])


def owner_kb(on):
    return rk([B_OADM, B_OLADM], [B_OBAN, B_OLBAN], [B_OUSR, B_OTR], [B_OON if on else B_OOFF], [B_HOME])


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
    {"name": "resend_requisites",
     "description": "Повторно отправить клиенту реквизиты и QR по его неоплаченному заказу (если просит или потерял).",
     "parameters": {"type": "OBJECT", "properties": {"order_id": {"type": "INTEGER"}}}},
    {"name": "call_human", "description": "Позвать живого менеджера: жалоба, нестандартный вопрос, просьба клиента.",
     "parameters": {"type": "OBJECT", "properties": {"reason": {"type": "STRING"}}, "required": ["reason"]}},
]}]

SALES_RULES = """
ГЛАВНАЯ ЦЕЛЬ — довести клиента до оплаты заказа. Ты не просто отвечаешь, а ведёшь клиента по шагам и убеждаешь.
- КАЖДОЕ сообщение заканчивай конкретным следующим шагом или вопросом (что выбрать, сколько штук, подтвердить заказ, оплатить). Клиент всегда должен понимать, что делать дальше.
- Сначала выясни потребность (1 короткий вопрос), потом предложи 1–2 лучших варианта и объясни выгоду для клиента, а не весь каталог.
- Возражения («дорого», «я подумаю», «сомневаюсь»): уточни причину, подчеркни ценность и пользу, предложи вариант дешевле или другой из каталога, мягко подтолкни к решению.
- Честная срочность: если в наличии осталось 3 шт. или меньше — скажи, что остаток небольшой. Никогда не выдумывай скидки, акции, сроки и дефицит.
- Когда клиент определился — сам предложи оформить: собери данные, перескажи заказ и спроси «Подтверждаете?».
- После оформления подтолкни к оплате сразу: реквизиты уже отправлены, после оплаты нужно нажать кнопку «🧾 Отправить чек» в меню внизу и прислать чек.
- Если клиент просит реквизиты повторно или потерял их — вызови resend_requisites.
- Не дави грубо и не груби: тепло, уверенно, по делу. 2–4 коротких предложения."""


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
    steps.append("5. После создания заказа бот САМ отдельным сообщением пришлёт клиенту реквизиты (и QR). "
                 "Реквизиты сам не пиши. Коротко скажи: заказ создан, номер и сумма, оплатите по реквизитам выше "
                 "и нажмите «🧾 Отправить чек» в меню внизу.")
    parts = [s["system_prompt"], "",
             f"Бизнес: {s['business_name']}. Валюта: {s['currency']}.",
             f"Стиль общения: {s['tone']}.",
             f"Доставка: {s['delivery_info'] or 'уточняй у менеджера'}. Режим работы: {s['work_hours'] or 'не указан'}.",
             f"Мин. сумма заказа: {s['min_order']}.",
             "Когда уместно, предлагай сопутствующие товары из каталога." if s["upsell"] == "1" else "Не предлагай допродажи.",
             f"Клиент: {u['name']} (@{u['username'] or 'нет'}).",
             SALES_RULES]
    if s["offer"]:
        parts.append("\nПРИОРИТЕТ ВЛАДЕЛЬЦА — что предлагать покупателям (упоминай при любом подходящем случае, "
                     "это единственные акции/условия, о которых можно говорить):\n" + s["offer"])
    open_orders = await q("SELECT id,total FROM orders WHERE uid=? AND status='awaiting_payment'", (u["tg_id"],))
    if open_orders:
        parts.append("\nУ клиента есть НЕОПЛАЧЕННЫЕ заказы: " + ", ".join(f"#{o['id']} на {o['total']:g} {s['currency']}" for o in open_orders)
                     + ". Мягко веди к оплате: напомни, что реквизиты отправлены, после оплаты нужна кнопка «🧾 Отправить чек». "
                       "Если сомневается — помоги снять сомнения.")
    parts.append("\nФОРМАТ: пиши простым текстом без markdown (без **, #, таблиц). Коротко.\n\nПОРЯДОК ОФОРМЛЕНИЯ:\n" + "\n".join(steps))
    parts.append("\nНикогда не выдумывай цены, скидки, сроки и наличие. Если не уверен — вызови call_human.")
    return "\n".join(parts)


async def gem_post(body):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{await S('model')}:generateContent"
    data = {}
    for _try in range(2):
        try:
            r = await http.post(url, headers={"x-goog-api-key": GEMINI_KEY}, json=body)
            data = r.json()
        except Exception as e:
            log.error("Gemini http: %s", e)
            data = {}
        if "candidates" in data:
            break
        log.error("Gemini: %s", str(data)[:500])
        await asyncio.sleep(2)
    return data


async def gem_media(raw: bytes, mime: str, prompt: str):
    """Голос -> текст, фото -> описание."""
    body = {"contents": [{"role": "user", "parts": [
        {"inlineData": {"mimeType": mime, "data": base64.b64encode(raw).decode()}}, {"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}}
    data = await gem_post(body)
    if "candidates" not in data:
        return None
    parts = (data["candidates"][0].get("content") or {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip() or None


async def gemini_chat(uid, u):
    hist = await q("SELECT role,text FROM messages WHERE uid=? ORDER BY id DESC LIMIT 24", (uid,))
    contents = [{"role": h["role"], "parts": [{"text": h["text"]}]} for h in reversed(hist)]
    while contents and contents[0]["role"] != "user":
        contents.pop(0)
    system = await build_system(u)
    for _ in range(6):
        body = {"system_instruction": {"parts": [{"text": system}]}, "contents": contents,
                "tools": TOOLS, "generationConfig": {"temperature": TEMP}}
        data = await gem_post(body)
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


async def do_handoff(uid, reason, question=None):
    await q("UPDATE users SET handoff=1 WHERE tg_id=?", (uid,), commit=True)
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    head = f"🙋 Нужен человек: {u['name']} @{u['username'] or '—'} uid:{uid}\nПричина: {reason}"
    if question:
        head += f"\n\n❓ {question}"
    await notify(head + "\n\n↩️ Отвечайте реплаем на это сообщение — я перешлю клиенту.", kb([("🤖 Вернуть боту", f"cr:{uid}")]))


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
    if name == "resend_requisites":
        if a.get("order_id"):
            o = await q1("SELECT * FROM orders WHERE id=? AND uid=? AND status='awaiting_payment'", (int(a["order_id"]), uid))
        else:
            o = await q1("SELECT * FROM orders WHERE uid=? AND status='awaiting_payment' ORDER BY id DESC LIMIT 1", (uid,))
        if not o:
            return {"error": "У клиента нет неоплаченных заказов."}
        await send_requisites(uid, o["id"], json.loads(o["items"]), o["total"])
        return {"ok": True, "note": "Реквизиты отправлены отдельным сообщением. Напомни про кнопку «🧾 Отправить чек» внизу."}
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
                "note": "Реквизиты (и QR) уже отправлены клиенту отдельным сообщением."}
    return {"error": "unknown tool"}


async def send_requisites(uid, oid, items, total):
    cur, req, note, ph = await S("currency"), await S("requisites"), await S("payment_note"), await S("requisites_photo")
    head = f"🧾 Заказ #{oid}\n{fmt_items(items)}\n\nК оплате: {total:g} {cur}"
    if not req and not ph:
        await safe_send(uid, head + "\n\nМенеджер скоро пришлёт реквизиты.")
        await notify(f"⚠️ В заказе #{oid} нет реквизитов: заполните их в ⚙️ Настройки → 💳 Реквизиты / 🖼 QR и отправьте клиенту.")
        return
    if ph:  # QR / фото реквизитов
        kind, _, fid = ph.partition(":")
        try:
            send = bot.send_photo if kind == "photo" else bot.send_document
            await send(uid, fid, caption=f"💳 QR / реквизиты для оплаты заказа #{oid}\nСумма: {total:g} {cur}")
        except Exception as e:
            log.warning("qr -> %s: %s", uid, e)
    await safe_send(uid, head + (f"\n\n💳 Реквизиты:\n{req}" if req else "") + (f"\n\n{note}" if note else ""))


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
    u2 = await q1("SELECT role, handoff FROM users WHERE tg_id=?", (uid,))
    await safe_send(uid, reply, reply_kb(u2["role"], True) if u2 and u2["handoff"] else None)


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
    prod_edit = State(); set_val = State(); set_photo = State(); own_target = State()
    bcast = State(); receipt = State(); ask_mgr = State()


nav, own, adm, cust = Router(), Router(), Router(), Router()
own.message.filter(IsOwner()); own.callback_query.filter(IsOwner())
adm.message.filter(IsAdmin()); adm.callback_query.filter(IsAdmin())


async def show(cb: CallbackQuery, text, markup=None):
    try:
        await cb.message.edit_text(text[:4000], reply_markup=markup)
    except TelegramBadRequest:
        pass
    await cb.answer()


# ───────────────────────── Общая навигация (нижнее меню) ─────────────────────────
@nav.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext, role: str):
    await state.clear()
    text = await S("greeting")
    if role in ("admin", "owner"):
        text += f"\n\nВы вошли как {ICON[role]} {'владелец' if role == 'owner' else 'админ'}. Кнопки управления — внизу."
    await m.answer(text, reply_markup=reply_kb(role))


@nav.message(Command("menu"))
@nav.message(F.text == B_HOME)
async def cmd_menu(m: Message, state: FSMContext, role: str):
    await state.clear()
    await m.answer("🏠 Главное меню", reply_markup=reply_kb(role))


@nav.message(Command("id"))
async def cmd_id(m: Message):
    await m.answer(f"Ваш id: {m.from_user.id}")


@nav.message(Command("cancel"))
@nav.message(F.text == B_CANCEL)
async def cmd_cancel(m: Message, state: FSMContext, role: str):
    await state.clear()
    hand = (await q1("SELECT handoff FROM users WHERE tg_id=?", (m.from_user.id,)) or {}).get("handoff")
    await m.answer("Отменено.", reply_markup=reply_kb(role, bool(hand)))


@nav.message(Command("reset"))
async def cmd_reset(m: Message, state: FSMContext, role: str):
    await state.clear()
    await q("DELETE FROM messages WHERE uid=?", (m.from_user.id,), commit=True)
    await q("UPDATE users SET handoff=0 WHERE tg_id=?", (m.from_user.id,), commit=True)
    await m.answer("🔄 Диалог сброшен. Чем помочь?", reply_markup=reply_kb(role))


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
    await m.answer(text[:4000], reply_markup=kb(*rows))


@nav.message(F.text == B_PICK)
async def pick_for_me(m: Message, state: FSMContext):
    await state.clear()
    await chat_with_ai(m.from_user.id, "Помоги мне выбрать товар: задай 1–2 коротких вопроса про задачу и бюджет, "
                                       "а затем предложи лучшие варианты из каталога.")


@nav.message(F.text == B_RCPT)
async def btn_receipt(m: Message, state: FSMContext):
    await state.clear()
    orders = await q("SELECT * FROM orders WHERE uid=? AND status='awaiting_payment' ORDER BY id DESC", (m.from_user.id,))
    if not orders:
        return await m.answer("Нет заказов, ожидающих оплаты. Выберите товар — и я помогу оформить заказ 🙂")
    if len(orders) == 1:
        return await start_receipt(m.from_user.id, orders[0]["id"], state)
    cur = await S("currency")
    await m.answer("По какому заказу чек?", reply_markup=kb(*[[(f"#{o['id']} · {o['total']:g} {cur}", f"rcpt:{o['id']}")] for o in orders[:10]]))


@nav.message(F.text == B_HUM)
async def human_btn(m: Message, state: FSMContext):
    await state.set_state(St.ask_mgr)
    await m.answer("Что вы хотите спросить у менеджера? ✍️\nНапишите вопрос одним сообщением — я сразу передам его администраторам.",
                   reply_markup=cancel_kb())


@nav.message(F.text == B_BACK)
async def back_to_bot(m: Message, state: FSMContext, role: str):
    await state.clear()
    await q("UPDATE users SET handoff=0 WHERE tg_id=?", (m.from_user.id,), commit=True)
    await m.answer("🤖 Ассистент снова с вами! Чем помочь?", reply_markup=reply_kb(role))


# ───────────────────────── Клиент: менеджер, инлайн-действия, чеки, ИИ ─────────────────────────
@cust.message(St.ask_mgr, F.text | F.photo)
async def ask_manager(m: Message, state: FSMContext, role: str):
    uid, u = m.from_user.id, await q1("SELECT * FROM users WHERE tg_id=?", (m.from_user.id,))
    question = (m.text or m.caption or "(фото без подписи)").strip()
    await state.clear()
    await q("INSERT INTO messages(uid,role,text) VALUES(?,?,?)", (uid, "user", f"[Вопрос менеджеру] {question}"), commit=True)
    await q("UPDATE users SET handoff=1 WHERE tg_id=?", (uid,), commit=True)
    head = (f"🙋 Вопрос менеджеру от {u['name']} @{u['username'] or '—'} uid:{uid}\n\n❓ {question}"
            "\n\n↩️ Отвечайте реплаем на это сообщение — я перешлю клиенту.")
    for sid in await staff_ids():
        try:
            if m.photo:
                await bot.send_photo(sid, m.photo[-1].file_id, caption=head[:1000], reply_markup=kb([("🤖 Вернуть боту", f"cr:{uid}")]))
            else:
                await bot.send_message(sid, head[:4000], reply_markup=kb([("🤖 Вернуть боту", f"cr:{uid}")]))
        except Exception as e:
            log.warning("ask_mgr -> %s: %s", sid, e)
    await m.answer(await S("handoff_text"), reply_markup=reply_kb(role, True))


@cust.message(St.ask_mgr)
async def ask_manager_other(m: Message):
    await m.answer("Напишите вопрос текстом (можно с фото) или нажмите «❌ Отмена».")


@cust.callback_query(F.data == "need_human")
async def cb_need_human(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    await state.set_state(St.ask_mgr)
    await bot.send_message(cb.from_user.id, "Что вы хотите спросить у менеджера? ✍️", reply_markup=cancel_kb())


@cust.callback_query(F.data == "back2bot")
async def cb_back(cb: CallbackQuery, role: str):
    await q("UPDATE users SET handoff=0 WHERE tg_id=?", (cb.from_user.id,), commit=True)
    await cb.answer("🤖 Ассистент снова с вами")
    await safe_send(cb.from_user.id, "Я снова на связи! Чем помочь?", reply_kb(role))


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


@cust.callback_query(F.data.startswith("rq:"))
async def cb_requisites_again(cb: CallbackQuery):
    o = await q1("SELECT * FROM orders WHERE id=? AND uid=? AND status='awaiting_payment'", (int(cb.data[3:]), cb.from_user.id))
    if not o:
        return await cb.answer("Заказ уже не ждёт оплаты", show_alert=True)
    await cb.answer()
    await send_requisites(cb.from_user.id, o["id"], json.loads(o["items"]), o["total"])


async def start_receipt(uid, oid, state: FSMContext):
    await state.set_state(St.receipt)
    await state.update_data(rcpt_order=oid)
    await bot.send_message(uid, f"Отправьте фото или файл чека по заказу #{oid} 📎\n(«❌ Отмена» — выйти)", reply_markup=cancel_kb())


@cust.callback_query(F.data.startswith("rcpt:"))
async def cb_receipt(cb: CallbackQuery, state: FSMContext):
    o = await q1("SELECT * FROM orders WHERE id=? AND uid=?", (int(cb.data[5:]), cb.from_user.id))
    if not o:
        return await cb.answer("Заказ не найден", show_alert=True)
    if o["status"] == "checking":
        return await cb.answer("Чек уже на проверке 🔎", show_alert=True)
    if o["status"] != "awaiting_payment":
        return await cb.answer("По этому заказу оплата не требуется", show_alert=True)
    await cb.answer()
    await start_receipt(cb.from_user.id, o["id"], state)


async def accept_receipt(m: Message, state: FSMContext, role: str, o):
    await state.clear()
    file_id, kind = (m.photo[-1].file_id, "photo") if m.photo else (m.document.file_id, "doc")
    rid = await q("INSERT INTO receipts(order_id,uid,file_id,kind) VALUES(?,?,?,?)", (o["id"], m.from_user.id, file_id, kind), commit=True)
    await q("UPDATE orders SET status='checking' WHERE id=?", (o["id"],), commit=True)
    await m.answer(f"✅ Чек по заказу #{o['id']} получен и передан на проверку. Сообщим результат здесь 🙌",
                   reply_markup=reply_kb(role))
    await push_receipt(rid, await staff_ids())


async def find_receipt_order(uid, oid=None):
    o = await q1("SELECT * FROM orders WHERE id=? AND uid=?", (oid, uid)) if oid else None
    if not o or o["status"] != "awaiting_payment":
        o = await q1("SELECT * FROM orders WHERE uid=? AND status='awaiting_payment' ORDER BY id DESC LIMIT 1", (uid,))
    return o


@cust.message(St.receipt, F.photo | F.document)
async def got_receipt(m: Message, state: FSMContext, role: str):
    oid = (await state.get_data()).get("rcpt_order")
    o = await find_receipt_order(m.from_user.id, oid)
    if not o:
        await state.clear()
        return await m.answer("Не нашёл заказов, ожидающих оплаты. Если нужна помощь, нажмите «🙋 Менеджер».", reply_markup=reply_kb(role))
    await accept_receipt(m, state, role, o)


@cust.message(St.receipt)
async def receipt_other(m: Message):
    await m.answer("Пришлите чек фото или файлом. Для выхода — «❌ Отмена».")


@cust.message(StateFilter(None), F.voice)
async def got_voice(m: Message):
    if (m.voice.file_size or 0) > 8_000_000:
        return await m.answer("Голосовое слишком длинное 🙈 Запишите покороче или напишите текстом.")
    try:
        await bot.send_chat_action(m.chat.id, "typing")
    except Exception:
        pass
    buf = io.BytesIO()
    await bot.download(m.voice, destination=buf)
    text = await gem_media(buf.getvalue(), "audio/ogg", "Расшифруй голосовое сообщение дословно, на языке оригинала. Верни только текст.")
    if not text:
        return await m.answer("Не смог разобрать голосовое 🙈 Напишите, пожалуйста, текстом.")
    await m.answer(f"🎤 Я услышал: «{text[:500]}»")
    await chat_with_ai(m.from_user.id, text)


@cust.message(StateFilter(None), F.photo)
async def got_photo(m: Message, state: FSMContext, role: str):
    uid = m.from_user.id
    if not m.caption:  # фото без подписи при неоплаченном заказе — это чек
        o = await find_receipt_order(uid)
        if o:
            return await accept_receipt(m, state, role, o)
    try:
        await bot.send_chat_action(m.chat.id, "typing")
    except Exception:
        pass
    buf = io.BytesIO()
    await bot.download(m.photo[-1], destination=buf)
    desc = await gem_media(buf.getvalue(), "image/jpeg",
                           "Кратко (1–2 предложения) опиши, что на фото. Если это товар — укажи тип, цвет, ключевые особенности.")
    if not desc:
        return await m.answer("Не смог разобрать фото 🙈 Опишите словами, что ищете.")
    text = f"[Клиент прислал фото: {desc}] {m.caption or ''}".strip() + "\nНайди в каталоге подходящие или похожие товары."
    await chat_with_ai(uid, text)


@cust.message(StateFilter(None), F.document)
async def got_document(m: Message, state: FSMContext, role: str):
    o = await find_receipt_order(m.from_user.id)
    if o:
        return await accept_receipt(m, state, role, o)
    await m.answer("Получил файл, но заказов, ожидающих оплаты, нет. Нужна помощь — нажмите «🙋 Менеджер».")


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


async def rlist_view():
    rs = await q("SELECT * FROM receipts WHERE status='pending' ORDER BY id")
    return ("🧾 Чеки на проверке" if rs else "Чеков на проверке нет 🎉",
            kb(*[[(f"Чек #{r['id']} · заказ #{r['order_id']}", f"rv:{r['id']}")] for r in rs[:20]]))


@adm.message(F.text == B_ARCP)
async def m_rlist(m: Message, state: FSMContext):
    await state.clear()
    t, k = await rlist_view()
    await m.answer(t, reply_markup=k)


@adm.callback_query(F.data.startswith("rv:"))
async def cb_rview(cb: CallbackQuery):
    rid = int(cb.data[3:])
    r = await q1("SELECT * FROM receipts WHERE id=? AND status='pending'", (rid,))
    if not r:
        return await cb.answer("Уже обработан", show_alert=True)
    await cb.answer()
    await push_receipt(rid, [cb.from_user.id])


# ───────────────────────── Админ-панель ─────────────────────────
@adm.message(F.text == B_ADM)
async def open_panel(m: Message, state: FSMContext):
    await state.clear()
    n = (await q1("SELECT COUNT(*) n FROM receipts WHERE status='pending'"))["n"]
    await m.answer(f"🛠 Админ-панель\n🧾 Чеков на проверке: {n}", reply_markup=panel_kb())


@adm.message(F.text == B_ASTAT)
async def m_stats(m: Message, state: FSMContext):
    await state.clear()
    rows = await q("SELECT status, COUNT(*) n, COALESCE(SUM(total),0) s FROM orders GROUP BY status")
    cur = await S("currency")
    lines = [f"{ST[r['status']]}: {r['n']} шт. / {r['s']:g} {cur}" for r in rows] or ["Заказов пока нет"]
    rev = sum(r["s"] for r in rows if r["status"] in ("paid", "shipped", "done"))
    users = (await q1("SELECT COUNT(*) n FROM users"))["n"]
    pend = (await q1("SELECT COUNT(*) n FROM receipts WHERE status='pending'"))["n"]
    await m.answer("📊 Статистика\n\n" + "\n".join(lines) + f"\n\n💰 Выручка: {rev:g} {cur}\n👥 Пользователей: {users}\n🧾 Чеков на проверке: {pend}")


# Заказы
async def orders_view():
    rows = await q("SELECT * FROM orders ORDER BY id DESC LIMIT 15")
    cur = await S("currency")
    return ("📋 Последние заказы" if rows else "Заказов пока нет",
            kb(*[[(f"#{o['id']} {ST[o['status']][:2]} {o['total']:g}{cur} {o['name']}", f"o:{o['id']}")] for o in rows]))


async def order_view(oid):
    o = await q1("SELECT * FROM orders WHERE id=?", (oid,))
    if not o:
        return None, None
    cur = await S("currency")
    st = [[(v, f"os:{o['id']}:{k}")] for k, v in ST.items() if k != o["status"]]
    text = (f"Заказ #{o['id']} — {ST[o['status']]}\n{o['ts']}\n\n{fmt_items(json.loads(o['items']))}\nИтого: {o['total']:g} {cur}\n"
            f"👤 {o['name']}  📞 {o['phone'] or '—'}\n📍 {o['address'] or '—'}\n💬 {o['comment'] or '—'}\nuid:{o['uid']}")
    return text, kb(*st, [("⬅️ К заказам", "orders")])


@adm.message(F.text == B_AORD)
async def m_orders(m: Message, state: FSMContext):
    await state.clear()
    t, k = await orders_view()
    await m.answer(t, reply_markup=k)


@adm.callback_query(F.data == "orders")
async def cb_orders(cb: CallbackQuery):
    t, k = await orders_view()
    await show(cb, t, k)


@adm.callback_query(F.data.startswith("o:"))
async def cb_order(cb: CallbackQuery):
    t, k = await order_view(int(cb.data[2:]))
    if not t:
        return await cb.answer("Не найден")
    await show(cb, t, k)


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
    t, k = await order_view(int(oid))
    await show(cb, t, k)


# Каталог
async def cat_view():
    cur = await S("currency")
    ps = await q("SELECT * FROM products ORDER BY id")
    return ("🗂 Товары" if ps else "Каталог пуст. Нажмите «➕ Добавить товар» внизу 👇",
            kb(*[[(f"{p['name']} — {p['price']:g}{cur} ({p['stock']} шт.)", f"p:{p['id']}")] for p in ps]))


@adm.message(F.text == B_ACAT)
async def m_cat(m: Message, state: FSMContext):
    await state.clear()
    t, k = await cat_view()
    await m.answer(t, reply_markup=k)


@adm.callback_query(F.data == "cat")
async def cb_cat(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    t, k = await cat_view()
    await show(cb, t, k)


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
                  [("🗑 Удалить", f"pd:{pid}")], [("⬅️ Товары", "cat")]))


@adm.callback_query(F.data.startswith("pd:"))
async def cb_prod_del(cb: CallbackQuery):
    await q("DELETE FROM products WHERE id=?", (int(cb.data[3:]),), commit=True)
    await show(cb, "🗑 Удалено", kb([("⬅️ Товары", "cat")]))


@adm.callback_query(F.data.startswith("pe:"))
async def cb_prod_edit(cb: CallbackQuery, state: FSMContext):
    _, pid, field = cb.data.split(":")
    if field not in ("name", "price", "stock", "description"):
        return await cb.answer()
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


@adm.message(F.text == B_AADD)
async def cat_add(m: Message, state: FSMContext):
    await state.set_state(St.cat_name)
    await m.answer("Название товара?", reply_markup=cancel_kb())


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
    await m.answer(f"✅ Добавлено: {d['name']}\nМожно добавить ещё — нажмите «➕ Добавить товар».", reply_markup=panel_kb())


# Настройки ассистента
async def settings_markup():
    rows = []
    for k, (label, _d, t) in SET.items():
        if t == "hidden":
            continue
        v = await S(k)
        pv = ("✅" if v == "1" else "⛔") if t == "toggle" else (v if isinstance(t, list) else ("✓" if v else "—"))
        rows.append([(f"{label}: {pv}"[:60], f"s:{k}")])
    return kb(*rows)


@adm.message(F.text == B_SET)
async def open_settings(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("⚙️ Настройки ассистента", reply_markup=await settings_markup())


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
    if t == "photo":
        await state.set_state(St.set_photo)
        has = bool(await S(key))
        return await show(cb, f"{label}\n\nСейчас: {'загружено ✅' if has else 'нет'}\n\n"
                              "Отправьте картинку с QR-кодом (или скриншот реквизитов) как ФОТО. "
                              "Подпись к фото, если она есть, станет текстом реквизитов. Клиент получит картинку вместе с заказом.\n(/cancel — отмена)",
                          kb([("🗑 Убрать фото", "rphoto_del")], [("⬅️ Назад", "set")]))
    await state.set_state(St.set_val)
    await state.update_data(key=key)
    await show(cb, f"{label}\n\nСейчас:\n{(await S(key))[:3000] or '—'}\n\nОтправьте новое значение («-» очистить, /cancel — отмена)",
               kb([("↩️ По умолчанию", f"sr:{key}")], [("⬅️ Назад", "set")]))


@adm.callback_query(F.data == "rphoto_del")
async def cb_rphoto_del(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await set_S("requisites_photo", "")
    await show(cb, "🗑 Фото убрано.\n\n⚙️ Настройки ассистента", await settings_markup())


@adm.message(St.set_photo, F.photo | F.document)
async def set_photo(m: Message, state: FSMContext):
    if m.photo:
        v = "photo:" + m.photo[-1].file_id
    elif m.document and (m.document.mime_type or "").startswith("image/"):
        v = "doc:" + m.document.file_id
    else:
        return await m.answer("Нужна картинка (фото QR-кода).")
    await set_S("requisites_photo", v)
    if m.caption:
        await set_S("requisites", m.caption.strip())
    await state.clear()
    await m.answer("✅ QR / фото сохранено. Клиенты получат его вместе с реквизитами.", reply_markup=await settings_markup())


@adm.message(St.set_photo)
async def set_photo_other(m: Message):
    await m.answer("Пришлите картинку (QR-код) или нажмите /cancel.")


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
async def set_val(m: Message, state: FSMContext, role: str):
    key, val = (await state.get_data())["key"], m.text.strip()
    if val == "-":
        val = ""
    if key == "min_order" and val:
        try:
            x = float(val.replace(",", "."))
            assert 0 <= x <= 10 ** 9
            val = val.replace(",", ".")
        except Exception:
            return await m.answer("Нужно число")
    await set_S(key, val)
    await state.clear()
    if key == "offer":
        return await m.answer("✅ Сохранено. ИИ будет предлагать это покупателям." if val else "✅ Очищено.",
                              reply_markup=reply_kb(role))
    await m.answer("✅ Сохранено", reply_markup=await settings_markup())


# 💡 Что предлагать покупателям (видна только админам и владельцу)
@adm.message(F.text == B_OFFER)
async def offer_btn(m: Message, state: FSMContext):
    await state.set_state(St.set_val)
    await state.update_data(key="offer")
    cur = await S("offer")
    await m.answer("💡 Что предлагать покупателям\n\n"
                   "Напишите, что ИИ-продавец должен продвигать в первую очередь: товар, комплект, акцию или условие. "
                   "Например: «Предлагай чехол к каждому телефону» или «Скидка 10% на второй товар до воскресенья». "
                   "ИИ будет упоминать это в разговорах и не станет придумывать другие скидки.\n\n"
                   f"Сейчас: {cur or 'не задано'}\n\nОтправьте новый текст («-» — очистить, «❌ Отмена» — выйти).",
                   reply_markup=cancel_kb())


# Рассылка
@adm.message(F.text == B_ABC)
async def bcast_start(m: Message, state: FSMContext):
    await state.set_state(St.bcast)
    await m.answer("📣 Пришлите текст рассылки для всех пользователей.", reply_markup=cancel_kb())


@adm.message(St.bcast, F.text)
async def bcast_text(m: Message, state: FSMContext):
    await state.update_data(text=m.text)
    n = (await q1("SELECT COUNT(*) n FROM users WHERE role!='banned'"))["n"]
    await m.answer(f"Отправить {n} получателям?\n\n{m.text[:1500]}", reply_markup=kb([("✅ Отправить", "bc_go"), ("Отмена", "bc_no")]))


@adm.callback_query(F.data == "bc_no")
async def bcast_no(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await show(cb, "Рассылка отменена.")


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
    await safe_send(cb.from_user.id, f"✅ Доставлено: {ok}", panel_kb())


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
    urole = (await q1("SELECT role FROM users WHERE tg_id=?", (uid,)) or {}).get("role", "customer")
    await cb.answer("🤖 Диалог возвращён боту", show_alert=True)
    await safe_send(uid, "Я снова на связи! Чем помочь?", reply_kb(urole))


# ───────────────────────── Панель владельца ─────────────────────────
async def find_user(text):
    t = text.strip().lstrip("@").lower()
    return await q1("SELECT * FROM users WHERE tg_id=?", (int(t),)) if t.isdigit() else await q1("SELECT * FROM users WHERE username=?", (t,))


async def apply_role(target, role):
    await q("UPDATE users SET role=?, handoff=0 WHERE tg_id=?", (role, target), commit=True)
    msg = {"admin": "🛡 Вам назначена роль администратора! Кнопки управления появились внизу.",
           "customer": "Ваша роль изменена: теперь вы обычный пользователь.", "banned": "🚫 Доступ закрыт."}[role]
    await safe_send(target, msg, ReplyKeyboardRemove() if role == "banned" else reply_kb(role))


@own.message(F.text == B_OWN)
async def open_owner(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("👑 Панель владельца", reply_markup=owner_kb(await S("bot_enabled") == "1"))


@own.message(F.text.in_({B_OON, B_OOFF}))
async def owner_toggle(m: Message, state: FSMContext):
    await state.clear()
    turn_on = m.text == B_OOFF  # кнопка «🟢 Включить бота»
    await set_S("bot_enabled", "1" if turn_on else "0")
    await m.answer("🟢 Бот включён." if turn_on else "🔴 Бот выключен: клиентам отвечает заглушка.", reply_markup=owner_kb(turn_on))


ACTIONS = {B_OADM: ("admin", "назначить админом"), B_OBAN: ("ban", "забанить"), B_OTR: ("transfer", "передать права владельца")}


@own.message(F.text.in_(set(ACTIONS)))
async def owner_action(m: Message, state: FSMContext):
    action, what = ACTIONS[m.text]
    await state.set_state(St.own_target)
    await state.update_data(action=action)
    await m.answer(f"Отправьте @username или id пользователя, которого нужно {what}.\n"
                   "Он должен хотя бы раз написать боту.", reply_markup=cancel_kb())


@own.message(St.own_target, F.text)
async def own_target(m: Message, state: FSMContext):
    action = (await state.get_data())["action"]
    u = await find_user(m.text)
    if not u:
        return await m.answer("Не нашёл. Пусть он сначала напишет боту /start. Ещё раз или «❌ Отмена»")
    if u["tg_id"] == m.from_user.id:
        return await m.answer("Это вы 🙂 Укажите другого пользователя.")
    await state.clear()
    if action == "transfer":
        return await m.answer(f"⚠️ Передать права владельца: {u['name']} @{u['username'] or '—'}?\nВы станете админом.",
                              reply_markup=kb([("✅ Да, передать", f"otc:{u['tg_id']}"), ("Отмена", "ohome")]))
    await apply_role(u["tg_id"], "admin" if action == "admin" else "banned")
    await m.answer(f"✅ {u['name']}: {'назначен админом' if action == 'admin' else 'забанен'}", reply_markup=owner_kb(await S("bot_enabled") == "1"))


@own.callback_query(F.data == "ohome")
async def cb_ohome(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await show(cb, "Отменено.")


async def olist_view(role):
    us = await q("SELECT * FROM users WHERE role=? ORDER BY ts DESC LIMIT 20", (role,))
    title = {"admin": "👥 Админы", "banned": "♻️ Забаненные", "customer": "👤 Пользователи (последние 20)"}[role]
    return (title if us else title + "\n\nСписок пуст"), kb(*[[(f"{u['name']} @{u['username'] or '—'}", f"ou:{u['tg_id']}")] for u in us])


@own.message(F.text.in_({B_OLADM, B_OLBAN, B_OUSR}))
async def owner_list(m: Message, state: FSMContext):
    await state.clear()
    role = {B_OLADM: "admin", B_OLBAN: "banned", B_OUSR: "customer"}[m.text]
    t, k = await olist_view(role)
    await m.answer(t, reply_markup=k)


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
    await show(cb, f"{ICON[u['role']]} {u['name']} @{u['username'] or '—'}\nid {uid}\nРоль: {u['role']}", kb(*rows))


@own.callback_query(F.data.startswith("orole:"))
async def cb_orole(cb: CallbackQuery):
    _, uid, role = cb.data.split(":")
    uid = int(uid)
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    if uid == cb.from_user.id or not u or u["role"] == "owner" or role not in ("admin", "customer", "banned"):
        return await cb.answer("Нельзя", show_alert=True)
    await apply_role(uid, role)
    await show(cb, f"✅ {u['name']}: роль → {role}")


@own.callback_query(F.data.startswith("ot:"))
async def cb_ot(cb: CallbackQuery):
    uid = int(cb.data[3:])
    u = await q1("SELECT * FROM users WHERE tg_id=?", (uid,))
    if not u:
        return await cb.answer()
    await show(cb, f"⚠️ Передать права владельца: {u['name']} @{u['username'] or '—'}?\nВы станете админом.",
               kb([("✅ Да, передать", f"otc:{uid}"), ("Отмена", "ohome")]))


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


# ───────────────────────── Напоминания об оплате ─────────────────────────
REMIND_AFTER = [30, 180, 1440]  # минуты с момента заказа


async def reminder_loop():
    """ИИ-продавец не бросает заказ: мягко напоминает об оплате (через 30 мин, 3 ч, 24 ч)."""
    while True:
        await asyncio.sleep(300)
        try:
            if await S("bot_enabled") != "1":
                continue
            cur = await S("currency")
            rows = await q("SELECT *, (julianday('now')-julianday(ts))*1440 AS age FROM orders "
                           "WHERE status='awaiting_payment' AND reminded<3")
            for o in rows:
                n = o["reminded"] or 0
                if n >= 3 or o["age"] < REMIND_AFTER[n]:
                    continue
                if not await qrc("UPDATE orders SET reminded=reminded+1 WHERE id=? AND status='awaiting_payment' AND reminded=?", (o["id"], n)):
                    continue
                texts = [
                    f"👋 Ваш заказ #{o['id']} на {o['total']:g} {cur} ждёт оплаты. Осталось оплатить по реквизитам и нажать «🧾 Отправить чек» — и мы сразу возьмём заказ в работу 🙂",
                    f"Напоминаю про заказ #{o['id']} ({o['total']:g} {cur}): товар закреплён за вами, остаётся только оплатить. Есть вопросы или сомнения? Напишите — помогу!",
                    f"Последнее напоминание по заказу #{o['id']}. Если всё в силе — оплатите и пришлите чек. Если передумали, заказ можно отменить в «📦 Мои заказы», а я подберу другой вариант 😊",
                ]
                await safe_send(o["uid"], texts[n], kb([("💳 Реквизиты ещё раз", f"rq:{o['id']}")],
                                                       [("🧾 Я оплатил(а) — отправить чек", f"rcpt:{o['id']}")]))
        except Exception:
            log.exception("reminders")


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
    asyncio.create_task(reminder_loop())
    dp = Dispatcher()
    dp.message.outer_middleware(Gate())
    dp.callback_query.outer_middleware(Gate())
    dp.include_routers(nav, own, adm, cust)
    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
