import sqlite3, requests, logging, time
con = sqlite3.connect('westwood.sqlite3')
cur = con.cursor()
#Sample query
#for row in cur.execute(f'Select * from westwood_ability where westwood_ability.name = "Adaptability"'):
#    print(row)
pokemon = cur.execute(f'Select name,learnset from westwood_pokemonlearnsets') #unfinished
logging.basicConfig(level=logging.INFO)

#Process for creating a reference dictionary for westwood and locationFetch game names. - I need this later, but I'm not using it right now.
# con = sqlite3.connect(westwoodData)
# cur = con.cursor()
# gameQuery = cur.execute("""
# SELECT wg.id, wg.name
# FROM westwood_game wg 
# """)
# gameIDS = {}
# for id, game in gameQuery:
#     game = str(game)
#     game = game.replace("Pokemon","").lower()
#     game = game.strip()
#     gameIDS[game] = game
# con.close()