from telebot import types

main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
main_btn1 = types.KeyboardButton("Get New Email ➕")
main_btn2 = types.KeyboardButton("Check Inbox 📨")
main_btn3 = types.KeyboardButton("Settings ⚙️")
main_markup.row(main_btn1)
main_markup.row(main_btn2, main_btn3)


admin_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_btn1 = types.KeyboardButton("Get New Email ➕")
admin_btn2 = types.KeyboardButton("Check Inbox 📨")
admin_btn3 = types.KeyboardButton("Settings ⚙️")
admin_btn4 = types.KeyboardButton("Users 👥")
admin_markup.row(admin_btn1)
admin_markup.row(admin_btn2, admin_btn3)
admin_markup.row(admin_btn4)
