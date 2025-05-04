def is_similar_to_definition(player_answer, correct_def):
    import ollama
    prompt = f"Is the following answer similar in meaning to this definition?\nDefinition: {correct_def}\nAnswer: {player_answer}\nRespond only with 'yes' or 'no'."
    response = ollama.chat(model='mistral', messages=[{"role": "user", "content": prompt}])
    return 'yes' in response['message']['content'].lower()

import os
import json
import random
import subprocess
import difflib
import speech_recognition as sr
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--voice', action='store_true', help='Enable voice input')
args = parser.parse_args()
voice_enabled = args.voice

WORDS_FILE = "words.json"
SCORES_FILE = "scores.json"

def load_words():
    with open(WORDS_FILE, "r") as f:
        return json.load(f)

def load_scores():
    if not os.path.exists(SCORES_FILE):
        return {}
    with open(SCORES_FILE, "r") as f:
        return json.load(f)

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f)

def ask_question(word, correct_def):
    print(f"\nDefine: {word.upper()}")
    if voice_enabled:
        print("\n🎤 Press Enter to type your answer, or just start speaking...")
        input("🎙️ Listening...")
        r = sr.Recognizer()
        with sr.Microphone() as mic:
            audio = r.listen(mic, phrase_time_limit=10)
        try:
            player_answer = r.recognize_google(audio).strip()
        except Exception:
            print("❌ Could not understand audio.")
            return 0
    else:
        print("\n📝 Type your answer:")
        player_answer = input("> ").strip()

    if player_answer.lower() == word.lower():
        print("❌ Try defining the word, not repeating it!")
        return 0

    if is_similar_to_definition(player_answer, correct_def):
        print(f"✅ +3 points  [{correct_def}]")
        return 3
    else:
        print("Incorrect. Choose the correct definition:")
        options = [correct_def]
        all_defs = [w["definition"] for w in words if w["definition"] != correct_def]
        options += random.sample(all_defs, k=3) if len(all_defs) >= 3 else all_defs
        random.shuffle(options)
        for i, opt in enumerate(options):
            print(f"{chr(65+i)}) {opt}")
        choice = input("Your choice (A/B/C/D): ").strip().upper()
        if choice in "ABCD"[:len(options)] and options[ord(choice)-65] == correct_def:
            print("✅ +1 point")
            return 1
        else:
            print(f"❌ The correct answer was: {correct_def}")
            return 0

def launch_bonus_game():
    print("You've reached 50 points! Choose a bonus game:")
    print("a) Bricks")
    print("b) Dino Run")
    print("c) Gorilla Defense")
    print("d) Skip for now")
    choice = input("> ").lower()
    if choice == "a":
        subprocess.run(["python3", "bricks.py"])
    elif choice == "b":
        subprocess.run(["python3", "dino_game.py"])
    elif choice == "c":
        subprocess.run(["python3", "gorilla_game.py"])
    else:
        print("Skipping bonus game.")

def game_loop(player_name):
    global words
    scores = load_scores()
    if player_name not in scores:
        scores[player_name] = 0

    while True:
        word_info = random.choice(words)
        points = ask_question(word_info["word"], word_info["definition"])
        scores[player_name] += points
        save_scores(scores)
        print(f"Total score: {scores[player_name]}")

        if scores[player_name] >= 50 and scores[player_name] % 20 < 5:
            launch_bonus_game()

if __name__ == "__main__":
    words = load_words()
    name = input("Enter your name, explorer: ").strip().lower()
    game_loop(name)
