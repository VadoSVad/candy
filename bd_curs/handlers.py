import telebot
from db import database_connection
from queries import view_table, execute_query, execute_best_price_weight_ratio_query
import pandas as pd
import matplotlib.pyplot as plt
import io

# Настройка matplotlib для использования Agg бэкенда
import matplotlib
matplotlib.use('Agg')

selected_role = None
bot = telebot.TeleBot("6531991006:AAEV1HbtO6DuX_DxxYJHj3SbzbnNztPnyYU")

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    keyboard.add(*[telebot.types.KeyboardButton(text=role) for role in ["administrator", "buhgalter", "driver"]])
    bot.send_message(message.chat.id, "Привет, добро пожаловать в бота базы данных кондитерской фабрики.\nПожалуйста выберите роль:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in ["administrator", "buhgalter", "driver"])
def process_role_selection(message):
    global selected_role
    selected_role = message.text
    if selected_role not in ["administrator", "buhgalter", "driver"]:
        bot.send_message(message.chat.id, "Некорректная роль")
    else:
        if selected_role == "administrator":
            bot.send_message(message.chat.id, "У вас все права")
        elif selected_role == "buhgalter":
            bot.send_message(message.chat.id, "Вы можете читать, обновлять и записывать новые данные")
        elif selected_role == "driver":
            bot.send_message(message.chat.id, "У вас ограниченный доступ к нескольким таблицам для чтения")
        show_main_menu(message)

def show_main_menu(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    buttons = ["Посмотреть таблицы", "Просмотреть запросы", "Работа с таблицами"]
    keyboard.add(*[telebot.types.KeyboardButton(text=button) for button in buttons])
    bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in ["Посмотреть таблицы", "Просмотреть запросы", "Работа с таблицами"])
def process_main_menu_selection(message):
    selected_option = message.text
    if selected_option == "Посмотреть таблицы":
        show_table_selection(message)
    elif selected_option == "Просмотреть запросы":
        show_query_selection(message)
    elif selected_option == "Работа с таблицами":
        bot.send_message(message.chat.id, "Эта функция пока не реализована.")
    else:
        bot.send_message(message.chat.id, "Некорректный выбор.")
        show_main_menu(message)

def show_query_selection(message):
    options = [
        "Общая сумма сырья",
        "Сумма цены заказов за год и самый дорогой заказ",
        "Лучшее соотношение цена/вес",
        "Первый водитель, приехавший по адресу магазина",
        "Список ингредиентов с наименьшим сроком годности",
        "Самый популярный товар в конкретном магазине",
        "Сотрудники, работающие в каждом цехе, и их количество",
        "Магазины, в которых директора заказали наибольшее количество продукции определенного вида",
        "Общая сумма заказанной продукции конкретным заказчиком по категориям: конфеты, шоколад и т.д.",
        "Вывод какой бухгалтер ведет того или иного сотрудника, работающего в том или ином цехе."
    ]
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    keyboard.add(*[telebot.types.KeyboardButton(text=option) for option in options])
    bot.send_message(message.chat.id, "Пожалуйста выберите запрос:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text in [
    "Общая сумма сырья",
    "Сумма цены заказов за год и самый дорогой заказ",
    "Лучшее соотношение цена/вес",
    "Первый водитель, приехавший по адресу магазина",
    "Список ингредиентов с наименьшим сроком годности",
    "Самый популярный товар в конкретном магазине",
    "Сотрудники, работающие в каждом цехе, и их количество",
    "Магазины, в которых директора заказали наибольшее количество продукции определенного вида",
    "Общая сумма заказанной продукции конкретным заказчиком по категориям: конфеты, шоколад и т.д.",
    "Вывод какой бухгалтер ведет того или иного сотрудника, работающего в том или ином цехе."
])
def process_query_selection(message):
    selected_query = message.text
    query_map = {
        "Общая сумма сырья": "SELECT total_ingredients_in_store()",
        "Сумма цены заказов за год и самый дорогой заказ": "SELECT max_order_amount_this_year()",
        "Лучшее соотношение цена/вес": "SELECT best_price_weight_ratio()",
        "Первый водитель, приехавший по адресу магазина": "CALL get_first_driver_to_store(%s)",
        "Список ингредиентов с наименьшим сроком годности": "CALL get_ingredients_with_shortest_shelf_life()",
        "Самый популярный товар в конкретном магазине": "CALL get_most_ordered_product_in_store(%s)",
        "Сотрудники, работающие в каждом цехе, и их количество": "CALL get_employees_by_ceh()",
        "Магазины, в которых директора заказали наибольшее количество продукции определенного вида": "CALL get_store_with_most_orders_by_product(%s)",
        "Общая сумма заказанной продукции конкретным заказчиком по категориям: конфеты, шоколад и т.д.": "CALL get_total_ordered_amount_by_product_type(%s)",
        "Вывод какой бухгалтер ведет того или иного сотрудника, работающего в том или ином цехе.": "CALL get_accountants_for_employee(%s)",
    }
    query = query_map.get(selected_query)
    if query:
        if '%s' in query:
            bot.send_message(message.chat.id, "Введите аргумент:")
            bot.register_next_step_handler(message, lambda m: execute_query_with_argument(m, selected_role, query, selected_query))
        else:
            result = execute_query(selected_role, query)
            if selected_query == "Лучшее соотношение цена/вес":
                result_text = f"Результат запроса '{selected_query}' представлен на графике"
                bot.send_message(message.chat.id, result_text)
                buf = execute_best_price_weight_ratio_query(selected_role, query)
                bot.send_photo(message.chat.id, buf)
            else:
                process_query_result(message, result, selected_query)
    else:
        bot.send_message(message.chat.id, "Некорректный запрос")
    show_main_menu(message)
def show_table_selection(message):
    global selected_role
    if selected_role:
        with database_connection(selected_role) as conn:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True)
            keyboard.add(*[telebot.types.KeyboardButton(text=table[0]) for table in tables])
            bot.send_message(message.chat.id, "Пожалуйста выберите таблицу:", reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def process_table_selection(message):
    selected_table = message.text
    if selected_table:
        df = view_table(selected_role, selected_table)
        table_text = "```\n" + df.to_markdown(index=False) + "\n```"
        bot.send_message(message.chat.id, table_text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "Неверное имя, выберите корректное название таблицы")
    show_main_menu(message)

def process_query_result(message, result, query_option):
    if result:
        if query_option == "Список ингредиентов с наименьшим сроком годности":
            ingredients_list = result[0].split(';')
            df = pd.DataFrame([ingredient.split(':') for ingredient in ingredients_list], columns=["Ингредиент", "Дней до окончания срока годности"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```", parse_mode="Markdown")
            create_pie_chart(message.chat.id, df)
        elif query_option == "Магазины, в которых директора заказали наибольшее количество продукции определенного вида":
            store_list = result[0].split(';')
            df = pd.DataFrame([store.split(':') for store in store_list], columns=["Магазин", "Кол-во товара"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```", parse_mode="Markdown")
        elif query_option == "Общая сумма заказанной продукции конкретным заказчиком по категориям: конфеты, шоколад и т.д.":
            category_list = result[0].split(';')
            df = pd.DataFrame([category.split(':') for category in category_list], columns=["Заказчик", "Сумма"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```", parse_mode="Markdown")
            create_line_chart(message.chat.id, df)
        elif query_option == "Вывод какой бухгалтер ведет того или иного сотрудника, работающего в том или ином цехе.":
            buh_list = result[0].split(';')
            df = pd.DataFrame([buh.split(':') for buh in buh_list], columns=["Имя сотрудника", "Цех, где он работает"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```", parse_mode="Markdown")
        elif query_option == "Сотрудники, работающие в каждом цехе, и их количество":
            sotrudnik_list = result[0].split(';')
            df = pd.DataFrame([sotrudnik.split(':') for sotrudnik in sotrudnik_list],columns=["Цех", "Кол-во сотрудников"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```",parse_mode="Markdown")
        else:
            result_text = f"Результат запроса '{query_option}': ``` {result[0]} ```"
            bot.send_message(message.chat.id, result_text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "Некорректный запрос или ошибка выполнения запроса")
    show_main_menu(message)

def create_pie_chart(chat_id, df):
    grouped_df = df.groupby("Дней до окончания срока годности")["Ингредиент"].apply(lambda x: ', '.join(x)).reset_index()
    sizes = grouped_df["Ингредиент"].apply(lambda x: len(x.split(', ')))
    labels = grouped_df["Дней до окончания срока годности"]
    ingredient_lists = grouped_df["Ингредиент"].apply(lambda x: x.split(', '))
    plt.figure(figsize=(6, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title("Срок годности ингредиентов")
    legend_labels = [f"{label}: {', '.join(ingredient_list)}" for label, ingredient_list in zip(labels, ingredient_lists)]
    plt.legend(legend_labels, loc="best", fontsize="small")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    bot.send_photo(chat_id, buf)

def create_line_chart(chat_id, df):
    df["Сумма"] = pd.to_numeric(df["Сумма"])
    df.sort_values(by="Заказчик", inplace=True)
    plt.figure(figsize=(10, 6))
    plt.plot(df["Заказчик"], df["Сумма"], marker='o')
    plt.title("Общая сумма заказанной продукции по категориям")
    plt.xlabel("Заказчик")
    plt.ylabel("Сумма")
    plt.grid(True)
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    bot.send_photo(chat_id, buf)

def execute_query_with_argument(message, role, query, query_option):
    argument = message.text
    if '%s' in query:
        query = query % argument
    elif '{}' in query:
        query = query.format(argument)

    result = execute_query(role, query)
    if query_option == "Магазины, в которых директора заказали наибольшее количество продукции определенного вида":
        if result:
            store_list = result[0].split(';')
            df = pd.DataFrame([store.split(':') for store in store_list], columns=["Магазин", "Кол-во товара"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```",parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "Некорректный запрос или ошибка выполнения запроса")
    elif query_option == "Общая сумма заказанной продукции конкретным заказчиком по категориям: конфеты, шоколад и т.д.":
        if result:
            category_list = result[0].split(';')
            df = pd.DataFrame([category.split(':') for category in category_list], columns=["Заказчик", "Сумма"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```",parse_mode="Markdown")
            create_line_chart(message.chat.id, df)
        else:
            bot.send_message(message.chat.id, "Некорректный запрос или ошибка выполнения запроса")
    elif query_option == "Вывод какой бухгалтер ведет того или иного сотрудника, работающего в том или ином цехе.":
        if result:
            buh_list = result[0].split(';')
            df = pd.DataFrame([buh.split(':') for buh in buh_list], columns=["Имя сотрудника", "Цех, где он работает"])
            table_text = df.to_markdown(index=False)
            bot.send_message(message.chat.id, f"Результат запроса '{query_option}':\n```\n{table_text}\n```",parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "Некорректный запрос или ошибка выполнения запроса")
    else:
        if result:
            result_text = f"Результат запроса '{query_option}': ``` {result[0]} ```"
            bot.send_message(message.chat.id, result_text, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, "Некорректный запрос или ошибка выполнения запроса")
    show_main_menu(message)

bot.polling()