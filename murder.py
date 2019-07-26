import random

remainingPlayers = {}
killedPlayers = {}
playersWantingToBeReassigned=[]

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
        if(checkDoubles(targetlist,playerlist)):
            return targetlist

def checkDoubles(list1,list2):
    for p1, p2 in zip(list1, list2):
        if p1 == p2:
            return False
        else:
            continue
    return True

def getPotentialKiller(victim):
    for p in remainingPlayers.keys():
        if remainingPlayers[p] == victim:
            return p
    return None

def eliminatePlayer(victim):
    #get (potential) killer
    killer = getPotentialKiller(victim)
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

def addToReassignment(player):
    if player in remainingPlayers:
        playersWantingToBeReassigned.append(player)

def reassign():
    if len(playersWantingToBeReassigned)>1:
        pass #Not implemented
