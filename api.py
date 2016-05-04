
"""
CONCENTRATION GAME API

api.py -- Contains ConcentrationApi, with numerous functions
for communicating User, Game, and Score related information
to and from users.
"""

# Imports and Setup
from datetime import datetime

import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb

from models import User, UserForm, UserForms
from models import Game, NewGameForm, GameForm
from models import MiniGameForm, MiniGameForms
from models import HistoryForm
from models import FlipCardForm, CardForm, MakeGuessForm, HintForm
from models import Score, ScoreForm, ScoreForms
from models import StringMessage
from utils import get_by_urlsafe

from settings import WEB_CLIENT_ID
EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# Game Logic
import game as gm

# Various Request Containers
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)

GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1))

FLIP_CARD_REQUEST = endpoints.ResourceContainer(
        queryCard=messages.IntegerField(1),
        urlsafe_game_key=messages.StringField(2))

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
        MakeGuessForm,
        urlsafe_game_key=messages.StringField(1))

USER_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(1),
        email=messages.StringField(2))

USER_INFO_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(1))

MEMCACHE_HIGH_SCORE = 'TOP_SCORE'


### ### CONCENTRATION API ### ###
@endpoints.api( name='concentration',
                version='v1',
                allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
                scopes=[EMAIL_SCOPE])
class ConcentrationApi(remote.Service):
    """Concentration Game API v0.1"""


    ## USER METHODS

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        # Check that the username is not in use
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        # Create a new user, send a confirmation message
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))


    @endpoints.method(request_message=USER_INFO_REQUEST,
                      response_message=UserForm,
                      path='user/info',
                      name='user_info',
                      http_method='GET')
    def user_info(self, request):
        """Get stats about a user"""
        user = User.query(User.name == request.user_name).get()
        # Check that user exists
        if not user:
            raise endpoints.NotFoundException('No such user.')
        else:
            # Return a summary form with user information
            return user.to_form()


    @endpoints.method(request_message=USER_INFO_REQUEST,
                      response_message=MiniGameForms,
                      path='user/all',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return a list of all of a User's games"""
        user = User.query(User.name == request.user_name).get()
        # Check that user exists
        if not user:
            raise endpoints.NotFoundException('No such user.')
        else:
            # Fetch all games
            q = Game.query(Game.user == user.key)
            games = q.fetch()
            # Return a set of simplified game info forms
            return MiniGameForms(
                games=[g.to_mini_form() for g in games]
            )


    @endpoints.method(request_message=USER_INFO_REQUEST,
                      response_message=MiniGameForms,
                      path='user/current',
                      name='get_current_games',
                      http_method='GET')
    def get_current_games(self, request):
        """Return a list of all of a User's active (in-progress) games"""
        user = User.query(User.name == request.user_name).get()
        # Check that user exists
        if not user:
            raise endpoints.NotFoundException('No such user.')
        else:
            # Fetch all games
            q = Game.query(Game.user == user.key).filter(Game.status == 'In Progress')
            games = q.fetch()
            # Return a set of simplified game info forms
            return MiniGameForms(
                games=[g.to_mini_form() for g in games]
            )


    ## GAME METHODS

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='PUT')
    def cancel_game(self, request):
        """Cancel an in-progress (but not completed) game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Make sure we can cancel the specified game
        if not game:
            raise endpoints.NotFoundException("Can't cancel! Game doesn't exist!")
        elif game.status == 'Won':
            raise endpoints.BadRequestException("Can't cancel a game that's been won!")
        elif game.status == 'Canceled':
            raise endpoints.BadRequestException("You've already cancelled that game.")
        else:
            # Cancel the game and return a confirmation
            game.status = 'Canceled'
            game.put()
            return StringMessage(message='Game canceled.')


    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        # Make sure user exists
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            # Create the new Game
            game = Game.new_game(user.key, request.cards)
        except:
            raise endpoints.BadRequestException('Request Failed')
        # Increment total games by 1, but if it's initially zero, deal
        # with the error that gets thrown
        try:
            user.total_games += 1
        except TypeError:
            user.total_games = 1
        user.put()
        # Send the new game back to the user, ready to play
        return game.to_form('Let the Guessing Begin!')


    @endpoints.method(request_message=GET_GAME_REQUEST, 
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}', 
                      http_method='GET', 
                      name='show_game')
    def show_game(self, request):
        """Return the board state for the specified game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Check that the game exists
        if not game:
            raise endpoints.NotFoundException('No game found!')
        else:
            # Return the game information, prompting user to make a move
            return game.to_form('Make your move!')


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=HistoryForm,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Show the history of moves for a game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Check that the game exists
        if not game:
            raise endpoints.NotFoundException('No such game!')
        else:
            # Return a game summary and history of moves
            return game.to_history_form()


    ## GAME METHODS -- CARD ACTIONS

    @endpoints.method(request_message=FLIP_CARD_REQUEST, 
                      response_message=CardForm,
                      path='game/{urlsafe_game_key}/flip', 
                      http_method='GET', 
                      name='flip_card')
    def flip_card(self, request):
        """Responds to a guessed card by revealing a card's value"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Check that the game exists
        if not game:
            raise endpoints.NotFoundException('No game found!')
        elif game.status != 'In Progress':
            raise endpoints.BadRequestException('Not an active game, guesses no longer allowed')
        else:
            # Retrieve the board and return the specified card's value
            board = game.board
            guessedCard = getattr(request, 'queryCard')
            result = gm.turnCard(guessedCard, board)
            return CardForm(cardValue=result)


    @endpoints.method(request_message=MAKE_MOVE_REQUEST, 
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}/move', 
                      http_method='POST', 
                      name='make_move')
    def make_move(self, request):
        """Accepts two cards and reveals whether they match"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Make sure the game exists and is in progress
        if not game:
            raise endpoints.NotFoundException('No game found!')
        elif game.status != 'In Progress':
            raise endpoints.BadRequestException('Not an active game, moves no longer allowed')
        else:
            # Retrieve the board and played cards
            board = game.board
            displayBoard = game.boardState
            card1 = getattr(request, 'card1')
            card2 = getattr(request, 'card2')
            if card1 == card2:
                # The user is guessing the same card twice
                raise endpoints.BadRequestException("You can't pick the same card twice!")
            else:
                # Evaluate the result of the move and update game information
                message, resultBoard = gm.compareCards(card1, card2, board, displayBoard)
                game.guesses += 1
                game.boardState = resultBoard
                # Check to see if the game has now been won
                if gm.isGameWon(game.boardState):
                    message += ' Congratulations -- You win! All cards matched!'
                    game.status = 'Won'
                    game.win_game()

                # Append the current move to the game history
                game.history.append('guess: {0} result: {1}'.format([card1, card2], message))
                
                game.put()
                return game.to_form(message=message)


    @endpoints.method(request_message=FLIP_CARD_REQUEST,
                      response_message=HintForm,
                      path='game/{urlsafe_game_key}/hint',
                      http_method='GET',
                      name='get_hint')
    def get_hint(self, request):
        """Gives a hint for a card that matches a selected card"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        # Check that the game exists:
        if not game:
            raise endpoints.NotFoundException('No game found!')
        elif game.status != 'In Progress':
            raise endpoints.BadRequestException('Not an active game, no hints or moves permitted')
        else:
            # Get the card and generate a hint
            selectedCard = getattr(request, 'queryCard')
            hint = gm.giveHint(selectedCard, game.board)
            return HintForm(hint=hint)

    ## SCORE METHODS

    @endpoints.method(request_message=message_types.VoidMessage,
                      response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])


    @endpoints.method(request_message=USER_INFO_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        # Make sure user exists
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        # Retrieve and return all relevant scores
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(request_message=message_types.VoidMessage,
                      response_message=ScoreForms,
                      path='scores/high',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Generate a list of high scores"""
        q = Score.query().order(-Score.score)
        # Just take the top ten scores
        q.fetch(10)
        return ScoreForms(items=[score.to_form() for score in q])


    @endpoints.method(request_message=message_types.VoidMessage,
                      response_message=UserForms,
                      path='users/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Return the players, ranked by average score"""
        q = User.query().order(-User.avg_score)
        # Return all players, ranked
        q.fetch()
        return UserForms(users=[user.to_form() for user in q])


    @endpoints.method(request_message=message_types.VoidMessage,
                      response_message=StringMessage,
                      path='/scores/top',
                      name='get_top_score',
                      http_method='GET')
    def get_top_score(self, request):
        """Get the cached highest score"""
        return StringMessage(message=memcache.get(MEMCACHE_HIGH_SCORE) or '')


    @staticmethod
    def _cache_high_score():
        """Populates memcache with a high score announcement"""
        q = Score.query().order(-Score.score)
        q.get()
        if q:
            # Retrieve the high score information, if available
            user = q.user_name
            score = q.score
            date = q.date
            memcache.set(MEMCACHE_HIGH_SCORE, 
                         '''Congratulations to {0}, with the current high 
                         score of {1}, set on {2}!'''.format(user, score, date))


api = endpoints.api_server([ConcentrationApi])
