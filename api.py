from flask import Flask, request, jsonify, render_template
from models import PinballMachine, Player, Score
from data_manager import load_data, save_data
import datetime
import os



app = Flask(__name__)
data = load_data()

print( os.environ['GIST_TOKEN'] )
print("Debug")

@app.route('/')

def index():
    return render_template('index.html')

def is_score_valid(new_score, scores):
    # Implement logic to validate the score
    # For example, check if the score is within a reasonable range compared to other scores for the same pinball machine
    return True

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
    return jsonify(data['pinball_machines'])

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
    if not is_score_valid(new_score, data['scores']):
        return jsonify({"error": "Score seems unrealistic"}), 400
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

@app.route('/score/<int:id>', methods=['DELETE'])
def delete_score(id):
    if id >= len(data['scores']):
        return jsonify({"error": "Score not found"}), 404
    del data['scores'][id]
    save_data(data)
    return jsonify({"message": "Score deleted"}), 200

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
        for score in highscores:
            player_scores[score['player']] = player_scores.get(score['player'], 0) + score['points']

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
    app.run(host='0.0.0.0', port=5000, debug=True)