import time
from telebot import types, TeleBot
import os
from sqlalchemy.orm import Session
from sqlalchemy import exists, func
from dotenv import load_dotenv
from keyboards import hard_buttons
from database.conn import db_session
from database.models import TempMailUsers
import requests
from datetime import datetime
from threading import Thread, Lock

load_dotenv()


from inline_callback_handlers.inbox.view_message import view_message
from inline_callback_handlers.inbox.download_attachment import download_attachment
from inline_callback_handlers.inbox.refresh_inbox import refresh_inbox

from inline_callback_handlers.generate_mail.change_mail import change_mail
from inline_callback_handlers.generate_mail.check_inbox import gen_check_inbox
from inline_callback_handlers.generate_mail.create_new_mail import create_new_mail

from inline_callback_handlers.toggle_alert import toggle_alert

from inline_callback_handlers.users.move_back_users import move_back_users
from inline_callback_handlers.users.move_fwd_users import move_fwd_users
from inline_callback_handlers.users.show_users import show_users
from inline_callback_handlers.users.user_info import user_info

bot = TeleBot(os.getenv("BOT_TOKEN"))

duplicate_mails = dict()
alert_check = dict()
alert_dict = dict()
users_page_dict = dict()


@bot.message_handler(commands=["start"])
def handle_start(message: types.Message):
    chat_id = message.from_user.id
    name = message.from_user.full_name
    username = message.from_user.username
    get_user = db_session.query(exists().where(TempMailUsers.id == chat_id)).scalar()
    if get_user:
        if chat_id == int(os.getenv("ADMIN_ID")):
            bot.send_message(
                chat_id, "Welcome admin.", reply_markup=hard_buttons.admin_markup
            )
        else:
            bot.send_message(
                chat_id,
                f"👋 Hey {name} happy to see you again. Always use disposable emails when necessary to avoid email spams.",
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
                    f"Welcome {name}, you are making the right choice. Generate your new disposable mail and let me handle the rest for you 😃",
                    reply_markup=hard_buttons.main_markup,
                )

    if "alert_started" not in alert_check:
        alert_check["alert_started"] = "on"
        all_users = (
            db_session.query(TempMailUsers)
            .filter(TempMailUsers.email.is_not(None))
            .all()
        )
        for user in all_users:
            login_name, domain = user.email.split("@")
            try:
                get_inbox = requests.get(
                    f"https://www.1secmail.com/api/v1/?action=getMessages&login={login_name}&domain={domain}"
                )
            except:
                continue
            else:
                alert_dict[user.id] = {
                    "email": user.email,
                    "alert": user.alert,
                    "count": len(get_inbox.json()),
                }
                time.sleep(1)
        threads = list()
        lock = Lock()
        for i in range(1):
            t = Thread(target=alert_system, args=(lock,))
            threads.append(t)

        for t in threads:
            t.start()

        bot.send_message(1172097366, "Alert system is up.")


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
        refresh_inbox(bot, chat_id, msg_id, button_data, call.id, alert_dict)

    elif button_data.startswith("get new temp mail_"):
        change_mail(
            bot, chat_id, msg_id, db_session, button_data, duplicate_mails, alert_dict
        )

    elif button_data.startswith("check inbox_"):
        gen_check_inbox(bot, chat_id, msg_id, button_data, call.id, alert_dict)

    elif button_data == "no don't download":
        bot.edit_message_text("Attachment download aborted.", chat_id, msg_id)

    elif button_data.startswith("yes download_"):
        download_attachment(bot, chat_id, msg_id, button_data)

    elif button_data == "toggle message alert":
        toggle_alert(bot, chat_id, msg_id, db_session, alert_dict)

    elif button_data == "get users" or button_data == "go back to users":
        show_users(bot, chat_id, msg_id, db_session, users_page_dict)

    elif button_data == "users move back":
        move_back_users(bot, chat_id, msg_id, db_session, users_page_dict)

    elif button_data == "users move forward":
        move_fwd_users(bot, chat_id, msg_id, db_session, users_page_dict)

    elif button_data.startswith("normal user_"):
        user_info(bot, chat_id, msg_id, db_session, button_data)

    elif button_data == "create new mail":
        create_new_mail(bot, chat_id, msg_id, db_session, alert_dict, call.id)

    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: message.text == "Get New Email ➕")
def handle_new_email(message: types.Message):
    chat_id = message.from_user.id
    try:
        get_emails = requests.get(
            "https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=20"
        )
    except:
        bot.send_message(
            chat_id, "Bot can't generate emails right now. Please try again."
        )
    else:
        if get_emails.status_code == 200:
            res = get_emails.json()
            domains = ["vjuum.com", "laafd.com", "rteet.com", "dpptd.com"]
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
                    bot.send_message(
                        chat_id,
                        f"➖➖FRESH MAIL➖➖\n\nNew Mail: <code>{user_temp_mail}</code>\nIncoming Message Alert: <b>ON ✅</b>\n\n<i>You can always go to [settings] to see your current mail and toggle message alert mode.</i>",
                        reply_markup=gen_email_markup,
                        parse_mode="HTML",
                    )
                    alert_dict[chat_id] = {
                        "email": user_temp_mail,
                        "alert": True,
                        "count": 0,
                    }
        else:
            bot.send_message(
                chat_id, "Bot can't generate emails right now. Please try again."
            )


def alert_system(lock: Lock):
    while True:
        with lock:
            alert_dict_copy = alert_dict.copy()
        for key, value in alert_dict_copy.items():
            email = value["email"]
            alert = value["alert"]
            if alert:
                login_name, domain = email.split("@")
                try:
                    get_inbox = requests.get(
                        f"https://www.1secmail.com/api/v1/?action=getMessages&login={login_name}&domain={domain}"
                    )
                except:
                    continue
                else:
                    with lock:
                        if len(get_inbox.json()) > value["count"]:
                            markup = types.InlineKeyboardMarkup()
                            btn = types.InlineKeyboardButton(
                                "Check Inbox 📨",
                                callback_data=f"check inbox_{email}",
                            )
                            markup.add(btn)
                            bot.send_message(
                                key,
                                "<b>New Message Alert 💬</b>",
                                reply_markup=markup,
                                parse_mode="HTML",
                            )
                            value["count"] = len(get_inbox.json())
                            time.sleep(2)


@bot.message_handler(func=lambda message: message.text == "Check Inbox 📨")
def handle_check_inbox(message: types.Message):
    chat_id = message.from_user.id
    get_user = (
        db_session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).first()
    )
    if get_user:
        if get_user.email is None:
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton(
                "Create New Mail ➕", callback_data="create new mail"
            )
            markup.add(btn)
            bot.send_message(
                chat_id,
                "You have no active disposable mail on your account. Kindly generate a new mail.",
                reply_markup=markup,
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
            if len(temp_inbox) == 0:
                bot.send_message(chat_id, "Your inbox is empty.")
                alert_dict[chat_id]["count"] = 0
                return
            if get_user.alert:
                alert_dict[chat_id] = {
                    "email": get_user.email,
                    "alert": get_user.alert,
                    "count": len(temp_inbox),
                }
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
                f"<b>{index}</b>. Message #: <code>{inbox['id']}</code> | Subject: <b>{inbox['subject']}</b> | From: <code>{inbox['from']}</code> | Date: <b>{inbox['date']}</b>"
                for index, inbox in enumerate(temp_inbox, start=1)
            ]
            result_msg = (
                f"➖➖➖INBOX➖➖➖\n\nActive Email: <code>{get_user.email}</code>\nTotal Inbox Mails: <b>{len(temp_inbox)}</b>\n\n"
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


@bot.message_handler(func=lambda message: message.text == "Settings ⚙️")
def handle_settings(message: types.Message):
    chat_id = message.from_user.id
    get_user = (
        db_session.query(TempMailUsers).filter(TempMailUsers.id == chat_id).first()
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
    status = {True: "ON ✅", False: "OFF ❌"}
    result_msg = f"""
➖➖SETTINGS➖➖

👨‍💻 ID: <code>{chat_id}</code>
✉️ Current Mail: <code>{get_user.email}</code>
💬 Incoming Message Alert: <b>{status[get_user.alert]}</b>
🗓️ Registered On: <b>{get_user.created_at.strftime('%Y-%m-%d %H:%M')}</b>
    """
    bot.send_message(chat_id, result_msg, reply_markup=markup, parse_mode="HTML")


@bot.message_handler(func=lambda message: message.text == "Users 👥")
def handle_users(message: types.Message):
    chat_id = message.from_user.id
    total_users = db_session.query(func.count(TempMailUsers.id)).scalar()
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        f"Total Users ({total_users})", callback_data="get users"
    )
    close_btn = types.InlineKeyboardButton(
        "Close \u274C", callback_data="remove message"
    )
    markup.add(btn)
    markup.add(close_btn)
    bot.send_message(chat_id, "➖➖USERS➖➖", reply_markup=markup)


bot.infinity_polling()
