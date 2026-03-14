import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

import config
import database as db
from github_parser import search_unity_repos
from ai_generator import generate_post, is_game

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WAITING_EDIT: dict[int, int] = {}


# ============================================================
# КЛАВИАТУРЫ
# ============================================================

def approval_keyboard(repo_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"approve:{repo_id}"),
            InlineKeyboardButton("❌ Отклонить",    callback_data=f"reject:{repo_id}"),
        ],
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit:{repo_id}"),
            InlineKeyboardButton("📋 Копировать",    callback_data=f"copy:{repo_id}"),
        ],
    ])


# ============================================================
# ОТПРАВКА РЕПОЗИТОРИЯ АДМИНИСТРАТОРУ
# ============================================================

async def send_to_admin(app: Application, repo_id: int, repo: dict, post_text: str):
    itch_line = f"\n🕹 <b>itch.io:</b> {repo['itch_url']}" if repo.get("itch_url") else ""
    # Сообщение 1: информация о репозитории
    info = (
        f"🔔 <b>Новый репозиторий на модерации</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 <b>Репо:</b> {repo['repo_name']}\n"
        f"⭐ <b>Звёзды:</b> {repo['stars']}\n"
        f"📅 <b>Создан:</b> {repo['created_at']}\n"
        f"🔗 <b>Ссылка:</b> {repo['url']}{itch_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await app.bot.send_message(
        chat_id=config.ADMIN_ID,
        text=info,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    header = post_text

    screenshots = repo.get("screenshots", [])
    if screenshots:
        try:
            from telegram import InputMediaPhoto
            if len(screenshots) == 1:
                msg = await app.bot.send_photo(
                    chat_id=config.ADMIN_ID,
                    photo=screenshots[0],
                    caption=header,
                    parse_mode=ParseMode.HTML,
                    reply_markup=approval_keyboard(repo_id),
                )
            else:
                # Отправляем альбом — первое фото с caption
                media = [InputMediaPhoto(media=screenshots[0], caption=header, parse_mode=ParseMode.HTML)]
                for url in screenshots[1:]:
                    media.append(InputMediaPhoto(media=url))
                await app.bot.send_media_group(chat_id=config.ADMIN_ID, media=media)
                # Кнопки отдельным сообщением
                msg = await app.bot.send_message(
                    chat_id=config.ADMIN_ID,
                    text="👆 Выберите действие:",
                    reply_markup=approval_keyboard(repo_id),
                )
        except Exception as e:
            logger.warning(f"Не удалось отправить фото: {e}")
            msg = await app.bot.send_message(
                chat_id=config.ADMIN_ID,
                text=header,
                parse_mode=ParseMode.HTML,
                reply_markup=approval_keyboard(repo_id),
                disable_web_page_preview=True,
            )
    else:
        msg = await app.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=header,
            parse_mode=ParseMode.HTML,
            reply_markup=approval_keyboard(repo_id),
            disable_web_page_preview=True,
        )

    db.save_pending_message(repo_id, msg.message_id)
    logger.info(f"Репо #{repo_id} отправлен на модерацию: {repo['url']}")


# ============================================================
# ПОИСК РЕПОЗИТОРИЕВ (запускается по расписанию)
# ============================================================

async def check_repos(context: ContextTypes.DEFAULT_TYPE, reply_to=None):
    logger.info("⏱ Ищу Unity-репозитории...")
    new_count = 0

    repos = search_unity_repos()

    for repo in repos:
        if db.is_seen(repo["url"]):
            continue

        if not is_game(repo):
            logger.info(f"[FILTER] Не игра, пропускаем: {repo['repo_name']}")
            db.add_repo(repo["url"], repo["repo_name"], "skipped")
            db.update_status(db._get_id_by_url(repo["url"]), "rejected")
            continue

        post_text = generate_post(repo)

        repo_id = db.add_repo(
            repo_url=repo["url"],
            repo_name=repo["repo_name"],
            generated_text=post_text,
        )

        await send_to_admin(context.application, repo_id, repo, post_text)
        new_count += 1

        # Один новый репозиторий за цикл — не спамим
        break

    logger.info(f"✅ Поиск завершён. Новых репозиториев: {new_count}")

    if reply_to and new_count == 0:
        await reply_to.reply_text("✅ Новых репозиториев не найдено.")
    elif reply_to:
        await reply_to.reply_text(f"✅ Найдено новых репозиториев: {new_count}")


# ============================================================
# ОБРАБОТЧИКИ КНОПОК
# ============================================================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != config.ADMIN_ID:
        await query.answer("⛔ Только для администратора", show_alert=True)
        return

    action, repo_id_str = query.data.split(":", 1)
    repo_id = int(repo_id_str)
    repo = db.get_repo(repo_id)

    if not repo:
        await query.edit_message_caption("❌ Репозиторий не найден в базе.")
        return

    # ---- ОДОБРИТЬ ----
    if action == "approve":
        await publish_repo(context, repo_id, repo)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass

    # ---- ОТКЛОНИТЬ ----
    elif action == "reject":
        db.update_status(repo_id, "rejected")
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        await context.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=f"❌ Репозиторий #{repo_id} отклонён.",
        )

    # ---- РЕДАКТИРОВАТЬ ----
    elif action == "edit":
        WAITING_EDIT[query.from_user.id] = repo_id
        await context.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=(
                "✏️ Отправьте новый текст поста.\n"
                "Поддерживается HTML: <b>жирный</b>, <i>курсив</i>, "
                "<code>&lt;a href='...'&gt;ссылка&lt;/a&gt;</code>\n\n"
                "<i>Или /cancel для отмены</i>"
            ),
            parse_mode=ParseMode.HTML,
        )

    # ---- КОПИРОВАТЬ ----
    elif action == "copy":
        await context.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=repo["generated_text"],
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )


async def handle_edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WAITING_EDIT:
        return

    repo_id = WAITING_EDIT.pop(user_id)
    new_text = update.message.text

    db.update_generated_text(repo_id, new_text)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Опубликовать", callback_data=f"approve:{repo_id}"),
            InlineKeyboardButton("❌ Отклонить",    callback_data=f"reject:{repo_id}"),
        ]
    ])
    await update.message.reply_text(
        f"✅ Текст обновлён. Предпросмотр:\n\n{new_text}",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# ПУБЛИКАЦИЯ В КАНАЛ
# ============================================================

async def publish_repo(context: ContextTypes.DEFAULT_TYPE, repo_id: int, repo: dict):
    post_text = repo["generated_text"]

    await context.bot.send_message(
        chat_id=config.CHANNEL_ID,
        text=post_text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=False,
    )
    db.update_status(repo_id, "published")
    logger.info(f"📢 Репозиторий #{repo_id} опубликован в {config.CHANNEL_ID}")


# ============================================================
# КОМАНДЫ
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    await update.message.reply_text(
        "👋 <b>Unity Bot запущен!</b>\n\n"
        "Ищу Unity-проекты на GitHub и присылаю на одобрение.\n\n"
        "Команды:\n"
        "/start — это сообщение\n"
        "/check — найти репозиторий вручную\n"
        "/status — статистика\n"
        "/cancel — отменить редактирование",
        parse_mode=ParseMode.HTML,
    )


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    await update.message.reply_text("🔍 Ищу Unity-репозитории...")
    await check_repos(context, reply_to=update.message)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        return
    stats = db.get_stats()
    await update.message.reply_text(
        f"📊 <b>Статистика бота</b>\n\n"
        f"📦 Всего репозиториев: {stats['total']}\n"
        f"✅ Опубликовано:       {stats['published']}\n"
        f"⏳ На модерации:       {stats['pending']}\n"
        f"❌ Отклонено:          {stats['rejected']}\n\n"
        f"🕐 Проверка каждые {config.CHECK_INTERVAL_HOURS} ч.",
        parse_mode=ParseMode.HTML,
    )


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in WAITING_EDIT:
        WAITING_EDIT.pop(user_id)
        await update.message.reply_text("✅ Редактирование отменено.")


# ============================================================
# ТОЧКА ВХОДА
# ============================================================

def main():
    db.init_db()

    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("check",  cmd_check))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(config.ADMIN_ID),
        handle_edit_text,
    ))

    app.job_queue.run_repeating(
        check_repos,
        interval=config.CHECK_INTERVAL_HOURS * 3600,
        first=10,
    )

    logger.info(f"🤖 Unity Bot запущен. Проверка каждые {config.CHECK_INTERVAL_HOURS} ч.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
