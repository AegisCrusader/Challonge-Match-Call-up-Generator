from urllib.request import Request, urlopen 
from os import path, system, remove
from json import loads, dumps
from pyperclip import copy
import sys

system("cls")

if getattr(sys, 'frozen', False):
    SCRIPT_DIRECTORY = path.dirname(sys.executable)
else:
    SCRIPT_DIRECTORY = path.dirname(path.abspath(__file__))

# Default normal match string
normalMatchString = "> __**MATCH CALL**__\n{} vs {}\nPlease play your match and react to this message to check in! Post your scores in this channel when you are finished."
# Default stream match string
streamMatchString = "> __**STREAM MATCH CALL**__\n{} vs {}\nPlease start your match and wait for the stream host to join before playing. Also react to this message to check in!"

class Match:
    def __init__(self, player1Name: str, player2Name: str, player1DiscordID: int, player2DiscordID: int):
        self.player1Name = player1Name
        self.player2Name = player2Name
        self.player1Call = player1Name
        self.player2Call = player2Name
        if player1DiscordID:
            self.player1Call = "<@{}>/".format(str(player1DiscordID)) + player1Name
        if player2DiscordID:
            self.player2Call = "<@{}>/".format(str(player2DiscordID)) + player2Name
    
    def getMatchCallString(self, isStreamMatch: bool) -> str:
        if isStreamMatch:
            return streamMatchString.format(self.player1Call, self.player2Call)
        else:
            return normalMatchString.format(self.player1Call, self.player2Call)

# Returns page source of URL 
def scrapePage(url: str) -> str:
    req = Request(
        url=url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    return urlopen(req).read().decode('utf-8')

try:
    normalMatchFile = open(path.join(SCRIPT_DIRECTORY, "match.txt"), "r")
    normalMatchString = normalMatchFile.read()
    normalMatchFile.close()
except IOError:
    # If there is no match.txt, it will create a file with the default text
    print("Could not find match.txt, deploying default.")
    with open(path.join(SCRIPT_DIRECTORY, "match.txt"), "w") as configFile:
        configFile.write(normalMatchString)

try:
    streamMatchFile = open(path.join(SCRIPT_DIRECTORY, "stream.txt"), "r")
    streamMatchString = streamMatchFile.read()
    streamMatchFile.close()
except IOError:
    # If there is no stream.txt, it will create a file with the default text
    print("Could not find stream.txt, deploying default.")
    with open(path.join(SCRIPT_DIRECTORY, "stream.txt"), "w") as configFile:
        configFile.write(streamMatchString)

try:
    with open(path.join(SCRIPT_DIRECTORY, "config.json"), "r") as configFile:
        configString = configFile.read()
        configJSON = loads(configString)
        apiKey = configJSON["apiKey"]
except Exception:
    print("Could not find/load config.json, beginning setup...")
    configDict = dict()
    apiKey = input("Please enter your API Key. It can be found in your Challonge account settings: ").strip()
    configDict["apiKey"] = apiKey
    # Save the API key so the user does not have to type it again
    with open(path.join(SCRIPT_DIRECTORY, "config.json"), "w") as configFile:
        configFile.write(dumps(configDict, indent=0))



#First we get the link
while True:
    try:
        tournamentURL = input("Please input full tournament URL: ")
        tournamentSource: str = scrapePage(tournamentURL)
        
        #Searching out tournament ID
        startTournamentIDSearch = tournamentSource.find(r'"tournament":{"id":') + 19
        endTournamentIDSearch = tournamentSource.find(",", startTournamentIDSearch)
        tournamentID = tournamentSource[startTournamentIDSearch:endTournamentIDSearch]
        print("Tournament ID found: " + str(tournamentID))
        break
    except Exception:
        system("cls")
        print("Unable to find tournament for \"{}\", please try again.".format(tournamentURL))





while True: 
    system("cls")
    #searching out tournament participants
    try: 
        tournamentSource = scrapePage("https://api.challonge.com/v1/tournaments/" + str(tournamentID) + ".json?api_key=" + apiKey + "&include_participants=1")
    except:
        print("There was an issue loading the tournament. Please check that your API Key is correct. Would you like to re-enter your key?\nY: Yes\nN: No\n")
        keyResetInput = input("Reset Key: ").strip().lower()
        if keyResetInput == "y":
            remove(path.join(SCRIPT_DIRECTORY, "config.json"))
        system("cls")
        input("This program will now close. Press any key to continue: ")
        quit()
        

    #load the JSON
    tournamentJSON = loads(tournamentSource)
    print("Name: " + tournamentJSON["tournament"]["name"])
    print("Game: " + tournamentJSON["tournament"]["game_name"])
    print("Participant Count: " + str(tournamentJSON["tournament"]["participants_count"]))
    
    tournamentStarted = tournamentJSON["tournament"]["state"] != "pending"

    #Get participants
    participantsJSON = tournamentJSON["tournament"]["participants"]

    print("\nLoading participants...")
    #loads the saved list of players
    fullPlayerDict: dict = dict()
    # For actual players in the tournament
    activePlayerDict: dict = dict()
    try:
        savedPlayers = open(path.join(SCRIPT_DIRECTORY, "players.json"), "r")
        fullPlayerDict = loads(savedPlayers.read())
        savedPlayers.close()
    except IOError:
        print("Generating players.json")

    newPlayerCount = 0
    knownPlayerCount = 0
    noDiscordCount = 0
    #Finding new players that aren't already logged.
    for participant in participantsJSON:
        #get the name
        participantName = participant["participant"]["name"]
        
        # retrieve the username instead if the regular name is blank for some ungodly stupid reason
        if participantName == "":
            participantName = participant["participant"]["username"]
        
        # If they are new, add them to the books.
        if participantName not in fullPlayerDict:
            fullPlayerDict[participantName] = None
            newPlayerCount += 1
            noDiscordCount += 1         
        else:
            knownPlayerCount += 1
            if fullPlayerDict[participantName] == None:
                noDiscordCount += 1

        playerInfo = {
            "name": participantName,
            "discordID": fullPlayerDict[participantName]
        }
        activePlayerDict[participant["participant"]["id"]] = playerInfo

    print("New players: " + str(newPlayerCount))
    print("Known players: " + str(knownPlayerCount))
    print("Players missing Discord ID: " + str(noDiscordCount))

    # Saving players.json
    try:
        with open(path.join(SCRIPT_DIRECTORY, "players.json"), "w") as outfile:
            outfile.write(dumps(fullPlayerDict, indent=0))
    except IOError:
        print("Failed to save players.json")

    if not tournamentStarted:
        print("The tournament has not started yet.")

    print("\nQ: Quit")
    if tournamentStarted:
        print("0: Load Tournament Matches")
    print("1: Refresh Tournament & Participants")


    mainMenuInput = input("Select an option: ").strip().lower()
    if mainMenuInput == "q":
        quit()
    elif mainMenuInput == "0" and tournamentStarted:
        # Begin calling current available matches.
        matchSource = scrapePage("https://api.challonge.com/v1/tournaments/" + str(tournamentID) + "/matches.json?api_key=" + apiKey)
        matchJSON = loads(matchSource)
        callStreamMatch = False
        matchList: list[Match] = list()
        matchCallInt = None
        while True:
            # Loading matchlist
            if matchCallInt == None:
                matchList.clear()
                for tournamentMatch in matchJSON:
                    if tournamentMatch["match"]["player2_id"] and tournamentMatch["match"]["state"] == "open": 
                        player1ID = tournamentMatch["match"]["player1_id"]
                        player2ID = tournamentMatch["match"]["player2_id"]
                        matchList.append(Match(
                            activePlayerDict[player1ID]["name"],
                            activePlayerDict[player2ID]["name"],
                            activePlayerDict[player1ID]["discordID"],
                            activePlayerDict[player2ID]["discordID"],
                            ))
                        print(activePlayerDict[tournamentMatch["match"]["player1_id"]]["name"], "vs", activePlayerDict[tournamentMatch["match"]["player2_id"]]["name"], tournamentMatch["match"]["state"])

            matchMenu = """Welcome to Shosoul's challonge match caller!
Stream Match Mode: {}

Commands:
B: Back
R: Refresh Matches
S: Toggle Stream Match Mode

Pending Callable Matches:""".format("YES" if callStreamMatch else "NO")
            matchIndex = 0
            for match in matchList:
                matchMenu += "\n{}: {} VS {}".format(str(matchIndex), match.player1Name, match.player2Name)
                if matchCallInt == matchIndex:
                    matchMenu += " (Copied!)"
                matchIndex += 1
            matchCallInt = None
            system("cls")
            print(matchMenu + "\n")

            menuInput: str = input("Awaiting option: ").strip().lower()
            if menuInput == "b":
                break
            elif menuInput == "r":
                matchSource = scrapePage("https://api.challonge.com/v1/tournaments/" + str(tournamentID) + "/matches.json?api_key=" + apiKey)
                matchJSON = loads(matchSource)
                system("cls")
            elif menuInput == "s":
                callStreamMatch = not callStreamMatch
            elif menuInput.isnumeric():
                try:
                    matchCallInt = int(menuInput)
                    copy(matchList[matchCallInt].getMatchCallString(callStreamMatch))
                    
                except Exception:
                    pass
                    
    
