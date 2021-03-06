"""models.py - Contains class definitions for Datastore entities
used by the Concentration Game API. Definitions for User, Game, and
Score classes, with associated methods. Additionally, contains 
definitions for Forms used in transmitting messages to users."""

### Imports

import random
import pickle
from datetime import date

import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb

### Import game logic

import game as gm

### User Related Classes and Methods

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    total_games = ndb.IntegerProperty(default = 0)
    total_score = ndb.IntegerProperty(default = 0)
    avg_score = ndb.FloatProperty(default = 0)

    def to_form(self):
        """Returns a UserForm representation of a User"""
        form = UserForm()
        form.name = self.name
        form.urlsafe_key = self.key.urlsafe()
        form.total_games = self.total_games
        form.total_score = self.total_score
        form.avg_score = round(self.avg_score)
        return form

    def calc_score(self):
        """Calculate the player's average score -- to be 
        called whenever a new game is won"""
        avg_score = self.total_score / self.total_games
        return avg_score

### Game Related Class and Methods

class Game(ndb.Model):
    """Game object"""
    board = ndb.StringProperty(repeated=True)
    boardState = ndb.StringProperty(repeated=True)
    guesses = ndb.IntegerProperty(required=True, default=0)
    cards = ndb.IntegerProperty(required=True, default=52)
    status = ndb.StringProperty(required=True, default='In Progress')
    user = ndb.KeyProperty(required=True, kind='User')
    history = ndb.PickleProperty(repeated=True)
    score = ndb.FloatProperty()

    @classmethod
    def new_game(self, user, cards=52):
        """Creates and returns a new game"""
        if cards < 8 or cards > 52 or cards % 2 != 0:
            raise ValueError('Cards dealt must be an even number between 8 and 52')
        newGame = Game(board=gm.constructBoard(cards),
                    boardState=gm.initialBoardState(cards),
                    guesses=0,
                    cards=cards,
                    status='In Progress',
                    user=user)
        newGame.put()
        return newGame

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.guesses = self.guesses
        form.cards = self.cards
        form.status = self.status
        form.message = message
        form.boardState = self.boardState
        return form

    def to_mini_form(self):
        """Return a MiniGameForm representation of a Game"""
        form = MiniGameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.guesses = self.guesses
        form.cards = self.cards
        form.status = self.status
        return form

    def to_history_form(self):
        """Returns a game history form after a game has been won"""
        form = HistoryForm()
        form.urlsafe_key = self.key.urlsafe()
        form.cards = self.cards
        form.guesses = self.guesses
        form.board = self.board
        form.score = self.score
        form.history = [h for h in self.history]
        return form

    def win_game(self):
        """Updates score and user information once game is won"""
        # Add the game to the score 'board'
        total_score = int(round((self.cards ** 4) / self.guesses))
        self.score = total_score
        self.put()
        score = Score(user=self.user, date=date.today(), cards=self.cards, 
                      guesses=self.guesses, score=total_score)
        score.put()
        user = self.user.get()
        # Add the current score to the user's total score, but handle error
        # if user's current score is 0
        try:
            user.total_score += total_score
        except TypeError:
            user.total_score = total_score
        user.put()
        user.avg_score = user.calc_score()
        user.put()


### Score Class and Methods

class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    cards = ndb.IntegerProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    score = ndb.FloatProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, 
                         cards=self.cards,
                         date=str(self.date), 
                         guesses=self.guesses, 
                         score=self.score)


### Game Forms -- Display

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1)
    guesses = messages.IntegerField(2)
    status = messages.StringField(3)
    message = messages.StringField(4)
    boardState = messages.StringField(5, repeated=True)
    user_name = messages.StringField(6)
    cards = messages.IntegerField(7)


class MiniGameForm(messages.Message):
    """Abbreviated Game Form for reporting, rather than play purposes"""
    urlsafe_key = messages.StringField(1)
    guesses = messages.IntegerField(2)
    cards = messages.IntegerField(3)
    status = messages.StringField(4)

class HistoryForm(messages.Message):
    """Form to display a game history, as well as score information"""
    urlsafe_key = messages.StringField(1)
    cards = messages.IntegerField(2)
    guesses = messages.IntegerField(3)
    board = messages.StringField(4, repeated=True)
    score = messages.FloatField(5)
    history = messages.StringField(6, repeated=True)


class MiniGameForms(messages.Message):
    """Hold a list of abbreviated Game Forms"""
    games = messages.MessageField(MiniGameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    cards = messages.IntegerField(2, default=52)


### Gameplay Forms

class FlipCardForm(messages.Message):
    """Form to allow players to guess a card by supplying its index"""
    queryCard = messages.IntegerField(1, required=True)


class CardForm(messages.Message):
    """Form to respond to player guess by revealing a card value"""
    cardValue = messages.StringField(1)


class MakeGuessForm(messages.Message):
    """Used to make a move in an existing game"""
    card1 = messages.IntegerField(1, required=True)
    card2 = messages.IntegerField(2, required=True)


class HintForm(messages.Message):
    """Send the index of a matching card (hint) back to a user"""
    hint = messages.IntegerField(1, required=True)


### Score Forms

class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    cards = messages.IntegerField(3, required=True)
    guesses = messages.IntegerField(4, required=True)
    score = messages.FloatField(5, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


## User and Rankings Message Classes

class UserForm(messages.Message):
    """User detail form"""
    name = messages.StringField(1)
    urlsafe_key = messages.StringField(2)
    total_games = messages.IntegerField(3)
    total_score = messages.IntegerField(4)
    avg_score = messages.FloatField(5)


class UserForms(messages.Message):
    """Return information mulitiple users for ranking"""
    users = messages.MessageField(UserForm, 1, repeated=True)


### Assorted Message Classes

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
