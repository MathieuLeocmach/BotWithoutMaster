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

    class Meta:
        database = db

class Player(Model):
    name = CharField(default="")
    player_id = IntegerField(default=0)

    class Meta:
        database = db

class GameFollowed(Model):
    Game = ForeignKeyField(Game)
    Follower = ForeignKeyField(Player)

    class Meta:
        database = db

db.connect()
if create:
    sys.stdout.write("Creating database...")
    sys.stdout.flush()
    db.create_tables([Game, Player, GameFollowed])
    sys.stdout.write("OK\n")
    sys.stdout.flush()

print("Showing database...")
games = Game.select()
print(f"Game.select(): {games}")
for game in games:
    print(f"game {game} name={game.name} overtone={game.overtone} channel_id={game.channel_id} guild={game.guild} channel_name={game.channel_name} start_date={game.start_date} debug={game.debug} overplayer={game.overplayer} phase={game.phase} activerogue={game.activerogue} activetone={game.activetone}")

db.close()


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
