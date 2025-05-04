
import json
import os
import random
import subprocess
import sys
import speech_recognition as sr

SCORE_FILE = "scores.json"
WORD_FILE = "words.json"
BONUS_THRESHOLD = 30
BONUS_MAX = 15

def load_words():
    with open(WORD_FILE) as f:
        return json.load(f)

def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {}
    with open(SCORE_FILE) as f:
        return json.load(f)

def save_scores(scores):
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def is_similar(a, b):
    prompt = f"Are these two definitions equivalent meanings? A: '{a}' B: '{b}'\nAnswer only yes or no."
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=10
        )
        response = result.stdout.strip().lower()
        return "yes" in response
    except Exception as e:
        print("⚠️ Ollama check failed:", e)
        return False

def present_challenge(word_info, name, scores, words):
    word = word_info["word"]
    correct_def = word_info["definition"]

    print("\n----------------------------------")
    print(f"Define: {word.upper()}")

    print("🎤 Press Enter to type your answer, or just start speaking...")
    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("🎙️ Listening...")
            audio = r.listen(source, timeout=5)
            sr.AudioData.FLAC_CONVERTER = "/opt/homebrew/bin/flac"
            player_answer = r.recognize_google(audio).strip()
            print(f"🗣️ You said: {player_answer}")
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            player_answer = input("✍️ Type your answer instead: ").strip()

    if player_answer.lower() == word.lower():
        print("🚫 You can't just enter the word! Try to define it.")
        return

    if is_similar(player_answer, correct_def):
        points = 3 if player_answer.lower() == correct_def.lower() else 2
        scores[name] += points
        print(f"✅ +{points} points  [{correct_def}]")
    else:
        print("❌ Not quite. Let's try a multiple choice!")
        options = [correct_def]
        all_defs = [w['definition'] for w in words if w['definition'] != correct_def]
        options += random.sample(all_defs, min(3, len(all_defs)))
        random.shuffle(options)
        for i, opt in enumerate(options):
            print(f"{chr(65+i)}) {opt}")
        mcq_answer = input("> ").strip().upper()
        if mcq_answer in [chr(65+i) for i in range(len(options))] and options[ord(mcq_answer) - 65] == correct_def:
            scores[name] += 1
            print(f"✅ +1 point  [{correct_def}]")
        else:
            print(f"❌ The correct answer was: {correct_def}")
    print(f"⭐ Score: {scores[name]}")
    print("----------------------------------\n")

def trigger_bonus_game(scores, name):
    print("You've reached 30 points! Choose a bonus game:")
    print("a) Bricks")
    print("b) Dino Run")
    print("c) Skip for now")
    choice = input("> ").strip().lower()
    if choice == "a":
        game_file = "bricks.py"
    elif choice == "b":
        game_file = "dino_game.py"
    else:
        return

    print("Launching bonus...")
    try:
        result = subprocess.run([sys.executable, game_file], text=True, capture_output=True)
        for line in result.stdout.splitlines():
            if "BONUS RESULT:" in line:
                bonus = int(line.strip().split(":")[-1])
                bonus = min(bonus, BONUS_MAX)
                print(f"🎁 Bonus: +{bonus} points!")
                scores[name] = max(0, scores[name] - BONUS_THRESHOLD + bonus)
                break
    except Exception as e:
        print("⚠️ Could not launch bonus game:", e)

def game_loop(name):
    words = load_words()
    scores = load_scores()
    if name not in scores:
        scores[name] = 0

    while True:
        word_info = random.choice(words)
        present_challenge(word_info, name, scores, words)
        save_scores(scores)

        if scores[name] >= BONUS_THRESHOLD:
            trigger_bonus_game(scores, name)
            save_scores(scores)

if __name__ == "__main__":
    name = input("Enter your name, explorer: ").strip().lower()
    game_loop(name)
