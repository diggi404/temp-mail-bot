from telebot import types

main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_btn1 = types.KeyboardButton("Get New Email ➕")
main_btn2 = types.KeyboardButton("Check Inbox 📨")
main_btn3 = types.KeyboardButton("Settings ⚙️")
main_markup.row(main_btn1)
main_markup.row(main_btn2, main_btn3)
