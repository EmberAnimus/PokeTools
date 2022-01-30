import sqlite3, requests, logging, time
con = sqlite3.connect('westwood.sqlite3')
cur = con.cursor()
#Sample query
#for row in cur.execute(f'Select * from westwood_ability where westwood_ability.name = "Adaptability"'):
#    print(row)
pokemon = cur.execute(f'Select name,learnset from westwood_pokemonlearnsets') #unfinished
logging.basicConfig(level=logging.INFO)