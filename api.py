
from datetime import datetime

import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb

from models import User
from models import Game, NewGameForm, GameForm
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


### ### CONCENTRATION API ### ###
@endpoints.api( name='concentration',
                version='v1',
                allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
                scopes=[EMAIL_SCOPE])
class ConcentrationApi(remote.Service):
    """Concentration Game API v0.1"""

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



    ## GAME METHODS

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
            path='game/{urlsafe_game_key}', http_method='GET', name='showGame')
    def showGame(self, request):
        """Return the board state for the specified game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('No game found!')
        else:
            return game.to_form('Make your move!')


    ## GAME METHODS -- CARD ACTIONS


    @endpoints.method(FLIP_CARD_REQUEST, CardForm,
            path='game/{urlsafe_game_key}/flip', http_method='POST', name='flipCard')
    def flipCard(self, request):
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
            path='game/{urlsafe_game_key}/move', http_method='POST', name='makeMove')
    def makeMove(self, request):
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


api = endpoints.api_server([ConcentrationApi])
