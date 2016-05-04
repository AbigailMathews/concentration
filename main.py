#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""

import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import ConcentrationApi

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to Users with incomplete games.
        Called every 12 hours using a cron job"""
        app_id = app_identity.get_application_id()
        # Find all in-progress games
        games = Game.query(Game.status == 'In Progress')
        # Make a list of all names of users with in-progress games
        users = []
        for game in games:
            users.append(game.user.get().name)
        
        # Deduplicate the list of users, only sending 1 email to each user
        de_dup_users = []
        for u in users:
            if u not in de_dup_users:
                de_dup_users.append(u)

        for username in de_dup_users:
            q = User.query(User.name == username)
            user = q.get()
            if user.email != None:
                subject = 'This is a reminder!'
                body = 'Hello {}, You have unfinished Concentration games!'.format(user.name)
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                               user.email,
                               subject,
                               body)


class UpdateTopScore(webapp2.RequestHandler):
    def post(self):
        """Update top score announcement in memcache."""
        ConcentrationApi._cache_high_score()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_high_score', UpdateTopScore),
], debug=True)
