from telebot import TeleBot, types
from sqlalchemy.orm import Session
from database.models import TempMailUsers


def show_users(
    bot: TeleBot, chat_id: int, msg_id: int, db_session: Session, users_page_dict: dict
):
    get_users = (
        db_session.query(TempMailUsers.id, TempMailUsers.name)
        .order_by(TempMailUsers.created_at.desc())
        .all()
    )
    temp_markups = []
    markup = types.InlineKeyboardMarkup()
    for index, user in enumerate(get_users, start=1):
        if index <= 10:
            btn = types.InlineKeyboardButton(
                f"{index}. {user[1]}", callback_data=f"normal user_{user[0]}"
            )
            temp_markups.append(btn)
        else:
            break
    for m in temp_markups:
        markup.add(m)
    left_btn = types.InlineKeyboardButton("<", callback_data="users move back")
    page_btn = types.InlineKeyboardButton("1", callback_data="nothing")
    right_btn = types.InlineKeyboardButton(">", callback_data="users move forward")
    markup.add(left_btn, page_btn, right_btn)
    close_btn = types.InlineKeyboardButton(
        "Close \u274C", callback_data="remove message"
    )
    markup.add(close_btn)
    users_page_dict[chat_id] = 1
    bot.edit_message_text("➖➖USERS➖➖", chat_id, msg_id, reply_markup=markup)
