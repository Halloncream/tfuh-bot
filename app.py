from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

interviewer_prompt = """
Du är ChatRude9000 – en vältalig, subtil och psykologiskt vass intervjuare. Du är inte otrevlig, men du är heller inte rädd för tystnad eller obekväma frågor. Du talar som en terapeut med militär precision. 

Ditt syfte är att förstå människan du talar med, särskilt kopplat till:
- Organisatorisk psykologi
- Ledarskap och påverkan
- Lärande och motivation

Instruktioner:
- Inled alltid med att välkomna användaren till intervjun och säg att det finns 35 frågor.
- Frågorna ställs en i taget.
- Efter varje svar: analysera det.
    - Om svaret är för kort, irrelevant eller undvikande – fråga samma fråga igen, fast omformulerad.
    - Om svaret innehåller teman som organisation, ledarskap eller lärande – ställ en uppföljningsfråga.
    - Om svaret är tillräckligt – gå vidare till nästa huvudfråga.
- Avsluta aldrig samtalet utan att be om en reflektion kring intervjun.
- Skriv aldrig ut hela frågelistan.
"""

starter_questions = [
    "Vad har du för roll eller titel i organisationen?",
    "Har du någon formell utbildning eller träning?",
    "Hur länge har du arbetat här?",
    "Varför sökte du det här jobbet?",
    "Vilka är de tre bästa sakerna med att arbeta här?",
    "Och de tre sämsta?",
    "Finns det någon i organisationen du ser som en förebild?",
    "Är det någon som visar dig särskild omtanke?",
    "Hur inspireras du professionellt?",
    "Påverkar ledarskapet din arbetsinsats?",
    "På vilken nivå sker den påverkan?",
    "Anser du att ledarskapet är effektivt?",
    "Tycker du att verksamheten rör sig i rätt riktning?",
    "Känner du dig hörd på jobbet?",
    "Vad skulle du vilja göra mer av i ditt arbete?",
    "Är ansvarsområdena tydliga för dig?",
    "Kan du hålla balansen mellan arbete och fritid?",
    "Vad är organisationens vision eller mål enligt dig?",
    "Känner du av grupptryck?",
    "Hur upplever du ledarskapets förmåga att förmedla idéer?",
    "Förstår du helheten i förändringar som sker?",
    "Är du generellt mottaglig för förändring?",
    "Spelar det roll om du följer instruktioner?",
    "Tycker du om att lära dig nya saker på jobbet?",
    "Använder du AI?",
    "Hur hanterar du tekniska problem?",
    "Hur hanterar du mänskliga problem?",
    "Följs problem upp på något systematiskt sätt?",
    "Vem är du lojal mot – kollegor eller ledning?",
    "Vad ökar din motivation?",
    "Vad minskar den?",
    "Tror du att dina insatser påverkar organisationens samverkan med andra?",
    "Drivs du mer av personlig utveckling eller pengar?",
    "Hjälper du dina kollegor?",
    "Hjälper de dig?",
    "Har du några tankar eller känslor efter den här intervjun?"
]

question_index = 0

@app.route("/chat", methods=["POST"])
def chat():
    global question_index
    data = request.get_json()
    user_input = data.get("message", "")
    history = data.get("history", [])

    messages = [{"role": "system", "content": interviewer_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})

    current_question = starter_questions[question_index] if question_index < len(starter_questions) else "Tack för din medverkan."
    messages.append({"role": "assistant", "content": current_question})

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Log to file with time
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"interview_log_{timestamp}.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"User: {user_input}\n")
        log_file.write(f"ChatRude9000: {reply}\n\n")

    # Beslutslogik för hur vi går vidare
    if "denna fråga igen" in reply.lower() or "förstår inte" in reply.lower():
        pass  # stanna kvar på samma fråga
    elif "uppföljning" in reply.lower():
        pass  # stanna kvar
    elif "nästa fråga" in reply.lower() or len(reply) > 200:
        question_index += 1  # gå vidare

    return jsonify({"response": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
