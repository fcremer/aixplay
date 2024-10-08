from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin
from models import PinballMachine, Player, Score
from data_manager import load_data, save_data
from time import sleep

import datetime
import os



app = Flask(__name__)

data = load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ifpa')
def ifpa():
    return render_template('ifpa.html')

@app.route('/score-overview/<pinball>/<player>')
def score_overview(pinball, player):
    # Filter scores for the selected pinball machine
    pinball_scores = [score for score in data['scores'] if score['pinball_abbreviation'] == pinball]

    # If no scores found for the pinball, return empty data
    if not pinball_scores:
        return jsonify({'minScore': None, 'maxScore': None, 'playerScore': None})

    # Determine the highest score per player
    highest_scores_per_player = {}
    for score in pinball_scores:
        player_abbr = score['player_abbreviation']
        if player_abbr not in highest_scores_per_player or highest_scores_per_player[player_abbr] < score['points']:
            highest_scores_per_player[player_abbr] = score['points']

    # Create a list of highest scores for the pinball machine
    highest_scores = list(highest_scores_per_player.values())

    # Sort the scores in descending order
    highest_scores.sort(reverse=True)

    # Determine min_score based on the number of scores
    min_score = highest_scores[14] if len(highest_scores) > 15 else min(highest_scores)

    # Get the maximum score for the pinball machine
    max_score = max(highest_scores)

    # Determine the latest score for the requested player
    player_latest_score = highest_scores_per_player.get(player, None)

    return jsonify({
        'minScore': min_score,
        'maxScore': max_score,
        'playerScore': player_latest_score
    })



def is_score_valid(pinball_abbreviation, new_score, scores_data):
    """
    Validates a new score for a specific pinball machine.

    Args:
    pinball_abbreviation (str): Abbreviation of the pinball machine.
    new_score (int): The new score to be validated.
    scores_data (list of dict): List of scores data dictionaries.

    Returns:
    bool: True if the score is valid, False otherwise.
    """
    # Filter scores for the specific pinball machine
    filtered_scores = [score['points'] for score in scores_data if score['pinball_abbreviation'] == pinball_abbreviation]

    # Ensure there are at least 5 scores to compare with
    if len(filtered_scores) < 5:
        return True  # Not enough data to validate

    # Calculate the average of the existing scores
    avg_score = sum(filtered_scores) / len(filtered_scores)
    print("avg"+str(avg_score))
    # Check if the new score deviates by more than 50% from the average
    return new_score <= 1.5 * avg_score

@app.route('/validate_score', methods=['POST'])
def validate_score():
    # Daten aus der POST-Anfrage extrahieren
    body = request.json
    pinball_abbreviation = body.get('pinball_abbreviation')
    new_score = body.get('new_score')

    # Stellen Sie sicher, dass die erforderlichen Daten vorhanden sind
    if not all([pinball_abbreviation, new_score]):
        return jsonify({'error': 'Missing data'}), 400

    # Filtern Sie die vorhandenen Scores und überprüfen Sie, ob sie die erforderlichen Schlüssel enthalten
    filtered_scores = [score for score in data['scores']
                       if 'pinball_abbreviation' in score and 'score' in score
                       and score['pinball_abbreviation'] == pinball_abbreviation]

    if not filtered_scores:
        return jsonify({'error': 'No valid existing scores for given abbreviation'}), 404

    # Ermitteln Sie den besten (höchsten) Score für die gegebene pinball_abbreviation
    best_score = max(filtered_scores, key=lambda x: x['score'])['score']

    # Berechnen Sie die Abweichung des neuen Scores vom besten Score
    deviation = new_score - best_score

    # Rufen Sie Ihre Validierungsfunktion mit der Abweichung auf
    is_valid = is_score_valid(pinball_abbreviation, new_score, deviation)

    # Rückgabe des Ergebnisses
    return jsonify({'is_valid': is_valid})



@app.route('/admin')
def score_admin():
    # Laden Sie die notwendigen Daten
    scores = data['scores']
    players = {player['abbreviation']: player['name'] for player in data['players']}
    pinballs = {machine['abbreviation']: machine['long_name'] for machine in data['pinball_machines']}
    scores.sort(key=lambda x: datetime.datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)

    # Umwandeln der Scores in ein für das Frontend geeignetes Format
    scores_display = []
    for score in scores:
        scores_display.append({
          #  'id': score['id'],  # Nehmen Sie an, dass jede Punktzahl eine eindeutige ID hat
            'player': players.get(score['player_abbreviation'], 'unknown player'),
            'pinball': pinballs.get(score['pinball_abbreviation'], 'Unknown machine'),
            'points': score['points'],
            'date': score['date'],
            'player_abbreviation': score['player_abbreviation'],
            'pinball_abbreviation': score['pinball_abbreviation']
        })

    return render_template('admin.html', scores=scores_display)


@app.route('/bigscreen')
def bigscreen():
    # Umwandeln der Spieler- und Pinball-Listen in Wörterbücher für einfachen Zugriff
    player_dict = {player['abbreviation']: player['name'] for player in data['players']}
    pinball_dict = {machine['abbreviation']: machine['long_name'] for machine in data['pinball_machines']}

    # Berechnen der Anzahl der von jedem Spieler gespielten einzigartigen Maschinen
    played_machines_per_player = {player['abbreviation']: set() for player in data['players']}
    for score in data['scores']:
        played_machines_per_player[score['player_abbreviation']].add(score['pinball_abbreviation'])

    # Erstellen der Daten für die erste Tabelle (Spielerstatistiken)
    players_table_data = [
        {
            'name': player['name'],
            'played_machines': len(played_machines_per_player[player['abbreviation']]),
            'total_machines': len(data['pinball_machines'])
        }
        for player in data['players'] if len(played_machines_per_player[player['abbreviation']]) > 0
    ]

    # Sortieren der Spieler nach der Anzahl der gespielten Maschinen in absteigender Reihenfolge
    last_15_scores = data['scores'][-15:]

    sorted_scores = last_15_scores[::-1]
    # Hinzufügen von Ranginformationen zu jedem Score
    scores_table_data = []
    for score in sorted_scores:
        machine_scores = sorted(
            [s for s in data['scores'] if s['pinball_abbreviation'] == score['pinball_abbreviation']],
            key=lambda x: x['points'], reverse=True)
        rank = next((i + 1 for i, s in enumerate(machine_scores) if
                     s['player_abbreviation'] == score['player_abbreviation'] and s['points'] == score['points']), "-")

        scores_table_data.append({
            'machine_long_name': pinball_dict.get(score['pinball_abbreviation'], 'Unbekannte Maschine'),
            'player_full_name': player_dict.get(score['player_abbreviation'], 'Unbekannter Spieler'),
            'points': score['points'],
            'rank': rank
        })

    return render_template('bigscreen.html', players_table_data=players_table_data, scores_table_data=scores_table_data)



@app.route('/mobile')
def mobile():
    return render_template('mobile.html')

@app.route('/playeroverview')
def player_overview():
    return render_template('playeroverview.html')

@app.route('/pinball', methods=['POST'])
def add_pinball():
    new_pinball = PinballMachine(**request.json)
    data['pinball_machines'].append(vars(new_pinball))
    save_data(data)
    return jsonify({"message": "Pinball machine added"}), 201

@app.route('/pinball', methods=['GET'])
def get_pinball_machines():
    sorted_pinball_machines = sorted(data['pinball_machines'],
                                     key=lambda x: x['long_name'],
                                     reverse=False)
    return jsonify(sorted_pinball_machines)

@app.route('/player', methods=['POST'])
def add_player():
    new_player = Player(**request.json)
    data['players'].append(vars(new_player))
    save_data(data)
    return jsonify({"message": "Player added"}), 201

@app.route('/players', methods=['GET'])
def get_players():
    return jsonify(data['players'])


@app.route('/get_player/<player_abbreviation>', methods=['GET'])
def get_player(player_abbreviation):
    # Find the specified player in the data list
    player_info = next((player for player in data['players'] if player['abbreviation'] == player_abbreviation), None)

    if player_info is None:
        return jsonify({'error': 'Player not found'}), 404

    # Initialize sets for played machines and dates
    played_machines = set()
    played_dates = set()  # Set for unique play dates
    played_machines_info = []  # List for played machines with rank

    # Loop through the scores to find machines played by the player
    for score in data['scores']:
        if score['player_abbreviation'] == player_abbreviation:
            played_machines.add(score['pinball_abbreviation'])
            played_dates.add(score['date'])  # Add the date to the set

    # Collect information about the played machines and their ranks
    for machine in played_machines:
        # Find all scores for each machine
        machine_scores = [s for s in data['scores'] if s['pinball_abbreviation'] == machine]
        # Sort the scores in descending order
        machine_scores.sort(key=lambda x: x['points'], reverse=True)
        # Determine the rank of the player
        rank = next((index for index, s in enumerate(machine_scores, start=1) if s['player_abbreviation'] == player_abbreviation), None)
        played_machines_info.append({'machine': machine, 'rank': rank})

    # Sort the played machines by rank in descending order
    played_machines_info.sort(key=lambda x: x['rank'], reverse=True)

    # Calculate tournament progress
    total_machines = len(data['pinball_machines'])
    machines_with_score = len(played_machines)
    tournament_progress = f"{machines_with_score}/{total_machines}"

    # Get the list of machines not yet played by the player
    all_machines = set(machine['abbreviation'] for machine in data['pinball_machines'])
    not_played_machines = all_machines - played_machines

    # Return the extended player information
    return jsonify({
        'player_info': player_info,
        'played_machines': played_machines_info,
        'not_played_machines': list(not_played_machines),
        'played_dates': len(played_dates),  # Number of unique play dates
        'tournament_progress': tournament_progress  # Tournament progress in the format "X/Y"
    })
@app.route('/score', methods=['POST'])
def add_score():
    new_score = Score(**request.json)
    data['scores'].append(vars(new_score))
    save_data(data)
    return jsonify({"message": "Score added"}), 201

@app.route('/scores/pinball/<pinball_abbreviation>', methods=['GET'])
def get_scores_by_pinball(pinball_abbreviation):
    scores = [s for s in data['scores'] if s['pinball_abbreviation'] == pinball_abbreviation]
    return jsonify(scores), 200

@app.route('/scores/player/<player_abbreviation>', methods=['GET'])
def get_scores_by_player(player_abbreviation):
    scores = [s for s in data['scores'] if s['player_abbreviation'] == player_abbreviation]
    return jsonify(scores), 200

@app.route('/scores/date/<date>', methods=['GET'])
def get_scores_by_date(date):
    date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
    scores = [s for s in data['scores'] if datetime.datetime.strptime(s['date'], '%Y-%m-%d') == date_obj]
    return jsonify(scores), 200

@app.route('/delete_score/<pinball_abbreviation>/<player_abbreviation>/<int:score_value>', methods=['DELETE'])
def delete_score(pinball_abbreviation, player_abbreviation, score_value):
    # Finden des entsprechenden Scores
    score_to_delete = next((score for score in data['scores']
                            if score['pinball_abbreviation'] == pinball_abbreviation
                            and score['player_abbreviation'] == player_abbreviation
                            and score['points'] == score_value), None)

    if score_to_delete:
        # Score aus der Liste entfernen
        data['scores'].remove(score_to_delete)
        save_data(data)
        return jsonify({"message": "Score deleted"}), 200
    else:
        return jsonify({"error": "Score not found"}), 404



@app.route('/highscore/pinball/<pinball_abbreviation>', methods=['GET'])
def get_highscore_by_pinball(pinball_abbreviation):
    highscores_with_points = calculate_highscores(pinball_abbreviation)
    return jsonify(highscores_with_points), 200



@app.route('/total_highscore', methods=['GET'])
def get_total_highscore():
    player_scores = {}
    all_pinballs = set(score['pinball_abbreviation'] for score in data['scores'])
    for pinball in all_pinballs:
        highscores = calculate_highscores(pinball)
        #print("Pinball: " + pinball + " Score: " + str(highscores))
        #print(highscores)
        for score in highscores:
            player_scores[score['player']] = player_scores.get(score['player'], 0) + score['points']
            sleep(0.000005) #ToDo: dirty fix for Full name display bug
            #if str(score['player']) == "FC":
            #    print("Player:" + str(score['player']) + " Sum: " + str(player_scores[score['player']]) + " " + str(score['points']) +" at Pin: " + pinball )

    #print(player_scores)
    sorted_scores = sorted(player_scores.items(), key=lambda x: x[1], reverse=True)
    total_highscores_with_rank = []
    rank = 1
    for player, points in sorted_scores:
        total_highscores_with_rank.append({
            'rank': rank,
            'player': player,
            'total_points': points
        })
        rank += 1

    return jsonify(total_highscores_with_rank), 200




@app.route('/player/<player_abbreviation>', methods=['GET'])
def print_scores_by_player(player_abbreviation):
    # Fetch all scores for the specified player
    scores = [s for s in data['scores'] if s['player_abbreviation'] == player_abbreviation]

    if not scores:
        return jsonify({"error": f"No scores found for player '{player_abbreviation}'"}), 404

    # Print the scores to the console
    print(f"Scores for player '{player_abbreviation}':")
    for score in scores:
        print(f"Pinball: {score['pinball_abbreviation']}, Score: {score['points']}, Date: {score['date']}")

    # Return the scores as a JSON response
    return jsonify(scores), 200


def calculate_highscores(pinball_abbreviation):
    scores_by_player = {}

    # Create a dictionary to quickly lookup if a player is a guest
    player_guest_status = {player['abbreviation']: player.get('guest', False) for player in data['players']}

    # Track the highest score for each player for the specific pinball machine
    for score in data['scores']:
        if score['pinball_abbreviation'] == pinball_abbreviation:
            player_abbreviation = score['player_abbreviation']

            if player_abbreviation not in scores_by_player or \
                    scores_by_player[player_abbreviation]['points'] < score['points']:
                scores_by_player[player_abbreviation] = score

    # Convert the dictionary to a list and sort by points in descending order
    highscores = list(scores_by_player.values())
    highscores.sort(key=lambda x: x['points'], reverse=True)

    # Assign ranking points, ensuring players with the same points get the same rank
    highscores_with_rank_and_points = []
    points = 15
    rank = 1
    previous_points = None
    previous_rank = 1  # Keep track of the previous rank to ensure correct rank sharing

    for score in highscores:
        player_abbreviation = score['player_abbreviation']
        is_guest = player_guest_status.get(player_abbreviation, False)

        # If the current player's points are different from the previous player's points, update the rank
        if previous_points is not None and score['points'] != previous_points:
            previous_rank = rank  # Update previous rank to the current rank

        # Ensure players ranked lower than 15 receive 0 points
        assigned_points = points if rank <= 15 else 0

        score_entry = {
            'player': player_abbreviation,
            'score': score['points'],
            'rank': previous_rank,
            'points': assigned_points
        }

        if is_guest:
            score_entry['guest'] = True

        highscores_with_rank_and_points.append(score_entry)

        previous_points = score['points']
        if not is_guest:
            rank += 1

        # Only decrement points if the player is not a guest and rank is within the top 15
        if not is_guest and rank <= 15:
            points -= 1 if points > 1 else 0

    return highscores_with_rank_and_points
@app.route('/player/<player_abbreviation>', methods=['DELETE'])
def delete_player(player_abbreviation):
    # Find and delete all scores associated with the player
    data['scores'] = [score for score in data['scores'] if score['player_abbreviation'] != player_abbreviation]

    # Find and delete the player from the list of players
    player_to_delete = next((player for player in data['players'] if player['abbreviation'] == player_abbreviation), None)

    if player_to_delete:
        data['players'].remove(player_to_delete)
        save_data(data)  # Save the updated data after deletion
        return jsonify({"message": f"Player '{player_abbreviation}' and their scores deleted"}), 200
    else:
        return jsonify({"error": "Player not found"}), 404

@app.route('/purgeguests', methods=['DELETE'])
def delete_all_guests():
    # Find all guest players (where 'guest' is True or exists and is True)
    guest_players = [player for player in data['players'] if player.get('guest') is True]

    # Iterate through the list of guest players and delete them
    for guest in guest_players:
        delete_player(guest['abbreviation'])

    return jsonify({"message": f"{len(guest_players)} guest players deleted"}), 200

@app.route('/pinball/<pinball_abbreviation>', methods=['DELETE'])
def delete_pinball_machine(pinball_abbreviation):
    # Step 1: Delete all scores related to the pinball machine
    global data  # Ensuring we're modifying the global `data` object
    original_score_count = len(data['scores'])
    data['scores'] = [score for score in data['scores'] if score['pinball_abbreviation'] != pinball_abbreviation]
    deleted_scores_count = original_score_count - len(data['scores'])

    # Step 2: Delete the pinball machine itself
    pinball_to_delete = next((machine for machine in data['pinball_machines'] if machine['abbreviation'] == pinball_abbreviation), None)

    if pinball_to_delete:
        data['pinball_machines'].remove(pinball_to_delete)
        save_data(data)  # Save the updated data after deletion
        return jsonify({"message": f"Pinball machine '{pinball_abbreviation}' and {deleted_scores_count} related scores deleted"}), 200
    else:
        return jsonify({"error": "Pinball machine not found"}), 404


@app.route('/latestscores', methods=['GET'])
def get_latest_scores():
    # Get today's date in 'YYYY-MM-DD' format
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    # Filter scores for today's date
    today_scores = [score for score in data['scores'] if score['date'] == today]

    # Prepare the response list
    latest_scores_response = []

    # For each score submitted today, calculate rank using calculate_highscores
    for score in today_scores:
        pinball_abbreviation = score['pinball_abbreviation']
        player_abbreviation = score['player_abbreviation']

        # Calculate highscores for the pinball machine
        highscores = calculate_highscores(pinball_abbreviation)

        # Find the rank of the player in today's score within the high scores
        rank = next((i + 1 for i, hs in enumerate(highscores) if hs['player'] == player_abbreviation), None)

        latest_scores_response.append({
            'player': player_abbreviation,
            'pinball': pinball_abbreviation,
            'points': score['points'],
            'date': score['date'],
            'rank': rank  # Include the calculated rank in the output
        })

    return jsonify(latest_scores_response), 200

@app.route('/matchsuggestion', methods=['GET'])
def match_suggestion():
    # Get today's date in 'YYYY-MM-DD' format
    today = datetime.datetime.now().strftime('%Y-%m-%d')

    # Identify active players based on today's scores
    today_scores = [score for score in data['scores'] if score['date'] == today]
    active_players = {score['player_abbreviation'] for score in today_scores}

    # Determine unplayed machines for each active player
    player_unplayed_machines = {}
    for player_abbr in active_players:
        player_data_response = get_player(player_abbr)
        player_data = player_data_response.json
        if 'not_played_machines' in player_data:
            player_unplayed_machines[player_abbr] = player_data['not_played_machines']

    # Prepare match suggestions based on unplayed machines
    match_suggestions = []
    all_pinball_machines = set(machine['abbreviation'] for machine in data['pinball_machines'])

    # Track the number of suggestions per player
    suggestions_count = {player: 0 for player in active_players}

    # Try to assign two players for each machine
    for machine in all_pinball_machines:
        # Get players who have not played this machine and have fewer than 2 suggestions
        players_for_machine = [player for player, machines in player_unplayed_machines.items()
                               if machine in machines and suggestions_count[player] < 2]

        # Ensure there are at least two players who haven't played the machine
        if len(players_for_machine) >= 2:
            player1, player2 = players_for_machine[:2]  # Take the first two players
            match_suggestions.append({
                'pinball': machine,
                'player1': player1,
                'player2': player2
            })

            # Increment suggestion counts
            suggestions_count[player1] += 1
            suggestions_count[player2] += 1

            # Remove players if they reached their maximum suggestions
            if suggestions_count[player1] >= 2:
                del player_unplayed_machines[player1]
            if suggestions_count[player2] >= 2:
                del player_unplayed_machines[player2]

    return jsonify(match_suggestions), 200

@app.route('/matchsuggestion/<player1>/<player2>', methods=['GET'])
def match_suggestion_for_players(player1, player2):
    # Retrieve unplayed machines for player1
    player1_data_response = get_player(player1)
    player1_data = player1_data_response.json
    if 'not_played_machines' not in player1_data:
        return jsonify({'error': f'Player {player1} not found or data unavailable'}), 404

    # Retrieve unplayed machines for player2
    player2_data_response = get_player(player2)
    player2_data = player2_data_response.json
    if 'not_played_machines' not in player2_data:
        return jsonify({'error': f'Player {player2} not found or data unavailable'}), 404

    # Find common unplayed machines for both players
    player1_unplayed = set(player1_data['not_played_machines'])
    player2_unplayed = set(player2_data['not_played_machines'])
    common_unplayed_machines = list(player1_unplayed.intersection(player2_unplayed))

    return jsonify({'common_unplayed_machines': common_unplayed_machines}), 200
@app.route('/getfreescores', methods=['GET'])
def getfreescores():
    # Create a dictionary to count scores for each pinball machine
    score_counts = {}
    # Count the number of scores for each pinball machine
    for score in data['scores']:
        pinball_abbr = score['pinball_abbreviation']
        if pinball_abbr in score_counts:
            score_counts[pinball_abbr] += 1
        else:
            score_counts[pinball_abbr] = 1
        print(pinball_abbr +" "+ str(score_counts[pinball_abbr]))

    # Identify machines with fewer than 15 scores
    easy_machines = [abbr for abbr, count in score_counts.items() if count < 14]
    # Ensure to include machines with zero scores
    all_machines = {machine['abbreviation'] for machine in data['pinball_machines']}
    machines_with_few_scores = set(easy_machines)
    # Combine machines with few scores and no scores
    result = list(machines_with_few_scores)

    return jsonify(result), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)