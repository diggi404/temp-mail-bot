from telebot import TeleBot, types
from sqlalchemy.orm import Session
from database.models import TempMailUsers
import requests


def create_new_mail(
    bot: TeleBot,
    chat_id: int,
    msg_id: int,
    db_session: Session,
    alert_dict: dict,
    call_id: int,
):
    try:
        get_emails = requests.get(
            "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=20"
        )
    except:
        bot.answer_callback_query(
            call_id, "Error getting new mail. Please try again.", show_alert=True
        )
    else:
        if get_emails.status_code == 200:
            res = get_emails.json()
            domains = ["vjuum.com", "laafd.com"]
            emails = [e for e in res if e.split("@")[1] in domains]
            check_temp = [
                user.email
                for user in db_session.query(TempMailUsers)
                .filter(TempMailUsers.email.in_(emails))
                .all()
            ]
            available_mails = set(emails) - set(check_temp)
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
                    ).update({"email": user_temp_mail, "alert": True})
                    session.commit()
                except Exception as e:
                    print(e)
                    session.rollback()
                else:
                    bot.edit_message_text(
                        f"➖➖FRESH MAIL➖➖\n\nNew Mail: <code>{user_temp_mail}</code>\nIncoming Message Alert: <b>ON ✅</b>\n\n<i>You can always go to [settings] to see your current mail and toggle message alert mode.</i>",
                        chat_id,
                        msg_id,
                        reply_markup=gen_email_markup,
                        parse_mode="HTML",
                    )
                    alert_dict[chat_id] = {
                        "email": user_temp_mail,
                        "alert": True,
                        "count": 0,
                    }
        else:
            bot.answer_callback_query(
                call_id, "Error getting new mail. Please try again.", show_alert=True
            )
