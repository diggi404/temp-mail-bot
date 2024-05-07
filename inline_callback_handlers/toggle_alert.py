from telebot import TeleBot, types
from sqlalchemy.orm import Session
from database.models import TempMailUsers


def toggle_alert(
    bot: TeleBot, chat_id: int, msg_id: int, db_session: Session, alert_dict: dict
):
    get_user = (
        db_session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).first()
    )
    with db_session as session:
        try:
            session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).update(
                {"alert": False if get_user.alert else True}
            )
            session.commit()
        except Exception as e:
            print(e)
            session.rollback()
            bot.send_message(
                chat_id,
                "Sorry you can't change incoming alert mode. Try again later.",
            )
        else:
            alert_dict[chat_id]["alert"] = get_user.alert
            status = {True: "ON ✅", False: "OFF ❌"}
            bot.delete_message(chat_id, msg_id)
            bot.send_message(
                chat_id,
                f"Alert Mode: {status[get_user.alert]}",
            )
            markup = types.InlineKeyboardMarkup()
            close_btn = types.InlineKeyboardButton(
                "Close \u274C", callback_data="remove message"
            )
            btn = types.InlineKeyboardButton(
                "Toggle Message Alert 🔄", callback_data="toggle message alert"
            )
            markup.add(btn)
            markup.add(close_btn)
            result_msg = f"""
➖➖SETTINGS➖➖

👨‍💻 ID: <code>{chat_id}</code>
✉️ Current Mail: <code>{get_user.email}</code>
💬 Incoming Message Alert: <b>{status[get_user.alert]}</b>
🗓️ Registered On: <b>{get_user.created_at.strftime('%Y-%m-%d %H:%M')}</b>
    """
    bot.send_message(chat_id, result_msg, reply_markup=markup, parse_mode="HTML")
