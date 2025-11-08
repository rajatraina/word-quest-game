word_scores = {}
math_scores = {}

import os
import json
import random
import subprocess
import argparse
import threading
from math import gcd
from flask import Flask, render_template, jsonify, request

# Game configuration
WORDS_FILE = "words.json"
SCORES_FILE = "scores.json"

# Name to grade mapping for math questions
NAME_TO_GRADE = {
    'mira': 3,
    'raya': 6,
    'vik': 6,
    'rajat': 12,
    'penka': 12
}

# Core game logic functions (no I/O)
def get_ollama_model():
    """Get the best available Ollama model. Returns model name or None."""
    import ollama
    from ollama._types import ResponseError
    
    try:
        models_response = ollama.list()
        available_models = [m.model for m in models_response.models] if hasattr(models_response, 'models') else []
        
        if available_models:
            model_names = ['mistral', 'llama2', 'llama3', 'phi', 'gemma']
            found_model = None
            
            for model_name in model_names:
                for available in available_models:
                    if model_name in available.lower():
                        found_model = available
                        break
                if found_model:
                    break
            
            if found_model:
                return found_model
            else:
                return available_models[0]
    except Exception:
        return None
    
    return None

def is_similar_to_definition(player_answer, correct_def):
    import ollama
    from ollama._types import ResponseError
    
    model_to_use = get_ollama_model()
    if not model_to_use:
        return False
    
    try:
        prompt = f"Is the following answer similar in meaning to this definition?\nDefinition: {correct_def}\nAnswer: {player_answer}\nRespond only with 'yes' or 'no'."
        response = ollama.chat(model=model_to_use, messages=[{"role": "user", "content": prompt}])
        return 'yes' in response['message']['content'].lower()
    
    except ResponseError:
        return False
    except Exception:
        return False

def warmup_ollama():
    """Warm up the Ollama model with a simple request to reduce first-request latency."""
    def _warmup():
        import ollama
        from ollama._types import ResponseError
        
        try:
            model_to_use = get_ollama_model()
            if model_to_use:
                # Make a simple warmup request
                ollama.chat(model=model_to_use, messages=[{"role": "user", "content": "Say 'yes'"}])
        except Exception:
            # Silently fail - warmup is optional
            pass
    
    # Run warmup in background thread to not block
    thread = threading.Thread(target=_warmup, daemon=True)
    thread.start()

def load_words():
    with open(WORDS_FILE, "r") as f:
        return json.load(f)

def load_scores():
    global word_scores, math_scores
    if not os.path.exists(SCORES_FILE):
        return {}
    with open(SCORES_FILE, "r") as f:
        data = json.load(f)
        word_scores = data.get('word_scores', {})
        math_scores = data.get('math_scores', {})
        return data

def save_scores(scores):
    global word_scores, math_scores
    with open(SCORES_FILE, "w") as f:
        json.dump({**scores, 'word_scores': word_scores, 'math_scores': math_scores}, f)
        f.write('\n')

def check_answer(player_name, word, player_answer, correct_def, words):
    """Check if answer is correct. Returns (is_correct, points, message, show_mc, mc_options, correct_index)"""
    global word_scores
    
    if player_answer.lower() == word.lower():
        return (False, 0, "❌ Try defining the word, not repeating it!", False, None, None)
    
    # Load scores first to get current state
    scores = load_scores()
    user_scores = word_scores.setdefault(player_name, {})
    
    # Check if answer matches definition
    if len(player_answer.lower()) > 2 and (player_answer.lower() == correct_def.lower() or is_similar_to_definition(player_answer, correct_def)):
        user_scores[word] = user_scores.get(word, 0) + 3
        scores[player_name] = scores.get(player_name, 0) + 3
        save_scores(scores)
        return (True, 3, f"✅ +3 points  [{correct_def}]", False, None, None)
    
    # Generate multiple choice options
    options = [correct_def]
    all_defs = [w["definition"] for w in words if w["definition"] != correct_def]
    options += random.sample(all_defs, k=min(3, len(all_defs)))
    random.shuffle(options)
    correct_index = options.index(correct_def)
    
    return (False, 0, "Incorrect. Choose the correct definition:", True, options, correct_index)

def check_mc_answer(player_name, word, selected_index, correct_index, correct_def):
    """Check multiple choice answer. Returns (is_correct, points, message)"""
    global word_scores
    
    # Load scores first to get current state
    scores = load_scores()
    user_scores = word_scores.setdefault(player_name, {})
    
    if selected_index == correct_index:
        user_scores[word] = user_scores.get(word, 0) + 1
        scores[player_name] = scores.get(player_name, 0) + 1
        save_scores(scores)
        return (True, 1, "✅ +1 point")
    else:
        user_scores[word] = user_scores.get(word, 0)
        save_scores(scores)
        return (False, 0, f"❌ The correct answer was: {correct_def}")

def get_next_word(player_name, words):
    """Get the next word to quiz. Returns word_info dict."""
    global word_scores
    user_word_scores = word_scores.get(player_name, {})
    
    sorted_words = sorted(words, key=lambda w: user_word_scores.get(w['word'], -float('inf')))
    weakest_words = sorted_words[:10]
    random.shuffle(weakest_words)
    return weakest_words[0]

def get_player_score(player_name, game_type='words'):
    """Get player's current score for the given game type."""
    scores = load_scores()
    if game_type == 'math':
        # Math scores are stored separately in math_scores dict
        return math_scores.get(player_name, 0)
    # Word scores are stored in the main scores dict
    return scores.get(player_name, 0)

# Math question generation functions
def get_grade_for_name(name):
    """Get grade level for a given name."""
    return NAME_TO_GRADE.get(name.lower(), 5)  # Default to grade 5

def normalize_value(value_str):
    """
    Convert a value string (integer or fraction) to a normalized tuple for comparison.
    Returns (numerator, denominator) tuple where the fraction is in simplest form.
    For integers, returns (value, 1).
    """
    if isinstance(value_str, (int, float)):
        value_str = str(int(value_str))
    
    if '/' in value_str:
        try:
            num_str, den_str = value_str.split('/')
            num = int(num_str)
            den = int(den_str)
            if den == 0:
                return (num, den)  # Invalid, but return as-is
            # Simplify the fraction
            g = gcd(abs(num), abs(den))
            num = num // g
            den = den // g
            # Normalize sign (keep sign in numerator)
            if den < 0:
                num = -num
                den = -den
            return (num, den)
        except (ValueError, ZeroDivisionError):
            return value_str  # Return as-is if can't parse
    else:
        try:
            num = int(value_str)
            return (num, 1)
        except ValueError:
            return value_str  # Return as-is if can't parse

def generate_math_question(grade):
    """Generate a math question appropriate for the given grade level. Returns (question, correct_answer, options)."""
    max_attempts = 50  # Prevent infinite loops
    
    if grade <= 2:
        # Grade 2: Simple addition/subtraction within 20
        a = random.randint(1, 10)
        b = random.randint(1, 10)
        op = random.choice(['+', '-'])
        if op == '+':
            correct = a + b
            question = f"{a} + {b} = ?"
        else:
            # Ensure non-negative result
            if a < b:
                a, b = b, a
            correct = a - b
            question = f"{a} - {b} = ?"
        
        # Generate wrong answers, ensuring uniqueness
        wrong1 = correct + random.randint(1, 5)
        wrong2 = correct - random.randint(1, 5) if correct > 1 else correct + random.randint(6, 10)
        wrong3 = correct + random.randint(-3, 3)
        attempts = 0
        while (wrong3 == correct or wrong3 == wrong1 or wrong3 == wrong2 or wrong3 < 0) and attempts < max_attempts:
            wrong3 = correct + random.randint(-3, 3)
            attempts += 1
        
        # Ensure wrong1 and wrong2 are different
        attempts = 0
        while wrong1 == wrong2 and attempts < max_attempts:
            wrong2 = correct - random.randint(1, 5) if correct > 1 else correct + random.randint(6, 10)
            attempts += 1
        
    elif grade <= 5:
        # Grade 5: Addition/subtraction with larger numbers, simple multiplication
        op = random.choice(['+', '-', '*'])
        if op == '+':
            a = random.randint(10, 100)
            b = random.randint(10, 100)
            correct = a + b
            question = f"{a} + {b} = ?"
        elif op == '-':
            a = random.randint(50, 200)
            b = random.randint(10, a)
            correct = a - b
            question = f"{a} - {b} = ?"
        else:  # multiplication
            a = random.randint(2, 12)
            b = random.randint(2, 12)
            correct = a * b
            question = f"{a} × {b} = ?"
        
        # Generate wrong answers, ensuring uniqueness
        wrong1 = correct + random.randint(5, 15)
        wrong2 = correct - random.randint(5, 15) if correct > 10 else correct + random.randint(16, 25)
        wrong3 = correct + random.randint(-10, 10)
        attempts = 0
        while (wrong3 == correct or wrong3 == wrong1 or wrong3 == wrong2 or wrong3 < 0) and attempts < max_attempts:
            wrong3 = correct + random.randint(-10, 10)
            attempts += 1
        
        # Ensure wrong1 and wrong2 are different
        attempts = 0
        while wrong1 == wrong2 and attempts < max_attempts:
            wrong2 = correct - random.randint(5, 15) if correct > 10 else correct + random.randint(16, 25)
            attempts += 1
    
    else:  # Grade 12
        # Grade 12: Algebra, fractions, more complex operations
        question_type = random.choice(['algebra', 'fraction', 'exponent', 'sqrt'])
        
        if question_type == 'algebra':
            # Simple linear equation: ax + b = c, solve for x
            x_val = random.randint(1, 10)
            a = random.randint(2, 5)
            b = random.randint(1, 10)
            c = a * x_val + b
            correct = x_val
            question = f"If {a}x + {b} = {c}, what is x?"
            wrong1 = x_val + random.randint(1, 3)
            wrong2 = x_val - random.randint(1, 3) if x_val > 2 else x_val + random.randint(4, 6)
            wrong3 = (c - b) // a + random.randint(-2, 2)
            attempts = 0
            while (wrong3 == correct or wrong3 == wrong1 or wrong3 == wrong2 or wrong3 <= 0) and attempts < max_attempts:
                wrong3 = (c - b) // a + random.randint(-2, 2)
                attempts += 1
            
            # Ensure wrong1 and wrong2 are different
            attempts = 0
            while wrong1 == wrong2 and attempts < max_attempts:
                wrong2 = x_val - random.randint(1, 3) if x_val > 2 else x_val + random.randint(4, 6)
                attempts += 1
        
        elif question_type == 'fraction':
            # Simple fraction addition/subtraction
            num1 = random.randint(1, 5)
            den1 = random.randint(2, 6)
            num2 = random.randint(1, 5)
            den2 = random.randint(2, 6)
            # For simplicity, use common denominator
            common_den = den1 * den2
            sum_num = num1 * den2 + num2 * den1
            # Simplify (basic)
            g = gcd(sum_num, common_den)
            correct_num = sum_num // g
            correct_den = common_den // g
            correct = f"{correct_num}/{correct_den}"
            question = f"{num1}/{den1} + {num2}/{den2} = ?"
            
            # Generate wrong answers as fractions, ensuring they're numerically different
            wrong_answers = []
            seen_values = {normalize_value(correct)}  # Track normalized values, not strings
            
            attempts = 0
            while len(wrong_answers) < 3 and attempts < max_attempts:
                # Generate candidate wrong answers
                candidates = [
                    f"{sum_num + random.randint(1, 3)}/{common_den}",  # Modified numerator
                    f"{sum_num}/{common_den + random.randint(1, 3)}",  # Modified denominator
                    f"{num1 + num2}/{den1 + den2}",  # Incorrect addition
                    f"{random.randint(1, 20)}/{random.randint(2, 20)}"  # Random fraction
                ]
                
                for candidate in candidates:
                    normalized = normalize_value(candidate)
                    if normalized not in seen_values:
                        wrong_answers.append(candidate)
                        seen_values.add(normalized)
                        if len(wrong_answers) == 3:
                            break
                
                # If still need more, generate random fractions
                if len(wrong_answers) < 3:
                    new_wrong = f"{random.randint(1, 30)}/{random.randint(2, 30)}"
                    normalized = normalize_value(new_wrong)
                    if normalized not in seen_values:
                        wrong_answers.append(new_wrong)
                        seen_values.add(normalized)
                
                attempts += 1
            
            # Ensure we have 3 wrong answers
            while len(wrong_answers) < 3:
                new_wrong = f"{random.randint(1, 30)}/{random.randint(2, 30)}"
                normalized = normalize_value(new_wrong)
                if normalized not in seen_values:
                    wrong_answers.append(new_wrong)
                    seen_values.add(normalized)
            
            wrong1, wrong2, wrong3 = wrong_answers[0], wrong_answers[1], wrong_answers[2]
        
        elif question_type == 'exponent':
            base = random.randint(2, 5)
            exp = random.randint(2, 4)
            correct = base ** exp
            question = f"{base}²" if exp == 2 else f"{base}³" if exp == 3 else f"{base}^{exp}"
            wrong1 = base * exp
            wrong2 = base + exp
            wrong3 = (base + 1) ** exp
            
            # Ensure uniqueness
            attempts = 0
            while (wrong1 == correct or wrong2 == correct or wrong3 == correct or
                   wrong1 == wrong2 or wrong1 == wrong3 or wrong2 == wrong3) and attempts < max_attempts:
                wrong1 = base * exp + random.randint(-2, 2)
                wrong2 = base + exp + random.randint(-2, 2)
                wrong3 = (base + random.randint(-1, 2)) ** exp
                attempts += 1
        
        else:  # sqrt
            num = random.choice([4, 9, 16, 25, 36, 49, 64, 81, 100])
            correct = int(num ** 0.5)
            question = f"√{num} = ?"
            wrong1 = correct + 1
            wrong2 = correct - 1 if correct > 1 else correct + 2
            wrong3 = correct + 2
            
            # Ensure uniqueness
            attempts = 0
            while (wrong1 == wrong2 or wrong1 == wrong3 or wrong2 == wrong3) and attempts < max_attempts:
                wrong2 = correct - 1 if correct > 1 else correct + 2
                wrong3 = correct + random.randint(2, 3)
                attempts += 1
    
    # Create options list and ensure all are numerically unique
    options = [str(correct), str(wrong1), str(wrong2), str(wrong3)]
    
    # Final check: ensure all options are numerically unique (not just string unique)
    seen_normalized = set()
    unique_options = []
    
    for opt in options:
        normalized = normalize_value(opt)
        if normalized not in seen_normalized:
            unique_options.append(opt)
            seen_normalized.add(normalized)
    
    # If we have duplicates by value, regenerate wrong answers
    if len(unique_options) < 4:
        attempts = 0
        seen_normalized = {normalize_value(str(correct))}  # Start with correct answer
        unique_options = [str(correct)]
        
        is_fraction = isinstance(correct, str) and '/' in str(correct)
        
        while len(unique_options) < 4 and attempts < max_attempts * 2:  # More attempts for final check
            if is_fraction:  # Fraction case
                # For fractions, generate new wrong answers that are numerically different
                candidate = f"{random.randint(1, 30)}/{random.randint(2, 30)}"
                normalized = normalize_value(candidate)
                if normalized not in seen_normalized:
                    unique_options.append(candidate)
                    seen_normalized.add(normalized)
            else:  # Integer case
                if grade <= 2:
                    candidate = int(correct) + random.randint(-10, 10)
                elif grade <= 5:
                    candidate = int(correct) + random.randint(-20, 20)
                else:
                    candidate = int(correct) + random.randint(-10, 10)
                if candidate > 0:
                    normalized = normalize_value(str(candidate))
                    if normalized not in seen_normalized:
                        unique_options.append(str(candidate))
                        seen_normalized.add(normalized)
            attempts += 1
        
        # Ensure we have at least 4 options (use original if needed, but prefer unique)
        if len(unique_options) >= 2:
            options = unique_options
        # If we still don't have 4, we'll use what we have (shouldn't happen often)
    
    random.shuffle(options)
    correct_index = options.index(str(correct))
    
    return {
        'question': question,
        'correct_answer': str(correct),
        'options': options,
        'correct_index': correct_index
    }

def get_next_math_question(player_name):
    """Get the next math question for a player based on their grade."""
    grade = get_grade_for_name(player_name)
    return generate_math_question(grade)

def check_math_answer(player_name, selected_index, correct_index, correct_answer):
    """Check math multiple choice answer. Returns (is_correct, points, message)"""
    global math_scores
    
    scores = load_scores()
    
    if selected_index == correct_index:
        # Update math score separately (just one total score per player)
        math_scores[player_name] = math_scores.get(player_name, 0) + 3
        save_scores(scores)
        return (True, 3, "✅ +3 points")
    else:
        # Ensure math_scores entry exists even for incorrect answers
        if player_name not in math_scores:
            math_scores[player_name] = 0
        save_scores(scores)
        return (False, 0, f"❌ The correct answer was: {correct_answer}")

# CLI interface functions
def ask_question_cli(word, correct_def, words, player_name, voice_enabled=False):
    """CLI version of ask_question. Returns points earned."""
    import speech_recognition as sr
    
    print(f"\nDefine: {word.upper()}")
    
    if voice_enabled:
        try:
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
        except AttributeError as e:
            if "PyAudio" in str(e) or "pyaudio" in str(e).lower():
                print("⚠️  PyAudio not installed. Voice input unavailable.")
                print("   Install with: brew install portaudio && pip3 install pyaudio")
                print("   Falling back to text input...\n")
                print("\n📝 Type your answer:")
                player_answer = input("> ").strip()
            else:
                raise
        except Exception as e:
            print(f"⚠️  Voice input error: {e}")
            print("   Falling back to text input...\n")
            print("\n📝 Type your answer:")
            player_answer = input("> ").strip()
    else:
        print("\n📝 Type your answer:")
        player_answer = input("> ").strip()
    
    is_correct, points, message, show_mc, mc_options, correct_index = check_answer(
        player_name, word, player_answer, correct_def, words
    )
    
    if is_correct:
        print(message)
        return points
    elif show_mc:
        print(message)
        for i, opt in enumerate(mc_options):
            print(f"{chr(65+i)}) {opt}")
        choice = input("Your choice (A/B/C/D): ").strip().upper()
        if len(choice) > 0 and choice in "ABCD"[:len(mc_options)]:
            selected_index = ord(choice) - 65
            is_correct, points, message = check_mc_answer(
                player_name, word, selected_index, correct_index, correct_def
            )
            print(message)
            return points
        else:
            print(f"❌ The correct answer was: \033[4m{correct_def}\033[0m")
            return 0
    else:
        print(message)
        return 0

def launch_bonus_game_cli():
    """CLI version of bonus game selection."""
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

def game_loop_cli(player_name, words, games_enabled=False, voice_enabled=False):
    """CLI game loop."""
    scores = load_scores()
    if player_name not in scores:
        scores[player_name] = 0
    
    while True:
        word_info = get_next_word(player_name, words)
        points = ask_question_cli(word_info["word"], word_info["definition"], words, player_name, voice_enabled)
        scores[player_name] += points
        save_scores(scores)
        print(f"Total score: {scores[player_name]}")
        
        if games_enabled and scores[player_name] >= 50 and scores[player_name] % 20 < 5:
            cost = launch_bonus_game_cli()
            scores[player_name] -= cost

# Flask web interface
app = Flask(__name__)
words = load_words()

@app.route('/')
def index():
    return render_template('word_quest.html')

@app.route('/api/start', methods=['POST'])
def start_game():
    data = request.json
    player_name = data.get('name', '').strip().lower()
    game_type = data.get('game_type', 'words').strip().lower()
    
    if not player_name:
        return jsonify({'error': 'Name required'}), 400
    
    if game_type not in ['words', 'math']:
        return jsonify({'error': 'Invalid game type. Must be "words" or "math"'}), 400
    
    scores = load_scores()
    
    # Initialize scores based on game type
    if game_type == 'math':
        if player_name not in math_scores:
            math_scores[player_name] = 0
        current_score = math_scores[player_name]
    else:
        if player_name not in scores:
            scores[player_name] = 0
        current_score = scores[player_name]
    
    save_scores(scores)
    
    # Warm up Ollama model in background to reduce first-request latency (only for words)
    if game_type == 'words':
        warmup_ollama()
    
    return jsonify({
        'status': 'started',
        'score': current_score,
        'game_type': game_type
    })

@app.route('/api/question', methods=['GET'])
def get_question():
    player_name = request.args.get('player', '').strip().lower()
    game_type = request.args.get('game_type', 'words').strip().lower()
    
    if not player_name:
        return jsonify({'error': 'Player name required'}), 400
    
    if game_type == 'math':
        math_question = get_next_math_question(player_name)
        return jsonify({
            'question': math_question['question'],
            'options': math_question['options'],
            'correct_index': math_question['correct_index'],
            'correct_answer': math_question['correct_answer'],
            'score': get_player_score(player_name, 'math'),
            'game_type': 'math'
        })
    else:
        word_info = get_next_word(player_name, words)
        return jsonify({
            'word': word_info['word'],
            'definition': word_info['definition'],
            'score': get_player_score(player_name, 'words'),
            'game_type': 'words'
        })

@app.route('/api/answer', methods=['POST'])
def check_answer_api():
    data = request.json
    player_name = data.get('player', '').strip().lower()
    word = data.get('word')
    answer = data.get('answer', '').strip()
    correct_def = data.get('definition')
    
    if not player_name or not word or not answer or not correct_def:
        return jsonify({'error': 'Missing required fields'}), 400
    
    is_correct, points, message, show_mc, mc_options, correct_index = check_answer(
        player_name, word, answer, correct_def, words
    )
    
    if is_correct:
        return jsonify({
            'correct': True,
            'points': points,
            'score': get_player_score(player_name),
            'message': message
        })
    elif show_mc:
        return jsonify({
            'correct': False,
            'show_mc': True,
            'options': mc_options,
            'correct_index': correct_index
        })
    else:
        return jsonify({
            'correct': False,
            'show_mc': False,
            'message': message
        })

@app.route('/api/mc_answer', methods=['POST'])
def check_mc_answer_api():
    data = request.json
    player_name = data.get('player', '').strip().lower()
    selected_index = data.get('selected_index')
    correct_index = data.get('correct_index')
    correct_def = data.get('correct_definition')
    correct_answer = data.get('correct_answer')  # For math
    word = data.get('word')
    game_type = data.get('game_type', 'words').strip().lower()
    
    if game_type == 'math':
        if not all([player_name, selected_index is not None, correct_index is not None, correct_answer]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        is_correct, points, message = check_math_answer(
            player_name, selected_index, correct_index, correct_answer
        )
        
        return jsonify({
            'correct': is_correct,
            'points': points,
            'score': get_player_score(player_name, 'math'),
            'message': message
        })
    else:
        if not all([player_name, selected_index is not None, correct_index is not None, correct_def, word]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        is_correct, points, message = check_mc_answer(
            player_name, word, selected_index, correct_index, correct_def
        )
        
        return jsonify({
            'correct': is_correct,
            'points': points,
            'score': get_player_score(player_name, 'words'),
            'message': message
        })

# Main entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cli', action='store_true', help='Use command-line interface instead of web UI')
    parser.add_argument('--voice', action='store_true', help='Enable voice input (CLI only)')
    parser.add_argument('--games', action='store_true', help='Enable bonus games at milestone scores')
    parser.add_argument('--port', type=int, default=5000, help='Port for web server (default: 5000)')
    args = parser.parse_args()
    
    if args.cli:
        # CLI mode
        player_name = input("Enter your name, explorer: ").strip().lower()
        game_loop_cli(player_name, words, args.games, args.voice)
    else:
        # Web mode
        print(f"Starting Word Quest Game web server...")
        print(f"Open your browser to: http://localhost:{args.port}")
        app.run(debug=False, host='0.0.0.0', port=args.port)
