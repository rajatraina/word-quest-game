import json, subprocess, random
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
    try:
        if SCORES_FILE.exists():
            with open(SCORES_FILE) as f:
                return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ scores.json is empty or corrupted. Resetting...")
    return {}

def save_scores(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=2)

def get_player_name():
    return input("Explorer name: ").strip().lower()

def update_score(scores, name, points):
    scores[name] = scores.get(name, 0) + points
    save_scores(scores)
    return scores[name]

def is_close_match(word, correct_def, user_def):
    if len(user_def.strip()) < 3:
        return False
    prompt = f"""
You are a teacher. The correct definition of the word '{word}' is: '{correct_def}'.
A student gave this definition: '{user_def}'.

Only say YES if the student attempted a real definition and it closely matches the correct meaning.
Do NOT say YES for blank, vague, nonsense, or placeholder answers (like '?', 'idk', 'something', etc).

Respond only with YES or NO.
"""
    return "yes" in run_ollama(prompt).lower()

def generate_mcq_from_words(word, correct_def, all_word_defs):
    distractors = [entry["definition"] for entry in all_word_defs if entry["word"] != word]
    distractors = random.sample(distractors, min(3, len(distractors)))
    all_options = [{"text": correct_def, "correct": True}] + [{"text": d, "correct": False} for d in distractors]
    random.shuffle(all_options)
    labels = ["A", "B", "C", "D"]
    labeled = [f"{label}) {opt['text']}" for label, opt in zip(labels, all_options)]
    correct_label = labels[[i for i, opt in enumerate(all_options) if opt["correct"]][0]]
    return labeled, correct_label

def present_challenge(word_info, name, scores, all_words):
    word = word_info["word"]
    correct_def = word_info["definition"]

    print(f"\n{word.upper()}")
    typed_answer = input("> ").strip()

    if is_close_match(word, correct_def, typed_answer):
        points = 3
        print(f"✅ +{points} points  [{correct_def}]")
    else:
        print("❌ Let's try multiple choice.")
        options, correct_letter = generate_mcq_from_words(word, correct_def, all_words)
        for opt in options:
            print(opt)
        user_choice = input("> ").strip().upper()
        if user_choice == correct_letter:
            points = 1
            print(f"✅ +{points} point")
        else:
            points = 0
            print(f"❌ Correct answer: {correct_letter}")

    new_score = update_score(scores, name, points)
    print(f"🏅 Total: {new_score} points")

    if new_score >= 30:
        trigger_bricks_bonus(scores, name)

def trigger_bricks_bonus(scores, name):
    choice = input("You reached 30 points! Play Brick Bonus? (y/n): ").strip().lower()
    if choice == "y":
        print("Launching bonus...")
        result = subprocess.run(["python3", "bricks.py"], capture_output=True, text=True)
        lines = result.stdout.splitlines()
        for line in lines:
            if "BONUS RESULT" in line:
                try:
                    bonus = int(line.split(":")[1].strip())
                    print(f"+{bonus} bonus points")
                    update_score(scores, name, bonus)
                except:
                    pass
        scores[name] -= 30
        save_scores(scores)

def game_loop(name):
    words = load_words()
    shuffle(words)
    scores = load_scores()
    print(f"Welcome, {name.title()}! Total: {scores.get(name, 0)}\n")
    for word_info in words:
        present_challenge(word_info, name, scores, words)
    print(f"\nFinal score: {scores[name]}")

if __name__ == "__main__":
    player = get_player_name()
    game_loop(player)

