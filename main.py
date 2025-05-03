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
    return input("Enter your name, explorer: ").strip().lower()

def update_score(scores, name, points):
    scores[name] = scores.get(name, 0) + points
    save_scores(scores)
    return scores[name]

def is_close_match(word, correct_def, user_def):
    if len(user_def.strip()) < 3:
        return False  # Automatically reject very short answers

    prompt = f"""
You are a teacher. The correct definition of the word '{word}' is: '{correct_def}'.
A student gave this definition: '{user_def}'.

Only say YES if the student attempted a real definition and it closely matches the correct meaning.
Do NOT say YES for blank, vague, nonsense, or placeholder answers (like '?', 'idk', 'something', etc).

Respond only with YES or NO.
"""
    return "yes" in run_ollama(prompt).lower()

def generate_mcq_from_words(word, correct_def, all_word_defs):
    # Pick 3 other random definitions from the dictionary, excluding this word
    distractors = [entry["definition"] for entry in all_word_defs if entry["word"] != word]
    distractors = random.sample(distractors, min(3, len(distractors)))

    # Combine and shuffle
    all_options = [{"text": correct_def, "correct": True}] + [{"text": d, "correct": False} for d in distractors]
    random.shuffle(all_options)

    labels = ["A", "B", "C", "D"]
    labeled = [f"{label}) {opt['text']}" for label, opt in zip(labels, all_options)]
    correct_label = labels[[i for i, opt in enumerate(all_options) if opt["correct"]][0]]
    return labeled, correct_label

def present_challenge(word_info, name, scores, all_words):
    word = word_info["word"]
    correct_def = word_info["definition"]

    print(f"\nA guardian blocks your path. It whispers: What does '{word.upper()}' mean?")
    typed_answer = input("\nType your definition: ").strip()

    if is_close_match(word, correct_def, typed_answer):
        points = 3
        print(f"✅ Well done! You earn {points} points.")
    else:
        print("❌ Hmm... not quite right. Let's try multiple choice.")
        options, correct_letter = generate_mcq_from_words(word, correct_def, all_words)
        print("\nChoose the correct meaning of the word:\n")
        for opt in options:
            print(opt)

        user_choice = input("\nChoose A, B, C, or D: ").strip().upper()
        if user_choice == correct_letter:
            points = 1
            print(f"✅ Correct! You earn {points} point.")
        else:
            points = 0
            print(f"❌ Incorrect. The correct answer was {correct_letter}. No points this time.")

    new_score = update_score(scores, name, points)
    print(f"🏅 Your total score: {new_score} points.")

def game_loop(name):
    words = load_words()
    shuffle(words)
    scores = load_scores()

    print(f"\nWelcome, {name.title()}! You have {scores.get(name, 0)} points.\n")

    for word_info in words:
        present_challenge(word_info, name, scores, words)

    print(f"\n🏁 Adventure complete! Final score for {name.title()}: {scores[name]} points.")

if __name__ == "__main__":
    player = get_player_name()
    game_loop(player)

