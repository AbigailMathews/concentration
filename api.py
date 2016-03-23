
from datetime import datetime

import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache, taskqueue
from google.appengine.ext import ndb

from models import Player, PlayerForm, PlayerUpdateForm
#from models import StringMessage, NewGameForm, GameForm
from utils import get_by_urlsafe
from utils2 import getUserId

from settings import WEB_CLIENT_ID
EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

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


api = endpoints.api_server([ConcentrationApi])