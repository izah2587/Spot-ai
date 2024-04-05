class Player:
    def __init__(self, id, name, game_code):
        self.id = id
        self.name = name
        self.game_code = game_code
        self.responses = []
        self.score = 0

    def update_score(self, score):
        self.score += score

    def add_response(self, response):
        self.responses.append(response)

    def get_latest_response(self):
        if self.responses:
            return self.responses[-1]
        return None

class Game:
    def __init__(self, game_code, game_status, created_at):
        self.game_id = game_code
        self.game_status = game_status
        self.created_at = created_at
        self.players = []  # List to store Player objects
        self.prompts = []  # List to store prompts for each round
        self.current_round = 0
        self.ai_response = None

    def add_player(self, player):
        self.players.append(player)

    def set_prompt(self, prompt, ai_response):
        self.prompts.append(prompt)
        self.ai_response = ai_response

    def get_current_prompt(self):
        return self.prompts[self.current_round] if self.current_round < len(self.prompts) else None

    def advance_round(self):
        self.current_round += 1

    def display_responses(self):
        for player in self.players:
            print(f"{player.name}: {player.get_last_response()}")

