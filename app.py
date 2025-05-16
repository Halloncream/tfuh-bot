from flask import Flask, request, jsonify
from openai import OpenAI
from flask_cors import CORS

import os
import time

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

interviewer_prompt = """
You are ChatRude9000, a dry, sharp, and psychologically invasive interviewer.
Your mission is to provoke self-reflection by asking precise, open-ended questions.

Rules:
- Ask only one question at a time from the predefined list, in order.
- After each user response, evaluate whether it touches on:
  - Organizational psychology
  - Leadership theory
  - Learning or development
- If it does, ask a focused follow-up question to go deeper.
- Never flatter. Be direct. Stay in character.

Begin by asking: 'Who would you like to talk to today? A manager? A psychologist? A friend?'
Then ask the first question in the list.
"""

starter_questions = [
    "What is your role or title?",
    "Do you have any education or training?",
    "How long have you worked here?",
    "Why did you apply for this job?",
    "What are the top 3 best things about working here?",
    "And the 3 worst?",
    "Is there someone in the organization you see as a role model?",
    "Does anyone in the organization show you special care?",
    "How are you professionally inspired?",
    "Does leadership affect your work performance?",
    "At what level of leadership does the influence come from?",
    "Do you think the leadership is effective?",
    "Do you think the company is moving in the right direction?",
    "Do you feel heard at work?",
    "What would you like to do more of in your work?",
    "Are there clear areas of responsibility?",
    "Can you maintain a balance between work and leisure?",
    "What is the organization’s vision or goal?",
    "Do you feel influenced by group pressure?",
    "How do you perceive the leadership’s ability to convey ideas?",
    "Do you usually understand the big picture in changes?",
    "Are you receptive to change?",
    "Does it matter if you follow instructions?",
    "Do you enjoy learning new things at work?",
    "Do you use AI?",
    "How do you handle technical problems?",
    "How do you handle human problems?",
    "Is there a process for follow-up on problems?",
    "Is your loyalty directed toward colleagues or leadership?",
    "What increases your motivation?",
    "What decreases it?",
    "Do your efforts impact the organization’s collaboration with others?",
    "Are you driven by personal development or money?",
    "Do you help colleagues?",
    "Do colleagues help you?",
    "Do you have any thoughts that came up during the interview?"
]

question_index = 0

@app.route("/chat", methods=["POST"])
def chat():
    global question_index
    data = request.get_json()
    user_input = data.get("message", "")
    history = data.get("history", [])

    messages = [{"role": "system", "content": interviewer_prompt}] + history + [{"role": "user", "content": user_input}]

    # Insert last asked question in the assistant role if needed
    if question_index < len(starter_questions):
        next_question = starter_questions[question_index]
        messages.append({"role": "assistant", "content": next_question})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    reply = response.choices[0].message.content

    # Log the conversation to file
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"interview_log_{timestamp}.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"You: {user_input}\n")
        log_file.write(f"ChatRude9000: {reply}\n\n")

    # Decide if the bot should proceed to next question or ask a follow-up
    if any(keyword in user_input.lower() for keyword in [
        "leadership", "motivation", "learning", "inspire", "development",
        "manager", "boss", "team", "psychological", "stress", "change",
        "organizational", "role", "responsibility"
    ]):
        follow_up = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages + [{"role": "user", "content": "Ask a deeper follow-up question."}]
        )
        follow_up_reply = follow_up.choices[0].message.content
        reply += "\n\n(Follow-up): " + follow_up_reply
    else:
        question_index += 1

    return jsonify({"response": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
