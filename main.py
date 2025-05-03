import json, subprocess
from pathlib import Path
from random import shuffle

WORDS_FILE = Path("words.json")
SCORES_FILE = Path("scores.json")

def run_ollama(prompt):
    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=prompt.encode(),
        capture_output=True
    )
    return result.stdout.decode().strip()

def load_words():
    with open(WORDS_FILE) as f:
        return json.load(f)

def load_scores():
    if SCORES_FILE.exists():
        with open(SCORES_FILE) as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def get_player_name():
    return input("Enter your name, explorer: ").strip().lower()

def update_score(scores, name, points):
    scores[name] = scores.get(name, 0) + points
    save_scores(scores)
    return scores[name]

def is_close_match(word, correct_def, user_def):
    prompt = f"""
You're a teacher. The correct definition of the word '{word}' is: '{correct_def}'.
A student gave this definition: '{user_def}'.
Is this close enough to count as correct for a 10-year-old learner? Answer only YES or NO.
"""
    return "yes" in run_ollama(prompt).lower()

def generate_mcq(word, correct_def):
    prompt = f"""
Create a multiple choice question to test the meaning of the word '{word}'.
Include four answer choices (A–D), one correct and three wrong, all plausible.
Label them clearly and mark the correct answer with '*' at the end of the correct line.
Example format:
A) correct answer *
B) wrong
C) wrong
D) wrong
Just give the options.
"""
    return run_ollama(prompt)

def present_challenge(word_info, name, scores):
    word = word_info["word"]
    correct_def = word_info["definition"]

    print(f"\nA guardian blocks your path. It whispers: What does '{word.upper()}' mean?")
    typed_answer = input("\nType your definition: ").strip()

    if is_close_match(word, correct_def, typed_answer):
        points = 3
        print(f"Correct! You earn {points} points.")
    else:
        print("Hmm... not quite right. Let's try multiple choice.")
        mcq = generate_mcq(word, correct_def)
        print("\n" + mcq)

        user_choice = input("\nChoose A, B, C, or D: ").strip().upper()
        correct_line = [line for line in mcq.splitlines() if line.strip().endswith("*")]
        if correct_line and user_choice in correct_line[0]:
            points = 1
            print(f"Correct! You earn {points} point.")
        else:
            points = 0
            print("Incorrect. No points this time.")

    new_score = update_score(scores, name, points)
    print(f"Your total score: {new_score} points.")

def game_loop(name):
    words = load_words()
    shuffle(words)
    scores = load_scores()

    print(f"\nWelcome, {name.title()}! You have {scores.get(name, 0)} points.\n")

    for word_info in words:
        present_challenge(word_info, name, scores)

    print(f"\nAdventure complete! Final score for {name.title()}: {scores[name]} points.")

if __name__ == "__main__":
    player = get_player_name()
    game_loop(player)

