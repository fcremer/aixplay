from flask import Flask, request, jsonify, render_template
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
    # Findet den angegebenen Spieler in der Datenliste
    player_info = next((player for player in data['players'] if player['abbreviation'] == player_abbreviation), None)

    if player_info is None:
        return jsonify({'error': 'Spieler nicht gefunden'}), 404

    played_machines = set()
    played_dates = set()  # Menge für einzigartige Spieltage
    played_machines_info = []  # Liste für gespielte Maschinen mit Rang

    for score in data['scores']:
        if score['player_abbreviation'] == player_abbreviation:
            played_machines.add(score['pinball_abbreviation'])
            played_dates.add(score['date'])  # Fügt das Datum zum Set hinzu

    for machine in played_machines:
        # Finden aller Scores für jede Maschine
        machine_scores = [s for s in data['scores'] if s['pinball_abbreviation'] == machine]
        # Sortieren der Scores in absteigender Reihenfolge
        machine_scores.sort(key=lambda x: x['points'], reverse=True)
        # Bestimmen des Rangs des Spielers
        rank = next((index for index, s in enumerate(machine_scores, start=1) if s['player_abbreviation'] == player_abbreviation), None)
        played_machines_info.append({'machine': machine, 'rank': rank})

    # Sortieren der gespielten Maschinen nach Rang in absteigender Reihenfolge
    played_machines_info.sort(key=lambda x: x['rank'], reverse=True)

    all_machines = set(machine['abbreviation'] for machine in data['pinball_machines'])
    not_played_machines = all_machines - played_machines

    return jsonify({
        'player_info': player_info,
        'played_machines': played_machines_info,
        'not_played_machines': list(not_played_machines),
        'played_dates': len(played_dates)  # Anzahl der einzigartigen Spieltage
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


def calculate_highscores(pinball_abbreviation):
    scores_by_player = {}
    for score in data['scores']:
        if score['pinball_abbreviation'] == pinball_abbreviation:
            if score['player_abbreviation'] not in scores_by_player or \
                    scores_by_player[score['player_abbreviation']]['points'] < score['points']:
                scores_by_player[score['player_abbreviation']] = score

    highscores = list(scores_by_player.values())
    highscores.sort(key=lambda x: x['points'], reverse=True)

    highscores_with_points = []
    points = 15
    for score in highscores[:15]:
        highscores_with_points.append({
            'player': score['player_abbreviation'],
            'score': score['points'],
            'points': points
        })
        points -= 1 if points > 1 else 0
    return highscores_with_points


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)