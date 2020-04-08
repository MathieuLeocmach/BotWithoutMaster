import discord
import requests
from random import randint
import re
import os
import sys
import peewee
from dbwithoutmaster import db, Game, Player, GameFollowed

client = discord.Client()
db.connect()

def new_logger():
    import logging

    # create logger
    logger = logging.getLogger('simple_example')
    logger.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    
    # create file handler and set level to debug
    fh = logging.FileHandler("botwithoutmaster.log", mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)

    # add formatter to fh
    fh.setFormatter(formatter)
    

    # add fh to logger
    logger.addHandler(fh)
    
    return logger

log=new_logger()
mydice = []


def get_dice(number_to_fetch):
    global log
    
    dice_list = []
    str_number_to_fetch = str(number_to_fetch)
    for essai in range(0,3):
        r = requests.get('https://www.random.org/dice?num='+str_number_to_fetch)
        if r.status_code != 200:
            log.info("Récupération de {str_number_to_fetch}: erreur http {status_code}".format(status_code=r.status_code, str_number_to_fetch=str_number_to_fetch))
            return []
        else:
            break
    
    resultat = re.findall(r"dice(\d+?)\.png", r.text, re.MULTILINE)
    if resultat == []:
        log.info("Je n'ai pas trouvé le dé dans le résultat de la page web: {}".format(repr(resultat)))
        return []
        

    for mon_de in resultat:
        try:
            mon_de_int = int(mon_de)
            dice_list.append(mon_de_int)
        except:
            log.info("mon_de n'est pas un entier: {}".format(repr(mon_de)))
            return []
            
    return dice_list


def d6():
    global log
    
    r = requests.get('https://www.random.org/dice?num=1')
    if r.status_code != 200:
        log.info("Récupération d'un dé: erreur http {status_code}".format(status_code=r.status_code))
        return randint(1,6)
    else:
        resultat = re.findall(r"You rolled (\d+?) die.+?dice(\d+?)\.png", r.text, re.MULTILINE)
        if resultat == []:
            log.info("Je n'ai pas trouvé le dé dans le résultat de la page web")
            return randint(1,6)
        else:
            log.info(repr(resultat))
            try:
                for mytupple in resultat:
                    (nombre, resultat_du_de) = mytupple
                    return resultat_du_de
            except:
                log.info("erreur: resultat n'est pas une liste de tupples")
                return randint(1,6)

def glum_or_jovial():
    global mydice, log

    mon_de=mydice.pop()
    if mon_de%2 == 1:
        glum_or_jovial = "GLUM"
    else:
        glum_or_jovial = "JOVIAL"
    return glum_or_jovial

def bone():
    global mydice, log
    
    #log.info(repr(len(mydice)))
    if len(mydice) < 50:
        log.info("len(mydice)<50, fetching more bones")
        mydice = mydice + get_dice(50)
    #log.info(mydice)    
    mydice.reverse()
    bone=mydice.pop()
    mydice.reverse()
    #log.info(mydice)
    return bone

@client.event
async def on_ready():
    global mydice, log
    
    mydice = get_dice(60)

    await client.change_presence(activity=discord.Game(name="ask me \"Who are you @BotWithoutMaster ?\" to know more about me."))
    await client.change_presence(activity=discord.Game(name="type /info"))


    log.info("The bot is ready!")
    
@client.event
async def on_message(message):
    global mydice, log

    if message.author == client.user:  # I don't react at my own words
        return

    if Game.select().where(Game.channel_id == message.channel.id):
        game = Game.get(Game.channel_id == message.channel.id)
    else:
        game = None

    if len(mydice) < 30:   # I make sure I allways have a full bag of dice rolls
        log.info("Fetching 60 new random dice... (len(mydice)=={})".format(len(mydice)))
        mydice = mydice + get_dice(60)
        log.info("Now, len(mydice)=={}".format(len(mydice)))
        
    log.info(repr(message.content) + " " + repr(message.author.nick) + " " + repr(message.author.display_name) + " " + repr(message.mentions)+ " " + repr(message.channel.name)+ " " + repr(message.channel.id))
    if (message.content[:1] == "/") and ("bones" in message.content):
        stymied = False
        mystery = False
        morale = False



        if game is None:
            game = Game.create(guild=message.channel.guild.name, channel_name=message.channel.name, channel_id=message.channel.id)
            game.save()

        log.info("servername="+message.channel.guild.name)

        if "/rollbones" in message.content:
            glum=bone()
            jovial=bone()
            await message.channel.send("(glum="+str(glum)+" jovial="+str(jovial)+")")
            if glum == jovial:
                #await message.channel.send("Stymied!")
                stymied = True
                if glum <= 3 and jovial <= 3:
                    #await message.channel.send("Mystery!")
                    mystery = True
                if game.overtone=="":
                    TONE="CHOOSE"
                elif game.overtone=="GLUM":
                    TONE="JOVIAL"
                else:
                    TONE="GLUM"
            else:
                if glum > jovial:
                    #await message.channel.send("glum!")
                    TONE="GLUM"
                if glum < jovial:
                    #await message.channel.send("jovial!")
                    TONE="JOVIAL"
                if glum <= 3 and jovial <= 3:
                    #await message.channel.send("Morale!")
                    morale = True
            
            if game.overplayer == "":
                await message.channel.send("Gather around fellow rogues ! Overplayer is "+message.author.mention+", they will begin a "+TONE+" tale.")
                game.overplayer=message.author.mention
                #await client.change_presence(activity=discord.Game(name="Swords Without Master. "+message.author.display_name+" is the Overplayer. Ask me  \"Who are you @BotWithoutMaster ?\" to know more about me."))
                game.overtone=glum_or_jovial()
                game.name = game.guild + "/" + game.channel_name
                game.save()



                emoji_list = {}
                for i in range(1, 7):
                    emoji_list[str(i) + "_glum"] = False
                    emoji_list[str(i) + "_jovial"] = False
                print(emoji_list)

                for server_emoji in client.emojis:
                    if server_emoji.name in emoji_list:
                        emoji_list[server_emoji.name] = True

                print(emoji_list)
                Ok = True
                for emoji in emoji_list:
                    if emoji == False:
                        Ok = False

                if not Ok:
                    print("emojis not ok")
                else:
                    print("emojis are ok")



            elif game.overplayer==message.author.mention:
                if TONE=="CHOOSE":
                    if game.overtone=="GLUM":
                        game.overtone="JOVIAL"
                    else:
                        game.overtone="GLUM"
                else:
                    game.overtone=TONE
                await message.channel.send("Our Overplayer "+game.overplayer+" launched a new phase, and speaks in a "+game.overtone+" voice...")
                await client.change_presence(activity=discord.Game(name=message.author.display_name+"Swords Without Master. "+message.author.display_name+" is the Overplayer, "+game.activetone+" is the Overtone"))
                game.save()
            else:
                stymied_text = ""
                if stymied:
                    if mystery:
                        stymied_text = "\nThey are stymied by what they just discovered. Write down a Mystery !"
                    else:
                        stymied_text = "\nThey are STYMIED by what just happened."
                morale_text = ""
                if morale:
                    morale_text = "\nThey just learned a MORALE. Write it down !"

                overtone_text="\nThe Overtone is "+game.overtone+"."
                await message.channel.send(message.author.mention+" now speaks in a "+TONE+" voice..."+stymied_text+morale_text+overtone_text)
                game.activerogue=message.author.mention
                game.activetone=TONE
                game.save()


        #elif " gives the bones to " in message.content:
        elif "/givebones" in message.content:
            #await message.channel.send(repr(message.mentions))
            if message.mentions == []:
                await message.channel.send("I didn't understand whom you tried to give the bones to, "+message.author.mention)
            else:
                game.activerogue= message.mentions[0].mention
                game.save()
                await message.channel.send(message.author.mention+" gives the bones to "+game.activerogue)
                await client.change_presence(activity=discord.Game(name=message.author.display_name+"Swords Without Master. "+message.author.display_name+" is the Overplayer, "+game.activerogue+" holds the bones"))

    if (message.content[:1] == "/") and ("endgame" in message.content):
        if game == None:
            await message.channel.send("There is no game currently running here that I know of, " + message.author.mention + ".")
        elif game.overplayer == None:
            await message.channel.send("There is no game currently running that I know of, "+ message.author.mention + ".")
        else:
            await message.channel.send("Game run by Nooverplayer "+ str(game.overplayer) + " has now ended. I am too dumb to tell if the story was great.")
            game.overplayer=None
            game.overtone=""
            game.activerogue=None
            game.activetone=""
            game.delete().execute()
            #await client.change_presence(activity=discord.Game(name="ask me \"Who are you @BotWithoutMaster ?\" to know more about me."))
        
    #if (client.user in message.mentions) and ("who are you" in message.content.lower()):
    if len(message.content) >= 5 and (message.content.lower()[:5] == "/info"):
        await message.channel.send("I am " + client.user.name + ", " + message.author.mention + ", and I am a helper for Swords Without Master games.\nUse */rollbones* to roll bones, and */givebones* to pass them around. \nUse */endgame* when you are satiated or rest in peace.")
        if game:
            tmp_message = f"Info on game *{game.name}* started on _{game.start_date}_:\nOverplayer is {game.overplayer} and the Overtone is currently {game.overtone}."
            if game.activerogue != "":
                if game.activetone != "":
                    tmp_message += f"\nActive rogue is {game.activerogue}, they have not rolled the bones yet.\n"
                else:
                    tmp_message += f"\nActive rogue is {game.activerogue}, currently speaking in a {game.activetone} tone.\n"
            await message.channel.send(tmp_message)
            if game.debug:
                await message.channel.send("Debug is On. Type /toggledebug to disable.")
                await message.channel.send(f"game.name={game.name}\ngame.channel_id={game.channel_id}\ngame.guild={game.guild}\ngame.channel_name={game.channel_name}\ngame.debug={game.debug}\ngame.activerogue={game.activerogue}\ngame.activetone={game.activetone}")
        else:
            await message.channel.send("_There is no game currently running in this channel._")

    if message.content[0] == "/" and "/toggledebug" in message.content.lower() and game is not None:
        game.debug = not game.debug
        game.save()
        log.info("Toggled debug on game "+game.name+" ; game debug state is now "+repr(game.debug))
        if game.debug:
            await message.channel.send("Debug is now On. Type /toggledebug to disable.")
        else:
            await message.channel.send("Debug is now Off. Type /toggledebug to enable.")

import json            
BOT_ID=json.load(open("bot_id.json","r"))
#log.info(repr(BOT_ID))
#log.info(repr(get_dice(60)))

#sys.exit(1)

try:
    client.run(BOT_ID)
except Exception as e:
    log.info(repr(Exception))
