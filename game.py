import pydealer as pd


def isGameWon(boardState):
    if 'U' in boardState:
        return False
    return True

def constructBoard(numCards=52):
    """"Create a board out of a shuffleed deck of numCards
    numCards (default 52): number of cards in the board (even #, 8-52)"""
    deck = pd.Deck()
    ## Split the deck using the initial set of cards if numCards < 52
    if numCards < 52:
        deck = splitDeck(deck, numCards)
        
    deck.shuffle(times=5)

    board = []
    for c in deck:
        board.append(pd.card.card_abbrev(c.value, c.suit))
        #else:
        #    board.append(pd.card.card_name(c.value, c.suit))
        #board.append(c)
    return board


def initialBoardState(numCards=52):
    """Create a board that can display the current state of the game, i.e.
    whether any given card has been correctly matched yet, or not"""
    displayBoard = []
    for n in range(0, numCards):
        displayBoard.append('U')
    return displayBoard


def splitDeck(deck, numCards):
    if numCards % 2 != 0:
        numCards += 1
    if numCards < 8:
        numCards = 8
    deck, hold = deck.split(numCards)
    return deck


def turnCard(indexValue, myBoard):
    cardname = myBoard[indexValue]
    cardvalue = cardname[0]
    print(cardname)
    return cardvalue


def compareCards(index1, index2, myBoard, displayBoard):
    pass


def playGame():
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

