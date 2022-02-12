import sqlite3, requests, logging, time
con = sqlite3.connect('PokeTools/westwood.sqlite3')
cur = con.cursor()
#Sample query
#for row in cur.execute(f'Select * from westwood_ability where westwood_ability.name = "Adaptability"'):
#    print(row)
#pokemon = cur.execute(f'Select name,learnset from westwood_pokemonlearnsets') #unfinished
logging.basicConfig(level=logging.INFO)

class calculatedFields:
    #calculated fields - 
    def getDefensiveCoverage(pokemon, game, enemyPokemon=False):
        #Take list of pokemon, return defensive coverage
        pass

    def getOffensiveCoverage(pokemon, game, enemyPokemon=False):
        #Take list of pokemon, return offensive coverage
        pass

#Damage Calc information - IF possible. Depends on if there is web-app implementation.
class uiInfo:
    #Sets information for UI elements to get data from (selectable values, etc).
    #By rule this is all information that can be returned by SQL searches, without needing to calculate exensive data.

    def unfoldSQL(contents): #Extracts the contents from the SQL call and returns them
        rows = []
        for row in contents[0]:
            rows.append(row)
        return rows
    
    def appendSQL(contents, *append):
        for row in contents:
            index = contents.index(row)
            contents[index] += tuple(append)            
        return contents
    def getMoves(pokemon, game):
        #Get TM/HM, Tutor, Egg, and LvlUp learnsets.
        tutorMoves = []
        tutorSqlQuery = """SELECT wp.name, wm.name, wm3.type_1, wm3.base_power, wm3.power_points, wm3.accuracy, wm3.priority,
                        wm3.damage_category, wm3.effect, wm3.description, wg1.name
                        FROM {} wp 
                        INNER JOIN westwood_pokemontutorsets wp1 ON ( wp.name = wp1.name  )  
                        INNER JOIN westwood_tutorsetslistelement wt ON ( wp1.tutor_sets = wt.list_id  )  
                        INNER JOIN westwood_tutorset wt1 ON ( wt.element_id = wt1.id  )  
                        INNER JOIN westwood_tutorsetmoveslistelement wt2 ON ( wt1.tutor_set_moves = wt2.list_id  )  
                        INNER JOIN westwood_tutorsetmove wt3 ON ( wt2.element_id = wt3.id  )  
                        INNER JOIN westwood_move wm ON ( wt3.name = wm.name  )  
                        INNER JOIN westwood_moverecordslistelement wm1 ON ( wm.move_records = wm1.list_id  )  
                        INNER JOIN westwood_moverecord wm2 ON ( wm1.element_id = wm2.id  )  
                        INNER JOIN westwood_movedefinition wm3 ON ( wm2.move_definition_id = wm3.id  )  
                        INNER JOIN westwood_gameslistelement wg ON ( wm2.games = wg.list_id  )  
                        INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  )
                        INNER JOIN westwood_gameslistelement wg2 ON ( wt1.games = wg2.list_id  )  
                        INNER JOIN westwood_game wg3 ON ( wg2.element_id = wg1.id  )                         
                        WHERE wp.name = ? AND wg1.name = ? AND wg3.name = ? """
        
        tmMoves = []
        tmSqlQuery = """SELECT wp.name, wm.name, wm3.type_1, wm3.base_power, wm3.power_points, wm3.accuracy, wm3.priority,
                        wm3.damage_category, wm3.effect, wm3.description, wg1.name
                        FROM {} wp 
                        INNER JOIN westwood_pokemontmsets wp1 ON ( wp.name = wp1.name  )  
                        INNER JOIN westwood_tmsetslistelement wt ON ( wp1.tm_sets = wt.list_id  )  
                        INNER JOIN westwood_tmset wt1 ON ( wt.element_id = wt1.id  )  
                        INNER JOIN westwood_tmsetmoveslistelement wt2 ON ( wt1.tmset_moves = wt2.list_id  )  
                        INNER JOIN westwood_tmsetmove wt3 ON ( wt2.element_id = wt3.id  )  
                        INNER JOIN westwood_move wm ON ( wt3.name = wm.name  )  
                        INNER JOIN westwood_moverecordslistelement wm1 ON ( wm.move_records = wm1.list_id  )  
                        INNER JOIN westwood_moverecord wm2 ON ( wm1.element_id = wm2.id  )  
                        INNER JOIN westwood_movedefinition wm3 ON ( wm2.move_definition_id = wm3.id  )  
                        INNER JOIN westwood_gameslistelement wg ON ( wm2.games = wg.list_id  )  
                        INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  ) 
                        INNER JOIN westwood_gameslistelement wg2 ON ( wt1.games = wg2.list_id  )  
                        INNER JOIN westwood_game wg3 ON ( wg2.element_id = wg1.id  )                         
                        WHERE wp.name = ? AND wg1.name = ?  AND wg3.name = ?"""

        learnsetMoves = []
        learnsetSqlQuery = """SELECT wp.name, wm.name, wt3.level, wm3.type_1, wm3.base_power, wm3.power_points, wm3.accuracy, wm3.priority,
                        wm3.damage_category, wm3.effect, wm3.description, wg1.name
                        FROM {} wp 
                        INNER JOIN westwood_pokemonlearnsets wp1 ON ( wp.name = wp1.name  )  
                        INNER JOIN westwood_learnsetslistelement wt ON ( wp1.learnsets = wt.list_id  )  
                        INNER JOIN westwood_learnset wt1 ON ( wt.element_id = wt1.id  )  
                        INNER JOIN westwood_learnsetmoveslistelement wt2 ON ( wt1.learnset_moves = wt2.list_id  )  
                        INNER JOIN westwood_learnsetmove wt3 ON ( wt2.element_id = wt3.id  )  
                        INNER JOIN westwood_move wm ON ( wt3.name = wm.name  )  
                        INNER JOIN westwood_moverecordslistelement wm1 ON ( wm.move_records = wm1.list_id  )  
                        INNER JOIN westwood_moverecord wm2 ON ( wm1.element_id = wm2.id  )  
                        INNER JOIN westwood_movedefinition wm3 ON ( wm2.move_definition_id = wm3.id  )  
                        INNER JOIN westwood_gameslistelement wg ON ( wm2.games = wg.list_id  )  
                        INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  ) 
                        INNER JOIN westwood_gameslistelement wg2 ON ( wt1.games = wg2.list_id  )  
                        INNER JOIN westwood_game wg3 ON ( wg2.element_id = wg1.id  )                         
                        WHERE wp.name = ? AND wg1.name = ? AND wg3.name = ?
                        ORDER BY wt3.level ASC"""
        
        #Base query for the the various move data. The only changes we have to make are calling the pokemon and pokemonform tables.
        #Being they aren't fk joined, we can't really join each respective queries into a single execute function.

        sqlPokemonTable = "westwood_pokemon"
        sqlPokemonFormsTable = "westwood_pokemonform"

        cur.execute(tutorSqlQuery.format(sqlPokemonTable), (pokemon, game, game))
        tutorMovesTemp = cur.fetchall()
        tutorMoves.append(tutorMovesTemp)
        cur.execute(tutorSqlQuery.format(sqlPokemonFormsTable), (pokemon, game, game))
        tutorMovesTemp = (cur.fetchall())
        tutorMoves.append(tutorMovesTemp)

        cur.execute(tmSqlQuery.format(sqlPokemonTable), (pokemon, game, game))
        tmMovesTemp = cur.fetchall()
        tmMoves.append(tmMovesTemp)
        cur.execute(tmSqlQuery.format(sqlPokemonFormsTable), (pokemon, game, game))
        tmMovesTemp = cur.fetchall()
        tmMoves.append(tmMovesTemp)

        cur.execute(learnsetSqlQuery.format(sqlPokemonTable), (pokemon, game, game))
        learnsetMovesTemp = cur.fetchall()
        learnsetMoves.append(learnsetMovesTemp)
        cur.execute(learnsetSqlQuery.format(sqlPokemonFormsTable), (pokemon, game, game))
        learnsetMovesTemp = cur.fetchall()
        learnsetMoves.append(learnsetMovesTemp)

        tutorMoves = uiInfo.unfoldSQL(tutorMoves)
        tmMoves = uiInfo.unfoldSQL(tmMoves)
        learnsetMoves = uiInfo.unfoldSQL(learnsetMoves)

        tutorMoves = uiInfo.appendSQL(tutorMoves, "Tutor")
        tmMoves = uiInfo.appendSQL(tmMoves, "TM")
        learnsetMoves = uiInfo.appendSQL(learnsetMoves, "Learnset")

        return tutorMoves, tmMoves, learnsetMoves
        
    def locationFilter(location, game):
        #Filter by encounter location
        pass

    def encounterDetails(route, game, pokemon):
        #Get encounter details
        pass

    def pokemonStats(pokemon, game, nature="modest"):
        #Get pokemon stats. Combine all referenced information for westwood_pokemon DB into list, accounting for nature if provided.
        pass
for i in uiInfo.getMoves("Eevee","Pokemon Platinum"): 
    for x in i:
        if len(x)>0: print(x)