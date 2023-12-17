from telebot import TeleBot, types
from sqlalchemy.orm import Session
from database.models import TempMailUsers
import requests
import os


def view_message(bot: TeleBot, chat_id: int, msg_id: int, db_session: Session):
    take_msg = bot.send_message(chat_id, "Enter the message id: ")
    bot.register_next_step_handler(
        take_msg, lambda message: step_view_message(message, bot, db_session, msg_id)
    )


def step_view_message(
    message: types.Message, bot: TeleBot, db_session: Session, major_msg_id: int
):
    chat_id = message.from_user.id
    msg = message.text
    try:
        inbox_msg_id = int(msg)
    except:
        bot.send_message(chat_id, "You entered an invalid number.")
    else:
        get_user = (
            db_session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).first()
        )
        try:
            login_name, domain = get_user.email.split("@")
            get_inbox_msg = requests.get(
                f"https://www.1secmail.com/api/v1/?action=readMessage&login={login_name}&domain={domain}&id={inbox_msg_id}"
            )
        except:
            bot.send_message(
                chat_id, "Error getting inbox message. Please try again later."
            )
        else:
            if get_inbox_msg.status_code == 200:
                if get_inbox_msg.text == "Message not found":
                    bot.send_message(chat_id, "Message content can't be found.")
                else:
                    msg_details = get_inbox_msg.json()
                    with open(f"{inbox_msg_id}.html", "w") as content:
                        content.write(msg_details["body"])
                    bot.send_message(
                        chat_id,
                        f"From: <code>{msg_details['from']}</code>\nSubject: <b>{msg_details['subject']}</b>\nDate: <b>{msg_details['date']}</b>",
                        parse_mode="HTML",
                    )
                    with open(f"{inbox_msg_id}.html", "rb") as document:
                        bot.send_document(chat_id, document)
                    os.remove(f"{inbox_msg_id}.html")
                    if len(msg_details["attachments"]) != 0:
                        attachments = msg_details["attachments"]
                        bot.send_message(
                            chat_id, "<b>Attachments Found!</b>", parse_mode="HTML"
                        )
                        attachment_list = [
                            f"<b>{index}</b>. File name: <b>{a['filename']}</b>"
                            for index, a in enumerate(attachments, start=1)
                        ]
                        result_msg = (
                            f"Total attachments: <b>{len(attachments)}</b>\n\n"
                            + "\n".join(attachment_list)
                        )
                        bot.send_message(chat_id, result_msg, parse_mode="HTML")
                        attachment_markup = types.InlineKeyboardMarkup()
                        attachment_btn1 = types.InlineKeyboardButton(
                            "Yes ✅",
                            callback_data=f"yes download_{get_user.email}_{inbox_msg_id}",
                        )
                        attachment_btn2 = types.InlineKeyboardButton(
                            "No ❌", callback_data="no don't download"
                        )
                        attachment_markup.add(attachment_btn1, attachment_btn2)
                        bot.send_message(
                            chat_id,
                            "Do you want to download these attachments now?",
                            reply_markup=attachment_markup,
                        )

            else:
                bot.send_message(
                    chat_id, "Error getting inbox message. Please try again later."
                )
