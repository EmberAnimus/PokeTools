import requests, logging, time, json
logging.basicConfig(level=logging.INFO)
#sets function to fetch webpage JSON.
def fetch_json(url):
    webpage = requests.get(url)
    web_json = webpage.json()
    return web_json
try:
    #tests for locationData file. will fail otherwise
    file = open("locationData.json","r")
    file.close()
except:
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
    with open('locationData.json','w') as locFile: #Dump the route data (variable is game_data, yes I know its confusing) to file.
        json.dump(game_data, locFile)
        locFile.close()
