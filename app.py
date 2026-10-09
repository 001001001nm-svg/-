import os
import random
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Настройка Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

generation_config = {"temperature": 0.7}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=(
        "Ты — профессиональный учитель и составитель школьных викторин. "
        "Генерируй интересные, интеллектуальные и строго корректные вопросы для школьников. "
        "ПРАВИЛА:\n"
        "1. Запрещены любые заглушки вроде 'Вопрос №...' или 'Ответ на вопрос'. Вопрос должен быть реальным.\n"
        "2. Ответ должен быть кратким и точным (одно слово, дата или короткая фраза).\n"
        "3. Отвечай СТРОГО в формате JSON с двумя ключами: 'question' и 'answer'."
    )
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_question', methods=['POST'])
def generate_question():
    data = request.json
    subject = data.get('subject', 'Общие знания')
    grade = data.get('grade', '5-9 класс')
    lang = data.get('lang', 'ru')
    
    lang_prompt = "на русском языке"
    if lang == 'kg':
        lang_prompt = "на кыргызском языке"
    elif lang == 'en':
        lang_prompt = "на английском языке"
        
    prompt = f"Сгенерируй один интересный вопрос по предмету '{subject}' для уровня '{grade}' {lang_prompt}. Верни результат строго в формате JSON: {{\"question\": \"текст вопроса\", \"answer\": \"краткий правильный ответ\"}}"
    
    try:
        if not GEMINI_API_KEY:
            raise Exception("No API key")
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        import json
        result = json.loads(text.strip())
        return jsonify(result)
    except Exception as e:
        fallbacks = [
            {"question": "Какая планета Солнечной системы находится ближе всего к Солнцу?", "answer": "Меркурий"},
            {"question": "Чему равен корень из 144?", "answer": "12"},
            {"question": "В каком году началась вторая мировая война?", "answer": "1939"},
            {"question": "Какой газ преобладает в атмосфере Земли?", "answer": "Азот"}
        ]
        return jsonify(random.choice(fallbacks))

if __name__ == '__main__':
    app.run(debug=True)
