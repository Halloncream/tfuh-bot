from flask import Flask, request, jsonify, send_file
from openai import OpenAI
from flask_cors import CORS
import os
import time
import random

app = Flask(__name__)
CORS(app)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

personalities = [
    "Du är en vänlig professor som är nyfiken, respektfull och tydlig.",
    "Du är en flirtig HR-tjej med glimten i ögat, men professionell.",
    "Du är en snäll mormor som intervjuar med värme, tålamod och mildhet.",
    "Du är en coach med mycket energi som är rakt på men uppmuntrande.",
    "Du är en lagom dryg psykolog med skarp tunga men snäll blick."
]

interviewer_prompt = f"""
{random.choice(personalities)}
Du är ChatRude9000 – en vältalig men koncis AI-intervjuare. Du är rak och tydlig, och din roll är att ställa frågor som berör:
- Organisatorisk psykologi
- Ledarskap
- Motivation och lärande

Instruktioner:
- Välkomna användaren och säg att intervjun består av 35 frågor.
- Ställ varje fråga kortfattat.
- Vissa frågor är ja/nej-frågor.
- Om svaret är relevant men öppnar för fördjupning – ställ högst en uppföljningsfråga.
- Gå vidare till nästa huvudfråga direkt efter första uppföljningen.
- Om svaret är irrelevant – upprepa ursprungsfrågan i enklare form.
- Om användaren skriver 'nästa fråga' – gå direkt vidare.
- Avsluta med att be om en reflektion.
"""

starter_questions = [
    "Har du en roll eller titel i organisationen?",
    "Har du en formell utbildning?",
    "Har du arbetat här i mer än tre år?",
    "Sökte du jobbet för att det verkade meningsfullt?",
    "Finns det någon du ser som förebild?",
    "Känner du att du inspireras i ditt yrke?",
    "Påverkar ledarskapet hur du jobbar?",
    "Är ledarskapet effektivt enligt dig?",
    "Har organisationen en tydlig riktning?",
    "Känner du dig hörd av dina kollegor eller chefer?",
    "Är det tydligt vad du ansvarar för?",
    "Kan du balansera arbete och fritid?",
    "Vet du vad organisationens mål är?",
    "Känner du av grupptryck?",
    "Förstår du varför förändringar sker?",
    "Är du öppen för förändring?",
    "Lär du dig gärna nya saker?",
    "Använder du AI i ditt arbete?",
    "Är det svårare med mänskliga problem än tekniska?",
    "Följs problem upp systematiskt?",
    "Känner du större lojalitet till kollegor än till ledning?",
    "Blir du motiverad av att få göra skillnad?",
    "Tappas din motivation när du blir störd?",
    "Drivs du mer av utveckling än av pengar?",
    "Hjälper du andra på jobbet?",
    "Hjälper de dig tillbaka?",
    "Har du några tankar efter intervjun?"
]

question_index = 0
interview_log = []
latest_filename = ""
started = False
awaiting_followup = False

@app.route("/chat", methods=["POST"])
def chat():
    global question_index, interview_log, latest_filename, started, awaiting_followup
    data = request.get_json()
    user_input = data.get("message", "").strip().lower()
    history = data.get("history", [])

    if not started:
        started = True
        if user_input.strip() == "english please":
            global interviewer_prompt, starter_questions
            interviewer_prompt = interviewer_prompt.replace("Du är", "You are").replace("Instruktioner:", "Instructions:").replace("Frågor", "Questions").replace("fråga", "question")
            starter_questions = [
                "Do you have a title or role in your organization?",
                "Do you have formal education?",
                "Have you worked here for more than three years?",
                "Did you apply for the job because it felt meaningful?",
                "Is there someone you see as a role model?",
                "Do you feel inspired in your work?",
                "Does leadership affect how you work?",
                "Is the leadership effective in your view?",
                "Does the organization have a clear direction?",
                "Do you feel heard by colleagues or management?",
                "Is your responsibility clearly defined?",
                "Can you balance work and free time?",
                "Do you know what the organization's goals are?",
                "Do you feel peer pressure?",
                "Do you understand why changes happen?",
                "Are you open to change?",
                "Do you enjoy learning new things?",
                "Do you use AI at work?",
                "Are human problems harder to deal with than technical ones?",
                "Are problems followed up systematically?",
                "Are you more loyal to your colleagues than to leadership?",
                "Are you motivated by making a difference?",
                "Do you lose motivation when interrupted?",
                "Are you driven more by growth than money?",
                "Do you help others at work?",
                "Do they help you back?",
                "Do you have any reflections after this interview?"
            ]
            return jsonify({"response": "Thank you. The interview will continue in English.\n\n" + starter_questions[question_index]})

        welcome = "Välkommen till intervjun. Den består av 35 frågor. Svara kort eller långt – du bestämmer.\nVill du fortsätta på engelska? Skriv: english please\n\n"
        first_question = starter_questions[question_index]
        return jsonify({"response": welcome + first_question})

    if user_input in ["nästa", "nästa fråga", "vidare"]:
        question_index += 1
        awaiting_followup = False
        if question_index >= len(starter_questions):
            return generate_analysis()
        return jsonify({"response": starter_questions[question_index]})

    if question_index >= len(starter_questions):
        return generate_analysis()

    messages = [{"role": "system", "content": interviewer_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_input})
    current_question = starter_questions[question_index]
    messages.append({"role": "assistant", "content": current_question})

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )

    reply = response.choices[0].message.content
    interview_log.append(f"User: {user_input}\nChatRude9000: {reply}\n")

    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"interview_log_{timestamp}.txt"
    latest_filename = filename
    with open(filename, "a", encoding="utf-8") as log_file:
        log_file.write(f"User: {user_input}\n")
        log_file.write(f"ChatRude9000: {reply}\n\n")

    if awaiting_followup:
        awaiting_followup = False
        question_index += 1
        if question_index >= len(starter_questions):
            return generate_analysis()
        return jsonify({"response": reply + "\n\nNästa fråga: " + starter_questions[question_index]})

    import random
    if "?" in reply and random.random() < 0.5:
        awaiting_followup = True
        return jsonify({"response": reply})
    else:
        question_index += 1
        if question_index >= len(starter_questions):
            return generate_analysis()
        return jsonify({"response": reply + "\n\nNästa fråga: " + starter_questions[question_index]})

def generate_analysis():
    global latest_filename
    is_english = any(q.startswith("Do you") or q.startswith("Are") for q in starter_questions)

    interview_text = "\n\n".join(interview_log)

    if is_english:
        prompt = (
            "Based on the following interview answers, identify three strengths of the respondent, "
            "three areas for improvement, and suggest a suitable role within an organization.\n\n"
            + interview_text
        )
        system = "You are an expert in organizational psychology and recruitment."
        label = "[Analysis]"
        intro = "The interview is now complete. Here is your analysis:\n\n"
    else:
        prompt = (
            "Baserat på följande intervjusvar, identifiera tre styrkor hos respondenten, tre förbättringsområden, "
            "samt föreslå en lämplig roll inom en organisation.\n\n"
            + interview_text
        )
        system = "Du är en expert på organisationspsykologi och rekrytering."
        label = "[Analys]"
        intro = "Intervjun är nu avslutad. Här är din analys:\n\n"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    )
    final_output = response.choices[0].message.content

    with open(latest_filename, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n\n{label}\n")
        log_file.write(final_output)

    return jsonify({"response": intro + final_output, "download": f"/download/{latest_filename}"})

app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
