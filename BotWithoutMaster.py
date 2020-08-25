import discord
import requests
from random import randint
from collections import deque
import re
import os
import sys
from datetime import date, datetime
from dbwithoutmaster import db, Game, Rogue, RogueGame, show_db

client = discord.Client()
#db.connect()

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
mydice = deque()
tones = ["COMIQUE", "SERIEUX"]


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
    return mon_de%2

def bone():
    global mydice, log

    #log.info(repr(len(mydice)))
    if len(mydice) < 50:
        log.info("len(mydice)<50, fetching more bones")
        mydice.extend(get_dice(50))
    #log.info(mydice)
    bone=mydice.popleft()
    #log.info(mydice)
    return bone

@client.event
async def on_ready():
    global mydice, log

    mydice = deque(get_dice(60))

    await client.change_presence(activity=discord.Game(name="type /info"))


    log.info("The bot is ready!")

@client.event
async def on_message(message):
    global mydice, log, tones

    if message.author == client.user:  # I don't react at my own words
        return

    if len(mydice) < 30:   # I make sure I allways have a full bag of dice rolls
        log.info("Fetching 60 new random dice... (len(mydice)=={})".format(len(mydice)))
        mydice.extend(get_dice(60))
        log.info("Now, len(mydice)=={}".format(len(mydice)))

    log.info(f"{message.channel.guild.name}/{message.channel.name}({message.channel.id}) from {message.author.nick}/{message.author.display_name}({message.mentions}): {message.content}")

    if message.content[0] == "/":
        if Game.select().where(Game.channel_id == message.channel.id):
            game = Game.get(Game.channel_id == message.channel.id)
        else:
            game = Game.create(guild=message.channel.guild.name, channel_name=message.channel.name, channel_id=message.channel.id, name=f"{message.channel.guild.name}/{message.channel.name}")
            game.emojis = json.dumps({})
            game.save()

        emojis = json.loads(game.emojis)
        if emojis == {}:
            emoji_list = {}
            for i in range(1, 7):
                emoji_list[str(i) + "Glum"] = False
                emoji_list[str(i) + "Jovial"] = False
            print("tous faux: " +repr(emoji_list))

            for server_emoji in client.emojis:
                if server_emoji.name in emoji_list:
                    emoji_list[server_emoji.name] = True

            print("ici on sait lesquels existent: " + repr(emoji_list))
            Ok = True
            for emoji in emoji_list:
                print("emoji="+repr(emoji))
                if emoji_list[emoji] == False:
                    Ok = False
            print("ici on sait si OK: " + repr(Ok))
            if not Ok:
                print("emojis not ok")
                # game.emoji_list=emoji_list
                game.emoji = json.dumps({})
                if game.debug:
                    await message.channel.send(f"Emojis are not OK: {emoji_list}")
            else:
                print("emojis are ok")
                # game.emoji_list=emoji_list
                emojis = {}
                for emoji in client.emojis:
                    if emoji.name in emoji_list:
                        emojis[emoji.name] = emoji.id

                game.emojis = json.dumps(emojis)
                if game.debug:
                    tmp_message = ""
                    print(repr(emojis))
                    for emoji in emojis:
                        tmp_message += f"<:{emoji}:{emojis[emoji]}>"
                    await message.channel.send(f"Configuration of emojis was OK: {emoji_list} {tmp_message}")

            game.save()

        show_db()

        if "/toggledebug" in message.content.lower():
            game.debug = not game.debug
            game.save()
            log.info("Toggled debug on game " + game.name + " ; game debug state is now " + repr(game.debug))
            if game.debug:
                await message.channel.send("Debug is now On. Type /toggledebug to disable.")
            else:
                await message.channel.send("Debug is now Off. Type /toggledebug to enable.")
        elif "/startgame" in message.content.lower():
            if game.overplayer != "":
                await message.channel.send(f"Sorry {message.author.mention}, a game is already running. Type /info to know more.")
            else:
                TONE=glum_or_jovial()
                if " " in message.content:
                    words=message.content.split(" ")
                    phase=words[1]
                    await message.channel.send(f"Gather around fellow rogues ! Overplayer is {message.author.mention}, they will begin a {TONE} tale with a {phase} phase.")
                else:
                    phase=""
                    await message.channel.send(f"Gather around fellow rogues ! Overplayer is {message.author.mention}, they will begin a {TONE} tale.")
                game.overplayer=message.author.mention
                game.overtone=TONE
                game.activerogue=""
                game.activetone=""
                game.phase=phase
                #game.start_date=datetime.now
                print("just before")
                game.save()
                print("just after")


        elif "/rollbones" in message.content.lower():
            stymied = False
            mystery = False
            morale = False

            glum = bone()
            jovial = bone()

            if emojis != {}:
                emote_glum = "<:" + str(glum) + "Glum:" + str(emojis[str(glum) + "Glum"]) + ">"
                emote_jovial = "<:" + str(jovial) + "Jovial:" + str(emojis[str(jovial) + "Jovial"]) + ">"
                await message.channel.send(f"{emote_jovial} {emote_glum}")
                if game.debug:
                    await message.channel.send(f"({tones[0]}={jovial} {tones[1]}={glum})")
            else:
                await message.channel.send(f"{tones[0]}={jovial} {tones[1]}={glum}")


            if glum == jovial:
                stymied = True
                if glum <= 3 and jovial <= 3:
                    mystery = True
                if game.overtone==0:
                    TONE=1
                    game.overtone=1
                else:
                    TONE=0
                    game.overtone=0
            else:
                if glum > jovial:
                    TONE=1
                if glum < jovial:
                    TONE=0
                if glum <= 3 and jovial <= 3:
                    morale = True

            stymied_text = ""
            if stymied:
                if mystery:
                    stymied_text = "\nThey are stymied by what they just discovered. Write down a Mystery !"
                else:
                    stymied_text = "\nThey are STYMIED by what just happened."

            morale_text = ""
            if morale:
                morale_text = "\nThey just learned a MORALE. Write it down !"

            if game.overplayer != "":
                overtone_text=f"\nThe Overtone is {tones[game.overtone]}."
            else:
                overtone_text=""

            await message.channel.send(f"{message.author.mention} s'exprime sur un ton {tones[TONE]} ...{stymied_text}{morale_text}{overtone_text}")

            if game is not None:
                game.activerogue=message.author.mention
                game.activetone=TONE
                game.save()

        elif "/newphase" in message.content:
            if game.overplayer == "":
                await message.channel.send(f"Sorry {message.author.mention}, you need to start a new game (/startgame) before starting a new phase.")
            else:
                glum = bone()
                jovial = bone()

                if emojis != {}:
                    emote_glum = "<:" + str(glum) + "Glum:" + str(emojis[str(glum) + "Glum"]) + ">"
                    emote_jovial = "<:" + str(jovial) + "Jovial:" + str(emojis[str(jovial) + "Jovial"]) + ">"
                    await message.channel.send(f"{emote_jovial} {emote_glum}")
                    if game.debug:
                        await message.channel.send(f"({tones[0]}={jovial} {tones[1]}={glum})")
                else:
                    await message.channel.send(f"{tones[0]}={jovial} {tones[1]}={glum}")

                if glum == jovial:
                    if game.overtone == 0:
                        game.overtone = 1
                    else:
                        game.overtone = 0
                if " " in message.content:
                    words=message.content.split(" ")
                    phase=words[1]
                    await message.channel.send(f"Our Overplayer {game.overplayer} launched a new {phase} phase, and speaks in a {tones[game.overtone]} voice...")
                else:
                    phase=""
                    await message.channel.send(f"Our Overplayer {game.overplayer} launched a new phase, and speaks in a {tones[game.overtone]} voice...")
                game.overplayer = message.author.mention
                game.phase = phase
                game.save()
        elif "/givebones" in message.content:
            if message.mentions == []:
                await message.channel.send("I didn't understand whom you tried to give the bones to, "+message.author.mention)
            else:
                game.activerogue = message.mentions[0].mention
                game.activetone = 0
                game.save()
                await message.channel.send(f"{message.author.mention} gives the bones to {game.activerogue}")

        elif "/endgame" in message.content:
            if game.overplayer == "":
                await message.channel.send(f"There is no game currently running here that I know of, {message.author.mention}.")
            else:
                await message.channel.send(f"Game run by Overplayer {game.overplayer} has now ended. I am too dumb to tell if the story was great.")
                game.overplayer = ""
                game.overtone = 0
                game.activerogue = ""
                game.activetone = 0
                game.phase = ""
                game.emojis = {}
                game.save()

                if game.debug:
                    await message.channel.send(f"emojis where reset: {game.emojis}")

        elif "/replace" in message.content:
            if " " in message.content:
                words = message.content.split(" ")
                if len(words) == 3:
                    replaced = words[1]
                    his_tone = words[2]
                    if Rogue.select().join(Game).where(Game.channel_id == message.channel.id, Rogue.name == message.author.mention):
                        rogue = Rogue.get(Game.channel_id == message.channel.id, Rogue.name == message.author.mention)
                        show_db()
                    else:
                        rogue = Rogue.create(associated_game=game, name=message.author.mention, glum=tones[1], jovial=tones[0])

                    if replaced.upper() == tones[0]:
                        rogue.glum = his_tone
                    else:
                        rogue.jovial = his_tone

                    rogue.save()

        elif "/info" in message.content:
            tmp_message = f"I am {client.user.name}, {message.author.mention}, and I am a helper for Swords Without Master games.\nUse **/rollbones** to roll bones, and **/givebones** to pass them around. \nIf you want me to keep track of what is going on, use **/startgame [phase]** to start a game, **/newphase [phase]** to launch a new phase, and **/endgame** when you are satiated or rest in peace."
            if game.overplayer != "":
                if game.phase == "":
                    tmp_message += f"\n_Info on game **{game.name}**:\nOverplayer is {game.overplayer} and the Overtone is currently {tones[game.overtone]}._"
                else:
                    tmp_message += f"\n_Info on game **{game.name}**:\nOverplayer is {game.overplayer} and the Overtone of the current {game.phase} phase is {tones[game.overtone]}._"
                if game.activerogue != "":
                    if game.activetone == "":
                        tmp_message += f"\nActive rogue is {game.activerogue}, they have not rolled the bones yet.\n"
                    else:
                        tmp_message += f"\nActive rogue is {game.activerogue}, currently speaking in a {tones[game.activetone]} tone.\n"
            else:
                tmp_message += "\n_There is no game currently running in this channel._"
            await message.channel.send(tmp_message)

            if game.debug:
                await message.channel.send("Debug is On. Type /toggledebug to disable.")
                tmp_message = ""
                print(repr(emojis))
                for emoji in emojis:
                    tmp_message += f"<:{emoji}:{emojis[emoji]}>"
                await message.channel.send(f"game.name={game.name}\ngame.channel_id={game.channel_id}\ngame.guild={game.guild}\ngame.channel_name={game.channel_name}\ngame.debug={game.debug}\ngame.overplayer={game.overplayer}\ngame.overtone={tones[game.overtone]}\ngame.phase={game.phase}\ngame.activerogue={game.activerogue}\ngame.activetone={tones[game.activetone]}\ngame.start_date={game.start_date}\n{tmp_message}")

    show_db()

import json
BOT_ID=json.load(open("bot_id.json","r"))
#log.info(repr(BOT_ID))
#log.info(repr(get_dice(60)))

#sys.exit(1)
client.run(BOT_ID)

# try:
#     client.run(BOT_ID)
# except Exception as e:
#     log.info(repr(Exception))
