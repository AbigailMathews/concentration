import random
from datetime import date

import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb

import game as gm

### User Related Classes and Messages

class Player(ndb.Model):
    """Player object"""
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()
    gamesPlayed = ndb.IntegerProperty()
    totalMoves = ndb.IntegerProperty()


class PlayerForm(messages.Message):
    """ProfileForm -- Profile outbound form message"""
    displayName = messages.StringField(1)
    mainEmail = messages.StringField(2)
    gamesPlayed = messages.IntegerField(3)
    totalMoves = messages.IntegerField(4)


class PlayerUpdateForm(messages.Message):
	"""Form to allow users to change their display name"""
	displayName = messages.StringField(1)


### Game Related Classes and Messages

class Game(ndb.Model):
    """Game object"""
    board = ndb.StringProperty(repeated=True)
    boardState = ndb.StringProperty(repeated=True)
    guesses = ndb.IntegerProperty(required=True, default=0)
    cards = ndb.IntegerProperty(required=True, default=52)
    game_over = ndb.BooleanProperty(required=True, default=False)
    playerId = ndb.StringProperty()
    websafeKey = ndb.KeyProperty()

    @classmethod
    def new_game(self, playerId, key, cards=52):
        """Creates and returns a new game"""
        if cards < 8 or cards > 52 or cards % 2 != 0:
            raise ValueError('Cards dealt must be an even number between 8 and 52')
        newGame = Game(board=gm.constructBoard(cards),
                    boardState=gm.initialBoardState(cards),
                    guesses=0,
                    cards=cards,
                    game_over=False,
                    playerId=playerId,
                    websafeKey=key,
                    )
        newGame.put()
        return newGame

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.guesses = self.guesses
        form.cards = self.cards
        form.game_over = self.game_over
        form.message = message
        form.boardState = self.boardState
        form.board = self.board
        return form


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1)
    guesses = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4)
    boardState = messages.StringField(5, repeated=True)
    user_name = messages.StringField(6)
    cards = messages.IntegerField(7)
    board = messages.StringField(8, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    cards = messages.IntegerField(1, default=52)


### Assorted Message Classes

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
