import time
from telebot import types, TeleBot
import os
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from keyboards import hard_buttons
from database.conn import db_session
from database.models import TempMailUsers
import requests
from datetime import datetime
from threading import Thread

load_dotenv()


from inline_callback_handlers.inbox.view_message import view_message
from inline_callback_handlers.inbox.download_attachment import download_attachment
from inline_callback_handlers.inbox.refresh_inbox import refresh_inbox

from inline_callback_handlers.generate_mail.change_mail import change_mail
from inline_callback_handlers.generate_mail.check_inbox import gen_check_inbox

bot = TeleBot(os.getenv("BOT_TOKEN"))

duplicate_mails = dict()
total_inbox_dict = dict()


@bot.message_handler(commands=["start"])
def handle_start(message: types.Message):
    chat_id = message.from_user.id
    name = message.from_user.full_name
    username = message.from_user.username
    get_user = (
        db_session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).first()
    )
    if get_user:
        bot.send_message(
            chat_id,
            f"<i>Welcome <b>{name}</b> to our free disposable email service. Get unlimited number of temporal mails without any cost 🥳. Don't hesitate to contact support if you experience any issues.</i>",
            parse_mode="HTML",
            reply_markup=hard_buttons.main_markup,
        )
    else:
        with db_session as session:
            try:
                user_details = TempMailUsers(
                    id=chat_id,
                    username=username,
                    name=name,
                    updated_at=datetime.utcnow(),
                )
                session.add(user_details)
                session.commit()
            except Exception as e:
                print(e)
                session.rollback()
                bot.send_message(
                    chat_id, "User registration failed. Kinldy restart the bot."
                )
            else:
                bot.send_message(
                    chat_id,
                    f"Welcome {name} to our free disapoble email service.",
                    reply_markup=hard_buttons.main_markup,
                )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call: types.CallbackQuery):
    button_data = call.data
    chat_id = call.from_user.id
    msg_id = call.message.id

    if button_data == "remove message":
        bot.delete_message(chat_id, msg_id)

    elif button_data == "view inbox message":
        view_message(bot, chat_id, msg_id, db_session)

    elif button_data.startswith("refresh inbox_"):
        refresh_inbox(bot, chat_id, msg_id, button_data, call.id, total_inbox_dict)

    elif button_data.startswith("get new temp mail_"):
        change_mail(bot, chat_id, msg_id, db_session, button_data, duplicate_mails)

    elif button_data.startswith("check inbox_"):
        gen_check_inbox(bot, chat_id, msg_id, button_data, total_inbox_dict)

    elif button_data == "no don't download":
        bot.edit_message_text("Attachment download aborted.", chat_id, msg_id)

    elif button_data.startswith("yes download_"):
        download_attachment(bot, chat_id, msg_id, button_data)

    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.text == "Get New Email")
def handle_new_email(message: types.Message):
    chat_id = message.from_user.id
    try:
        get_emails = requests.get(
            "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=10"
        )
    except:
        bot.send_message(
            chat_id, "Bot can't generate emails right now. Please try again."
        )
    else:
        total_inbox_dict[chat_id] = 0
        if get_emails.status_code == 200:
            temp_list = get_emails.json()
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
                else:
                    bot.send_message(
                        chat_id,
                        f"New Mail: <code>{user_temp_mail}</code>",
                        reply_markup=gen_email_markup,
                        parse_mode="HTML",
                    )
                    thread = Thread(
                        target=incoming_inbox,
                        args=(chat_id, bot, 2, user_temp_mail, total_inbox_dict),
                    )
                    thread.start()

        else:
            bot.send_message(
                chat_id, "Bot can't generate emails right now. Please try again."
            )


def incoming_inbox(
    chat_id: int,
    bot: TeleBot,
    delay: int,
    temp_mail: str,
    total_inbox_dict: dict,
):
    login_name, domain = temp_mail.split("@")
    if chat_id not in total_inbox_dict:
        total_inbox_dict[chat_id] = 0
    while True:
        try:
            get_inbox = requests.get(
                f"https://www.1secmail.com/api/v1/?action=getMessages&login={login_name}&domain={domain}"
            )
        except:
            pass
        else:
            if len(get_inbox.json()) > total_inbox_dict[chat_id]:
                markup = types.InlineKeyboardMarkup()
                btn = types.InlineKeyboardButton(
                    "Check Inbox 📨", callback_data=f"check inbox_{temp_mail}"
                )
                markup.add(btn)
                bot.send_message(
                    chat_id,
                    "<b>New Inbox Message Alert 💬</b>",
                    reply_markup=markup,
                    parse_mode="HTML",
                )
                new_inboxes = len(get_inbox.json()) - total_inbox_dict[chat_id]
                total_inbox_dict[chat_id] += new_inboxes
            time.sleep(delay)


@bot.message_handler(func=lambda message: message.text == "Check Inbox")
def handle_check_inbox(message: types.Message):
    chat_id = message.from_user.id
    get_user = (
        db_session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).first()
    )
    if get_user:
        if get_user.email is None:
            bot.send_message(
                chat_id,
                "You have no active disposable mail on your account. Kindly generate a new mail.",
            )
            return
        login_name, domain = get_user.email.split("@")
        try:
            get_inbox = requests.get(
                f"https://www.1secmail.com/api/v1/?action=getMessages&login={login_name}&domain={domain}"
            )
        except:
            bot.send_message(
                chat_id, "Sorry you can't check inbox right now. Try again later."
            )
        else:
            temp_inbox = get_inbox.json()
            inbox_markup = types.InlineKeyboardMarkup()
            inbox_btn1 = types.InlineKeyboardButton(
                "View Message", callback_data="view inbox message"
            )
            inbox_btn2 = types.InlineKeyboardButton(
                "Refresh 🔄",
                callback_data=f"refresh inbox_{len(temp_inbox)}_{get_user.email}",
            )
            close_btn = types.InlineKeyboardButton(
                "Close \u274C", callback_data="remove message"
            )
            inbox_markup.add(inbox_btn1)
            inbox_markup.add(inbox_btn2, close_btn)
            temp_inbox_list = [
                f"<b>{index}</b>. Msg Id: <code>{inbox['id']}</code> | Subject: <b>{inbox['subject']}</b> | From: <code>{inbox['from']}</code> | Date: <b>{inbox['date']}</b>"
                for index, inbox in enumerate(temp_inbox, start=1)
            ]
            result_msg = (
                f"Active Email: <code>{get_user.email}</code>\nTotal Inbox Mails: <b>{len(temp_inbox)}</b>\n\n"
                + "\n\n".join(temp_inbox_list)
            )
            bot.send_message(
                chat_id,
                result_msg,
                parse_mode="HTML",
                reply_markup=inbox_markup,
            )
    else:
        bot.send_message(chat_id, "Sorry you have no active account with us.")


@bot.message_handler(func=lambda message: message.text == "Show Current Email")
def show_current_email(message: types.Message):
    chat_id = message.from_user.id
    get_user = (
        db_session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).first()
    )
    if get_user.email is not None:
        bot.send_message(
            chat_id, f"Active Email: <code>{get_user.email}</code>", parse_mode="HTML"
        )
    else:
        bot.send_message(
            chat_id,
            "You have no active disposable email. Kindly generate a new mail.",
        )


@bot.message_handler(func=lambda message: message.text == "Support")
def handle_support(message: types.Message):
    bot.send_message(message.from_user.id, "Contact support here @yeptg")


bot.infinity_polling()
