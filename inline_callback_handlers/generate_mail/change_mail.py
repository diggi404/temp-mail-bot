from telebot import TeleBot, types
from sqlalchemy.orm import Session
from database.models import TempMailUsers
import requests
import os


def change_mail(
    bot: TeleBot,
    chat_id: int,
    msg_id: int,
    db_session: Session,
    button_data: str,
    duplicate_mails: dict,
):
    prev_mail = button_data.split("_")[1]
    if chat_id in duplicate_mails:
        dup_mails = duplicate_mails.get(chat_id, [])
    else:
        duplicate_mails[chat_id] = [prev_mail]
        dup_mails = duplicate_mails.get(chat_id, [])
    try:
        get_emails = requests.get(
            "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=10"
        )
    except:
        bot.edit_message_text(
            "Bot can't generate emails right now. Please try again.",
            chat_id,
            msg_id,
        )
    else:
        if get_emails.status_code == 200:
            temp_list = get_emails.json()
            temp_list = set(temp_list) - set(dup_mails)
            temp_list = list(temp_list)
            check_temp = [
                user.email
                for user in db_session.query(TempMailUsers)
                .filter(TempMailUsers.email.in_(temp_list))
                .all()
            ]
            available_mails = set(temp_list) - set(check_temp)
            user_temp_mail = list(available_mails)[0]

            gen_email_markup = types.InlineKeyboardMarkup()
            gen_email_btn1 = types.InlineKeyboardButton(
                "Change 🚮", callback_data=f"get new temp mail_{user_temp_mail}"
            )
            gen_email_btn2 = types.InlineKeyboardButton(
                "Check Inbox 📨", callback_data=f"check inbox_{user_temp_mail}"
            )
            close_btn = types.InlineKeyboardButton(
                "Close \u274C", callback_data="remove message"
            )
            gen_email_markup.add(gen_email_btn2)
            gen_email_markup.add(gen_email_btn1, close_btn)
            with db_session as session:
                try:
                    session.query(TempMailUsers).filter(
                        TempMailUsers.id == chat_id
                    ).update({"email": user_temp_mail})
                    session.commit()
                except Exception as e:
                    print(e)
                    session.rollback()
                    bot.send_message(
                        chat_id,
                        "Sorry you can't change email right now. Try again later.",
                    )
                else:
                    bot.edit_message_text(
                        f"New Mail: <code>{user_temp_mail}</code>",
                        chat_id,
                        msg_id,
                        reply_markup=gen_email_markup,
                        parse_mode="HTML",
                    )
        else:
            bot.edit_message_text(
                "Bot can't generate emails right now. Please try again.",
                chat_id,
                msg_id,
            )
