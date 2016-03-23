import pydealer as pd
import pydealer.utils as pdutils




def constructBoard(numCards=52, abbrev=True):
    """"Create a board out of a shuffled deck of numCards
    numCards (default 52): number of cards in the board (even #, 8-52)"""
    deck = pd.Deck()
    ## Split the deck using the initial set of cards if numCards < 52
    if numCards < 52:
        deck = splitDeck(deck, 52)
        
    deck.shuffle(times=5)

    board = []
    for card in deck:
        if abbrev:
            board.append(pd.card.card_abbrev(deck[0].value, deck[0].suit))
        else:
            board.append(pd.card.card_name(deck[0].value, deck[0].suit))
    return board


def initialBoardState(numCards=52):
    """Create a board that can display the current state of the game, i.e.
    whether any given card has been correctly matched yet, or not"""
    displayBoard = []
    for n in numCards:
        displayBoard.append('U')
    return displayBoard


def splitDeck(deck, numCards):
    if numCards % 2 != 0:
        numCards += 1
    if numCards < 8:
        numCards = 8
    deck, hold = deck.split(numCards)
    return deck