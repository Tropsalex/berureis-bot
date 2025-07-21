from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    MessageHandler, filters, ConversationHandler
)

TOKEN = "7109128434:AAGmcO8tbMpK1lbEI0Y3As4lPmlqkOcVPvk"
ADMIN_USER_ID = 549270283

(
    FROM_CITY, TO_CITY, DATE, TIME,
    VEHICLE_CHOICE, BODY_CHOICE,
    CLIENT_PRICE, MARGIN_PERCENT,
    DETAILS,
    CHOOSE_FLIGHT_TO_DELETE,
    CONFIRM_DELETE,
    ENTER_OFFER,
    REGISTER_COMPANY,
    REGISTER_PHONE
) = range(14)

REISY = []
subscribers = set()
user_info = {}  # user_id: {"company": ..., "phone": ...}
blocked_users = set()


# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    subscribers.add(user_id)

    # Сохраняем имя и username
    user_info[user_id] = {
        "name": user.first_name,
        "username": user.username
    }

    if user_id in blocked_users:
        await update.message.reply_text("🚫 Вы заблокированы и не можете просматривать рейсы.")
        return

    keyboard = []
    for reis in REISY:
        btn_text = f"{reis['from']} → {reis['to']} | {reis['date']} | {reis['type']} | {reis['price']}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"view_{reis['id']}")])
    if user_id == ADMIN_USER_ID:
        keyboard.append([InlineKeyboardButton("➕ Добавить рейс", callback_data="add_flight")])
        keyboard.append([InlineKeyboardButton("🗑️ Удалить рейс", callback_data="del_flight")])
    await update.message.reply_text("📦 Доступные рейсы:", reply_markup=InlineKeyboardMarkup(keyboard))

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("🚫 Только для администратора.")
        return

    text = f"👥 Подписчиков: {len(subscribers)}\n\n🧾 ID:\n"
    for i, uid in enumerate(subscribers, start=1):
        info = user_info.get(uid, {})
        name = info.get("name", "Без имени")
        username = info.get("username")
        username_text = f"(@{username})" if username else "(без username)"
        text += f"{i}. {name} {username_text} — {uid}\n"

    await update.message.reply_text(text)

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    try:
        uid = int(context.args[0])
        blocked_users.add(uid)
        await update.message.reply_text(f"🚫 Пользователь {uid} заблокирован.")
    except:
        await update.message.reply_text("❌ Используй: /block <id>")

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_USER_ID:
        return
    try:
        uid = int(context.args[0])
        blocked_users.discard(uid)
        await update.message.reply_text(f"✅ Пользователь {uid} разблокирован.")
    except:
        await update.message.reply_text("❌ Используй: /unblock <id>")

# --- Добавление рейса (шаги) ---
async def get_from_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['from'] = update.message.text
    await update.message.reply_text("Введите город назначения:")
    return TO_CITY

async def get_to_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['to'] = update.message.text
    await update.message.reply_text("Введите дату (например, 2025-07-15):")
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['date'] = update.message.text
    await update.message.reply_text("Введите время (например, 14:30):")
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['time'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Фура", callback_data="ts_Фура")],
        [InlineKeyboardButton("10т", callback_data="ts_10т")],
        [InlineKeyboardButton("5т", callback_data="ts_5т")],
        [InlineKeyboardButton("3т", callback_data="ts_3т")],
        [InlineKeyboardButton("1.5т", callback_data="ts_1.5т")]
    ]
    await update.message.reply_text("Выберите тип ТС:", reply_markup=InlineKeyboardMarkup(keyboard))
    return VEHICLE_CHOICE

async def get_vehicle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['vehicle'] = query.data.replace("ts_", "")
    keyboard = [
        [InlineKeyboardButton("Тент", callback_data="body_Тент")],
        [InlineKeyboardButton("Изо", callback_data="body_Изо")],
        [InlineKeyboardButton("Реф", callback_data="body_Реф")],
        [InlineKeyboardButton("Борт", callback_data="body_Борт")],
        [InlineKeyboardButton("Любой закрытый", callback_data="body_Любой закрытый")]
    ]
    await query.edit_message_text("Выберите тип кузова:", reply_markup=InlineKeyboardMarkup(keyboard))
    return BODY_CHOICE

async def get_body_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    body = query.data.replace("body_", "")
    context.user_data['type'] = f"{context.user_data['vehicle']} / {body}"
    await query.edit_message_text("Введите ставку клиента с НДС:")
    return CLIENT_PRICE

async def get_client_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        client_price = int(update.message.text.strip().replace(" ", "").replace("₽", ""))
    except ValueError:
        await update.message.reply_text("❌ Введите число, без текста.")
        return CLIENT_PRICE
    context.user_data['client_price'] = client_price
    await update.message.reply_text("Введите маржу в % (например, 10):")
    return MARGIN_PERCENT

async def get_margin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        margin = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Введите только число.")
        return MARGIN_PERCENT
    client_price = context.user_data['client_price']
    price_with_vat = int(client_price - (client_price * margin / 100))
    price_without_vat = int(price_with_vat / 1.2)
    context.user_data['price'] = f"{price_with_vat:,} ₽ с НДС / {price_without_vat:,} ₽ без НДС".replace(",", " ")
    await update.message.reply_text("Введите детали рейса:")
    return DETAILS

async def get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['details'] = update.message.text
    new_id = max([r['id'] for r in REISY], default=0) + 1
    flight = {
        "id": new_id,
        "from": context.user_data['from'],
        "to": context.user_data['to'],
        "date": context.user_data['date'],
        "time": context.user_data['time'],
        "type": context.user_data['type'],
        "price": context.user_data['price'],
        "details": context.user_data['details']
    }
    REISY.append(flight)

    for user_id in subscribers:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🚛 Добавлен новый рейс! Нажмите /start, чтобы посмотреть."
            )
        except:
            pass
    await update.message.reply_text(
        f"✅ Рейс добавлен!\n\n"
        f"🚚 Рейс ID: {flight['id']}\n"
        f"Маршрут: {flight['from']} → {flight['to']}\n"
        f"Дата: {flight['date']} в {flight['time']}\n"
        f"Тип ТС: {flight['type']}\n"
        f"Ставка: {flight['price']}\n"
        f"Детали: {flight['details']}"
    )
    return ConversationHandler.END
    # --- Регистрация перевозчика ---
async def register_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["company"] = update.message.text
    await update.message.reply_text("📞 Введите ваш номер телефона:")
    return REGISTER_PHONE

async def register_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    company = context.user_data.get("company")
    phone = update.message.text.strip()
    user_info[user_id] = {"company": company, "phone": phone}
    await update.message.reply_text("✅ Вы зарегистрированы. Теперь можно забирать рейсы.")

    flight_id = context.user_data.get("pending_take")
    flight = next((r for r in REISY if r["id"] == flight_id), None)
    if flight:
        REISY.remove(flight)
        info = user_info[user_id]
        await context.bot.send_message(chat_id=user_id, text="✅ Рейс забран! Логист скоро с вами свяжется.")
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=(
                f"🚛 Рейс забран:\n"
                f"{flight['from']} → {flight['to']} | {flight['date']} в {flight['time']}\n"
                f"Пользователь: @{update.effective_user.username or update.effective_user.first_name} (id: {user_id})\n"
                f"📞 Телефон: {info['phone']}\n"
                f"🏢 ТК: {info['company']}"
            )
        )
    return ConversationHandler.END


# --- Предложение ставки ---
async def enter_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    flight_id = context.user_data.get("offer_flight_id")
    if flight_id is None:
        await update.message.reply_text("❌ Ошибка. Рейс не выбран.")
        return ConversationHandler.END

    offer_text = update.message.text.strip()
    flight = next((r for r in REISY if r["id"] == flight_id), None)
    if not flight:
        await update.message.reply_text("❌ Рейс не найден.")
        return ConversationHandler.END

    await context.bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=(
            f"💸 Новая ставка:\n"
            f"{flight['from']} → {flight['to']} | {flight['date']} в {flight['time']}\n"
            f"Ставка: {offer_text}\n"
            f"От: @{update.effective_user.username or update.effective_user.first_name} (id: {user_id})"
        )
    )
    await update.message.reply_text("✅ Ваша ставка отправлена логисту.")
    return ConversationHandler.END


# --- Обработка кнопок ---
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "add_flight":
        if user_id != ADMIN_USER_ID:
            await query.edit_message_text("❌ У вас нет прав.")
            return ConversationHandler.END
        await query.edit_message_text("Введите город отправления:")
        return FROM_CITY

    elif data == "del_flight":
        if user_id != ADMIN_USER_ID:
            await query.edit_message_text("❌ У вас нет прав.")
            return ConversationHandler.END
        if not REISY:
            await query.edit_message_text("📭 Нет рейсов.")
            return ConversationHandler.END
        keyboard = [
            [InlineKeyboardButton(f"{r['from']} → {r['to']} | {r['date']}", callback_data=f"delete_{r['id']}")]
            for r in REISY
        ]
        keyboard.append([InlineKeyboardButton("Отмена", callback_data="cancel")])
        await query.edit_message_text("🗑️ Выберите рейс:", reply_markup=InlineKeyboardMarkup(keyboard))
        return CHOOSE_FLIGHT_TO_DELETE

    elif data.startswith("delete_"):
        flight_id = int(data.split("_")[1])
        context.user_data['del_id'] = flight_id
        keyboard = [
            [InlineKeyboardButton("Удалить", callback_data="confirm_delete")],
            [InlineKeyboardButton("Отмена", callback_data="cancel")]
        ]
        await query.edit_message_text("⚠️ Подтвердите удаление", reply_markup=InlineKeyboardMarkup(keyboard))
        return CONFIRM_DELETE

    elif data == "confirm_delete":
        flight_id = context.user_data.get('del_id')
        flight = next((r for r in REISY if r["id"] == flight_id), None)
        if flight:
            REISY.remove(flight)
            await query.edit_message_text("✅ Рейс удалён.")
        else:
            await query.edit_message_text("❌ Рейс не найден.")
        return ConversationHandler.END

    elif data == "cancel":
        await query.edit_message_text("Отменено.")
        return ConversationHandler.END

    elif data.startswith("view_"):
        flight_id = int(data.split("_")[1])
        flight = next((r for r in REISY if r["id"] == flight_id), None)
        if not flight:
            await query.edit_message_text("❌ Рейс не найден.")
            return ConversationHandler.END
        msg = (
            f"🚚 Рейс ID: {flight['id']}\n"
            f"Маршрут: {flight['from']} → {flight['to']}\n"
            f"Дата: {flight['date']} в {flight['time']}\n"
            f"Тип ТС: {flight['type']}\n"
            f"Ставка: {flight['price']}\n"
            f"Детали: {flight['details']}"
        )
        keyboard = [
            [InlineKeyboardButton("✅ Забрать рейс", callback_data=f"take_{flight_id}")],
            [InlineKeyboardButton("💸 Предложить ставку", callback_data=f"offer_{flight_id}")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="cancel")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

    elif data.startswith("take_"):
        if user_id in blocked_users:
            await query.edit_message_text("🚫 Вы заблокированы и не можете забирать рейсы.")
            return ConversationHandler.END

        flight_id = int(data.split("_")[1])
        if user_id not in user_info:
            context.user_data["pending_take"] = flight_id
            await query.edit_message_text("Введите название вашей Транспортной компании:")
            return REGISTER_COMPANY

        flight = next((r for r in REISY if r["id"] == flight_id), None)
        if flight:
            REISY.remove(flight)
            info = user_info.get(user_id, {})
            await query.edit_message_text("✅ Благодарим за участие! Логист скоро с вами свяжется.")
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=(
                    f"🚛 Рейс забран:\n"
                    f"{flight['from']} → {flight['to']} | {flight['date']} в {flight['time']}\n"
                    f"Пользователь: @{query.from_user.username or query.from_user.first_name} (id: {user_id})\n"
                    f"📞 Телефон: {info.get('phone', 'не указан')}\n"
                    f"🏢 ТК: {info.get('company', 'не указана')}"
                )
            )
        else:
            await query.edit_message_text("❌ Рейс не найден.")
        return ConversationHandler.END

    elif data.startswith("offer_"):
        flight_id = int(data.split("_")[1])
        context.user_data["offer_flight_id"] = flight_id
        await query.edit_message_text("💬 Введите вашу ставку:")
        return ENTER_OFFER

    else:
        await query.edit_message_text("❓ Неизвестная команда.")
        return ConversationHandler.END


# --- Отмена ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END


# --- MAIN ---
def main():
    application = Application.builder().token(TOKEN).build()

    conv_add_flight = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="add_flight")],
        states={
            FROM_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_from_city)],
            TO_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_to_city)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            VEHICLE_CHOICE: [CallbackQueryHandler(get_vehicle_choice, pattern="ts_.*")],
            BODY_CHOICE: [CallbackQueryHandler(get_body_choice, pattern="body_.*")],
            CLIENT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_price)],
            MARGIN_PERCENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_margin)],
            DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_details)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )

    conv_register = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="take_.*")],
        states={
            REGISTER_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_company)],
            REGISTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )

    conv_offer = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="offer_.*")],
        states={
            ENTER_OFFER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_offer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )

    conv_delete = ConversationHandler(
        entry_points=[CallbackQueryHandler(button, pattern="del_flight")],
        states={
            CHOOSE_FLIGHT_TO_DELETE: [CallbackQueryHandler(button, pattern="delete_.*|cancel")],
            CONFIRM_DELETE: [CallbackQueryHandler(button, pattern="confirm_delete|cancel")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("block", block_user))
    application.add_handler(CommandHandler("unblock", unblock_user))
    application.add_handler(conv_add_flight)
    application.add_handler(conv_register)
    application.add_handler(conv_offer)
    application.add_handler(conv_delete)
    application.add_handler(CallbackQueryHandler(button))

    print("🚀 Бот запущен!")
    application.run_polling()


if __name__ == "__main__":
    main()


