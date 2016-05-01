import random
from datetime import date

import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb

import game as gm

### User Related Classes and Messages

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    total_games = ndb.FloatProperty(default=.1)
    total_score = ndb.FloatProperty(default=.1)
    avg_score = ndb.FloatProperty(default = 0)

    def to_form(self):
        form = UserForm()
        form.name = self.name
        form.urlsafe_key = self.key.urlsafe()
        form.total_games = self.total_games - .1
        form.total_score = self.total_score - .1
        form.avg_score = round(self.avg_score)
        return form

    def calc_score(self):
        avg_score = self.total_score / self.total_games
        return avg_score

### Game Related Classes and Messages

class Game(ndb.Model):
    """Game object"""
    board = ndb.StringProperty(repeated=True)
    boardState = ndb.StringProperty(repeated=True)
    guesses = ndb.IntegerProperty(required=True, default=0)
    cards = ndb.IntegerProperty(required=True, default=52)
    status = ndb.StringProperty(required=True, default='In Progress')
    user = ndb.KeyProperty(required=True, kind='User')

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
                    user=user
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
        form.status = self.status
        form.message = message
        form.boardState = self.boardState
        form.board = self.board
        return form

    def to_mini_form(self):
        """Return a MiniGameForm representation of a Game"""
        form = MiniGameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.guesses = self.guesses
        form.cards = self.cards
        form.status = self.status
        return form

    def win_game(self):
        # Add the game to the score 'board'
        total_score = round((self.cards ** 4) / self.guesses)
        score = Score(user=self.user, date=date.today(), cards=self.cards, 
                      guesses=self.guesses, score=total_score)
        score.put()
        user = self.user.get()
        user.total_score += total_score
        user.put()
        user.avg_score = user.calc_score()
        user.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    cards = ndb.IntegerProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    score = ndb.FloatProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         date=str(self.date), 
                         cards=self.cards,
                         guesses=self.guesses,
                         score=self.score)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1)
    guesses = messages.IntegerField(2)
    status = messages.StringField(3)
    message = messages.StringField(4)
    boardState = messages.StringField(5, repeated=True)
    user_name = messages.StringField(6)
    cards = messages.IntegerField(7)
    board = messages.StringField(8, repeated=True)


class MiniGameForm(messages.Message):
    """Abbreviated Game Form for reporting, rather than play purposes"""
    urlsafe_key = messages.StringField(1)
    guesses = messages.IntegerField(2)
    cards = messages.IntegerField(3)
    status = messages.StringField(4)


class MiniGameForms(messages.Message):
    """Hold a list of abbreviated Game Forms"""
    games = messages.MessageField(MiniGameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    cards = messages.IntegerField(2, default=52)


## Guess Message Classes

class FlipCardForm(messages.Message):
    """Form to allow players to guess a card by supplying its index"""
    flippedCard = messages.IntegerField(1)


class CardForm(messages.Message):
    """Form to respond to player guess by revealing a card value"""
    cardValue = messages.StringField(1)


class MakeGuessForm(messages.Message):
    """Used to make a move in an existing game"""
    card1 = messages.IntegerField(1, required=True)
    card2 = messages.IntegerField(2, required=True)


## Score Message Classes

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
    total_games = messages.FloatField(3)
    total_score = messages.FloatField(4)
    avg_score = messages.FloatField(5)


class UserForms(messages.Message):
    """Return information mulitiple users for ranking"""
    users = messages.MessageField(UserForm, 1, repeated=True)


### Assorted Message Classes

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
