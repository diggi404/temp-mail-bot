from telebot import TeleBot, types
import requests


def gen_check_inbox(
    bot: TeleBot, chat_id: int, msg_id: int, button_data: str, total_inbox_dict: dict
):
    temp_mail = button_data.split("_")[1]
    login_name, domain = temp_mail.split("@")
    try:
        get_inbox = requests.get(
            f"https://www.1secmail.com/api/v1/?action=getMessages&login={login_name}&domain={domain}"
        )
    except:
        bot.edit_message_text(
            "Sorry you can't check inbox right now. Try again later.", chat_id, msg_id
        )
    else:
        temp_inbox = get_inbox.json()
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
            f"Active Email: <code>{temp_mail}</code>\nTotal Inbox Mails: <b>{len(temp_inbox)}</b>\n\n"
            + "\n".join(temp_inbox_list)
        )
        if total_inbox_dict[chat_id] != len(temp_inbox):
            total_inbox_dict[chat_id] += len(temp_inbox)
        bot.edit_message_text(
            result_msg, chat_id, msg_id, parse_mode="HTML", reply_markup=inbox_markup
        )
