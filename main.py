word_scores = {}

def is_similar_to_definition(player_answer, correct_def):
    import ollama
    from ollama._types import ResponseError
    
    # Try to use Ollama to check similarity
    model_to_use = None
    
    try:
        # First, try to list available models to find the best one
        try:
            models_response = ollama.list()
            # The response has a 'models' attribute with Model objects
            available_models = [m.model for m in models_response.models] if hasattr(models_response, 'models') else []
            
            if available_models:
                # Try common model names in order of preference
                # Note: model names may include tags like "mistral:7b-instruct"
                model_names = ['mistral', 'llama2', 'llama3', 'phi', 'gemma']
                found_model = None
                
                for model_name in model_names:
                    for available in available_models:
                        # Check if model name (with or without tag) matches
                        if model_name in available.lower():
                            found_model = available
                            break
                    if found_model:
                        break
                
                # If no preferred model found, use the first available
                if found_model:
                    model_to_use = found_model
                else:
                    model_to_use = available_models[0]
            else:
                print("⚠️  No Ollama models found. Install one with: ollama pull mistral")
                return False
        except Exception as e:
            print(f"⚠️  Could not list Ollama models: {e}")
            return False
        
        # Use the found model
        prompt = f"Is the following answer similar in meaning to this definition?\nDefinition: {correct_def}\nAnswer: {player_answer}\nRespond only with 'yes' or 'no'."
        response = ollama.chat(model=model_to_use, messages=[{"role": "user", "content": prompt}])
        return 'yes' in response['message']['content'].lower()
    
    except ResponseError as e:
        if 'not found' in str(e).lower() or '404' in str(e):
            print(f"⚠️  Model '{model_to_use}' not found. Install it with: ollama pull mistral")
        return False
    except Exception:
        # Silently fail - will fall back to multiple choice
        return False

import os
import json
import random
import subprocess
import difflib
import speech_recognition as sr
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--voice', action='store_true', help='Enable voice input')
parser.add_argument('--games', action='store_true', help='Enable bonus games at milestone scores')
args = parser.parse_args()
voice_enabled = args.voice
games_enabled = args.games

WORDS_FILE = "words.json"
SCORES_FILE = "scores.json"

def load_words():
    with open(WORDS_FILE, "r") as f:
        return json.load(f)

def load_scores():
    global word_scores
    if not os.path.exists(SCORES_FILE):
        return {}
    with open(SCORES_FILE, "r") as f:
        data = json.load(f)
        word_scores = data.get('word_scores', {})
        return data

def save_scores(scores):
    global word_scores
    with open(SCORES_FILE, "w") as f:
        json.dump({**scores, 'word_scores': word_scores}, f)

def ask_question(word, correct_def):
    global word_scores
    user_scores = word_scores.setdefault(player_name, {})

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

    if len(player_answer.lower()) > 2 and (player_answer.lower() == correct_def.lower() or is_similar_to_definition(player_answer, correct_def)):
        print(f"✅ +3 points  [{correct_def}]")
        user_scores[word] = user_scores.get(word, 0) + 3
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
        if len(choice)>0 and choice in "ABCD"[:len(options)] and options[ord(choice)-65] == correct_def:
            print("✅ +1 point")
            user_scores[word] = user_scores.get(word, 0) + 1
            return 1
        else:
            print(f"❌ The correct answer was: {correct_def}")
            user_scores[word] = user_scores.get(word, 0)
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
        return 35
    elif choice == "b":
        subprocess.run(["python3", "dino_game.py"])
        return 35
    elif choice == "c":
        subprocess.run(["python3", "gorilla_game.py"])
        return 35
    else:
        print("Skipping bonus game.")
        return 0

def game_loop(player_name):
    global words
    scores = load_scores()
    if player_name not in scores:
        scores[player_name] = 0
    user_word_scores = word_scores.get(player_name, {})
    
    while True:
        sorted_words = sorted(words, key=lambda w: user_word_scores.get(w['word'], -float('inf')))
        word_info = random.choice(sorted_words[:10])
        points = ask_question(word_info["word"], word_info["definition"])
        scores[player_name] += points
        save_scores(scores)
        print(f"Total score: {scores[player_name]}")

        if games_enabled and scores[player_name] >= 50 and scores[player_name] % 20 < 5:
            cost = launch_bonus_game()
            scores[player_name] -= cost

if __name__ == "__main__":
    words = load_words()
    player_name = input("Enter your name, explorer: ").strip().lower()
    game_loop(player_name)
