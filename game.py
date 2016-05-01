"""Game functions to implement a Concentration (Memory) game using playing cards"""

import pydealer as pd


def isGameWon(boardState):
    """Check if the board still contains unmatched cards"""
    if 'U' in boardState:
        return False
    return True

def constructBoard(numCards=52):
    """"Create a board out of a shuffled deck of numCards
    numCards(default 52): number of cards in the board (even #, 8-52)"""
    deck = pd.Deck()
    ## Split the deck using the initial set of cards if numCards < 52
    if numCards < 52:
        deck = splitDeck(deck, numCards)
        
    deck.shuffle(times=5)

    board = []
    for c in deck:
        board.append(pd.card.card_abbrev(c.value, c.suit))

    return board


def initialBoardState(numCards=52):
    """Create a board that can display the current state of the game, i.e.
    whether any given card has been correctly matched yet, or not"""
    displayBoard = []
    for n in range(0, numCards):
        displayBoard.append('U')
    return displayBoard


def splitDeck(deck, numCards):
    """Create a deck that is smaller than the default 52 card deck,
    while making sure that there are an even number of cards, and each
    card has a real match."""
    if numCards % 2 != 0:
        numCards += 1
    if numCards < 8:
        numCards = 8
    deck, hold = deck.split(numCards)
    return deck


def turnCard(indexValue, myBoard):
    """Return the value of a guessed card."""
    cardname = myBoard[indexValue]
    return cardname


def compareCards(index1, index2, myBoard, displayBoard):
    """Compare two guessed cards to see if they match, representing
    a game turn"""
    card1 = myBoard[index1]
    card2 = myBoard[index2]
    message = "The first card had value {}. ".format(card1)
    message += "The second card had value {}. ".format(card2)
    if card1[0] == card2[0]:
        message += "It's a match!"
        displayBoard[index1] = 'M'
        displayBoard[index2] = 'M'
    else:
        message += "Sorry, no match this time. Guess again."
    return message, displayBoard


def playGame():
    """A command line implementation of Concentration, for testing purposes"""
    print("Welcome to Concentration, your memory game!")
    number_of_cards = input("How many cards would you like to play with? ")
    true_board = constructBoard(number_of_cards)
    display_board = initialBoardState(number_of_cards)
    while not (isGameWon(display_board)):
        guess1 = input("Which card do you pick? ")
        card1 = turnCard(guess1, true_board)
        guess2 = input("What is your second guess? ")
        card2 = turnCard(guess2, true_board)
        
        if card1 == card2:
            print("It's a match!")
            display_board[guess1] = 'M'
            display_board[guess2] = 'M'
            print(display_board)
    print("You win!")

