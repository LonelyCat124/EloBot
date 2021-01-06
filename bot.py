import discord
import math

client = discord.Client()

players = {}
scale = 100
K = 30
filter_count = 0


def fake_init():
    global players
    for i in range(10):
        player = {}
        player['wins'] = 0
        player['losses'] = 0
        player['ELO'] = 150
        players['{}'.format(i)] = player
    print(players)

def new_player(name, ELO):
    global players
    player = {}
    player['wins'] = 0
    player['losses'] = 0
    player['ELO'] = ELO
    players[name] = player

def print_table():
    global players, filter_count
    valid_players = []
    ELOs = []
    for player in players:
        if players[player]['wins'] + players[player]['losses'] >= filter_count:
            valid_players.append(player)
            ELOs.append(players[player]['ELO'])
    valid_players, ELOs = zip(*sorted(zip(valid_players, ELOs)))
    
    string = '```'
    string = string + '{:30s} {:6s}\n'.format('Name', 'Elo')
    for i in range(len(valid_players)):
        string = string + '{:30s} {:6f}\n'.format(valid_players[i], ELOs[i])
    string = string + '```'
    return string


def guess_balance(player_list):
    global players 
    Elos = []
    for player in player_list:
        Elos.append(players[player]['ELO'])
    player_list, Elos = zip(*sorted(zip(player_list, ELOs)))
    team1 = []
    team2 = []
    team1.append(player_list[0])
    team1Elo = Elos[0]
    team1count = 1
    team2.append(player_list[1])
    team2Elo = Elos[1]
    team2.append(player_list[2])
    team2Elo = team2Elo + Elos[2]
    team2count = 2
    next_slot = 3
    while team1count < 5 and team2count < 5:
        if team1Elo < team2Elo:
            team1.append(player_list[next_slot])
            team1Elo = team1Elo + Elos[next_slot]
            team1count = team1count + 1
            next_slot = next_slot + 1
        else:
            team2.append(player_list[next_slot])
            team2Elo = team2Elo + Elos[next_slot]
            team2count = team2count + 1
            next_slot = next_slot + 1
    if team1count < 5:
        for i in range(next_slot, 10):
            team1.append(player_list[i])
    if team2count < 5:
        for i in range(next_slot, 10):
            team2.append(player_list[i])
    string = '```\n'
    string = string + 'Team 1: {} {} {} {} {}\n'.format(team1[0], team1[1], team1[2], team1[3], team1[4])
    string = string + 'Team 2: {} {} {} {} {}\n'.format(team2[0], team2[1], team2[2], team2[3], team2[4])
    string = '```\n'
    return string


def process_result(winning_players, losing_players):
    global players, scale, K
    teama_rating = 0.0
    teamb_rating = 0.0
    for name in winning_players:
        teama_rating = teama_rating + players[name]['ELO']
    for name in losing_players:
        teamb_rating = teamb_rating + players[name]['ELO']
    
    x = teama_rating - teamb_rating
    exponent = -(x/scale)
    expected = 1.0 / (1.0 + math.exp(exponent))
    rating_change = (1-expected) * K
    for name in winning_players:
        players[name]['ELO'] = players[name]['ELO'] + rating_change
    for name in losing_players:
        players[name]['ELO'] = players[name]['ELO'] - rating_change
    print(players)


def edit_player(name, ELO):
    global players
    players[name]['ELO'] = ELO


@client.event
async def on_ready():
    fake_init()
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global players
    if message.author == client.user:
        return
    
    roles = message.author.roles
    respond = False
    for role in roles:
        if role.name == 'test_role':
            respond = True

    if message.content.startswith('!hello'):
        await message.channel.send('Hello {}!'.format(message.author.name))
        #print(message.author.roles)

    if message.content.startswith('!printtable') and respond:
        await message.channel.send(print_table())

    if message.content.startswith('!player') and respond:
        string = message.content
        array = string.split(' ')
        valid = True
        if len(array) != 3:
            valid = False
        if valid:
            name = array[1]
            ELO = array[2]
        
            try:
                ELO = float(ELO)
            except:
                valid = False
        
        if not valid:
            await message.channel.send('Incorrect format, try !player <name> <value>')
        elif players.get(name) != None:
            await message.channel.send("Player {} already in records".format(name))
        else:
            new_player(name, ELO)
            await message.channel.send('Added player {}'.format(name))


    if message.content.startswith('!help'):
        string = 'Available commands (* denotes admin only)\n'
        string = string + '!hello : Bot says hello :)'
        string = string + '!printtable : Prints the Elo table'
        string = string + '!balance <list of 10 player names> : Gives a rough guess at balancing (YMMV) - NYI'
        string = string + '* !result <five> <players> <who> <won> <game> <five> <players> <who> <lost> <game> : Reports a result'
        string = string + '* !player <name> <initial rating> : Add a new player to the leaderboard'
        string = string + '* !edit <name> <new rating> : Edit an existing player (they\'re added if not already present)'
        message.channel.send(string)
    
    if message.content.startswith('!edit') and respond:
        string = message.content
        array = string.split(' ')
        valid = True
        if len(array) != 3:
            valid = False
        if valid:
            name = array[1]
            ELO = array[2]
        
            try:
                ELO = float(ELO)
            except:
                valid = False
        
        if not valid:
            await message.channel.send('Incorrect format, try !player <name> <value>')
        elif players.get(name) == None:
            new_player(name, ELO)
            await message.channel.send('Added player {}'.format(name))
        else:
            edit_player(name,ELO)

    
    if message.content.startswith('!result') and respond:
        string = message.content
        string = string[8:]
        array = string.split(' ')
        valid = True
        known_players = True
        unknown_players = []
        if len(array) != 10:
            valid = False
        winning_players = []
        losing_players = []
        if valid:
            for i in range(5):
                winning_players.append(array[i])
                if players.get(array[i]) == None:
                    valid = False
                    known_players = False
                    unknown_players.append(array[i])
            for i in range(5,10):
                losing_players.append(array[i])
                if players.get(array[i]) == None:
                    valid = False
                    known_players = False
                    unknown_players.append(array[i])
        if not valid:
            if known_players:
                await message.channel.send('Incorrect format, try !result <five> <players> <who> <won> <game> <five> <players> <who> <lost> <game>')
            else:
                await message.channel.send('Unknown players in here, add with !player first: {}'.format(unknown_players))
        else:
            process_result(winning_players, losing_players)

        if message.content.startswith('!balance'):
        string = message.content
        string = string[9:]
        array = string.split(' ')
        valid = True
        known_players = True
        unknown_players = []
        if len(array) != 10:
            valid = False
        game_players = []
        if valid:
            for i in range(5):
                game_players.append(array[i])
                if players.get(array[i]) == None:
                    valid = False
                    known_players = False
                    unknown_players.append(array[i])
            for i in range(5,10):
                game_players.append(array[i])
                if players.get(array[i]) == None:
                    valid = False
                    known_players = False
                    unknown_players.append(array[i])
        if not valid:
            if known_players:
                await message.channel.send('Incorrect format, try !result <five> <players> <who> <won> <game> <five> <players> <who> <lost> <game>')
            else:
                await message.channel.send('Unknown players in here, add with !player first: {}'.format(unknown_players))
        else:
            await message.channel.send(guess_balance(game_players))



token = ''
with open('token.txt', 'r') as f:
    token = f.readline()
#print(token)
client.run(token)