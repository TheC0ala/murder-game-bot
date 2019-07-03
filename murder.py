import random

remainingPlayers = {}
killedPlayers = {}

activeGame = False

def initalizeGame(playerlist):
    reset()
    global activeGame
    if(len(playerlist)<2):
        print("Game needs at least 2 people (currently " + len(playerlist) + ")")
        return
    activeGame = True
    targets = shuffleList(playerlist)
    for i in range(len(playerlist)):
        remainingPlayers[playerlist[i]] = targets[i]

def reset():
    global activeGame
    activeGame = False
    killedPlayers.clear()
    remainingPlayers.clear()

def shuffleList(playerlist):
    targetlist = playerlist.copy()
    #Shuffle the list until no player has the own name as target
    while True:
        random.shuffle(targetlist)
        for p1, p2 in zip(targetlist,playerlist):
            if p1 == p2:
                break
            else:
                return targetlist

def eliminatePlayer(victim):
    #get (potential) killer
    for p in remainingPlayers.keys():
        if remainingPlayers[p]==victim:
            killer = p
    if killer is None:
        return
    killPlayer(killer, victim)

# kill player and set new target for killer
def killPlayer(killer, victim):
    if getTarget(killer) == victim:
        newtarget = remainingPlayers[victim]
        del remainingPlayers[victim]
        if len(remainingPlayers) == 1:
            declareWinner(killer)
            return
        remainingPlayers[killer] = newtarget
    else:
        print("Could not kill " + victim + " at the hands of " + killer)

# get target that player has to kill
def getTarget(player):
    if player in remainingPlayers:
        return remainingPlayers[player]
    print(player + " not alive!")

def getRemainingPlayers():
    return remainingPlayers

def isAlive(player):
    return player in remainingPlayers

def getKilledPlayers():
    return killedPlayers

def declareWinner(winner):
    print(winner + " has won the game!")
    global activeGame
    activeGame = False
