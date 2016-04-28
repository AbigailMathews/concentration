
from datetime import datetime

import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb

from models import User, UserForm
from models import Game, NewGameForm, GameForm
from models import MiniGameForm, MiniGameForms
from models import FlipCardForm, CardForm, MakeGuessForm
from models import StringMessage
from utils import get_by_urlsafe

from settings import WEB_CLIENT_ID
EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# Game Logic
import game as gm


NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)

GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)

FLIP_CARD_REQUEST = endpoints.ResourceContainer(
        FlipCardForm, 
        urlsafe_game_key=messages.StringField(1),)

MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
        MakeGuessForm,
        urlsafe_game_key=messages.StringField(1),)

USER_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(1),
        email=messages.StringField(2))

USER_INFO_REQUEST = endpoints.ResourceContainer(
        user_name=messages.StringField(1))


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
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
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
        if not user:
            raise endpoints.NotFoundException('No such user.')
        else:
            return user.to_form()


    @endpoints.method(request_message=USER_INFO_REQUEST,
                      response_message=MiniGameForms,
                      path='user/current',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return a list of all of a User's active games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('No such user.')
        else:
            q = Game.query(Game.user == user.key)
            games = q.fetch()
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
        """Cancel and in-progress (but not completed) game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException("Can't cancel! Game doesn't exist!")
        elif game.status == 'Won':
            raise endpoints.BadRequestException("Can't cancel a game that's been won!")
        elif game.status == 'Canceled':
            raise endpoints.BadRequestException("You've already cancelled that game.")
        else:
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
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.cards)
        except:
            raise endpoints.BadRequestException('Request Failed')
        return game.to_form('Let the Guessing Begin!')


    @endpoints.method(request_message=GET_GAME_REQUEST, response_message=GameForm,
            path='game/{urlsafe_game_key}', http_method='GET', name='show_game')
    def show_game(self, request):
        """Return the board state for the specified game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('No game found!')
        else:
            return game.to_form('Make your move!')


#    @endpoints.method(request_message=message_types.VoidMessage,
#                      response_message=GameHistoryForm,
#                      path='game/{urlsafe_game_key}/history',
#                      name='get_game_history',
#                      http_method='GET')
#    def get_game_history(self, request):
#        """Show the history of moves for a game"""


    ## GAME METHODS -- CARD ACTIONS


    @endpoints.method(FLIP_CARD_REQUEST, CardForm,
            path='game/{urlsafe_game_key}/flip', http_method='POST', name='flip_card')
    def flip_card(self, request):
        """Responds to a guessed card by revealing a card's value"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('No game found!')
        else:
            board = game.board
            guessedCard = getattr(request, 'flippedCard')
            result = gm.turnCard(guessedCard, board)
            return CardForm(cardValue=result)

    @endpoints.method(MAKE_MOVE_REQUEST, GameForm,
            path='game/{urlsafe_game_key}/move', http_method='POST', name='make_move')
    def make_move(self, request):
        """Accepts two cards and reveals whether they match"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('No game found!')
        else:
            board = game.board
            displayBoard = game.boardState
            card1 = getattr(request, 'card1')
            card2 = getattr(request, 'card2')
            if card1 == card2:
                # The user is guessing the same card twice
                raise endpoints.BadRequestException("You can't pick the same card twice!")
            else:
                message, resultBoard = gm.compareCards(card1, card2, board, displayBoard)
                game.guesses += 1
                game.boardState = resultBoard
                game.put()
                return game.to_form(message=message)


    ## SCORE METHODS

#    @endpoints.method(response_message=ScoreForms,
#                      path='scores',
#                      name='get_scores',
#                      http_method='GET')
#    def get_scores(self, request):
#        """Return all scores"""
#        return ScoreForms(items=[score.to_form() for score in Score.query()])


#    @endpoints.method(request_message=USER_REQUEST,
#                      response_message=ScoreForms,
#                      path='scores/user/{user_name}',
#                      name='get_user_scores',
#                      http_method='GET')
#    def get_user_scores(self, request):
#        """Returns all of an individual User's scores"""
#        user = User.query(User.name == request.user_name).get()
#        if not user:
#            raise endpoints.NotFoundException(
#                    'A User with that name does not exist!')
#        scores = Score.query(Score.user == user.key)
#        return ScoreForms(items=[score.to_form() for score in scores])


#    @endpoints.method(request_message=message_types.VoidMessage,
#                      response_message=ScoreForm,
#                      path='scores/high_scores',
#                      name='get_high_scores',
#                      http_method='GET')
#    def cancel_game(self, request):
#        """Generate a list of high scores"""


#    @endpoints.method(request_message=message_types.VoidMessage,
#                      response_message=UserRankForm,
#                      path='users/rankings',
#                      name='get_user_rankings',
#                      http_method='GET')
#    def get_user_rankings(self, request):
#        """Return a player's performance statistics"""


api = endpoints.api_server([ConcentrationApi])
