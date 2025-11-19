#!/usr/bin/env python3
"""
Script to fetch all cat breeds from The Cat API and save them in a format
suitable for the game.
"""

import requests
import json

def fetch_all_breeds():
    """Fetch all cat breeds from The Cat API."""
    url = 'https://api.thecatapi.com/v1/breeds'
    response = requests.get(url)
    
    if response.status_code == 200:
        breeds = response.json()
        print(f"Fetched {len(breeds)} breeds from The Cat API")
        return breeds
    else:
        print(f"Error fetching breeds: {response.status_code}")
        return []

def format_breed_for_game(breed, index):
    """Format a breed from The Cat API into game format."""
    # Get weight in imperial format
    weight_imperial = breed.get('weight', {}).get('imperial', 'Unknown')
    if weight_imperial and weight_imperial != 'Unknown':
        weight_str = f"{weight_imperial} lbs"
    else:
        weight_str = "Unknown"
    
    # Get temperament and split into list
    temperament = breed.get('temperament', '')
    if temperament:
        temperament_list = [t.strip() for t in temperament.split(',')]
    else:
        temperament_list = []
    
    # Create facts list from various attributes
    facts = []
    
    # Add description as first fact if available
    description = breed.get('description', '')
    if description:
        # Shorten description if too long
        if len(description) > 100:
            description = description[:97] + "..."
        facts.append(description)
    
    # Add life span
    life_span = breed.get('life_span', '')
    if life_span:
        facts.append(f"Lives {life_span} years")
    
    # Add child friendly info
    child_friendly = breed.get('child_friendly', 0)
    if child_friendly >= 4:
        facts.append("Great with kids!")
    elif child_friendly >= 2:
        facts.append("Good with kids")
    
    # Add dog friendly info
    dog_friendly = breed.get('dog_friendly', 0)
    if dog_friendly >= 4:
        facts.append("Loves dogs!")
    elif dog_friendly >= 2:
        facts.append("Gets along with dogs")
    
    # Add energy level
    energy_level = breed.get('energy_level', 0)
    if energy_level >= 4:
        facts.append("Very active and playful")
    elif energy_level <= 2:
        facts.append("Calm and relaxed")
    
    # Add intelligence
    intelligence = breed.get('intelligence', 0)
    if intelligence >= 4:
        facts.append("Super smart!")
    
    # Add special traits
    if breed.get('hairless', 0) == 1:
        facts.append("Hairless breed")
    if breed.get('rex', 0) == 1:
        facts.append("Curly or wavy coat")
    if breed.get('suppressed_tail', 0) == 1:
        facts.append("Short or no tail")
    if breed.get('short_legs', 0) == 1:
        facts.append("Short legs")
    if breed.get('hypoallergenic', 0) == 1:
        facts.append("Hypoallergenic")
    
    # Add temperament traits (limit to 3-4 most interesting)
    if temperament_list:
        facts.extend(temperament_list[:3])
    
    # Limit facts to 6-7 most interesting
    facts = facts[:7]
    
    # Get emoji based on breed characteristics
    emoji = '🐱'  # Default
    if breed.get('hairless', 0) == 1:
        emoji = '😹'
    elif breed.get('rex', 0) == 1:
        emoji = '😸'
    elif breed.get('suppressed_tail', 0) == 1:
        emoji = '😼'
    elif energy_level >= 4:
        emoji = '😻'
    elif intelligence >= 4:
        emoji = '😺'
    
    return {
        'breed_number': index + 1,
        'name': breed.get('name', 'Unknown'),
        'emoji': emoji,
        'origin': breed.get('origin', 'Unknown'),
        'weight': weight_str,
        'facts': facts,
        'life_span': life_span,
        'temperament': temperament,
        'child_friendly': child_friendly,
        'dog_friendly': dog_friendly,
        'energy_level': energy_level,
        'intelligence': intelligence,
        'description': description,
        'api_id': breed.get('id', '')  # Store API ID for image fetching
    }

def main():
    """Main function to fetch and format breeds."""
    print("Fetching cat breeds from The Cat API...")
    breeds = fetch_all_breeds()
    
    if not breeds:
        print("No breeds fetched. Exiting.")
        return
    
    # Format breeds for game
    formatted_breeds = []
    for i, breed in enumerate(breeds):
        formatted = format_breed_for_game(breed, i)
        formatted_breeds.append(formatted)
        print(f"  {i+1}. {formatted['name']} - {formatted['origin']}")
    
    # Save to JSON file
    output_file = 'cat_breeds_api.json'
    with open(output_file, 'w') as f:
        json.dump(formatted_breeds, f, indent=2)
    
    print(f"\nSaved {len(formatted_breeds)} breeds to {output_file}")
    print(f"\nTo use these breeds, update main.py to load from {output_file}")

if __name__ == '__main__':
    main()

