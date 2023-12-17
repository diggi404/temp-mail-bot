from telebot import TeleBot
import requests
import os


def download_attachment(bot: TeleBot, chat_id: int, msg_id: int, button_data: str):
    temp_mail = button_data.split("_")[1]
    inbox_msg_id = button_data.split("_")[2]
    inbox_msg_id = int(inbox_msg_id)
    try:
        login_name, domain = temp_mail.split("@")
        get_inbox_msg = requests.get(
            f"https://www.1secmail.com/api/v1/?action=readMessage&login={login_name}&domain={domain}&id={inbox_msg_id}"
        )
    except:
        bot.edit_message_text(
            "Sorry you can't download attachment now. Please try again later.",
            chat_id,
            msg_id,
        )
    else:
        if get_inbox_msg.status_code == 200:
            attachments = get_inbox_msg.json()["attachments"]
            file_names = [a["filename"] for a in attachments]
            bot.delete_message(chat_id, msg_id)
            for index, file in enumerate(file_names, start=1):
                try:
                    get_file = requests.get(
                        f"https://www.1secmail.com/api/v1/?action=download&login={login_name}&domain={domain}&id={inbox_msg_id}&file={file}"
                    )
                except:
                    if index == len(file_names):
                        bot.edit_message_text(
                            "Sorry you can't download attachment now. Please try again later.",
                            chat_id,
                            msg_id,
                        )
                else:
                    with open(file, "wb") as a_file:
                        a_file.write(get_file.content)

                    with open(file, "rb") as document:
                        bot.send_document(chat_id, document)

                    os.remove(file)

        else:
            bot.edit_message_text(
                "Sorry you can't download attachment now. Please try again later.",
                chat_id,
                msg_id,
            )
