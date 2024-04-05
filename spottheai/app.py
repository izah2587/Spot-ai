from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import datetime
import csv
from sqlalchemy.sql.expression import func


app = Flask(__name__)  # Specify template directory
app.secret_key = 'spotAI'  # Set a secret key for the session
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:izahaha#567@localhost/spotAI'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Game(db.Model):
    __tablename__ = 'games'
    game_code = db.Column(db.String(200), primary_key=True)
    game_status = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    current_round = db.Column(db.Integer, default=0)  # New field for tracking rounds
    prompt_ids = db.Column(db.String, default='')  # New field for storing prompt IDs

    def __init__(self, game_code, game_status, created_at):
        self.game_code = game_code
        self.game_status = game_status
        self.created_at = created_at

    def get_current_prompt_id(self):
        # Some logic to retrieve the current prompt ID
        # For example, if you're storing IDs in a comma-separated string:
        prompt_ids = self.prompt_ids.split(',')
        return int(prompt_ids[self.current_round - 1]) if self.current_round <= len(prompt_ids) else None

class Player(db.Model):
    __tablename__ = 'player'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    game_code = db.Column(db.String(200), db.ForeignKey('games.game_code'))
    is_host = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)

    def __init__(self, name, game_code, is_host=False):
        self.name = name
        self.game_code = game_code
        self.is_host = is_host

class Prompt(db.Model):
    __tablename__ = 'prompt'
    id = db.Column(db.Integer, primary_key=True)
    prompt_text = db.Column(db.Text)
    ai_response = db.Column(db.Text)

    def __init__(self, prompt_text, ai_response):
        self.prompt_text = prompt_text
        self.ai_response = ai_response

class PlayerResponse(db.Model):
    __tablename__ = 'player_responses'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompt.id'))
    response = db.Column(db.Text)
    round_number = db.Column(db.Integer)

    def __init__(self, player_id, prompt_id, response, round_number):
        self.player_id = player_id
        self.prompt_id = prompt_id
        self.response = response
        self.round_number = round_number

class PlayerChoice(db.Model):
    __tablename__ = 'player_choices'
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    game_code = db.Column(db.String(200), db.ForeignKey('games.game_code'))
    round_number = db.Column(db.Integer)
    response_id = db.Column(db.Integer, db.ForeignKey('player_responses.id'))
    
    def __init__(self, player_id, game_code, round_number, response_id):
        self.player_id = player_id
        self.game_code = game_code
        self.round_number = round_number
        self.response_id = response_id



def populate_prompts():
    with open('prompt.csv', mode='r', encoding='utf-8-sig') as file:  # Ensure you have the correct path
        reader = csv.DictReader(file)
        for row in reader:
            prompt_text, ai_response = row['prompt_text'], row['ai_response']
            existing_prompt = Prompt.query.filter_by(prompt_text=prompt_text).first()
            if not existing_prompt:  # Avoid duplicates
                prompt = Prompt(prompt_text=prompt_text, ai_response=ai_response)
                db.session.add(prompt)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join():
    name = request.form['name']
    game_code = request.form['game_code']
    # Check if the game exists
    game = Game.query.filter_by(game_code=game_code).first()
    
    if game is None:
        # Game does not exist, return an error message or redirect back to home with an error
        return redirect(url_for('index', error='Game not found'))
    else:
        # Check if the player is already in the game
        player = Player.query.filter_by(name=name, game_code=game_code).first()
        if player is None:
            # Add player to the game room
            player = Player(name=name, game_code=game_code)
            db.session.add(player)
            db.session.commit()

        # Set the player's name in the session
            session['player_name'] = name
            session['player_id'] = player.id
        
        # Redirect to the game lobby
        return redirect(url_for('game_lobby', game_code=game_code))



@app.route('/host', methods=['POST'])
def host():
    name = request.form['name']
    # Generate a unique game code
    game_code = "".join(random.choices("0123456789", k=4))
    # Make sure the generated game code is unique
    while Game.query.filter_by(game_code=game_code).first() is not None:
        game_code = "".join(random.choices("0123456789", k=4))

    # Create new game with the generated game code
    new_game = Game(game_code=game_code, game_status='waiting', created_at=datetime.datetime.now())
    db.session.add(new_game)

    # Add the host player to the game room
    host_player = Player(name=name, game_code=game_code, is_host=True)
    db.session.add(host_player)
    db.session.commit()

    #session
    session['player_name'] = name  # Set the host's name in the session
    session['is_host'] = True # Set the is_host flag in the session
    session['player_id'] = host_player.id

    # Redirect to the game room or return success message
    # You might want to redirect to a game room page or return game details
    return redirect(url_for('game_lobby', game_code=game_code))

@app.route('/game_lobby/<game_code>')
def game_lobby(game_code):
    game = Game.query.filter_by(game_code=game_code).first()
    if game and game.game_status == 'waiting':
        # Retrieve the current player's information from the session
        current_player_name = session.get('player_name')
        if current_player_name:
            # Now use current_player_name to find the player and check if they are the host
            player = Player.query.filter_by(name=current_player_name, game_code=game_code).first()
            if player:
                is_host = player.is_host
                # Pass the is_host flag to your template
                return render_template('game_lobby.html', game_code=game_code, host=is_host)
            else:
                return "Error: Player not found in this game."  # Or handle as appropriate
        else:
            return "Error: Player name not set in session."  # Or handle as appropriate
    else:
        return "Game not found or already started", 404
    
@app.route('/game_status/<game_code>')
def game_status(game_code):
    game = Game.query.filter_by(game_code=game_code).first()
    if game:
        return jsonify({'game_status': game.game_status}), 200
    else:
        return jsonify({'error': 'Game not found'}), 404


#new route for the game
@app.route('/start_game/<game_code>', methods=['POST'])
def start_game(game_code):
    game = Game.query.filter_by(game_code=game_code).first()
    if game and session.get('is_host', False):
        if game.current_round == 0:  # Only select prompts if the game hasn't started
            prompts = Prompt.query.order_by(func.random()).limit(3)  # Assuming 3 rounds
            game.prompt_ids = ','.join(str(prompt.id) for prompt in prompts)
            game.current_round = 1
        else:
            game.current_round += 1  # Or handle advancing rounds appropriately

        game.game_status = 'in_progress'
        db.session.commit()
        return jsonify({'success': 'Game started'}), 200
    return jsonify({'error': 'Not authorized or game not found'}), 403


@app.route('/play_game/<game_code>')
def play_game(game_code):
    game = Game.query.filter_by(game_code=game_code).first()
    if game and game.game_status == 'in_progress':
        prompt_ids = game.prompt_ids.split(',')
        current_prompt_id = prompt_ids[game.current_round - 1]  # -1 because list is 0-indexed
        prompt = Prompt.query.get(current_prompt_id)
        if prompt:
            return render_template('play_game.html', prompt=prompt.prompt_text, game_code=game_code, round=game.current_round)
        else:
            return "Prompt not found", 404
    return "Game not found or not started yet", 404

#new route for handling submissions
@app.route('/submit_response/<game_code>', methods=['POST'])
def submit_response(game_code):
    data = request.json
    response_text = data['response']
    player_name = session.get('player_name')
    print(f"Submitting response for player: {session.get('player_id')} in game: {game_code} with response: {data.get('response')}")

    game = Game.query.filter_by(game_code=game_code).first()
    player = Player.query.filter_by(name=player_name, game_code=game_code).first()

    if game and player:
        # Get the list of prompt IDs as a list of integers
        prompt_id_list = [int(id_str) for id_str in game.prompt_ids.split(',') if id_str]

        # Check if current_round is within the bounds of the prompt_id_list
        if 0 <= game.current_round - 1 < len(prompt_id_list):
            current_prompt_id = prompt_id_list[game.current_round - 1]  # -1 because list is 0-indexed

            # Save the player response
            new_response = PlayerResponse(player_id=player.id, prompt_id=current_prompt_id, response=response_text, round_number=game.current_round)
            db.session.add(new_response)
            db.session.commit()
            return jsonify({'success': 'Response submitted'}), 200
        else:
            return jsonify({'error': 'Invalid round number or no prompts left'}), 400

    return jsonify({'error': 'Game or player not found'}), 404

#route for checking if all players have submitted their responses


@app.route('/check_round_complete/<game_code>')
def check_round_complete(game_code):
    game = Game.query.filter_by(game_code=game_code).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    number_of_players = Player.query.filter_by(game_code=game_code).count()
    responses = PlayerResponse.query.join(Player, Player.id == PlayerResponse.player_id) \
                                     .filter(Player.game_code == game_code, PlayerResponse.round_number == game.current_round) \
                                     .count()

    if responses >= number_of_players:
        game.round_complete = True  # Set round completion flag
        db.session.commit()
        return jsonify({'round_complete': True})
    else:
        return jsonify({'round_complete': False})



@app.route('/get_responses/<game_code>')
def get_responses(game_code):
    game = Game.query.filter_by(game_code=game_code).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    # Parse the prompt_ids to get a list of prompt IDs
    prompt_id_list = [int(id_str) for id_str in game.prompt_ids.split(',') if id_str.strip()]
    
    # Get the current prompt ID based on the current round index
    current_prompt_id = prompt_id_list[game.current_round - 1] if (0 <= game.current_round - 1 < len(prompt_id_list)) else None

    if current_prompt_id is not None:
        current_prompt = Prompt.query.get(current_prompt_id)
        ai_response = current_prompt.ai_response if current_prompt else None
    else:
        ai_response = None

    player_responses = PlayerResponse.query.join(Player).filter(
        Player.game_code == game_code,
        PlayerResponse.round_number == game.current_round
    ).all()
    
    # Format the responses for sending to the client
    formatted_responses = [{'player_id': response.player_id, 'text': response.response} for response in player_responses]
    if ai_response:
        formatted_responses.append({'player_id': 'ai', 'text': ai_response})

    return jsonify(formatted_responses)

def get_responses_for_round(game_code, round_number):
    game = Game.query.filter_by(game_code=game_code).first()
    if not game:
        return []

    # Get the list of prompt IDs as a list of integers
    prompt_id_list = [int(id_str) for id_str in game.prompt_ids.split(',') if id_str.strip()]

    # Get the current prompt ID based on the round number
    current_prompt_id = prompt_id_list[round_number - 1] if (0 <= round_number - 1 < len(prompt_id_list)) else None

    if current_prompt_id is None:
        return []

    # Get all player responses for the current round
    player_responses = PlayerResponse.query.join(Player).filter(
        Player.game_code == game_code,
        PlayerResponse.round_number == round_number,
        PlayerResponse.prompt_id == current_prompt_id
    ).all()

    # Get the AI response for the current prompt
    ai_response = Prompt.query.get(current_prompt_id).ai_response if current_prompt_id else None

    # Format the responses for display
    formatted_responses = [{'player_id': response.player_id, 'text': response.response} for response in player_responses]
    if ai_response:
        formatted_responses.append({'player_id': 'ai', 'text': ai_response})

    return formatted_responses


#redirecting to options page after each round
@app.route('/display_options/<game_code>')
def display_options(game_code):
    game = Game.query.filter_by(game_code=game_code).first()
    if not game:
        return "Game not found", 404

    if game.game_status == 'in_progress':
        options = get_responses_for_round(game_code, game.current_round)
        return render_template('display_options.html', round=game.current_round, options=options, game_code=game_code)
    else:
        return "Round not complete or game not in progress", 400


@app.route('/submit_choice/<game_code>', methods=['POST'])
def submit_choice(game_code):
    data = request.json
    selected_response_id = data['response']
    print({'selected_response_id': selected_response_id})
    player_id = session.get('player_id')
    
    game = Game.query.filter_by(game_code=game_code).first()
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    if selected_response_id == 'ai':
        # Handle AI response
        print("congrats!")
        #increment the score of the player
        player = Player.query.get(player_id)
        player.score += 1

    else:

    # Create a new PlayerChoice entry
        new_choice = PlayerChoice(
            player_id=player_id,
            game_code=game_code,
            round_number=game.current_round,
            response_id=selected_response_id
        )
        db.session.add(new_choice)
        db.session.commit()

    # Check if all players have made a choice before advancing
    total_players = Player.query.filter_by(game_code=game_code).count()
    choices_made = PlayerChoice.query.filter_by(
        game_code=game_code,
        round_number=game.current_round
    ).count()

    if choices_made >= total_players:
        # All players have made their choice, advance the round
        game.current_round += 1
        db.session.commit()

    return jsonify({'success': 'Choice submitted'}), 200



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        populate_prompts()  # Call this function to populate the prompts table
        app.run(debug=True)