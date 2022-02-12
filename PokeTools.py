import sqlite3, requests, logging, time

con = sqlite3.connect('PokeTools/westwood.sqlite3')
cur = con.cursor()
#Sample query
#for row in cur.execute(f'Select * from westwood_ability where westwood_ability.name = "Adaptability"'):
#    print(row)
#pokemon = cur.execute(f'Select name,learnset from westwood_pokemonlearnsets') #unfinished
logging.basicConfig(level=logging.INFO)

sqlPokemonTable = "westwood_pokemon"
sqlPokemonFormsTable = "westwood_pokemonform"

class calculatedFields:
    #calculated fields - 
    def getDefensiveCoverage(pokemon, game, enemyPokemon=False):
        #Take list of pokemon, return defensive coverage
        pass

    def getOffensiveCoverage(pokemon, game, enemyPokemon=False):
        #Take list of pokemon, return offensive coverage
        pass

    def getPokeonTypeEffectiveness(type1, type2):
        #Take input types, then return effectivness array
        pass
    
    def getMoveEffectiveness(move):
        #Get move effectiveness
        pass

    def statAdjustment(statBlock, natureInfo):
        #adjust statblock to nature
        statList = list(statBlock[0:8])
        statIndex = ("names", "hp", "attack", "defense", "special_attack", "special_defense", "speed", "max_hp", "max_attack_hindered", 
                    "max_defense_hindered", "max_special_attack_hindered", "max_special_defense_hindered", "max_speed_hindered", "max_attack_neutral", 
                    "max_defense_neutral", "max_special_attack_neutral", "max_special_defense_neutral", "max_speed_neutral", "max_attack_beneficial", "max_defense_beneficial", 
                    "max_special_attack_beneficial", "max_special_defense_beneficial", "max_speed_beneficial", "game")
                    #Sets an index reference for the statBlock tuple

        statNames = ["attack","defense","special_attack","special_defense","speed"] #Sets a reference for the stats we search against
        if natureInfo[1]=='None' and natureInfo[2] == 'None':
            neutralIndex = {}
            for i in statNames:
                neutralIndex[i] = statIndex.index(f'max_{i.lower()}_neutral')
            for index in neutralIndex.values():
                statList.append(statBlock[index])
        else:
            beneficialStat = natureInfo[1].lower().replace(" ", "_")
            hinderedStat = natureInfo[2].lower().replace(" ", "_")
            indexList = {}
            for i in statNames:
                if i != beneficialStat and i != hinderedStat:
                    indexList[i] = statIndex.index(f'max_{i.lower()}_neutral')
                elif i == beneficialStat:
                    indexList[i] = statIndex.index(f'max_{beneficialStat}_beneficial')
                elif i == hinderedStat:
                    indexList[i] = statIndex.index(f'max_{hinderedStat}_hindered')
            for index in indexList.values():
                statList.append(statBlock[index])
        
        return tuple(statList)
                
#Damage Calc information - IF possible. Depends on if there is web-app implementation.
class uiInfo:
    #Sets information for UI elements to get data from (selectable values, etc).
    #By rule this is all information that can be returned by SQL searches, without needing to calculate exensive data.

    def unfoldSQL(contents): #Extracts the contents from the SQL call and returns them
        rows = []
        for row in contents[0]:
            rows.append(row)
        return rows
    
    def appendSQL(contents, *append): #Takes SQL contents, iterates over each row then appends the passed data by "adding" a tuple.
        for row in contents:
            index = contents.index(row)
            contents[index] += tuple(append)            
        return contents

    def getMoves(pokemon, game):
        #Get TM/HM, Tutor, Egg, and LvlUp learnsets.
        
        tutorMoves = uiInfo.getTutorMoves(pokemon, game)
        tmMoves = uiInfo.getTmMoves(pokemon, game)
        learnsetMoves = uiInfo.getLearnsetMoves(pokemon, game)

        return tutorMoves, tmMoves, learnsetMoves
        
    def getTmMoves(pokemon, game):
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

        cur.execute(tmSqlQuery.format(sqlPokemonTable), (pokemon, game, game))
        tmMovesTemp = cur.fetchall()
        tmMoves.append(tmMovesTemp)
        cur.execute(tmSqlQuery.format(sqlPokemonFormsTable), (pokemon, game, game))
        tmMovesTemp = cur.fetchall()
        tmMoves.append(tmMovesTemp)

        tmMoves = uiInfo.unfoldSQL(tmMoves)
        tmMoves = uiInfo.appendSQL(tmMoves, "TM")     

        return tmMoves

    def getTutorMoves(pokemon, game):
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
        
        cur.execute(tutorSqlQuery.format(sqlPokemonTable), (pokemon, game, game))
        tutorMovesTemp = cur.fetchall()
        tutorMoves.append(tutorMovesTemp)
        cur.execute(tutorSqlQuery.format(sqlPokemonFormsTable), (pokemon, game, game))
        tutorMovesTemp = (cur.fetchall())
        tutorMoves.append(tutorMovesTemp)        
        
        tutorMoves = uiInfo.unfoldSQL(tutorMoves)
        tutorMoves = uiInfo.appendSQL(tutorMoves, "Tutor")

        return tutorMoves

    def getLearnsetMoves(pokemon, game):
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
        
        cur.execute(learnsetSqlQuery.format(sqlPokemonTable), (pokemon, game, game))
        learnsetMovesTemp = cur.fetchall()
        learnsetMoves.append(learnsetMovesTemp)
        cur.execute(learnsetSqlQuery.format(sqlPokemonFormsTable), (pokemon, game, game))
        learnsetMovesTemp = cur.fetchall()
        learnsetMoves.append(learnsetMovesTemp)

        learnsetMoves = uiInfo.unfoldSQL(learnsetMoves)
        learnsetMoves = uiInfo.appendSQL(learnsetMoves, "Learnset")  

        return learnsetMoves
    
    def locationFilter(game):
        #Filter locations by game
        locationCon = sqlite3.connect("PokeTools/locationData.sqlite3")
        locationCur = locationCon.cursor()

        locationSQLQuery = """SELECT r.RouteName
                                FROM routeData r 
                                WHERE r.GameIndex = ?
                                GROUP BY r.RouteName"""

        gameIndexQuery = """SELECT wg.id
                            FROM westwood_game wg 
                            WHERE wg.name = ?"""

        cur.execute(gameIndexQuery, ([game]))
        gameIndex = cur.fetchall()
        gameIndex = uiInfo.unfoldSQL(gameIndex)

        locationCur.execute(locationSQLQuery, gameIndex)
        locationList = locationCur.fetchall()
        for i in range(0,len(locationList)):
            locationList[i] = locationList[i][0]
        locationList = tuple(locationList)
        locationCon.close()

        return locationList

    def getEncounterDetails(route, game, pokemon):
        #Get encounter details
        pass

    def getPokemonStats(pokemon, game, nature=["Serious"]):
        #Get pokemon stats. Combine the follwing information for the listed pokemon in the listed game into list, accounting for nature if provided.
        #Detailed stats, EV Yield, Typing
        statBlock = uiInfo.getStatBlock(pokemon, game)
        natureInfo = uiInfo.getNatureInfo(nature)
        typeSet = uiInfo.getType(pokemon, game)
        evYield = uiInfo.getEvYield(pokemon)
        
        pokemonStats = calculatedFields.statAdjustment(statBlock, natureInfo)

        return pokemonStats, typeSet, natureInfo, evYield

    def getNatureInfo(nature):

        if isinstance(nature,list):
            nature = str(nature[0]).capitalize() #Being all of the natures are indexed with a capitial first letter, we have to convert the input to such
        else:
            nature = nature.capitalize()
        nature = [nature] #Restores the input to being a list

        natureInfo = []
        natureSQLQuery = """SELECT wn.name, wn.increased_stat, wn.decreased_stat 
                            FROM westwood_nature wn
                            WHERE wn.name = ? """

        cur.execute(natureSQLQuery, (nature))
        natureInfoTemp = cur.fetchall()
        natureInfo.append(natureInfoTemp)
        natureInfo = uiInfo.unfoldSQL(natureInfo) 

        return natureInfo[0]

    def getStatBlock(pokemon, game):
        pokemonStats = []
        statsSQLQuery = """SELECT wp.name, ws1.hp, ws1.attack, ws1.defense, ws1.special_attack, ws1.special_defense, ws1.speed, ws1.max_hp, ws1.max_attack_hindered, ws1.max_defense_hindered, ws1.max_special_attack_hindered, ws1.max_special_defense_hindered, ws1.max_speed_hindered, ws1.max_attack_neutral, ws1.max_defense_neutral, ws1.max_special_attack_neutral, ws1.max_special_defense_neutral, ws1.max_speed_neutral, ws1.max_attack_beneficial, ws1.max_defense_beneficial, ws1.max_special_attack_beneficial, ws1.max_special_defense_beneficial, ws1.max_speed_beneficial, wg1.name
                            FROM {} wp 
                            INNER JOIN westwood_statsetslistelement ws ON ( wp.stat_sets = ws.list_id  )  
                            INNER JOIN westwood_statset ws1 ON ( ws.element_id = ws1.id  )  
                            INNER JOIN westwood_gameslistelement wg ON ( ws1.games = wg.list_id  )  
                            INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  )  
                            WHERE wp.name = ? AND wg1.name = ?"""        

        cur.execute(statsSQLQuery.format(sqlPokemonTable), (pokemon, game))
        pokemonStatsTemp = cur.fetchall()
        pokemonStats.append(pokemonStatsTemp)
        cur.execute(statsSQLQuery.format(sqlPokemonFormsTable), (pokemon, game))
        pokemonStatsTemp = cur.fetchall()
        pokemonStats.append(pokemonStatsTemp)
        pokemonStats = uiInfo.unfoldSQL(pokemonStats)  
        
        return pokemonStats[0]

    def getEvYield(pokemon):

        evYield = []
        evSQLQuery = """SELECT wp.name, we1.stat, we1.value
                        FROM {} wp 
                        INNER JOIN westwood_evyieldslistelement we ON ( wp.ev_yields = we.list_id  )  
                        INNER JOIN westwood_evyield we1 ON ( we.element_id = we1.id  )  
                        WHERE wp.name = ?"""

        cur.execute(evSQLQuery.format(sqlPokemonTable), ([pokemon]))
        evYieldTemp = cur.fetchall()
        evYield.append(evYieldTemp)
        cur.execute(evSQLQuery.format(sqlPokemonFormsTable), ([pokemon]))
        evYieldTemp = cur.fetchall()
        evYield.append(evYieldTemp)
        evYield = uiInfo.unfoldSQL(evYield)

        return evYield[0]

    def getType(pokemon, game):

        typeSet = []
        typeSQLQuery = """SELECT wp.name, wt1.type1, wt1.type2, wg1.name
                            FROM {} wp 
                            INNER JOIN westwood_typesetslistelement wt ON ( wp.type_sets = wt.list_id  )  
                            INNER JOIN westwood_typeset wt1 ON ( wt.element_id = wt1.id  )  
                            INNER JOIN westwood_gameslistelement wg ON ( wt1.games = wg.list_id  )  
                            INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  )  
                            WHERE wp.name = ? AND wg1.name = ?"""  

        cur.execute(typeSQLQuery.format(sqlPokemonTable), (pokemon, game))
        typeSetTemp = cur.fetchall()
        typeSet.append(typeSetTemp)
        cur.execute(typeSQLQuery.format(sqlPokemonFormsTable), (pokemon, game))
        typeSetTemp = cur.fetchall()
        typeSet.append(typeSetTemp)
        typeSet = uiInfo.unfoldSQL(typeSet)

        return typeSet[0]

if __name__ == "__main__":
    for i in uiInfo.getMoves("Eevee","Pokemon Platinum"):
        for x in i: 
            if len(x)>0: print(x)
    for i in uiInfo.getPokemonStats("Eevee","Pokemon Platinum"): 
        if len(i)>0: print(i)
    print(uiInfo.locationFilter("Pokemon Platinum"))