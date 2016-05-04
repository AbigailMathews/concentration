# Concentration Game API

This Concentration Game API was created as part of the Udacity Fullstack Nanodegree, Design-A-Game Project, and uses Google's App Engine in conjunction with Google Datastore to create a platform agnostic backend.

#### Author: Abigail Mathews
#### Date: May 2016
#### Version: 1.0


## Access:

To launch a new version of this API, with which to explore using the API Explorer, clone this repo to a local directory. Using the Google App Engine Launcher, you may interact with the project on localhost by selecting 'Add Existing Application' and navigating to the local directory where the project files reside. To use the App Explorer via localhost, navigate to [localhost:8080/_ah/api/explorer](localhost:8080/_ah/api/explorer). Note that 8080 is the default port; if you have more than one application running locally, the port for your application may be different. You will also need to modify the first line in app.yaml to reflect the application name you are using.

If you are having difficulties using Explorer over local HTTP, you may have success launching Chrome separately from within the Chrome browser directory as follows:
```chrome.exe --user-data-dir=test --unsafely-treat-insecure-origin-as-secure=http://localhost:8080```
Again, if your application is running on something other than the default port, you will need to alter the above command accordingly.

To launch a new version of this API using Google's architecture, it is necessary to register a new application at the [Google Developers Console](http://console.developers.google.com). Then, using the Google App Engine Launcher, you may deploy the previously cloned files to this new application. Additionally, a settings.py must be included, containing the WEB_CLIENT_ID and WEB_SECRET for the application.

This API is located at [concentration-1259.appspot.com](concentration-1259.appspot.com)


## Game Description:

Concentration (also known as Memory) is a card matching game. Each game contains a set containing between 8 and 52 randomly dealt cards from a standard card deck. The goal of the game is to match every card on the table with another card of the same face-value. During a play turn, a user should be presented with a visual representation of the board, with unmatched cards presented face-down -- this is the game's boardState. The user then selects two cards to play. If the cards match, they are removed from play. If they do not match, their values are revealed and they are returned, face-down, to the gameboard.


This implementation of Concentration allows players to 'flip' a single card before making a move, as well as get a hint that matches a specified card. There is currently no penalty for getting a hint, and hints are not limited in any way by the API -- this should be determined by the front-end implementation.


The user has unlimited opportunities to match cards, but the score is determined by the number of guesses made, as well as the number of cards initially dealt. Once all cards have been matched, the score is calculated and added to the player statistics and the overall score information. Score is calculated as cards^4/guesses.

Typical user/game flow:
1. create_user
2. new_game
3. flip_card, make_move -- where the card specified in flip_card should be used as card1 in make_move
	- optionally, flip_card or get_hint
	
    REPEAT until make_move.message contains 'Congratulations -- You win! All cards matched!'
4. get_game_history

Games can be played by numerous users simulataneously. Additionally, a user may have multiple in-progress games. Games can be retrieved by using the path parameter `urlsafe_game_key`.


## Files Included:
 - api.py: Contains endpoints
 - game.py: Contains game playing logic.
 - models.py: Entity and message definitions including helper methods.
 - main.py: Handlers called by the task queue or cron jobs.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration
 - index.yaml: Index generation (autogenerated)
 - appengine_config.py: Required to use nonstandard packages (in this case pydealer) in App Engine
 - design.txt: Describes design decisions and trade-offs
 - LICENSE.txt: License information
 - README.md: This document


## Endpoints Included:

### User Related Endpoints

- **create_user**
	- description: Create a User. Requires a unique username
	- path: 'user'
	- method: POST
	- parameters: user_name, email(optional)
	- returns: Confirmation message


- **user_info**
	- description: Get stats about a user
	- path: 'user/info'
	- method: GET
	- parameters: USER_INFO_REQUEST(contains: user_name)
	- returns: UserForm, containing name, urlsafe_key, total_games, total_score, avg_score


- **get_all_games**
	- description: Return a list of all of a User's games
	- path: 'user/all'
	- method: GET
	- parameters: USER_INFO_REQUEST(contains: user_name)
	- returns: MiniGameForms, containing urlsafe_key, guesses, cards, status


- **get_user_games**
	- description: Returns a list of a User's active (in-progress) games
	- path: 'user/current'
	- method: GET
	- parameters: USER_INFO_REQUEST(contains: user_name)
	- returns: MiniGameForms, containing urlsafe_key, guesses, cards, status


### Game Creation, Deletion and Information Endpoints

- **new_game**
	- description: Creates new game
	- path: 'game'
	- method: POST
	- parameters: NEW_GAME_REQUEST(contains: NewGameForm[user_name, cards])
	- returns: Confirmation message

- **show_game**
	- description: Return the board state for the specified game
	- path: 'game/{urlsafe_game_key}'
	- method: GET
	- parameters: user_name, email(optional)
	- returns: GameForm, containing urlsafe_key, guesses, status, message, boardState, user_name, cards

- **cancel_game**
	- description: Cancel an in-progress (but not completed) game
	- path: 'game/{urlsafe_game_key}/cancel'
	- method: PUT
	- parameters: GET_GAME_REQUEST(contains: urlsafe_game_key)
	- returns: Confirmation message

- **get_game_history**
	- description: Show the history of moves for a game
	- path: 'game/{urlsafe_game_key}/history'
	- method: GET
	- parameters: GET_GAME_REQUEST(contains: urlsafe_game_key)
	- returns: HistoryForm, containing urlsafe_key, cards, guesses, board, score, history



### Gameplay Related Endpoints

- **flip_card**
	- description: Responds to a guessed ard by revealing a card's value
	- path: 'game/{urlsafe_game_key}/flip'
	- method: GET
	- parameters: FLIP_CARD_REQUEST(contains FlipCardForm[queryCard], urlsafe_game_key)
	- returns: CardForm, containing cardValue

- **make_move**
	- description: Accepts two cards and reveals whether they match
	- path: 'game/{urlsafe_game_key}/move'
	- method: POST
	- parameters: MAKE_MOVE_REQUEST(contains MakeGuessForm[card1, card2], urlsafe_game_key)
	- returns: GameForm, containing urlsafe_key, guesses, status, message, boardState, user_name, cards

- **get_hint**
	- description: Gives a hint for a card that matches a selected card
	- path: 'game/{urlsafe_game_key}/hint'
	- method: GET
	- parameters: FLIP_CARD_REQUEST(contains FlipCardForm[queryCard], urlsafe_game_key)
	- returns: HintForm, containing hint

### Score Related Endpoints

- **get_scores**
	- description: Return all scores
	- path: 'scores'
	- method: GET
	- parameters: VOID
	- returns: ScoreForms, containing multiple ScoreForm, containing user_name, date, cards, guesses, score

- **get_user_scores**
	- description: Returns all of an individual User's scores
	- path: 'scores/user/{user_name}'
	- method: GET
	- parameters: USER_INFO_REQUEST(contains user_name)
	- returns: ScoreForms, containing multiple ScoreForm, containing user_name, date, cards, guesses, score

- **get_high_scores**
	- description: Generate a list of high scores
	- path: 'scores/high'
	- method: GET
	- parameters: VOID
	- returns: ScoreForms, containing multiple ScoreForm, containing user_name, date, cards, guesses, score

- **get_user_rankings**
	- description: Return the players, ranked by average score
	- path: 'users/rankings'
	- method: GET
	- parameters: VOID
	- returns: UserForms containing multiple UserForm, containing name, urlsafe_key, total_games, total_score, avg_score

- **get_top_score**
	- description: Get the cached highest score
	- path: '/scores/top'
	- method: GET
	- parameters: VOID
	- returns: StringMessage


## Models Included:

- **User**
	- Properties: 
	    - name (String, required)
	    - email (String)
	    - total_games (Integer)
	    - total_score (Integer)
	    - avg_score (Integer)
	- Methods: 
		- to_form -- Sends user information to the UserForm
		- calc_score -- Calculates a user's average score

- **Game**
	- Properties: 
	    - board (String, repeated)
	    - boardState (String, repeated)
	    - guesses (Integer, required)
	    - cards (Integer, required)
	    - status (String, required)
	    - user (Key, kind='User', required)
	    - history (Pickle, repeated)
	    - score (Float)
	- Methods:
		- new_game -- parameters = user, cards(opt, default =52) -- Create and return a new game
		- to_form -- paramenters = message -- Returns a GameForm representation of the game
		- to_mini_form -- Returns an abbreviated representation of the game
		- to_history_form -- Returns a game move history, along with some additional game statistics
		- win_game -- Complete a game and add score information to the scoreboard, as well as track user statistics

- **Score**
	- Properties: 
	    - user (Key, kind='User', required)
	    - date (Date, required)
	    - cards (Integer, required)
	    - guesses(Integer, required)
	    - score (Float, required)
	- Methods:
		- to_form -- Sends score information to the ScoreForm


## Forms Included:

### Game Forms (Display)

- **GameForm**
	- description: GameForm for outbound game state information

- **MiniGameForm**
	- description: Abbreviated Game Form for reporting, rather than play purposes

- **HistoryForm**
	- description: Form to display a game history, as well as score information

- **MiniGameForms**
	- description: Hold a list of abbreviated MiniGame Forms

- **NewGameForm**
	- description: Used to create a new game


### Gameplay Forms

- **FlipCardForm**
	- description: Form to allow players to guess a card by supplying its index

- **CardForm**
	- description: Form to respond to player guess by revealing a card value

- **MakeGuessForm**
	- description: Used to make a move in an existing game

- **HintForm**
	- description: Send the index of a matching card (hint) back to a user


### Score Forms

- **ScoreForm**
	- description: ScoreForm for outbound Score information

- **ScoreForms**
	- description: Return multiple ScoreForms


### User and Rankings Forms

- **UserForm**
	- description: User detail form

- **UserForms**
	- description: Return information mulitiple users for ranking


### Assorted Forms

- **StringMessage**
	- description: Outbound (single) string message


## Additional Features

This API also features a scheduled task that sends email alerts to any users who have provided an email address when registering and have unfinished games. This task is executed every 12 hours at present, and the timing of the alert can be modified in cron.yaml

A method **_cache_high_score** exists for caching the current top score, for use in announcements, for example. The current high score announcement can be retrieved from memcache as a StringMessage via the get_top_score endpoint.


## Background

This project was completed as part of the Udacity Fullstack Nanodegree program. Starter code for this project is available [here](https://github.com/udacity/FSND-P4-Design-A-Game). The utils.py in this project was provided as part of this code, and used as-is.


## License Information

This project is Copyright (c) 2016 Abigail Mathews, and is open source under the MIT license. See LICENSE.txt for more information.