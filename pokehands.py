from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        raw_decklist = request.form['decklist']
        parsed_decklist = parse_decklist(raw_decklist)
        draw_chances, prize_chances = calculate_probabilities(parsed_decklist)

        # Make sure to pass the variables to the template with the correct names
        return render_template('results.html', draw_chances=draw_chances, prize_chances=prize_chances)
    
    return render_template('home.html')






def parse_decklist(decklist_string):
    # Dictionary to hold the card names and quantities
    decklist = {}       
    
    # Mapping for basic energy types
    energy_types = {
        "{D}": "Dark",
        "{F}": "Fighting",
        "{G}": "Grass",
        "{L}": "Lightning",
        "{M}": "Metal",
        "{P}": "Psychic",
        "{R}": "Fire",
        "{W}": "Water"
    }

    # Normalize line endings and split the decklist string into lines
    lines = decklist_string.replace('\r\n', '\n').strip().split('\n')

    # Keep track of the current section (Pokémon, Trainer, or Energy)
    current_section = None

    # Helper function to remove set codes and collection numbers
    def clean_card_name(card_name, current_section):
        if current_section in ['Trainer', 'Energy']:
            # Split the card name into parts
            parts = card_name.split(' ')
            # Rebuild the card name excluding set codes and collection numbers
            cleaned_name = []
            for part in parts:
                if part.isupper() and len(part) == 3:  # Set code detected
                    break
                if part.isnumeric():  # Collection number detected
                    break
                cleaned_name.append(part)
            return ' '.join(cleaned_name)
        else:
            # For Pokémon, return the name as is
            return card_name



    # Iterate over each line to process it
    for line in lines:
        # Clean up the line to remove carriage returns and extra whitespace
        line = line.replace('\r', '').strip()

        # Update the current section if needed
        if line.startswith('Pokémon:'):
            current_section = 'Pokémon'
            continue
        elif line.startswith('Trainer:'):
            current_section = 'Trainer'
            continue
        elif line.startswith('Energy:'):
            current_section = 'Energy'
            continue
        elif line.startswith('Total Cards:') or not line:
            continue  # Skip this line

        # Split the line into quantity and the rest of the string
        parts = line.split(' ', 1)
        if len(parts) < 2 or not parts[0].isdigit():
            continue  # Skip lines that don't have a valid quantity

        quantity = int(parts[0])
        card_name = parts[1]

        # Replace energy type symbols in basic energy cards
        if current_section == 'Energy' and card_name.startswith('Basic'):
            for energy_symbol, energy_full_name in energy_types.items():
                if energy_symbol in card_name:
                    # Replace only the symbol, not the whole word "Energy"
                    card_name = card_name.replace(energy_symbol, energy_full_name)
                    break


        # Clean the card name using the helper function
        card_name = clean_card_name(card_name, current_section)

        # Add the card to the decklist with its quantity
        decklist[card_name] = decklist.get(card_name, 0) + quantity

    return decklist

from math import comb

def calculate_draw_chance(deck_size, copies_in_deck, cards_drawn):
    # Calculate the probability of NOT drawing the card
    prob_not_drawing_card = (
        comb(deck_size - copies_in_deck, cards_drawn) /
        comb(deck_size, cards_drawn)
    )
    # Subtract from 1 to get the probability of drawing the card
    return 1 - prob_not_drawing_card




def calculate_probabilities(decklist):
    deck_size = sum(decklist.values())  # Total number of cards in the deck
    draw_chances = {}
    prize_chances = {}

    for card, quantity in decklist.items():
        draw_chance = calculate_draw_chance(deck_size, quantity, 7) * 100  # Draw chance
        prize_chance = calculate_prize_card_probability(deck_size, quantity)  # Prize card chance
        draw_chances[card] = draw_chance
        prize_chances[card] = prize_chance

    # Sort cards by highest draw chance first
    sorted_draw_chances = dict(sorted(draw_chances.items(), key=lambda item: item[1], reverse=True))

    return sorted_draw_chances, prize_chances



from math import comb

def calculate_prize_card_probability(deck_size, copies_in_deck):
    adjusted_deck_size = deck_size - 7  # Deck size after drawing the initial hand
    prize_probabilities = {}

    for k in range(min(5, copies_in_deck) + 1):  # From 0 to min(4, copies_in_deck)
        total_prob = 0
        # Limit 'drawn' to the range from 0 to the number of cards drawn initially
        for drawn in range(min(7, copies_in_deck) + 1):  # From 0 to min(7, copies_in_deck)
            # Calculate probability of drawing 'drawn' copies in initial hand
            if 7 - drawn >= 0:  # Ensure non-negative
                prob_drawn_initial = (
                    comb(copies_in_deck, drawn) *
                    comb(deck_size - copies_in_deck, 7 - drawn) /
                    comb(deck_size, 7)
                )
            else:
                prob_drawn_initial = 0

            # Calculate probability of 'k' copies being in prize cards given 'drawn' in initial hand
            if k + drawn <= copies_in_deck and 6 - k >= 0:  # Ensure non-negative
                prob_k_in_prize_given_drawn = (
                    comb(copies_in_deck - drawn, k) *
                    comb(adjusted_deck_size - copies_in_deck + drawn, 6 - k) /
                    comb(adjusted_deck_size, 6)
                )
                total_prob += prob_drawn_initial * prob_k_in_prize_given_drawn

        prize_probabilities[k] = total_prob * 100  # Convert to percentage

    return prize_probabilities





# Run the application
if __name__ == '__main__':
    app.run(debug=True)



