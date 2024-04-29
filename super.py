import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import config
from no1 import get_no1_full_list, get_no1_list_text
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


help_message_text = """Бот выводит список лидеров хит-парадов разных стран за любой день <b>с 1956 по 2000 год</b>. 
Для использования бота нужно быть подписанным на канал <b>@best_20_century_hits</b>.

Введите дату в формате ДД.ММ.ГГГГ. Например, <b>03.09.1989</b>. 
Через некоторое время появится список песен со ссылками на youtube.

По всем вопросам пишите <tg-spoiler>@xivan74</tg-spoiler>.
"""

bot_message_text = "Ботам запрещено здесь находиться"

def str_is_date(date_str):
    try:
        str_date = datetime.strptime(date_str, config.DATE_FORMAT)
    except ValueError:
        return False
    return str_date


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_is_bot = update.message.from_user.is_bot
    if user_is_bot:
        return
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message_text, parse_mode="HTML")


async def help_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_is_bot = update.message.from_user.is_bot
    if user_is_bot:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_message_text, parse_mode="HTML")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_message_text, parse_mode="HTML")


async def user_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_is_bot = update.message.from_user.is_bot
    if user_is_bot:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_message_text, parse_mode="HTML")
    tg_channel_id = int(config.group_chat_id)
    user_id = update.message.from_user.id
    user_1_name = update.message.from_user.first_name
    user_2_name = update.message.from_user.last_name
    user_name = update.message.from_user.name
    print(user_id)
    subscrbd = await context.bot.get_chat_member(tg_channel_id, user_id)
    tg_channel_id = config.group_chat_id
    users_count = await context.bot.get_chat_member_count(tg_channel_id)
    print(subscrbd)
    print(subscrbd.status)
    print(users_count)
    if subscrbd and subscrbd.status != "left":
        subscrbd_text = (f"Поздравляю, {user_1_name}! Вы подписаны на канал <b>@best_20_century_hits</b>"
                        f" как еще {users_count-1} человек")
    else:
        subscrbd_text = (f"{user_1_name}, вы не подписаны на канал <b>@best_20_century_hits</b>. "
                         f"Сейчас самое подходящее время это сделать, как сделали {users_count} человек")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=subscrbd_text, parse_mode="HTML")


def get_no1_list_by_date(chart_date: datetime.date):
    return get_no1_list_text(chart_date, get_no1_full_list(chart_date))


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # now = datetime(year=1974, month=6, day=26)
    user_is_bot = update.message.from_user.is_bot
    if user_is_bot:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=bot_message_text, parse_mode="HTML")
    user_1_name = update.message.from_user.first_name
    user_2_name = update.message.from_user.last_name
    user_name = update.message.from_user.name
    wrong_date_text = "Не удалось распознать дату. Введите дату в формате ДД.ММ.ГГГГ. Например, <b>03.09.1989</b>."
    big_small_date_text = "Дата должна быть в промежутке <b>с 1956 по 2000 год</b>."
    text = update.message.text
    chart_date = str_is_date(text)
    if not chart_date:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=wrong_date_text, parse_mode="HTML")
        return
    if chart_date.year < 1956 or chart_date.year > 2000:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=big_small_date_text, parse_mode="HTML")
        return

    month_list = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    full_date = f"{chart_date.date().day} {month_list[chart_date.date().month-1]} {chart_date.date().year} года"
    wait_text = (f"{user_1_name}, ожидайте список лидеров хит-парадов на <b>{full_date}</b>.\n"
                 f"Если список не появится через пару минут, то попробуйте позже еще раз.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=wait_text, parse_mode="HTML")

    no1_list_text = f"{get_no1_list_by_date(chart_date)} специально для <b>{user_name}</b>"
    print(no1_list_text)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=no1_list_text, parse_mode="HTML")


if __name__ == '__main__':
    application = ApplicationBuilder().token(config.SUPER_BOT_TOKEN).build()

    start_handler = CommandHandler('start', start)
    help_handler = CommandHandler('help', help_message)
    subscribed_handler = CommandHandler('subscribed', user_subscribed)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    application.add_handler(start_handler)
    application.add_handler(help_handler)
    application.add_handler(subscribed_handler)
    application.add_handler(echo_handler)

    application.run_polling()