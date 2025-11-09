# Word Quest Game

A word meaning recall game designed to help kids learn and remember dictionary words. Players are quizzed on word definitions, with the game tracking their progress and prioritizing words they struggle with. When players reach 50 points, they unlock bonus mini-games as rewards.

## Project Overview

This interactive learning game combines vocabulary practice with gamification. The game:
- Presents words from a dictionary and asks players to define them
- Tracks individual word performance to focus on weaker areas
- Uses AI (Ollama) to intelligently check if player answers match the correct definitions
- Rewards players with bonus games when they reach milestone scores

## Files

- **main.py** - The main game loop that manages word quizzes, scoring, and bonus game unlocks.
- **words.json** - Contains the dictionary of words and their definitions that players will learn.
- **bricks.py** - A brick-breaker bonus game where players break bricks with a paddle and ball.
- **dino_game.py** - A dino run bonus game where players jump over obstacles.
- **gorilla_game.py** - A gorilla banana defense bonus game where players launch bananas to destroy rockets.

## Prerequisites

1. **Python 3** - Required to run the game
2. **Ollama Server** - Must be running in the background with the `mistral` model installed
   - Install Ollama from [ollama.ai](https://ollama.ai)
   - Run `ollama pull mistral` to download the model
   - Ensure the Ollama server is running before starting the game
3. **Pygame** - Required for the bonus games (installed via requirements.txt)

## Installation

1. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

2. Ensure Ollama is running with the mistral model:
   ```bash
   ollama serve
   ollama pull mistral
   ```

## Usage

### Web Interface (Default)

Run the web server:
```bash
python3 main.py
```

Then open your browser to: `http://localhost:5000`

**Accessing from Other Devices on the Same Network:**
The server is configured to accept connections from other devices on the same network (WiFi, Apple Family, etc.). To access from another MacBook, iPad, or any device on the same network:

1. Find the IP address of the machine running the server:
   - **macOS**: Open Terminal and run `ipconfig getifaddr en0` (or `en1` for WiFi)
   - **Linux**: Run `hostname -I` or `ip addr show`
   - The server will also display the IP address when it starts

2. On the other device, open a browser and go to: `http://[IP_ADDRESS]:5000`
   - For example: `http://192.168.1.100:5000`

3. Make sure both devices are on the same WiFi network

**Note:** You may need to allow incoming connections through your firewall if you encounter connection issues.

The web interface provides:
- Clickable buttons for multiple choice answers
- Text input box for definitions
- Visual feedback with color-coded responses
- Real-time score updates

### Command-Line Interface

For the traditional CLI experience:
```bash
python3 main.py --cli
```

Enable bonus games:
```bash
python3 main.py --cli --games
```

### Command-Line Options

- `--cli` - Use command-line interface instead of web UI
- `--games` - Enable bonus games at milestone scores
- `--port PORT` - Set port for web server (default: 5000)

The game will:
1. Ask for your name to track your progress
2. Present words and ask for their definitions
3. Award points based on correctness (3 points for correct definition, 1 point for correct multiple choice)
4. Prioritize words you've struggled with
5. Unlock bonus games at 50 points and every 20 points thereafter (if `--games` is enabled)

## Scoring

- **3 points**: Correctly define the word (checked via AI)
- **1 point**: Select the correct definition from multiple choice
- **0 points**: Incorrect answer
- **Bonus games**: Cost 35 points to play, unlocked at 50 points and every 20 points after
