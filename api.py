
from datetime import datetime

import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb

from models import Player, PlayerForm, PlayerUpdateForm
from models import Game, NewGameForm, GameForm
from models import FlipCardForm, CardForm
from models import StringMessage
from utils import get_by_urlsafe
from utils2 import getUserId

from settings import WEB_CLIENT_ID
EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

import game as gm


GAME_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage, websafeKey=messages.StringField(1),
)


@endpoints.api( name='concentration',
                version='v1',
                allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID],
                scopes=[EMAIL_SCOPE])
class ConcentrationApi(remote.Service):
    """Concentration Game API v0.1"""

# - - - User handling
#    @endpoints.method(request_message=USER_REQUEST,
#                      response_message=StringMessage,
#                      path='user',
#                      name='create_user',
#                      http_method='POST')
#    def create_player(self, request):
#        """Create a User"""
#        if User.query(User.name == request.user_name).get():
#            raise endpoints.ConflictException(
#                    'A User with that name already exists!')
#        user = User(name=request.user_name, email=request.email)
#        user.put()
#        return StringMessage(message='User {} created!'.format(
#                request.user_name))


    def _copyPlayerToForm(self, player):
        """Copy relevant fields from Player to its Form."""
        pf = PlayerForm()
        for field in pf.all_fields():
            if hasattr(player, field.name):
                setattr(pf, field.name, getattr(player, field.name))
        pf.check_initialized()
        return pf


    def _getPlayerFromUser(self):
        """Return Player from datastore, creating new Player if non-existent."""
        ## Use Oauth to authorize the user
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')
        
        user_id = getUserId(user)
        p_key = ndb.Key(Player, user_id)
        
        player = p_key.get()

        if not player:
            player = Player(
                key = p_key,
                displayName = user.nickname(), 
                mainEmail= user.email(),
                gamesPlayed = 0,
                totalMoves = 0,
            )
            player.put()
            
        return player     # return Profile


    def _doPlayer(self, save_request=None):
        """Return Player, possibly updating it first."""
        # get user Profile
        player = self._getPlayerFromUser()

        # if saveProfile(), process user-modifiable fields
        if save_request:
            val = getattr(save_request, 'displayName')
            if val:
                setattr(player, 'displayName', str(val))
            player.put()
        # return ProfileForm
        return self._copyPlayerToForm(player)


    ## USER METHODS

    @endpoints.method(message_types.VoidMessage, PlayerForm,
            path='get_player', http_method='GET', name='getPlayer')
    def getPlayer(self, request):
        """Return Player information"""
        return self._doPlayer()


    @endpoints.method(PlayerUpdateForm, PlayerForm,
            path='update_player', http_method='POST', name='updatePlayer')
    def saveProfile(self, request):
        """Update & return player information"""
        return self._doPlayer(request)


    ## GAME METHODS

    def _sendGameToForm(self, game, player):
        """Display the current state of a game"""
        gf = GameForm()
        for field in gf.all_fields():
            if hasattr(game, field.name):
                setattr(gf, field.name, getattr(game, field.name))
            #elif field.name == "websafeKey":
            #    setattr(gf, field.name, game.key.urlsafe())
        if player:
            setattr(gf, 'user_name', player.displayName)
        gf.check_initialized()
        return gf

    def _createGame(self, request):
        """Create a new game"""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization Required')
        user_id = getUserId(user)

        ## Set the player as the parent for the Game
        # get player key
        p_key = ndb.Key(Player, user_id)

        # create a new game id with the player id as the parent
        g_id = Game.allocate_ids(size=1, parent=p_key)[0]
        # make the game key
        g_key = ndb.Key(Game, g_id, parent=p_key)

        # Copy information from the new game form and create Game instance
        cards = getattr(request, 'cards')
        newGame = {}

        newGame['cards'] = cards
        newGame['key'] = g_key
        newGame['playerId'] = user_id

        thisGame = Game.new_game(**newGame)
        thisGame.put()

        player = p_key.get()
        return self._sendGameToForm(thisGame, player)

    def _showCard(self, request):
        """Flip a card over and reveal it's value"""
        guessedCard = getattr(request, 'flippedCard')
        board = getattr(request, 'board')
        return gm.turnCard(guessedCard, board)


    @endpoints.method(GAME_GET_REQUEST, GameForm,
            path='game/show/{websafeKey}', http_method='GET', name='showGame')
    def showGame(self, request):
        """Return the board state for the specified game"""
        game = ndb.Key(urlsafe=request.websafeKey)
        if not game:
            raise endpoints.NotFoundException(
                'No game found with key: %s' % request.websafeKey)
        player = game.parent().get()
        return self._sendGameToForm(game, player)


    @endpoints.method(NewGameForm, GameForm,
            path='game/new', http_method='POST', name='newGame')
    def newGame(self, request):
        """Create a new game"""
        return self._createGame(request)

    @endpoints.method(FlipCardForm, CardForm,
            path='game/flip', http_method='POST', name='flipCard')
    def flipCard(self, request):
        """Responds to a guessed card by revealing a card's value"""
        return self._showCard(request)

api = endpoints.api_server([ConcentrationApi])