import telebot
import sqlite3
import matplotlib.pyplot as plt
import numpy as np

TOKEN = "7887756811:AAFyo_adpSdMuDPr8FYRIeRrniSlJEUg484"
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("students.db", check_same_thread=False)
cursor = conn.cursor()

def calculate_percentages(user_id):
    cursor.execute("SELECT sat, act, ielts, toefl, gpa, olympiads, volunteering, research, work FROM users WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    if not data:
        return None

    sat, act, ielts, toefl, gpa, olympiads, volunteering, research, work = data

    sat_percent = (sat / 1600 * 100) if sat else (act / 36 * 100) if act else 0
    ielts_percent = (ielts / 9 * 100) if ielts else (toefl / 120 * 100) if toefl else 0
    gpa_percent = (gpa / 4 * 100) if gpa else 0
    academic_score = np.mean([sat_percent, ielts_percent, gpa_percent])

    olympiad_score = 100 if olympiads and "международный" in olympiads else 80 if olympiads and "республиканский" in olympiads else 60 if olympiads else 0
    volunteering_score = 100 if volunteering and "100 часов" in volunteering else 75 if volunteering and "50 часов" in volunteering else 40 if volunteering else 0
    research_score = 100 if research else 0
    work_score = 100 if work else 0
    extracurricular_score = np.mean([olympiad_score, volunteering_score, research_score, work_score])

    base_admission_chance = 100 if academic_score >= 80 else 70 if academic_score >= 60 else 50
    if extracurricular_score > 70:
        base_admission_chance += 10

    return round(academic_score), round(extracurricular_score), round(base_admission_chance)

def generate_chart(user_id):
    academic, extracurricular, admission = calculate_percentages(user_id)
    
    labels = ["Академическая подготовка", "Внеклассные достижения", "Шансы на поступление"]
    values = [academic, extracurricular, admission]

    plt.figure(figsize=(6, 6))
    plt.bar(labels, values, color=["blue", "green", "red"])
    plt.ylim(0, 100)
    plt.ylabel("Процент")
    plt.title("Анализ шансов поступления")
    
    img_path = f"chart_{user_id}.png"
    plt.savefig(img_path)
    plt.close()
    return img_path

@bot.message_handler(commands=['analyze'])
def analyze(message):
    user_id = message.chat.id
    result = calculate_percentages(user_id)
    
    if not result:
        bot.send_message(user_id, "Данные не найдены. Сначала пройди опрос!")
        return
    
    academic, extracurricular, admission = result
    img_path = generate_chart(user_id)

    text = f"📊 Твой анализ:\n\n" \
           f"🔵 Академическая подготовка: {academic}%\n" \
           f"🟢 Внеклассные достижения: {extracurricular}%\n" \
           f"🔴 Шансы на поступление: {admission}%\n\n"

    recommendations = []
    if academic < 60:
        recommendations.append("📌 Улучшить SAT/ACT, IELTS/TOEFL или GPA для увеличения шансов.")
    if extracurricular < 50:
        recommendations.append("📌 Добавить участие в олимпиадах, волонтёрстве или исследовательских проектах.")
    if admission < 60:
        recommendations.append("📌 Рассмотреть университеты с низкими академическими требованиями или высоким шансом на грант.")

    text += "\n".join(recommendations) if recommendations else "Отличные результаты! Ты можешь поступить в сильные университеты."

    bot.send_message(user_id, text, parse_mode="Markdown")
    with open(img_path, "rb") as img:
        bot.send_photo(user_id, img)

bot.polling()