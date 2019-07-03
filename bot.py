from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
import configparser
import murder
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
logger = logging.getLogger(__name__)

#configuration values
token = ""
admins = []
signedUpPlayers = []

GAME_RULE = "To kill your target, you have to give them an item, and they have to take it."

chatDir = {}

#PLAYERS = range(1)

def readConfig():
    config = configparser.ConfigParser()
    config.read('config.ini')
    global token, admins,signedUpPlayers
    token = config['DEFAULT']['token']
    admins = config['DEFAULT']['admins'].split(",")
    signedUpPlayers = config['DEFAULT']['players'].split(",")

def checkAdminPrivileges(update):
    #Currently via usernames, could also be implemented via id.
    return update.effective_user['username'] in admins

def isSignedUp(update):
    return update.effective_user['username'] in signedUpPlayers

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Hi " + update.effective_user['first_name'] +
                     "With this bot you can play the game 'murder'. If you want to participate, type /ready. The game"
                     " will commence when an admin start it. Once this happens, further instructions will follow.")
    chatDir[update.effective_user['username']] = update.message.chat_id
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are an admin.")

# MURDER
#(potential) player commands

def signUpForGame(bot, update):
    #called by /ready
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text="Admins can not participate in the game.")
        return
    if isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are already signed up!")
        return
    signedUpPlayers.append(update.effective_user['username'])
    bot.send_message(chat_id=update.message.chat_id, text="You are now signed up.")

def unReadyForGame(bot, update):
    #called by /unready
    if checkAdminPrivileges(update):
        bot.send_message(chat_id=update.message.chat_id, text="Admins can not participate in the game.")
        return
    if not isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are not signed up!")
        return
    if len(murder.remainingPlayers)>0 :
        bot.send_message(chat_id=update.message.chat_id, text="Game is already in progress. Use /dead to end your "
                                                              "participation. ")
        return
    signedUpPlayers.remove(update.effective_user['username'])
    bot.send_message(chat_id=update.message.chat_id, text="You are now signed up.")


def killTarget(bot, update):
    if not isSignedUp(update):
        bot.send_message(chat_id=update.message.chat_id, text="You are not a player")
        return
    if not murder.isAlive(update.effective_user['username']):
        bot.send_message(chat_id=update.message.chat_id, text="You are already dead!")
        return

    #Confirm to target
    target = murder.getTarget(update.effective_user['username'])
    bot.send_message(chat_id = chatDir[target],text= " It has been claimed that you are dead. Are these rumors true? Then please type /dead .")
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
    murder.eliminatePlayer(user)


# Admin commands

def getRemainingPlayers(bot,update):
    if checkAdminPrivileges(update):
        players = list(murder.remainingPlayers.keys())
        bot.send_message(chat_id=update.message.chat_id, text=players)
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def startGame(bot,update):
    if checkAdminPrivileges(update):
        murder.initalizeGame(signedUpPlayers)
        for player in signedUpPlayers:
            bot.send_message(chat_id=chatDir[player],
                             text='The game starts now!' + GAME_RULE + " When you killed your target, type /kill . To"
                                                                       " show your current target, type target")
            bot.send_message(chat_id=chatDir[player],
                             text='Your first target will be ' + murder.getTarget(player))
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

def endGame(bot,update):
    if checkAdminPrivileges(update):
        print(murder.remainingPlayers)
        murder.reset()
        return
    bot.send_message(chat_id=update.message.chat_id, text='You need to be admin to do that!')

#End of command declarations


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

#TODO add logging to everything
#TODO Check which user is performing an action -> if the user is in the admin group he can do other things than players
#TODO find a way to authenticate/identify players -> First name/ telegram handle ?
#TODO Implement for players: kill (kills the target) -> possibly with a request to the killed player to accept his death
# to prevent abuse
#TODO Players should be able to send /ready to the bot -> admins can then start, all that have typed /ready will take
# part
#TODO Dict of participating players Handle -> First Name


#Murder commands
#For Admins: startGame, remainingPlayers, endGame
#For Players: ready (You will then take part in the game when it starts), kill (when you have killed your target)
#           , getTarget, confirm (When another player claims to have killed you), unready


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
    dp.add_handler(CommandHandler('kill', killTarget))
    dp.add_handler(CommandHandler('target', getTarget))
    dp.add_handler(CommandHandler('startGame', startGame))
    dp.add_handler(CommandHandler('endGame', startGame))


    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
