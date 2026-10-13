import os, json, re
import requests
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")

SUBJECTS = {"Математика", "Физика", "Литература", "Кыргызский язык", "История мира",
            "История Кыргызстана", "Биология", "Русский язык"}


@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.route("/api/questions", methods=["POST"])
def questions():
    if not API_KEY:
        return jsonify(error="ANTHROPIC_API_KEY не задан"), 500
    data = request.get_json(silent=True) or {}
    try:
        grade = int(data.get("grade", 5))
        n = int(data.get("n", 20))
    except (TypeError, ValueError):
        return jsonify(error="bad params"), 400
    subject = data.get("subject", "")
    if not (1 <= grade <= 9) or subject not in SUBJECTS:
        return jsonify(error="bad params"), 400
    n = max(5, min(n, 20))

    lang = ("Вопросы по кыргызскому языку пиши на русском, а примеры слов давай на кыргызском."
            if subject == "Кыргызский язык" else "Пиши по-русски.")
    prompt = (f"Ты составитель школьных блиц-викторин. Составь ровно {n} разных вопросов для {grade} класса "
              f"школы Кыргызстана по предмету «{subject}» по школьной программе. Сложность растёт от лёгких к "
              f"сложным, но всё по уровню {grade} класса. Вопросы короткие, ответ однозначный и короткий "
              f"(слово, число, фраза). Темы не повторяй. {lang} Верни ТОЛЬКО JSON-массив вида "
              f'[{{"q":"вопрос","a":"ответ"}}], без пояснений и без markdown.')
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": MODEL, "max_tokens": 4000,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=100)
        r.raise_for_status()
        text = "".join(b.get("text", "") for b in r.json()["content"])
        text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
        items = json.loads(text)
        out = [{"q": str(x["q"]), "a": str(x["a"])} for x in items][:n]
        if len(out) < n:
            raise ValueError("мало вопросов")
        return jsonify(out)
    except Exception as e:
        print("AI error:", e)
        return jsonify(error="ai_failed"), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
