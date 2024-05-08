from telebot import TeleBot, types
from sqlalchemy.orm import Session
from database.models import TempMailUsers


def user_info(
    bot: TeleBot, chat_id: int, msg_id: int, db_session: Session, button_data: str
):
    user_id = int(button_data.split("_")[1])
    get_user = (
        db_session.query(TempMailUsers).filter(TempMailUsers.id == user_id).first()
    )
    status = {True: "ON ✅", False: "OFF ❌"}
    result_msg = f"""
➖➖➖➖USER INFO➖➖➖➖➖

User ID: {user_id}
Username: {'@' + get_user.username if get_user.username else None}
Current Mail: {get_user.email}
Alert Mode: {status[get_user.alert]}
Registered On: {get_user.created_at.strftime('%Y-%m-%d %H:%M')}
    """
    markup = types.InlineKeyboardMarkup()
    back_btn = types.InlineKeyboardButton("<< Back", callback_data="go back to users")
    markup.add(back_btn)
    bot.edit_message_text(result_msg, chat_id, msg_id, reply_markup=markup)
