import random
from datetime import date

import httplib
import endpoints
from protorpc import messages
from google.appengine.ext import ndb


### User Related Classes and Messages

class Player(ndb.Model):
    """Player object"""
    displayName = ndb.StringProperty()
    mainEmail = ndb.StringProperty()


class PlayerForm(messages.Message):
    """ProfileForm -- Profile outbound form message"""
    displayName = messages.StringField(1)
    mainEmail = messages.StringField(2)


class PlayerUpdateForm(messages.Message):
	"""Form to allow users to change their display name"""
	displayName = messages.StringField(1)