from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        raw_decklist = request.form['decklist']
        parsed_decklist = parse_decklist(raw_decklist)

        # Calculate draw and prize card probabilities
        draw_chances, prize_chances = calculate_probabilities(parsed_decklist)

        # Simulate the opening hand and prize cards
        initial_hand, prize_cards = simulate_opening_hand_and_prize_cards(parsed_decklist)

        # Render results.html with probabilities and simulated hands
        return render_template('results.html', draw_chances=draw_chances, prize_chances=prize_chances, initial_hand=initial_hand, prize_cards=prize_cards, raw_decklist=raw_decklist)

    return render_template('home.html')


KNOWN_SET_CODES = {"AOR", "AQ", "AR", "ASR", "B2", "BCR", "BKP", "BKT", "BLW", "BRS", "BS", "BST", "BUS", "CEC", "CEL", "CES", \
                    "CG", "CIN", "CL", "CPA", "CRE", "CRZ", "DAA", "DCR", "DET", "DEX", "DF", "DP", "DR", "DRM", "DRV", "DRX", "DS", \
                    "DX", "EM", "EPO", "EVO", "EVS", "EX", "FCO", "FFI", "FLF", "FLI", "FO", "FST", "G1", "G2", "GE", "GEN", "GRI", "HIF", \
                    "HL", "HP", "HS", "JU", "KSS", "LA", "LC", "LM", "LOR", "LOT", "LTR", "MA", "MD", "MEW", "MT", "N1", "N2", "N3", "N4", \
                    "NVI", "NXD", "OBF", "PAL", "PGO", "PHF", "PK", "PL", "PLB", "PAR", "PLF", "PLS", "PRC", "RCL", "RG", "ROS", "RR", "RS", "SF", "SHF", \
                    "SI", "SIT", "SK", "SLG", "SS", "SSH", "STS", "SUM", "SV", "SVI", "SW", "TEU", "TM", "TR", "TRR", "UD", "UF", "UL", "UNB", "UNM", \
                    "UPR", "VIV", "XY"}





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
                    # Replace the symbol with the full name and ensure "Energy" is added only once
                    card_name = "Basic " + energy_full_name + " Energy"
                    break


        # Clean the card name using the helper function
        card_name = clean_card_name(card_name, current_section)

        # Add the card to the decklist with its quantity
        decklist[card_name] = decklist.get(card_name, 0) + quantity

    return decklist


    # Helper function to remove set codes and collection numbers
def clean_card_name(card_name, current_section):
    if current_section in ['Trainer', 'Energy']:
        parts = card_name.split(' ')
        cleaned_name = []

        for part in parts:
            # Check if part is a known set code or set code with a suffix
            is_set_code_with_suffix = any(part.startswith(code) and (len(part) == 3 or part[3] == '-') for code in KNOWN_SET_CODES)
            if is_set_code_with_suffix:  # Check against known set codes with possible suffix
                break
            if part.isnumeric():  # Collection number detected
                break
            cleaned_name.append(part)

        return ' '.join(cleaned_name)
    else:
        return card_name
        

from math import comb


##########################OLD SHIT###############################################
def calculate_draw_chance(deck_size, copies_in_deck, cards_drawn):
    if cards_drawn > deck_size or deck_size == 0:  # Add a check to prevent division by zero
        return 0
    # Calculate the probability of NOT drawing the card
    prob_not_drawing_card = (
        comb(deck_size - copies_in_deck, cards_drawn) /
        comb(deck_size, cards_drawn)
    )
    # Subtract from 1 to get the probability of drawing the card
    return 1 - prob_not_drawing_card

############################### NEW SHIT ########################################
# def calculate_draw_chance(deck_size, copies_in_deck, cards_drawn):
#     probabilities = {}
#     for i in range(1, min(copies_in_deck, 4) + 1):  # Calculate for up to 4 copies
#         # Probability of drawing exactly i copies
#         prob_drawing_i_copies = (
#             comb(copies_in_deck, i) *
#             comb(deck_size - copies_in_deck, cards_drawn - i) /
#             comb(deck_size, cards_drawn)
#         )
#         probabilities[i] = prob_drawing_i_copies * 100  # Convert to percentage
#     return probabilities




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

# def calculate_probabilities(decklist):
#     deck_size = sum(decklist.values())  # Total number of cards in the deck
#     draw_chances = {}
#     prize_chances = {}

#     for card, quantity in decklist.items():
#         draw_chances[card] = calculate_draw_chance(deck_size, quantity, 7)  # Draw chance
#         prize_chances[card] = calculate_prize_card_probability(deck_size, quantity)  # Prize card chance

#     # Sort cards by highest draw chance first
#     sorted_draw_chances = {
#         card: {
#             i: draw_chances[card][i] * 100 if i in draw_chances[card] else 'N/A'
#             for i in range(1, 5)
#         }
#         for card in draw_chances
#     }

#     return sorted_draw_chances, prize_chances



from math import comb

def calculate_prize_card_probability(deck_size, copies_in_deck):
    if deck_size <= 13:  # Ensure there's enough cards for initial hand and prize cards
        return {k: 0 for k in range(5)}
    
    adjusted_deck_size = deck_size - 7  # Deck size after drawing the initial hand
    prize_probabilities = {}
    
    for k in range(min(5, copies_in_deck) + 1):  # From 0 to min(4, copies_in_deck)
        total_prob = 0
        for drawn in range(min(7, copies_in_deck) + 1):  # From 0 to min(7, copies_in_deck)
            # Calculate probability of drawing 'drawn' copies in initial hand
            if 7 - drawn >= 0 and deck_size - copies_in_deck >= 7 - drawn:  # Ensure non-negative and valid comb arguments
                prob_drawn_initial = (
                    comb(copies_in_deck, drawn) *
                    comb(deck_size - copies_in_deck, 7 - drawn) /
                    comb(deck_size, 7)
                )
            else:
                prob_drawn_initial = 0

            # Calculate probability of 'k' copies being in prize cards given 'drawn' in initial hand
            if k + drawn <= copies_in_deck and 6 - k >= 0:  # Ensure non-negative and valid comb arguments
                prob_k_in_prize_given_drawn = (
                    comb(copies_in_deck - drawn, k) *
                    comb(adjusted_deck_size - copies_in_deck + drawn, 6 - k) /
                    comb(adjusted_deck_size, 6)
                )
                total_prob += prob_drawn_initial * prob_k_in_prize_given_drawn

        prize_probabilities[k] = total_prob * 100  # Convert to percentage

    return prize_probabilities


import random

def simulate_opening_hand_and_prize_cards(decklist):
    # Flatten the decklist into a list of cards
    full_deck = []
    for card, quantity in decklist.items():
        full_deck.extend([card] * quantity)
    
    # Shuffle the full deck to randomize card order
    random.shuffle(full_deck)
    
    # Draw the initial 7 cards for the hand
    initial_hand = full_deck[:7]
    
    # Set aside the next 6 cards for the prize cards
    prize_cards = full_deck[7:13]
    
    return initial_hand, prize_cards




# Run the application
if __name__ == '__main__':
    app.run(debug=True)



