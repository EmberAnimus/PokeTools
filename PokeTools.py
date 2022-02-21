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
    def getDefensiveCoverage(pokemon:list, game:str):
        #Take list of pokemon, return defensive coverage
        coverage = {
            "4.0":[],
            "2.0":[],
            "1.0":[],
            "0.5":[],
            "0.25":[],
            "0.0":[]
        }
        for name in pokemon:
            type1, type2 = uiInfo.getType(name,game)[1:3]
            if type2 == '':
                tempEffectiveness = calculatedFields.getTypeEffectiveness(defType = type1)
                for multiplier in tempEffectiveness:
                    if not(multiplier[0] in coverage[str(multiplier[2])]):
                        coverage[str(multiplier[2])].append(multiplier[0])
            else: 
                tempEffectiveness = calculatedFields.getTypeEffectiveness(defType = type1)
                for i, effectiveness in enumerate(calculatedFields.getTypeEffectiveness(defType = type2)):
                    multiplier = effectiveness[2] * tempEffectiveness[i][2]
                    if not(effectiveness[0] in  coverage[str(multiplier)]):
                        coverage[str(multiplier)].append(effectiveness[0])

                    pass

        #Consider putting Coverage filter here   
        return coverage

    def getOffensiveCoverage(pokemon:dict, game:str, stab_only:bool=True):
        '''Pokemon must be a dict with pokemon names as keys and the movesets as lists.\n 
        If you don't want to include moves, then just enter the pokemon dict with empty lists. (default behaviour) \n
        If you want to calculate moves, set stab_only to False. '''
        #Take list of pokemon, return offensive coverage - with STAB (Same Type Attack Bonus) filter
        coverage = {
            "4.0":[],
            "2.0":[],
            "1.0":[],
            "0.5":[],
            "0.25":[],
            "0.0":[]
        }
        for name in pokemon.keys():
            stabType1, stabType2 = uiInfo.getType(name,game)[1:3]
            if stab_only == True:
                if stabType2 == '':
                    tempEffectiveness = calculatedFields.getTypeEffectiveness(offType = stabType1)
                    for multiplier in tempEffectiveness:
                        multiplier = str(multiplier)
                        if not(multiplier[1] in coverage[multiplier[2]]):
                            coverage[multiplier[2]].append(multiplier[1])
                else: 
                    tempEffectiveness = calculatedFields.getTypeEffectiveness(offType = stabType1)
                    for i, effectiveness in enumerate(calculatedFields.getTypeEffectiveness(offType = stabType2)):
                        multiplier = effectiveness[2] * tempEffectiveness[i][2]
                        multiplier = str(multiplier)
                        if not(effectiveness[1] in coverage[multiplier]):
                            coverage[multiplier].append(effectiveness[1])
            else:
                for move in pokemon[name]:
                    moveEffectiveness = calculatedFields.getMoveEffectiveness(move, game)
                    moveType = uiInfo.getMovesData(move, game)[1]
                    for _, type, multiplier in moveEffectiveness:
                        multiplier = str(multiplier)
                        if moveType == stabType1 or moveType == stabType2:
                            try:
                                stabIndex = coverage[multiplier].index(type)
                                coverage[multiplier][stabIndex].append(f'{type}*')
                            except ValueError:
                                coverage[multiplier].append(f'{type}*')
                            except:
                                pass
                        elif not(type in coverage[multiplier]) and not(f'{type}*' in coverage[multiplier]):
                            coverage[multiplier].append(type)

        #Consider putting Coverage filter here
        return coverage

    def getEncounterCoverage(pokemon:dict, game:str, enemypokemon:dict={"Abomasnow":[]}, stab_only:bool=True):
        '''Pokemon must be a dict with pokemon names as keys and the movesets as lists. 
        If you don't want to include moves, you may leave the list empty. This will calculate only stab options (default behaviour)'''       
        #Take a list of pokemon, game, and the list of enemy pokemon, return both defensive and offensive coverage.

        pass

    def getTypeEffectiveness(offType:str=None, defType:str=None):
        #Get type effectiveness list based on query. 
        #If just offensive type is entered, it will list what the offensive type hits for
        #If just the defensive type is entered, it'll check what it is hit for
        #If both are entered it'll check that specific matchup 
        typeEffectivenessSQLQueryOff = """SELECT we.source_type, we.target_type, we.damage_factor
                                        FROM westwood_effectivenessrecord we 
                                        WHERE we.source_type = ?"""

        typeEffectivenessSQLQueryDef = """SELECT we.source_type, we.target_type, we.damage_factor
                                        FROM westwood_effectivenessrecord we 
                                        WHERE we.target_type = ?"""                                        

        typeEffectivenessSQLQueryDual = """SELECT we.source_type, we.target_type, we.damage_factor
                                        FROM westwood_effectivenessrecord we 
                                        WHERE we.source_type = ? AND we.target_type = ?"""


        if defType == None and offType != None:
            if not(isinstance(offType, str)):
                for i in offType:
                    offType = i            
            cur.execute(typeEffectivenessSQLQueryOff, ([offType]))
            typeEffectiveness = cur.fetchall()
        
        elif defType != None and offType == None:

            if not(isinstance(defType, str)):
                for i in defType:
                    defType = i            
            cur.execute(typeEffectivenessSQLQueryDef, ([defType]))
            typeEffectiveness = cur.fetchall()
        else:
            if not(isinstance(offType, str)):
                for i in offType:
                    offType = i
            if not(isinstance(defType, str)):
                for i in defType:
                    defType = i
            cur.execute(typeEffectivenessSQLQueryDual, (offType, defType))
            typeEffectiveness = cur.fetchall()
        for i, typeStats in enumerate(typeEffectiveness):
            #Convert tuple to list, alter an element, then convert back to tuple and overwrite
            typeStats = list(typeStats)
            typeStats[2] = typeStats[2]/100
            typeStats = tuple(typeStats)
            typeEffectiveness[i] = typeStats
        return typeEffectiveness
        pass
        
    def getMoveEffectiveness(moveName:str, game:str):
        #Get move effectiveness stats of a move
        moveTypeSQLQuery = """SELECT wm3.type_1
                                FROM westwood_move wm 
                                INNER JOIN westwood_moverecordslistelement wm1 ON ( wm.move_records = wm1.list_id  )  
                                INNER JOIN westwood_moverecord wm2 ON ( wm1.element_id = wm2.id  )  
                                INNER JOIN westwood_movedefinition wm3 ON ( wm2.move_definition_id = wm3.id  )  
                                INNER JOIN westwood_gameslistelement wg ON ( wm2.games = wg.list_id  )  
                                INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  )  
                                WHERE wm.name = ? AND wg1.name = ?"""
        
        cur.execute(moveTypeSQLQuery, (moveName, game))
        moveType = cur.fetchall()
                #Finds the moves type, then continues once it has it
        try:
            effectivenessData = calculatedFields.getTypeEffectiveness(offType = moveType[0])
            if moveName == "Freeze Dry":
                waterList = list(effectivenessData[10])
                waterList[2] = 2.0
                waterTuple = tuple(waterList)
                effectivenessData[10] = waterTuple
        except IndexError:
            effectivenessData = []
        
        return effectivenessData

    def statAdjustment(statBlock:tuple, natureInfo:tuple):
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
                

class uiInfo:
    #Sets information for UI elements to get data from (selectable values, etc).
    #By rule this is all information that can be returned by SQL searches, without needing to calculate exensive data.
    def getTypeList():#Returns a tuple of types
        typeSQL = """SELECT wt.value
                    FROM westwood_type wt 
                    WHERE wt.value!='None'"""
        
        cur.execute(typeSQL)
        types = cur.fetchall()
        
        return types

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

    def getMovesData(name:str, game:str):
        #Get Data for a given move
        moveDataSqlQuery = '''SELECT wm.name, wm3.type_1, wm3.base_power, wm3.power_points, wm3.accuracy, wm3.priority, wm3.damage_category, wm3.description
                                FROM westwood_move wm 
                                INNER JOIN westwood_moverecordslistelement wm1 ON ( wm.move_records = wm1.list_id  )  
                                INNER JOIN westwood_moverecord wm2 ON ( wm1.element_id = wm2.id  )  
                                INNER JOIN westwood_movedefinition wm3 ON ( wm2.move_definition_id = wm3.id  )  
                                INNER JOIN westwood_gameslistelement wg ON ( wm2.games = wg.list_id  )  
                                INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  )  
                                WHERE wm.name = ? AND wg1.name = ?'''
        cur.execute(moveDataSqlQuery, (name, game))
        moveData = cur.fetchall()

        return moveData[0]

    def getMovesList(pokemon:str, game:str):
        #Get TM/HM, Tutor, Egg, and LvlUp learnsets.
        
        tutorMoves = uiInfo.getTutorMoves(pokemon, game)
        tmMoves = uiInfo.getTmMoves(pokemon, game)
        learnsetMoves = uiInfo.getLearnsetMoves(pokemon, game)

        return tutorMoves, tmMoves, learnsetMoves
        
    def getTmMoves(pokemon:str, game:str):
        #Gets a pokemon's TM moves
        tmMoves = []
        tmSqlQuery = """SELECT wp.name, wm.name, wg1.name
                        FROM {} wp 
                        INNER JOIN westwood_pokemontmsets wp1 ON ( wp.name = wp1.name  )  
                        INNER JOIN westwood_tmsetslistelement wt ON ( wp1.tm_sets = wt.list_id  )  
                        INNER JOIN westwood_tmset wt1 ON ( wt.element_id = wt1.id  )  
                        INNER JOIN westwood_tmsetmoveslistelement wt2 ON ( wt1.tmset_moves = wt2.list_id  )  
                        INNER JOIN westwood_tmsetmove wt3 ON ( wt2.element_id = wt3.id  )  
                        INNER JOIN westwood_move wm ON ( wt3.name = wm.name  )  
                        INNER JOIN westwood_gameslistelement wg ON ( wt1.games = wg.list_id  )  
                        INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  )                          
                        WHERE wp.name = ? AND wg1.name = ?"""

        cur.execute(tmSqlQuery.format(sqlPokemonTable), (pokemon, game))
        tmMovesTemp = cur.fetchall()
        tmMoves.append(tmMovesTemp)
        cur.execute(tmSqlQuery.format(sqlPokemonFormsTable), (pokemon, game))
        tmMovesTemp = cur.fetchall()
        tmMoves.append(tmMovesTemp)

        tmMoves = uiInfo.unfoldSQL(tmMoves)
        tmMoves = uiInfo.appendSQL(tmMoves, "TM")     

        return tmMoves

    def getTutorMoves(pokemon:str, game:str):
        #Gets a pokemon's tutor moves
        tutorMoves = []
        tutorSqlQuery = """SELECT wp.name, wm.name, wg3.name
                        FROM {} wp 
                        INNER JOIN westwood_pokemontutorsets wp1 ON ( wp.name = wp1.name  )  
                        INNER JOIN westwood_tutorsetslistelement wt ON ( wp1.tutor_sets = wt.list_id  )  
                        INNER JOIN westwood_tutorset wt1 ON ( wt.element_id = wt1.id  )  
                        INNER JOIN westwood_tutorsetmoveslistelement wt2 ON ( wt1.tutor_set_moves = wt2.list_id  )  
                        INNER JOIN westwood_tutorsetmove wt3 ON ( wt2.element_id = wt3.id  )  
                        INNER JOIN westwood_move wm ON ( wt3.name = wm.name  )
                        INNER JOIN westwood_gameslistelement wg2 ON ( wt1.games = wg2.list_id  )  
                        INNER JOIN westwood_game wg3 ON ( wg2.element_id = wg3.id  )                         
                        WHERE wp.name = ? AND wg3.name = ? """
        
        cur.execute(tutorSqlQuery.format(sqlPokemonTable), (pokemon, game))
        tutorMovesTemp = cur.fetchall()
        tutorMoves.append(tutorMovesTemp)
        cur.execute(tutorSqlQuery.format(sqlPokemonFormsTable), (pokemon, game))
        tutorMovesTemp = (cur.fetchall())
        tutorMoves.append(tutorMovesTemp)        
        
        tutorMoves = uiInfo.unfoldSQL(tutorMoves)
        tutorMoves = uiInfo.appendSQL(tutorMoves, "Tutor")

        return tutorMoves

    def getLearnsetMoves(pokemon:str, game:str):
        #Gets a pokemon's learnset moves
        learnsetMoves = []
        learnsetSqlQuery = """SELECT wp.name, wt3.name, wt3.level, wg1.name
                        FROM {} wp 
                        INNER JOIN westwood_pokemonlearnsets wp1 ON ( wp.name = wp1.name  )  
                        INNER JOIN westwood_learnsetslistelement wt ON ( wp1.learnsets = wt.list_id  )  
                        INNER JOIN westwood_learnset wt1 ON ( wt.element_id = wt1.id  )  
                        INNER JOIN westwood_learnsetmoveslistelement wt2 ON ( wt1.learnset_moves = wt2.list_id  )  
                        INNER JOIN westwood_learnsetmove wt3 ON ( wt2.element_id = wt3.id  ) 
                        INNER JOIN westwood_gameslistelement wg ON ( wt1.games = wg.list_id  )  
                        INNER JOIN westwood_game wg1 ON ( wg.element_id = wg1.id  )                          
                        WHERE wp.name = ? AND wg1.name = ?
                        ORDER BY wt3.level ASC"""
        
        cur.execute(learnsetSqlQuery.format(sqlPokemonTable), (pokemon, game))
        learnsetMovesTemp = cur.fetchall()
        learnsetMoves.append(learnsetMovesTemp)
        cur.execute(learnsetSqlQuery.format(sqlPokemonFormsTable), (pokemon, game))
        learnsetMovesTemp = cur.fetchall()
        learnsetMoves.append(learnsetMovesTemp)

        learnsetMoves = uiInfo.unfoldSQL(learnsetMoves)
        learnsetMoves = uiInfo.appendSQL(learnsetMoves, "Learnset")  

        return learnsetMoves
    
    def locationFilter(game:str):
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
        locationCon.close()

        return locationList

    def getEncounterDetails(route, game:str, pokemon:str):
        #Get encounter details
        pass

    def getPokemonStats(pokemon:str, game:str, nature=["Serious"]):
        #Get pokemon stats. Combine the follwing information for the listed pokemon in the listed game into list, accounting for nature if provided.
        #Detailed stats, EV Yield, Typing
        statBlock = uiInfo.getStatBlock(pokemon, game)
        natureInfo = uiInfo.getNatureInfo(nature)
        typeSet = uiInfo.getType(pokemon, game)
        evYield = uiInfo.getEvYield(pokemon)
        
        pokemonStats = calculatedFields.statAdjustment(statBlock, natureInfo)

        return pokemonStats, typeSet, natureInfo, evYield

    def getNatureInfo(nature:str):
        #Gets the nature information (stat increased and decreased)
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

    def getStatBlock(pokemon:str, game):
        #Gets the pokemon's statblock - including theoretical max/min for a stat.
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

    def getEvYield(pokemon:str):
        #Gets the EV Yield for a pokemon then merges multiple EV's into one tuple.
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
        tempEvYield = tuple([evYield[0][0]])
        for i in evYield:
            tempEvYield += i[1:]
        evYield = tempEvYield

        return evYield

    def getType(pokemon:str, game:str):
        #Gets typing for a given pokemon
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
    # for i in uiInfo.getMovesList("Eevee","Pokemon Platinum"):
    #    for x in i: 
    #        if len(x)>0: print(x)

    # for i in uiInfo.getPokemonStats("Abomasnow","Pokemon Platinum"): 
    #     if len(i)>0: print(i)

    # print(uiInfo.locationFilter("Pokemon Platinum"))

    # print(uiInfo.getTypeList())

    # print(calculatedFields.getMoveEffectiveness("Freeze Dry", "Pokemon X"))

    # print(uiInfo.getMovesData("Absorb", "Pokemon Platinum"))

    # for mult, types in calculatedFields.getOffensiveCoverage({"Absol":["Cut","Pursuit"],"Scizor":["Bug Buzz", "Strength"]},"Pokemon Platinum", False).items():
    #     print(f'{mult}: {types}')
    pass