import random
from telebot import TeleBot, types
import requests


def refresh_inbox(
    bot: TeleBot,
    chat_id: int,
    msg_id: int,
    button_data: str,
    call_id: int,
    alert_dict: dict,
):
    temp_mail = button_data.split("_")[2]
    prev_temps = button_data.split("_")[1]
    prev_temps = int(prev_temps)
    try:
        login_name, domain = temp_mail.split("@")
        get_inbox = requests.get(
            f"https://www.1secmail.com/api/v1/?action=getMessages&login={login_name}&domain={domain}"
        )
    except:
        bot.edit_message_text(
            "Error refreshing inbox. Please try recheck the inbox.", chat_id, msg_id
        )
    else:
        if get_inbox.status_code == 200:
            temp_inbox = get_inbox.json()
            if prev_temps == len(temp_inbox):
                bot.answer_callback_query(
                    call_id, "No new messages yet.", show_alert=True
                )
                alert_dict[chat_id]["count"] = len(temp_inbox)
                return
            alert_dict[chat_id]["email"] = temp_mail
            alert_dict[chat_id]["count"] = len(temp_inbox)
            inbox_markup = types.InlineKeyboardMarkup()
            inbox_btn1 = types.InlineKeyboardButton(
                "View Message", callback_data="view inbox message"
            )
            inbox_btn2 = types.InlineKeyboardButton(
                "Refresh 🔄",
                callback_data=f"refresh inbox_{len(temp_inbox)}_{temp_mail}",
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
                f"➖➖➖INBOX➖➖➖\n\nActive Email: <code>{temp_mail}</code>\nTotal Inbox Mails: <b>{len(temp_inbox)}</b>\n\n"
                + "\n\n".join(temp_inbox_list)
            )
            bot.edit_message_text(
                result_msg,
                chat_id,
                msg_id,
                reply_markup=inbox_markup,
                parse_mode="HTML",
            )
        else:
            bot.edit_message_text(
                "Error refreshing inbox. Please try recheck the inbox.", chat_id, msg_id
            )
