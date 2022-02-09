import requests, logging, time, json, sqlite3 #Import needed tools

logging.basicConfig(level=logging.INFO) #Establish Logging

filePath = "PokeTools/locationData.json" #Set file paths
westwoodSQL = "PokeTools/westwood.sqlite3"
locationSQL = "PokeTools/locationData.sqlite3"
#sets function to fetch webpage JSON.
def fetch_json(url):
    webpage = requests.get(url)
    web_json = webpage.json()
    return web_json
try:
    #tests for locationData file. will fail otherwise
    file = open(filePath,"r")
except IOError as err:
    logging.info = f'Error: {err}'
    #sets some api, and fetches total amount of locations for total length.
    data_api = "https://pokeapi.co/api/v2/location-area/"
    tempLocations = fetch_json(data_api)
    totalLocations = tempLocations['count']
    jsonLocations = fetch_json(f'{data_api}?limit={totalLocations}')
    #defines the dictionary for future use
    game_data = {}

    #iterates through the JSON for specific variables. Also gets the time so we can time each route, for debugging purposes.
    for i in range(0,totalLocations-1):
        route_start_time = time.monotonic()
        location_data_url = jsonLocations['results'][i]['url']
        locationData = fetch_json(location_data_url)
        encounters = locationData['pokemon_encounters']
        current_route = locationData['location']['name']
        game_data[current_route] = {}
        #sets sub-dictionary for the route

        for current_poke in encounters:
            #sets sub-dictionary for the pokemon
            poke_name = current_poke['pokemon']['name']
            game_data[current_route][poke_name] = {}

            for current_game_set in current_poke['version_details']:
                #checks for any existing game records, and sets a new sub-dictionary if there aren't any. After that it iterates over encounter data and sets variables where appropriate.
                game = current_game_set['version']['name']

                if game not in game_data[current_route][poke_name]:
                    game_data[current_route][poke_name][game] = {}

                for current_encounter in current_game_set['encounter_details']:
                    encounter_rate = current_encounter['chance']
                    min_level = current_encounter['min_level']
                    max_level = current_encounter['max_level']
                    encounter_method = current_encounter['method']['name']

                    try:
                        if game_data[current_route][poke_name][game][encounter_method]['min_level'] > min_level:
                            game_data[current_route][poke_name][game][encounter_method]['min_level'] = min_level

                        if game_data[current_route][poke_name][game][encounter_method]['max_level'] < max_level:
                            game_data[current_route][poke_name][game][encounter_method]['max_level'] = max_level

                        game_data[current_route][poke_name][game][encounter_method]['encounter_rate'] += encounter_rate

                    except KeyError:
                        game_data[current_route][poke_name][game][encounter_method] = {
                            'encounter_rate' : encounter_rate,
                            'min_level' : min_level,
                            'max_level' : max_level
                            }
        #gets the end of the route and logs the information before looping back for the next route
        route_end_time = time.monotonic()
        route_total_time = route_end_time - route_start_time
        logging.info(f'Route: {current_route} completed. Took {route_total_time} seconds. [{i+1}/{totalLocations}] complete.')
    #Final data structure from the iteration should look something like:
    # game_data = {
    #     RouteName: {
    #          PokemonName:{
    #              GameName:{
    #                  EncounterMethod:{
    #                      encounter_rate: cumulative encounter %,
    #                      'min_level': min encounter lvl,
    #                      'max_level': max encounter lvl
    #                  }
    #              }
    #          }
    #     }
    # }
    with open(filePath,'w') as file: #Dump the route data (variable is game_data, yes I know its confusing) to file.
        json.dump(game_data, file)
        file.close()
    file = open(filePath,"r") #Re-opens the file in read mode.

locationData = json.load(file) #reads the file and converts it to JSON
westwoodCon = sqlite3.connect(westwoodSQL)
westwoodCur = westwoodCon.cursor()
gameQuery = westwoodCur.execute("SELECT wg.id, wg.name FROM westwood_game wg ") #Selects the game table from the westwood database
gameIDS = []
for id, game in gameQuery: #converts the game names from the westwood format to the API format
    game = str(game)
    game = game.replace("Pokemon","").lower().strip()
    gameIDS.append(game) 
westwoodCur.close() #Close the westwood database
locationCon = sqlite3.connect(locationSQL)#Open/Create the locationData database
locationCur = locationCon.cursor()
locationCur.execute('SELECT count(name) FROM sqlite_master WHERE type="table" AND name="routeData"') #Check if the needed table exists
update = False
if locationCur.fetchone()[0]==1:
    #Table exists, prompt for update
    update = input("Table currently exists, do you wish to update the data? Y/N") 
else:
    #Create Table
    locationCur.execute('''CREATE TABLE routeData
                        (RouteName text, PokemonName text, GameIndex integer, EncounterMethod text, EncounterRate integer, MinLevel integer, MaxLevel integer)''')
    
if update=="Y" | locationCur.fetchone()[0]==0:#If an update is desired, or if the table is empty, update the table.
    locationCur.execute("DELETE FROM routeData")
    locationCon.commit()#Delete existing data

    locationList = []
    for RouteName, RouteSub in locationData.items():#Iterate through the locationData.json file for all information
        for PokemonName, PokeSub in RouteSub.items():
            for GameName, GameSub in PokeSub.items():
                TempGame = GameName.replace("-"," ")
                GameIndex = gameIDS.index(TempGame)
                for EncounterMethod, EncounterSub in GameSub.items():
                    EncounterRate = EncounterSub["encounter_rate"]
                    MinLevel = EncounterSub["min_level"]
                    MaxLevel = EncounterSub["max_level"]
                    locationList.append((RouteName,PokemonName,GameIndex,EncounterMethod,EncounterRate,MinLevel,MaxLevel))#Append to locationList as tuple
    locationCur.executemany("INSERT INTO routeData VALUES (?,?,?,?,?,?,?)",locationList)#Insert all rows (stored as tuples) to the database
    locationCon.commit()#Commit the change
    
elif update=="N":#If the table is not empty, and an update isn't desired, print message accordingly
    print("Table not updated. Closing program.")
else: #Print error message
    print('An error has occured.')
locationCon.close()#Close connection
file.close()#Close file