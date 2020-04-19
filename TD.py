import random
import sys

sys.path.append("..")  # so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *


##
# AIPlayer
# Description: The responsbility of this class is to interact with the game by
# deciding a valid move based on a given game state. This class has methods that
# will be implemented by students in Dr. Nuxoll's AI course.
#
# Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "TD Learning")

        self.alpha = .1
        self.discount = .9
        self.epsilon = .999
        self.turnCount = 0

        self.utilities = []


    ##
    # getPlacement
    #
    # Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    # Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    # Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        # implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:  # stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:  # stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    # getMove
    # Description: Gets the next move from the Player.
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: The Move to be made
    ##
    def getMove(self, currentState):
        moves = listAllLegalMoves(currentState)

        #based on epsilon choose whether to explore vs exploit
        if random.random() > self.epsilon:
            #exploit
            selectedMove = self.bestMove(currentState, moves)
        else:
            ##explore
            selectedMove = moves[random.randint(0, len(moves) - 1)]

        #update utility based on move
        self.updateUtility(currentState, selectedMove)

        #if the move is endTurn, increment counter
        if selectedMove.moveType == 2:
            self.turnCount += 1
            #every 10 turns update epsilon, it will decrease over time
            if self.turnCount % 10 == 0:
                self.epsilon = pow(.999, self.turnCount / 10)

        return selectedMove

    # return best move
    def bestMove(self,state, moves):
        bestMove = moves[0]
        bestMoveUtil = 0;
        for move in moves:
            nextState = getNextStateAdversarial(state, move)
            scores = self.stateScore(nextState)
            for utility in self.utilities:
              if scores[0] == utility[0] and scores[1] == utility[1] and scores[2] == utility[2]:
                  if utility[3] > bestMoveUtil:
                      bestMove = move
                      bestMoveUtil = utility[3]

        return bestMove

    #updates the utility for the given state
    def updateUtility(self, state, move):
        scores = self.stateScore(state)

        #check to see if state already exists in utilities list
        for utility in self.utilities:
            if scores[0] == utility[0] and scores[1] == utility[1] and scores[2] == utility[2]:
                utility[3] = self.calcUtility(state, move, utility[3])
                return

        #if state doesn't exist calc utility and add to utilities list
        scores.append(self.calcUtility(state,move,0))
        self.utilities.append(scores)


    def calcUtility(self, state, move, currUtil):
        reward = self.calcReward(state)
        nextState = getNextStateAdversarial(state, move)
        return currUtil + self.alpha * (reward + (self.discount*self.lookupUtility(nextState))-currUtil)


    def lookupUtility(self, state):
        scores = self.stateScore(state)
        for utility in self.utilities:
            if scores[0] == utility[0] and scores[1] == utility[1] and scores[2] == utility[2]:
                return utility[3]
        return 0

    #calculates the reward for being in state
    def calcReward(self, state):
        return 0


    #returns number of steps to gain 1 food, steps to win, number of workers
    def stateScore(self,state):
        workers = getAntList(state, state.whoseTurn, (WORKER,))
        food, drop, foodToDropdist = self.minFoodSpots(state)

        ant = workers[0]
        if ant.carrying:
            dist = stepsToReach(state, ant.coords, drop.coords)
        else:
            dist = stepsToReach(state, ant.coords, food.coords) + foodToDropdist

        stepsToFood = dist

        # food still needed
        foodNeeded = 11 - getCurrPlayerInventory(state).foodCount

        # estimate on how many turns it will take to reach food needed - 1
        stepsToWin = (foodNeeded - 1) * ((foodToDropdist*2) + 2)/len(workers)

        print(stepsToFood, stepsToWin, len(workers))
        return [stepsToFood, stepsToWin, len(workers)]

    # helper for stepsToFood
    # returns bestFood, bestBuilding, distance between the two
    def minFoodSpots(self, state):
        dropSpots = getConstrList(state, state.whoseTurn, (ANTHILL, TUNNEL))
        foodSpots = getCurrPlayerFood(None, state)
        minDist = 30
        for spot in dropSpots:
            for food in foodSpots:
                dist = stepsToReach(state, food.coords, spot.coords)
                if dist < minDist:
                    minDist = dist
                    bestFood = food
                    bestBuilding = spot

        return bestFood,bestBuilding, minDist


    ##
    # getAttack
    # Description: Gets the attack to be made from the Player
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        # Attack a random enemy.
        return enemyLocations[0]

    # at the end of each game same the utilities to a file in case of a crash
    def saveUtility(self):
        pass

    # load in utilies from file
    def loadUtility(self):
        pass

    ##
    # registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        #save utilities
        self.saveUtility()

