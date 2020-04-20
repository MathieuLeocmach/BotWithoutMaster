from peewee import *
from playhouse.migrate import *
from datetime import date, datetime
import sys
import os

db_file = 'dbwithoutmaster.db'

if not os.path.isfile(db_file):
    create = True
else:
    create = False

db = SqliteDatabase(db_file)

class Game(Model):
    guild = CharField(default="")
    channel_id = IntegerField(default=0)
    channel_name = CharField(default="")
    name = CharField(default="")
    start_date = DateTimeField(default=None, null=True)
    overplayer = CharField(default="")
    overtone = CharField(default="")
    phase = CharField(default="")
    activetone = CharField(default="")
    activerogue = CharField(default="")
    debug = BooleanField(default=False)
    emojis = CharField(default="")

    class Meta:
        database = db

class Rogue(Model):
    name = CharField(default="")

    class Meta:
        database = db

class RogueGame(Model):
    game = ForeignKeyField(Game)
    rogue = ForeignKeyField(Rogue)
    glum = CharField(default="")
    jovial = CharField(default="")

    class Meta:
        database = db

def show_db():
    print("Showing database...")
    games = Game.select()
    print(f"Game.select(): {games}")
    for game in games:
        print(
            f"game {game} name={game.name} overtone={game.overtone} channel_id={game.channel_id} guild={game.guild} channel_name={game.channel_name} start_date={game.start_date} debug={game.debug} overplayer={game.overplayer} phase={game.phase} activerogue={game.activerogue} activetone={game.activetone} emojis={game.emojis}")
        rogues = Rogue.select().join(RogueGame).join(Game).where(Game.channel_id == game.channel_id)
        for rogue in rogues:
            print(f"rogue {rogue.name} glum {rogue.glum} jovial {rogue.jovial}")


#db.connect()
if create:
    sys.stdout.write("Creating database...")
    sys.stdout.flush()
    db.create_tables([Game, Rogue, RogueGame])
    sys.stdout.write("OK\n")
    sys.stdout.flush()
#db.close()

show_db()

if __name__ == " __main__":

    if len(sys.argv) <= 1:
        print("This tool manages the db.")
        print("show: show info and most of the data from the db")
        print("create: create the db")
        print("empty: empty the db")
    elif len(sys.argv) >= 2:
        if sys.argv[1] == "show":
            print("Showing database...")
            liste = Game.select()
            print (repr(liste))
            print ("avant avant")
            for item in liste:
                print (repr(item))
                print (item.name, item.overtone, str(item.channel_id), item.guild, item.channel_name, str(item.start_date), str(item.overplayer), str(item.activerogue), item.activetone)

            pass    # this is a stub
        elif sys.argv[1] == "create":
            print("Creating database...")
            db.connect()
            db.create_tables([Game, Player, GameFollowed])
            db.close()
        elif sys.argv[1] == "empty":
            pass    # this is a stub
