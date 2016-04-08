"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

import game


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    board = ndb.StringProperty(required=True, repeated=True)
    boardState = ndb.StringProperty(required=True, repeated=True)
    guesses = ndb.IntegerProperty(required=True, default=0)
    cards = ndb.IntegerProperty(required=True, default=52)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls, user, cards=52):
        """Creates and returns a new game"""
        if cards < 8 or cards > 52 or cards % 2 != 0:
            raise ValueError('Cards dealt must be an even number between 8 and 52')
        game = Game(user=user,
                    board=game.constructBoard(self.cards),
                    boardState=game.initDisplayBoard(self.cards),
                    guesses=0,
                    cards=cards,
                    game_over=False,
                    )
        game.put()
        return game

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
        return form

#    def end_game(self, won=False):
#        """Ends the game - if won is True, the player won. - if won is False,
#       the player lost."""
#        self.game_over = True
#        self.put()
#        # Add the game to the score 'board'
#        score = Score(user=self.user, date=date.today(), won=won,
#                      guesses=self.attempts_allowed - self.attempts_remaining)
#       score.put()

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    guesses = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4)
    boardState = messages.StringField(5, required=True, repeated=True)
    user_name = messages.StringField(6, required=True)
    cards = messages.IntegerField(7)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    cards = messages.IntegerField(2, default=52)


#class Score(ndb.Model):
#    """Score object"""
#    user = ndb.KeyProperty(required=True, kind='User')
#    date = ndb.DateProperty(required=True)
#    won = ndb.BooleanProperty(required=True)
#    guesses = ndb.IntegerProperty(required=True)
#    cards = ndb.IntegerProperty(required=True)
#    features = ndb.StringProperty()

#    def to_form(self):
#        return ScoreForm(user_name=self.user.get().name, won=self.won,
#                         date=str(self.date), guesses=self.guesses,
#                         cards=self.cards, features=self.features)


#class MakeMoveForm(messages.Message):
#    """Used to make a move in an existing game"""
#    guess = messages.IntegerField(1, required=True)


#class ScoreForm(messages.Message):
#    """ScoreForm for outbound Score information"""
#    user_name = messages.StringField(1, required=True)
#    date = messages.StringField(2, required=True)
#   won = messages.BooleanField(3, required=True)
#    guesses = messages.IntegerField(4, required=True)


#class ScoreForms(messages.Message):
#    """Return multiple ScoreForms"""
#    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
