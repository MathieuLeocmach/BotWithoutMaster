import discord
import requests
from random import randint
import re
import os
import sys



client = discord.Client()


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
    global overplayer, overtone, activerogue, activetone, mydice, log
    
    overplayer=None
    overtone=""
    activerogue=None
    activetone=""
    mydice = get_dice(60)

    await client.change_presence(activity=discord.Game(name="ask me \"Who are you @BotWithoutMaster ?\" to know more about me."))
    
    log.info("The bot is ready!")
    
@client.event
async def on_message(message):
    global overplayer, overtone, activerogue, activetone, mydice, log

    if message.author == client.user:
        return
    
    if len(mydice) < 30:
        log.info("Fetching 60 new random dice... (len(mydice)=={})".format(len(mydice)))
        mydice = mydice + get_dice(60)
        log.info("Now, len(mydice)=={}".format(len(mydice)))
        
    log.info(repr(message.content) + " " + repr(message.author.nick) + " " + repr(message.author.display_name) + " " + repr(message.mentions))
    if (message.content[:1] == "/") and ("bones" in message.content):
        stymied = False
        mystery = False
        morale = False
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
                if overtone=="":
                    TONE="CHOOSE"
                elif overtone=="GLUM":
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
            
            if overplayer == None:
                await message.channel.send("Gather around fellow rogues ! Overplayer is "+message.author.mention+", he will begin a "+TONE+" tale.")
                overplayer=message.author.mention
                await client.change_presence(activity=discord.Game(name="Swords Without Master. "+message.author.display_name+" is the Overplayer. Ask me  \"Who are you @BotWithoutMaster ?\" to know more about me."))
                overtone=TONE
            elif overplayer==message.author.mention:
                if TONE=="CHOOSE":
                    if overtone=="GLUM":
                        overtone="JOVIAL"
                    else:
                        overtone="GLUM"
                else:
                    overtone=TONE
                await message.channel.send("Our Overplayer "+overplayer+" launched a new phase, and speaks in a "+overtone+" voice...")
                await client.change_presence(activity=discord.Game(name=message.author.display_name+"Swords Without Master. "+message.author.display_name+" is the Overplayer, "+activetone+" is the Overtone"))
            else:
                stymied_text = ""
                if stymied:
                    if mystery:
                        stymied_text = "\nHe is stymied by what he just discovered. Write down a Mystery !"
                    else:
                        stymied_text = "\nHe is STYMIED by what just happened."
                morale_text = ""
                if morale:
                    morale_text = "\nHe just learned a MORALE. Write it down !"

                overtone_text="\nThe Overtone is "+overtone+"."
                
                await message.channel.send(message.author.mention+" now speaks in a "+TONE+" voice..."+stymied_text+morale_text+overtone_text)
                activerogue=message.author.mention
                activetone=TONE
           
        #elif " gives the bones to " in message.content:
        elif "/givebones" in message.content:
            #await message.channel.send(repr(message.mentions))
            if message.mentions == []:
                await message.channel.send("I didn't understand whom you tried to give the bones to, "+message.author.mention)
            else:
                activerogue= message.mentions[0].mention
                await message.channel.send(message.author.mention+" gives the bones to "+activerogue)
                await client.change_presence(activity=discord.Game(name=message.author.display_name+"Swords Without Master. "+message.author.display_name+" is the Overplayer, "+activerogue+" holds the bones"))

    if (message.content[:1] == "/") and ("endgame" in message.content):
        if overplayer == None:
            await message.channel.send("There is no game currently running that I know of, "+ message.author.mention + ".")
        else:
            await message.channel.send("Game run by overplayer "+ overplayer + " has now ended. I am too dumb to tell if the story was great.")
            overplayer=None
            overtone=""
            activerogue=None
            activetone=""
            await client.change_presence(activity=discord.Game(name="ask me \"Who are you @BotWithoutMaster ?\" to know more about me."))
        
    if (client.user in message.mentions) and ("who are you" in message.content.lower()):
        await message.channel.send("I am " + client.user.name + ", " + message.author.mention + ", and I am a helper for Swords Without Master games.\nUse */rollbones* to roll bones, and */givebones* to pass them around. \nUse */endgame* when you are satiated or rest in peace.")
        
            
import json            
BOT_ID=json.load(open("bot_id.json","r"))
#log.info(repr(BOT_ID))
#log.info(repr(get_dice(60)))

#sys.exit(1)
client.run(BOT_ID)

