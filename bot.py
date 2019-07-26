from telegram.ext import Updater, CommandHandler
import configparser
import murder
from enum import Enum
import sys
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

# configuration values
token = ""
admins = []
signedUpPlayers = []

class gameState(Enum):
    SIGNUPS = 1
    GAMEINPROGRESS = 2
    GAMEDONE = 3

status = gameState.SIGNUPS

GAME_RULE = "To kill your target, you have to give them an item, and they have to take it."

chatDir = {}

def readConfig():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global token, admins, signedUpPlayers
    try:
        token = config['DEFAULT']['token']
    except KeyError:
        logger.error('No token specified, can not start bot')
        sys.exit()
    try:
        admins = config['DEFAULT']['admins'].split(",")
    except KeyError:
        logger.warning('No admins specified')
    try:
        signedUpPlayers = config['DEFAULT']['players'].split(",")
        # This won't work either way, because we need the player IDs to identify them.
    except KeyError:
        logger.warning('No players in config supplied')

def checkAdminPrivileges(update):
    # Currently via usernames, could also be implemented via id.
    logger.info('Checking if "%s" is admin', update.effective_user['username'])
    return update.effective_user['username'] in admins

def isSignedUp(update):
    return update.effective_user['username'] in signedUpPlayers

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hi " + update.effective_user['first_name'] + "!\n"
                     "With this bot you can play the game 'murder'. If you want to participate, type /ready. The game"
                     " will commence when an admin start it. Once this happens, further instructions will follow.")
    chatDir[update.effective_user['username']] = update.message.chat_id # Used to communicate with player proactively
    logger.info('started communication with "%s"', update.effective_user['username'])
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are an admin.")

# MURDER
#(potential) player commands

def signUpForGame(bot, update):
    # called by /ready
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text="Admins can not participate in the game.")
        return
    if isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are already signed up!")
        return
    if status != gameState.SIGNUPS:
        bot.send_message(chat_id=update.message.chat_id, text="Game is not ready for signups")
        return
    signedUpPlayers.append(update.effective_user['username'])
    logger.info('murder game: "%s" now ready', update.effective_user['username'])
    bot.send_message(chat_id=update.message.chat_id, text="You are now signed up.")

def unReadyForGame(bot, update):
    # called by /unready
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text="Admins can not participate in the game.")
        return
    if not isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are not signed up!")
        return
    if status != gameState.SIGNUPS:
        bot.send_message(chat_id=update.message.chat_id, text="Game might already be in progress. Use /dead to end your"
                                                              " participation. ")
        return
    signedUpPlayers.remove(update.effective_user['username'])
    logger.info('murder game: "%s" now unready', update.effective_user['username'])
    bot.send_message(chat_id=update.message.chat_id, text="You are now signed up.")


def killTarget(bot, update):
    if not isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are not a player")
        return
    if not murder.isAlive(update.effective_user['username']):
        bot.send_message(chat_id=update.message.chat_id, text="You are already dead!")
        return

    # Confirm to target
    target = murder.getTarget(update.effective_user['username'])
    logger.info('murder game: "%s" tries to kill "%s" ', update.effective_user['username'], target)
    bot.send_message(chat_id=chatDir[target],text=" It has been claimed that you are dead. Are these rumors true? "
                                                  "Then please type /dead.")
    return

def getTarget(bot, update):
    if not isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are not a player")
        return
    if not murder.isAlive(update.effective_user['username']):
        bot.send_message(chat_id=update.message.chat_id, text="You are already dead!")
        return
    target = murder.getTarget(update.effective_user['username'])
    bot.send_message(chat_id=update.message.chat_id, text="Your target is " + target)
    logger.info('murder game: "%s" requested target, got "%s"', update.effective_user['username'], target)

def confirmDeath(bot,update):
    #Called by typing /dead. 2 uses: confirm kill by other player / suicide.
    user = update.effective_user['username']
    if not isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are not a player")
        return
    if not murder.isAlive(user):
        bot.send_message(chat_id=update.message.chat_id, text="You are already dead!")
        return
    bot.send_message(chat_id=update.message.chat_id, text="You are now dead")
    killer = murder.getPotentialKiller(user)
    murder.eliminatePlayer(user)
    if len(murder.remainingPlayers)>1:
        bot.send_message(chat_id=chatDir[killer], text="Your victim is dead. Your next /target will be " + murder.getTarget(killer))

    logger.info('murder game: death of "%s"', user)


# Admin commands

def getRemainingPlayers(bot, update):
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text=murder.remainingPlayers)
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def startGame(bot,update):
    if checkAdminPrivileges(update):
        murder.initalizeGame(signedUpPlayers)
        if not murder.activeGame:
            logger.error("Tried unsuccessfully to start game")
            bot.send_message(chat_id=update.message.chat_id, text='Not enough players')
            return
        global status
        bot.send_message(chat_id=update.message.chat_id, text='Starting the game now')
        status = gameState.GAMEINPROGRESS
        for player in signedUpPlayers:
            bot.send_message(chat_id=chatDir[player],
                             text='The game starts now!' + GAME_RULE + " When you killed your target, type /kill. To"
                                                                       " show your current target, type /target")
            bot.send_message(chat_id=chatDir[player],
                             text='Your first target will be ' + murder.getTarget(player))
        logger.info('game started')
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def printChatDir(bot,update):
    if checkAdminPrivileges(update):
        print(chatDir)
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def getGameStats(bot,update):
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text='Remaining Players: ' + len(murder.remainingPlayers) +
                                                              ', Killed Players: ' + len(murder.killedPlayers))
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def endGame(bot,update):
    if checkAdminPrivileges(update):
        print(murder.remainingPlayers)
        global status
        status = gameState.SIGNUPS
        murder.reset()
        logger.info('game ended by admin "%s", with remaining players "%s"', update.effective_user['username'], str(murder.remainingPlayers))
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def resetGame(bot,update):
    if checkAdminPrivileges(update):
        global status, signedUpPlayers
        status = gameState.SIGNUPS
        murder.reset()
        signedUpPlayers = []
        logger.info('game reset by admin "%s"', update.effective_user['username'])
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def getGameState(bot,update):
    if checkAdminPrivileges(update):
        return status
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def debugKillFirst(bot,update):
    if status != gameState.GAMEINPROGRESS:
        bot.send_message(chat_id=update.message.chat_id, text='No game in progress!')
        return
    if checkAdminPrivileges(update):
        players = list(murder.remainingPlayers.keys())
        murder.eliminatePlayer(players[0])
        bot.send_message(chat_id=update.message.chat_id, text='Killed ' + players[0])
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

#End of command declarations

def gameFinishedCallback(update, context):
    logger.info('Checking if the game is over')
    # is called every 60 seconds to check if the game is over.
    global status
    if status == gameState.GAMEINPROGRESS and not murder.activeGame:
        #game is done
        status = gameState.GAMEDONE
        # notify all players, who the winner is
        for player in signedUpPlayers:
            update.send_message(chat_id=chatDir[player],
                             text='The game is over, ' + list(murder.getRemainingPlayers().keys())[0] + ' has won.')


    return


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# TODO Dict of participating players Handle -> First Name
# TODO Add a way to insert Chat-IDs into config
# TODO kill stats

# Murder commands
# For Admins: startGame, remainingPlayers, endGame, resetGame, gameState, debugKill
# For Players: ready (You will then take part in the game when it starts), kill (when you have killed your target)
#           , getTarget, dead (When another player claims to have killed you), unready


def main():
    readConfig()
    updater = Updater(token)
    dp = updater.dispatcher
    murder.reset()

    # General commands
    dp.add_handler(CommandHandler('start', start))

    # murder game commands
    dp.add_handler(CommandHandler('remainingPlayers', getRemainingPlayers))
    dp.add_handler(CommandHandler('ready', signUpForGame))
    dp.add_handler(CommandHandler('unready', unReadyForGame))
    dp.add_handler(CommandHandler('dead', confirmDeath))
    dp.add_handler(CommandHandler('suicide', confirmDeath))
    dp.add_handler(CommandHandler('kill', killTarget))
    dp.add_handler(CommandHandler('target', getTarget))
    dp.add_handler(CommandHandler('startGame', startGame))
    dp.add_handler(CommandHandler('endGame', endGame))
    dp.add_handler(CommandHandler('stats', getGameStats))
    dp.add_handler(CommandHandler('resetGame', resetGame))
    dp.add_handler(CommandHandler('gameState', getGameState))
    dp.add_handler(CommandHandler('debugKill', debugKillFirst))
    dp.add_handler(CommandHandler('printChatDir', printChatDir))

    j = updater.job_queue
    endOfGameJob = j.run_repeating(gameFinishedCallback, interval=60, first=0)

    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()