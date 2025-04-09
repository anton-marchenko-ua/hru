import io
import telebot
from telebot import types
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta

bot = telebot.TeleBot("7892648405:AAH5QbiItfRp7iBe7Xi2XG_m0YNYkQAcfyI")

user_state = {}

TICKERS = {
    '🔵 Apple': 'AAPL',
    '🟣 Microsoft': 'MSFT',
    '🟢 Google': 'GOOG',
    '🔴 Amazon': 'AMZN',
    '🟠 Tesla': 'TSLA',
    '✍️ Ввести вручну': 'manual'
}

MONTHS = {
    1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
    5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
    9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
}


def generate_year_keyboard():
    markup = types.InlineKeyboardMarkup()
    current_year = datetime.now().year
    row = []
    for year in range(current_year - 2, current_year + 1):
        row.append(types.InlineKeyboardButton(str(year), callback_data=f"year_{year}"))
        if len(row) == 3:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    return markup


def generate_month_keyboard(year):
    markup = types.InlineKeyboardMarkup()
    row = []
    for month in range(1, 13):
        row.append(types.InlineKeyboardButton(MONTHS[month], callback_data=f"month_{year}_{month}"))
        if len(row) == 3:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    return markup


def generate_day_keyboard(year, month):
    markup = types.InlineKeyboardMarkup()
    days_in_month = (datetime(year, month + 1, 1) - timedelta(days=1)).day if month != 12 else 31
    row = []
    for day in range(1, days_in_month + 1):
        row.append(types.InlineKeyboardButton(str(day), callback_data=f"day_{year}_{month}_{day}"))
        if len(row) == 7:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    return markup


@bot.message_handler(commands=['start', 'yf'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for name in TICKERS:
        markup.add(name)
    bot.send_message(message.chat.id, "Обери компанію або введи тікер:", reply_markup=markup)
    user_state[message.chat.id] = {'step': 'choose_ticker'}


@bot.message_handler(func=lambda message: user_state.get(message.chat.id, {}).get('step') == 'choose_ticker')
def choose_ticker(message):
    text = message.text
    if text in TICKERS:
        if TICKERS[text] == 'manual':
            bot.send_message(message.chat.id, "Введи тікер (наприклад, NVDA):")
            user_state[message.chat.id]['step'] = 'manual_input'
        else:
            user_state[message.chat.id]['ticker'] = TICKERS[text]
            start_date_selection(message)
    else:
        bot.send_message(message.chat.id, "Будь ласка, обери одну з кнопок.")


@bot.message_handler(func=lambda message: user_state.get(message.chat.id, {}).get('step') == 'manual_input')
def manual_input(message):
    user_state[message.chat.id]['ticker'] = message.text.upper()
    start_date_selection(message)


def start_date_selection(message):
    bot.send_message(message.chat.id, "Оберіть рік для дати початку:",
                     reply_markup=generate_year_keyboard())
    user_state[message.chat.id]['step'] = 'select_start_year'


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    state = user_state.get(chat_id, {})

    if not state:
        bot.answer_callback_query(call.id, "Сесія закінчилась. Почніть спочатку /start")
        return

    if state['step'] == 'select_start_year' and call.data.startswith('year_'):
        year = int(call.data.split('_')[1])
        state['start_year'] = year
        bot.edit_message_text("Оберіть місяць для дати початку:",
                              chat_id, call.message.message_id,
                              reply_markup=generate_month_keyboard(year))
        state['step'] = 'select_start_month'

    elif state['step'] == 'select_start_month' and call.data.startswith('month_'):
        _, year, month = call.data.split('_')
        state['start_month'] = int(month)
        bot.edit_message_text("Оберіть день для дати початку:",
                              chat_id, call.message.message_id,
                              reply_markup=generate_day_keyboard(int(year), int(month)))
        state['step'] = 'select_start_day'

    elif state['step'] == 'select_start_day' and call.data.startswith('day_'):
        _, year, month, day = call.data.split('_')
        start_date = datetime(int(year), int(month), int(day))
        state['start_date'] = start_date
        bot.edit_message_text(
            f"Дата початку: {start_date.strftime('%d.%m.%Y')}\nТепер оберіть рік для дати завершення:",
            chat_id, call.message.message_id,
            reply_markup=generate_year_keyboard())
        state['step'] = 'select_end_year'

    elif state['step'] == 'select_end_year' and call.data.startswith('year_'):
        year = int(call.data.split('_')[1])
        state['end_year'] = year
        bot.edit_message_text("Оберіть місяць для дати завершення:",
                              chat_id, call.message.message_id,
                              reply_markup=generate_month_keyboard(year))
        state['step'] = 'select_end_month'

    elif state['step'] == 'select_end_month' and call.data.startswith('month_'):
        _, year, month = call.data.split('_')
        state['end_month'] = int(month)
        bot.edit_message_text("Оберіть день для дати завершення:",
                              chat_id, call.message.message_id,
                              reply_markup=generate_day_keyboard(int(year), int(month)))
        state['step'] = 'select_end_day'

    elif state['step'] == 'select_end_day' and call.data.startswith('day_'):
        _, year, month, day = call.data.split('_')
        end_date = datetime(int(year), int(month), int(day))
        state['end_date'] = end_date
        bot.edit_message_text(
            f"Дякую! Створюю графік для періоду:\n{state['start_date'].strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            chat_id, call.message.message_id)
        draw_and_send_chart(chat_id)


def draw_and_send_chart(chat_id):
    state = user_state.get(chat_id, {})
    if not state:
        bot.send_message(chat_id, "Сесія закінчилась. Почніть спочатку /start")
        return

    ticker = state.get('ticker')
    start_date = state.get('start_date')
    end_date = state.get('end_date')

    if not all([ticker, start_date, end_date]):
        bot.send_message(chat_id, "Щось пішло не так. Почніть спочатку /start")
        return

    try:
        # Add 1 day to include the end date in results
        end_date_plus_one = end_date + timedelta(days=1)
        data = yf.download(ticker, start=start_date, end=end_date_plus_one)

        if data.empty:
            bot.send_message(chat_id, f"Немає даних для {ticker} у вказаний період.")
            return

        plt.figure(figsize=(10, 5))
        plt.plot(data['Close'], label=f"{ticker} Close", linewidth=2)
        plt.title(f"{ticker} {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
        plt.xlabel("Дата", fontsize=10)
        plt.ylabel("Ціна ($)", fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120)
        buf.seek(0)
        plt.close()

        bot.send_photo(chat_id, buf,
                       caption=f"Графік для {ticker}\nПеріод: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
        buf.close()
    except Exception as e:
        bot.send_message(chat_id, f"Помилка при створенні графіка: {str(e)}")
    finally:
        if chat_id in user_state:
            del user_state[chat_id]


if __name__ == '__main__':
    print("Bot is running...")
    bot.polling(none_stop=True)