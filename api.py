from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import PinballMachine, Player, Score
from data_manager import load_data, save_data
import datetime
import os

app = Flask(__name__)
CORS(app)
data = load_data()


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


def get_player(player_abbreviation):
    # Finds the specified player in the data list
    player_info = next((player for player in data['players'] if player['abbreviation'] == player_abbreviation), None)

    if player_info is None:
        return {'error': 'Player not found'}, 404

    played_machines = set()
    played_dates = set()  # Set for unique play days
    played_machines_info = []  # List for played machines with rank

    for score in data['scores']:
        if score['player_abbreviation'] == player_abbreviation:
            played_machines.add(score['pinball_abbreviation'])
            played_dates.add(score['date'])  # Add date to set

    for machine in played_machines:
        # Find all scores for each machine
        machine_scores = [s for s in data['scores'] if s['pinball_abbreviation'] == machine]
        # Sort scores in descending order
        machine_scores.sort(key=lambda x: x['points'], reverse=True)
        # Determine the player's rank
        rank = next((index for index, s in enumerate(machine_scores, start=1) if
                     s['player_abbreviation'] == player_abbreviation), None)
        played_machines_info.append({'machine': machine, 'rank': rank})

    # Sort played machines by rank in descending order
    played_machines_info.sort(key=lambda x: x['rank'], reverse=True)

    all_machines = set(machine['abbreviation'] for machine in data['pinball_machines'])
    not_played_machines = all_machines - played_machines

    return {
        'player_info': player_info,
        'played_machines': played_machines_info,
        'not_played_machines': list(not_played_machines),
        'played_dates': len(played_dates)  # Number of unique play days
    }


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
        player_data = get_player(player_abbr)
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000) 