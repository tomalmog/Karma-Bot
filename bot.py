# Import necessary modules
import discord
from discord.ext import commands
from discord.utils import get as dis_get
import random
from time import time
from _sqlite3 import *
import chess as pychess
from PIL import Image
import platform
import numpy as np

# Define the bot itself
client = commands.Bot(command_prefix='.')
client.remove_command('help')

# -------------------
# Important functions
# -------------------


def paste_image(original, new, location):
    im1 = original.load()
    im2 = new.load()
    for i in range(new.size[0]):
        for j in range(new.size[1]):
            if im2[i, j] != (0, 0, 0, 0):
                im1[i+location[0], j+location[1]] = im2[i, j]


def make_board(board_texture, board):
    x, y = 0, 0
    pieces_dict = {'r': 'rook', 'n': 'knight', 'b': 'bishop', 'q': 'queen', 'k': 'king', 'p': 'pawn'}
    pieces = board.pieces
    pieces = str(pieces).split("'")[1]
    for i in pieces:
        if i == '/':
            x, y = 0, y + 1
        elif i.lower() in pieces_dict:
            if i.lower() == i:
                color = 'black'
            else:
                color = 'white'
            if platform.system() == 'Windows':
                img = Image.open(f'Chess Textures\\{color}_{pieces_dict[i.lower()]}.png')
            else:
                img = Image.open(f'Chess Textures/{color}_{pieces_dict[i.lower()]}.png')
            paste_image(board_texture, img, (x * 64 + 64, y * 64, x * 64 + 64, y * 64 + 64))
            x += 1
        else:
            x += int(i)
        if x == 8 and y == 7:
            break
    if platform.system() == 'Windows':
        board_texture.save('Chess Textures\\board_with_pieces.png')
    else:
        board_texture.save('Chess Textures/board_with_pieces.png')


def make_connect_four_board(board):
    board_texture = Image.open("Connect Four Textures\\board_test.png")
    red_texture = Image.open("Connect Four Textures\\red.png")
    yellow_texture = Image.open("Connect Four Textures\\yellow.png")
    for i, j in enumerate(board):
        for k, l in enumerate(j):
            if l == 1:
                paste_image(board_texture, red_texture, (i*50, k*50))
            elif l == 2:
                paste_image(board_texture, yellow_texture, (i * 50, k * 50))
    board_texture.save("Connect Four Textures\\board_with_pieces.png")


def check_connect_four_win(board, pos, movement, piece, count):
    if count == 4:
        return True
    elif pos[0]+movement[0] >= 0 <= pos[1]+movement[1]:
        if board[pos[0] + movement[0]][pos[1] + movement[1]] == piece:
            pos[0] += movement[0]
            pos[1] += movement[1]
            return check_connect_four_win(board, pos, movement, piece, count + 1)
        else:
            return False





# -------------
# Server Events
# -------------


# Detects if a user has joined the server and gives the new user the 'Member' role
@client.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="🟨 Member")
    await member.add_roles(role)


# Detects if a user has left the server
@client.event
async def on_member_remove(member):
    print(f'{member} has left the server.')


# Detects messages and handles everything leveling based
@client.event
async def on_message(message):
    if not message.author.bot:
        conn = connect('leveling.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS
                  users (
                  user_id integer,
                  user_exp integer,
                  user_last_message real,
                  user_total_messages integer,
                  user_level integer,
                  user_next_level_exp integer
                  )""")
        conn.commit()
        user_id = message.author.id
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user_information = c.fetchone()

        currency_db = connect('currency.db')
        cursor = currency_db.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS
                  currency (
                  user_id integer,
                  user_balance real,
                  user_played_games integer,
                  user_debt real,
                  user_last_daily,
                  user_last_weekly
                  )""")
        currency_db.commit()
        cursor.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
        currency_info = cursor.fetchone()

        if not user_information:
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, random.randint(15, 25), time(), 1, 0, 75))
            cursor.execute("INSERT INTO currency VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, 500, 0, 0, 0, 0))
        else:
            user_exp = user_information[1]
            user_last_message = user_information[2]
            user_total_messages = user_information[3]
            user_level = user_information[4]
            user_next_level_exp = user_information[5]
            balance = currency_info[1]
            if user_last_message + 60 < time():
                user_exp += random.randint(15, 25)
                if user_exp >= user_next_level_exp:
                    user_level += 1
                    user_exp -= user_next_level_exp
                    user_next_level_exp = round(user_next_level_exp * 1.1)
                    balance += 1000
                    if str(message.guild).lower() == 'karma':
                        channel = client.get_channel(745735613533388882)
                        await channel.send(f"{message.author.mention} you have leveled up and gained 1000 credits, you are now level {user_level}")
                    else:
                        channel = message.channel
                        await channel.send(f"{message.author.mention} you have leveled up and gained 1000 credits, you are now level {user_level}")
            user_total_messages += 1
            c.execute(
                "UPDATE users SET user_exp=?, user_last_message=?, user_total_messages=?, user_level=?, user_next_level_exp=? WHERE user_id=?",
                (user_exp, time(), user_total_messages, user_level, user_next_level_exp, user_id))
            cursor.execute("UPDATE currency SET user_balance=? WHERE user_id=?", (balance, user_id))
        currency_db.commit()
        currency_db.close()
        conn.commit()
        conn.close()

    # Logs every message and puts it into admin logs
    admin_log = client.get_channel(745851154034065408)
    if message.author.id != 743616910205255791 and message.guild.name.lower() == 'karma':
        await admin_log.send(f'>>> {message.author}: {message.content}\n **from channel**: {message.channel}')

    await client.process_commands(message)


# Detects deleted messages
@client.event
async def on_message_delete(message):
    # Logs every deleted message and puts it into admin logs
    admin_log = client.get_channel(745851154034065408)
    if message.author.id != 743616910205255791 and message.guild.name.lower() == 'karma':
        await admin_log.send(
            f'>>> {message.author} has deleted: {message.content}\n **from channel**: {message.channel}')


# ---------------------
# Text Channel commands
# ---------------------

# Admin Commands

# Erases the x most recent lines, not including the original message
@client.command()
async def purge(ctx, *args):
    if ctx.message.author.guild_permissions.administrator:
        await ctx.channel.purge(limit=int(args[0]) + 1)
    else:
        await ctx.send('You do not have permission to do this')

# Member commands

# Returns the bot's ping
@client.command()
async def ping(ctx):
    await ctx.send(f'{round(client.latency * 1000)}ms')


# Return a randomly selected item from a list, as long as that item isn't == "jim"
@client.command()
async def choose(ctx, *args):
    try:
        winner = args[random.randint(0, len(args)-1)]
        await ctx.send(f'{winner} has won')
    except:
        await ctx.send(f'Invalid input, use .help for more information')


# Returns a random int from 90 - 100 if the author is Mema or Cluck, otherwise returns a random int from 0 - 50
@client.command()
async def rigged(ctx):
    if ctx.author.name in ["The Joker", "Cluck"]:
        await ctx.send(f'{ctx.author.mention} has rolled a(n) {random.randint(90, 100)}')
    else:
        await ctx.send(f'{ctx.author.mention} has rolled a(n) {random.randint(0, 50)}')


# Returns a random dice roll, is rigged in favor of Cluck and Mema
@client.command()
async def diceroll(ctx):
    await ctx.send(f'{ctx.author.mention} has rolled a(n) {random.randint(0, 100)} :game_die:')

# Returns the author's stats
@client.command()
async def stats(ctx):
    user_id = ctx.author.id
    conn = connect('leveling.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_information = c.fetchone()
    embed = discord.Embed(title=f'Stats: {ctx.author.name}')
    embed.add_field(name=f"Level", value=f"{user_information[4]}", inline=False)
    embed.add_field(name="Current XP", value=f"{user_information[1]}", inline=False)
    embed.add_field(name="XP Needed For Next Level", value=f"{user_information[5]}", inline=False)
    embed.add_field(name="Total Messages", value=f"{user_information[3]}", inline=False)
    await ctx.send(content=None, embed=embed)


# Plays a game of RPS
@client.command()
async def rps(ctx, move):
    try:
        wins = {'rock': 'scissors', 'paper': 'rock', 'scissors': 'paper'}
        bot_move = random.choice(list(wins))
        if wins[move] == bot_move: await ctx.send(f'You played {move}, Bot played {bot_move}. You win')
        elif wins[bot_move] == move: await ctx.send(f'You played {move}, Bot played {bot_move}. Bot wins')
        else: await ctx.send(f"You played {move}, Bot played {bot_move}. It's a tie")
    except:
        await ctx.send(f'Invalid input, use .help for more information')


# Flips a coin
@client.command()
async def cf(ctx):
    await ctx.send(random.choice(["Heads", "Tails"]))


# Plays Blackjack With The Bot
@client.command()
async def blackjack(ctx, *args):
    channel = ctx.channel
    author = ctx.author.name

    #Gets the users balance information
    user_id = ctx.author.id
    conn = connect('currency.db')
    c = conn.cursor()
    c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
    user_bal = c.fetchone()[1]

    #Checks for errors before starting the game
    try:
        bet = float(args[0])
    except:
        await ctx.send('Please enter an integer value as balance.')
        return None

    if bet > user_bal:
        await ctx.send('You have bet more than you have.')
        return None
    elif bet < 100:
        await ctx.send('The minimum bet is $100.')
        return None

    # Function to add cards up
    def add(hand):
        value = 0
        aces = 0
        for card in hand:
            if card not in ('jack', 'queen', 'king', 'ace'):
                value += int(card)
            elif card in ('jack', 'queen', 'king'):
                value += 10
            elif card == 'ace':
                aces += 1

        if value + aces - 1 > 10 or aces == 0:
            value += aces
        else:
            value += 10 + aces

        return value

    # Sets up starting deck for both dealer and player
    cards = ['ace', '2', '3', '4', '5', '6', '7'
        , '8', '9', '10', 'jack', 'queen', 'king']
    dealer = []
    dealer.append(random.choice(cards))
    shown = random.choice(cards)
    dealer.append(shown)
    hand = [random.choice(cards), random.choice(cards)]
    outcome = ''

    # Plays game
    while outcome not in ('lost', 'stand'):
        embed = discord.Embed(title="Game Stats", description="Cards")
        embed.add_field(name="Dealer", value=f"{shown}")
        embed.add_field(name="Your Hand", value=f"{hand}\n{add(hand)}")
        await ctx.send(content=None, embed=embed)

        if add(hand) != 21:
            def check(m):
                return (m.content.lower() == 'hit' or m.content.lower() == 'stand') and m.channel == channel and m.author.name == author
            msg = await client.wait_for('message', check=check)
            msg = msg.content
        else:
            msg = 'stand'

        if (msg).lower() == 'hit':
            hand.append(random.choice(cards))

            if add(hand) > 21:
                outcome = 'lost'

        elif (msg).lower() == 'stand':
            outcome = 'stand'

    # Determines outcome of the game
    if outcome == 'lost':
        embed = discord.Embed(title="You Lost!", description="Cards")
        embed.add_field(name="Dealer", value=f"{dealer}\n{add(dealer)}")
        embed.add_field(name="Your Hand", value=f"{hand}\n{add(hand)}")
        await ctx.send(content=None, embed=embed)
        await eco_give(ctx, ctx.author, -bet, 0)
    else:
        while add(dealer) < 17:
            dealer.append(random.choice(cards))
        if add(dealer) > 21 or add(hand) > add(dealer):
            embed = discord.Embed(title="You Won!", description="Cards")
            embed.add_field(name="Dealer", value=f"{dealer}\n{add(dealer)}")
            embed.add_field(name="Your Hand", value=f"{hand}\n{add(hand)}")
            await ctx.send(content=None, embed=embed)
            if len(hand) == 2 and add(hand) == 21:
                await eco_give(ctx, ctx.author, bet * 1.5, 0)
            else:
                await eco_give(ctx, ctx.author, bet, 0)

        elif add(dealer) > add(hand):
            embed = discord.Embed(title="You Lost!", description="Cards")
            embed.add_field(name="Dealer", value=f"{dealer}\n{add(dealer)}")
            embed.add_field(name="Your Hand", value=f"{hand}\n{add(hand)}")
            await ctx.send(content=None, embed=embed)
            await eco_give(ctx, ctx.author, -bet, 0)

        else:
            embed = discord.Embed(title="Draw!", description="Cards")
            embed.add_field(name="Dealer", value=f"{dealer}\n{add(dealer)}")
            embed.add_field(name="Your Hand", value=f"{hand}\n{add(hand)}")
            await ctx.send(content=None, embed=embed)


@client.command(pass_context=True)
async def chess(ctx, *args):
    board = pychess.Board()
    user_id = ctx.message.author.id
    channel = ctx.message.channel
    moves = 0
    run = False
    outcome = True


    def check_answer(m):
        return m.author.id == enemy_id

    def check_move(m):
        # if board.turn: return m.author.id==user_id
        # else: return m.author.id == enemy_id
        return m.author.id in [user_id, enemy_id]


    if len(ctx.message.mentions) == 0:
        await ctx.send('You did not specify an opponent.')
        run = False
        run_bot = True
    elif len(ctx.message.mentions) == 1:
        enemy_id = ctx.message.mentions[0].id
        await ctx.send(f'{ctx.message.mentions[0].mention} do you accept this challenge? Answer with Yes or No')
        response = await client.wait_for('message', check=check_answer)
        response = response.content.lower()
        if response == 'yes':
            await ctx.send(f'{ctx.message.author.mention} your challenge has been accepted')
            run = True
            run_bot = False
        else:
            await ctx.send(f'{ctx.message.author.mention} your challenge has been denied')
            run = False
            run_bot = False
            outcome = False


    while run:
        if platform.system() == 'Windows':
            print(f'\n\n\n\n\n\n\n\n\n{platform.system()}')
            board_texture = Image.open('Chess Textures\\board_with_numbers.png')
            make_board(board_texture, board)
            file = discord.File('Chess Textures\\board_with_pieces.png')
        else:
            board_texture = Image.open('Chess Textures/board_with_numbers.png')
            make_board(board_texture, board)
            file = discord.File('Chess Textures/board_with_pieces.png')

        await channel.send(file=file)
        msg = await client.wait_for('message', check=check_move)
        if not outcome:
            run = False
            break

        if msg.content.lower() == 'resign':
            outcome = False
            await ctx.send(f"{msg.author.mention} has resigned the game.")
            if msg.author.id == user_id: await ctx.send(f"{ctx.message.mentions[0].mention} you have won the game.")
            else: await ctx.send(f"{ctx.message.author.mention} you have won the game.")
        elif msg.content.lower() == 'draw':
            if msg.author.id == user_id:
                await ctx.send(f'{msg.author.mention} has offered a draw, {ctx.message.mentions[0].mention} do you accept?')
                draw_msg = await client.wait_for('message', check=lambda m:m.author.id == enemy_id)
                if draw_msg.content.lower() == 'yes':
                    await ctx.send("This game has ended in a draw.")
                    outcome = False
                else:
                    await ctx.send(f'{msg.author.mention} your draw offer has been rejected')
            else:
                await ctx.send(f'{msg.author.mention} has offered a draw, {ctx.message.author.mention} do you accept? Answer with Yes or No.')
                draw_msg = await client.wait_for('message', check=lambda m:m.author.id == ctx.message.author.id)
                if draw_msg.content.lower() == 'yes':
                    await ctx.send("This game has ended in a draw.")
                    outcome = False
                else:
                    await ctx.send(f'{msg.author.mention} your draw offer has been rejected')

        elif msg.content.lower() == 'help':
            e = discord.Embed(title='Chess Help')
            e.add_field(name='Resign', value='To resign a game, simply type \'resign\'.')
            e.add_field(name='Draw', value='To offer a draw, simply type \'draw\', if the opponent accepts the draw then the game ends in a tie.')
            e.add_field(name='How to move', value='To move a piece, first, find that piece\'s position with the given numbers '
                                                  'and letters, the position is the letter column, then the number row. '
                                                  'For example, the position of the piece in the bottom left corner is \'a1\'. '
                                                  'After you find the piece\'s position, find the position you want to move the piece to, and combine them. '
                                                  'A valid move at the start of the game would be \'e2e4\'.', inline=False)
            e.add_field(name='How to promote', value="To promote a pawn to a piece, simply type out the move and at the end add a 'q' for a queen, 'r' for a rook', 'n' for a knight and 'b' for a bishop."
                                                     ' For example, to promote a pawn on a7 to a queen, you would have to make the move \'a7a8q\'.')
            await ctx.send(content=None, embed=e)
        else:
            try:
                if msg.author.id == user_id and board.turn:
                    board.push_uci(msg.content.lower())
                    await ctx.send("Move performed successfully.")
                    moves += 1
                elif msg.author.id == enemy_id and not board.turn:
                    board.push_uci(msg.content.lower())
                    await ctx.send("Move performed successfully.")
                    moves += 1
            except ValueError:
                await ctx.send("Invalid Move, type \"help\" for information about how to move.")

        if board.is_seventyfive_moves():
            await ctx.send("This game has ended in a tie. This is due to the seventy five move rule.")
            outcome = False
        elif board.is_insufficient_material():
            await ctx.send("This game has ended in a tie. This is due to neither sides having sufficient material to checkmate.")
            outcome = False
        elif board.can_claim_draw():
            await ctx.send("This game has ended in a tie. This is due to threefold repetition.")
            outcome = False
        elif board.is_stalemate():
            await ctx.send("This game has ended in a tie. This is due to a player being put into a stalemate position.")
            outcome = False
        elif board.is_checkmate():
            if moves%2 == 1:
                await ctx.send(f'{ctx.message.author.mention} has won this game.')
                outcome = False
            else:
                await ctx.send(f'{ctx.message.mentions[0].mention} has won this game.')
                outcome = False


@client.command()
async def ree(ctx):
    print(client.user.id)



@client.command()
async def connect_four(ctx, *args):
    winner = ''
    loser = ''
    run = False
    valid_gamble = True
    against_bot = False
    if len(ctx.message.mentions) == 0:
        await ctx.send('Invalid User')
        run = False
    if len(args) > 1:
        user_id = ctx.author.id
        conn = connect('currency.db')
        c = conn.cursor()
        c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
        user_bal = c.fetchone()[1]
        conn.close()
        try:
            gamble = int(args[1])
        except:
            gamble = ''
        if type(gamble) == int:
            if gamble < 100:
                await ctx.send(f'{ctx.message.author.mention} you can only gamble values of 100 or more')
                run = False
                valid_gamble = False
            elif gamble > user_bal:
                await ctx.send(f'{ctx.message.author.mention} you can not gamble more than you own')
                run = False
                valid_gamble = False
            else:
                run = True
                valid_gamble = True
        else:
            await ctx.send(f'{ctx.message.author.mention} you can only gamble integer values')
            run = False
            valid_gamble = False
    if len(ctx.message.mentions) == 1 and valid_gamble:
        if ctx.message.mentions[0].id != 743616910205255791:
            channel = ctx.message.channel
            author = ctx.message.author
            opponent = ctx.message.mentions[0]
            await ctx.send(f'{opponent.mention} do you accept the challenge? Yes or No: ')
            def check_game_accept(m):
                return m.channel == channel and m.author.id == opponent.id
            msg = await client.wait_for('message', check=check_game_accept)
            if msg.content.lower() == 'yes':
                run = True
                await ctx.send(f'{author.mention}, {opponent.mention} has accepted your challenge')
            else:
                await ctx.send(f'{author.mention}, {opponent.mention} has declined your challenge')
                run = False
        else:
            if len(args) > 1:
                await ctx.send(f"You can't gamble against the bot in connect four")
                run = False
            else:
                channel = ctx.message.channel
                author = ctx.message.author
                opponent = ctx.message.mentions[0]
                against_bot = True
                run = True





    board = np.zeros((7, 6))
    turn = 0
    reverse = {'1️⃣': 1, '2️⃣': 2, '3️⃣': 3, '4️⃣': 4, '5️⃣': 5, '6️⃣': 6, '7️⃣': 7, '🏳':8}
    piece_per_row = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
    moves = [[0, 1], [1, 1], [-1, 1], [1, 0], [-1, 0], [0, -1], [1, -1], [-1, -1]]
    while run:
        make_connect_four_board(board)
        file = discord.File('Connect Four Textures\\board_with_pieces.png')
        on_disc_board = await channel.send(file=file)
        for i in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '🏳']:
            if i == '🏳':
                await on_disc_board.add_reaction(i)
            else:
                if piece_per_row[reverse[i]-1] <= 5:
                    await on_disc_board.add_reaction(i)
        if turn % 2 == 0:
            current = author
            opposite = opponent
            num = 1
            im = Image.open('Connect Four Textures\\red.png')
        else:
            current = opponent
            opposite = author
            num = 2
            im = Image.open('Connect Four Textures\\yellow.png')

        if against_bot and current != author:
            reaction = random.choice([x for x in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣'] if piece_per_row[reverse[x]-1] <= 5])
        else:
            move, user = await client.wait_for('reaction_add', check=lambda move, user: move.emoji in ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '🏳'] and user.name == current.name)
            reaction = move.emoji

        if reaction == '🏳':
            await ctx.send(f"{current.mention} has resigned the game, {opposite.mention} has won.")
            run = False
            winner = opposite
            loser = current
        else:
            choice = reverse[reaction] - 1
            count = 5-piece_per_row[choice]
            piece_per_row[choice] += 1
            board[choice][count] = num
            turn += 1
        for move in moves:
            try:
                if check_connect_four_win(board, [choice, count], move, num, 1):
                    make_connect_four_board(board)
                    file = discord.File('Connect Four Textures\\board_with_pieces.png')
                    await channel.send(file=file)
                    await ctx.send(f'{current.mention} has won the game against {opposite.mention}')
                    run = False
                    winner = current
                    loser = opposite
            except:
                pass

    if len(args) > 1 and winner!='':
        await eco_give(ctx, winner, int(args[1]), 0)
        await eco_give(ctx, loser, int(args[1])*-1, 0)








# Plays a game
@client.command()
async def boxthing(ctx):
    author = ctx.author.name

    board = [
        [':red_square:', ':red_square:', ':red_square:', ':red_square:', ':red_square:', ':red_square:',
         ':red_square:'],
        [':red_square:', ':white_large_square:', ':white_large_square:', ':white_large_square:', ':white_large_square:',
         ':white_large_square:', ':red_square:'],
        [':red_square:', ':white_large_square:', ':white_large_square:', ':white_large_square:', ':white_large_square:',
         ':white_large_square:', ':red_square:'],
        [':red_square:', ':white_large_square:', ':white_large_square:', ':white_square_button:',
         ':white_large_square:', ':white_large_square:', ':red_square:'],
        [':red_square:', ':white_large_square:', ':red_square:', ':white_large_square:', ':white_large_square:',
         ':white_large_square:', ':red_square:'],
        [':red_square:', ':white_large_square:', ':white_large_square:', ':white_large_square:', ':white_large_square:',
         ':white_large_square:', ':red_square:'],
        [':red_square:', ':red_square:', ':red_square:', ':red_square:', ':red_square:', ':red_square:', ':red_square:']
    ]

    coords = [3, 3]

    while True:
        display = ''
        for layer in board:
            display += ''.join(layer) + '\n'

        embed = discord.Embed(title="Game")
        embed.add_field(name='Use Reactions To Move or Stop the Bot', value=display)
        msg = await ctx.send(content=None, embed=embed)

        temp_coords = list(coords)

        await msg.add_reaction('⬆')
        await msg.add_reaction('⬇')
        await msg.add_reaction('➡')
        await msg.add_reaction('⬅')
        await msg.add_reaction('⛔')

        move, user = await client.wait_for('reaction_add',
                                           check=lambda move, user: move.emoji in '⬆⬇➡⬅⛔' and user.name == author)

        if move.emoji == '⬆' and board[coords[0] - 1][coords[1]] != ':red_square:':
            coords[0] -= 1
        elif move.emoji == '⬇' and board[coords[0] + 1][coords[1]] != ':red_square:':
            coords[0] += 1
        elif move.emoji == '⬅' and board[coords[0]][coords[1] - 1] != ':red_square:':
            coords[1] -= 1
        elif move.emoji == '➡' and board[coords[0]][coords[1] + 1] != ':red_square:':
            coords[1] += 1

        if temp_coords != coords:
            board[coords[0]][coords[1]] = ':white_square_button:'
            board[temp_coords[0]][temp_coords[1]] = ':white_large_square:'

        if move.emoji == '⛔':
            break


# Gives a help menu
@client.command()
async def help(ctx, *args):
    if not args:
        embed = discord.Embed(title="Important Commands", description=f"List of commands.\nUse {client.command_prefix}help (command) for more information")
        embed.add_field(name=f"{client.command_prefix}ping", value="`Shows the bot's ping`")
        embed.add_field(name=f"{client.command_prefix}choose (users)", value="`Choose from a list of people`")
        embed.add_field(name=f"{client.command_prefix}purge (number)", value="`Deletes messages`")
        embed.add_field(name=f"{client.command_prefix}rigged", value="`Does a diceroll rigged for Mema and Cluck`")
        embed.add_field(name=f"{client.command_prefix}diceroll", value="`Rolls a 100 sided dice`")
        embed.add_field(name=f"{client.command_prefix}stats", value="`Shows your leveling stats`")
        embed.add_field(name=f"{client.command_prefix}rps (move)", value="`Plays rock paper scissors with the bot`")
        embed.add_field(name=f"{client.command_prefix}blackjack (number)", value="`Plays blackjack with the bot`")
        await ctx.send(content=None, embed=embed)
    else:
        command = args[0]
        if command == 'ping':
            embed = discord.Embed(title=f"Command: ping")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}ping", inline=False)
            embed.add_field(name="Description:", value=f"This command returns the bot's ping", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'choose':
            embed = discord.Embed(title=f"Command: choose")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}choose (list)", inline=False)
            embed.add_field(name="Description:", value=f"This command chooses a random item from the list it is given."
                                                       f"\n Note, this list is seperated by spaces, not commas", inline=False)
            embed.add_field(name="Example:", value=f".choose 1 2 3", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'rigged':
            embed = discord.Embed(title=f"Command: rigged")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}rigged", inline=False)
            embed.add_field(name="Description:", value=f"This command returns a random number from 0-100, it is rigged in the bot creater's favour ",inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'diceroll':
            embed = discord.Embed(title=f"Command: diceroll")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}diceroll", inline=False)
            embed.add_field(name="Description:", value=f"This commands returns a random number from 0-100", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'stats':
            embed = discord.Embed(title=f"Command: stats")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}stats", inline=False)
            embed.add_field(name="Description:", value=f"This command returns the user's server statistics."
                                                      f"\n Note, this does cross over servers as long as they have the Karma Bot in them", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'rps':
            embed = discord.Embed(title=f"Command: rps")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}rps (move)", inline=False)
            embed.add_field(name="Description:", value=f"This command plays a game of rock, paper, scissors with the bot", inline=False)
            embed.add_field(name="Example:", value=f".rps paper", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'cf':
            embed = discord.Embed(title=f"Command: cf")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}cf", inline=False)
            embed.add_field(name="Description:", value=f"This command flips a coin and returns the result", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'blackjack':
            embed = discord.Embed(title=f"Command: blackjack")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}blackjack (number >= 100)", inline=False)
            embed.add_field(name="Description:", value=f"This command plays a game of blackjack with the bot."
                                                       f"\n Note, you will have to tell the bot whether or not you hit or stand", inline=False)
            embed.add_field(name="Example: ", value=f"{client.command_prefix}blackjack 100", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'pay':
            embed = discord.Embed(title=f"Command: pay")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}pay (user) (amount)", inline=False)
            embed.add_field(name="Description:", value=f"This command pays a specified user a specified amount of credits.", inline=False)
            embed.add_field(name="Example: ", value=f"{client.command_prefix}pay {client.user.mention} 750", inline=False)
            await ctx.send(content=None, embed=embed)
        elif command == 'bal':
            embed = discord.Embed(title=f"Command: bal")
            embed.add_field(name="Correct Usage: ", value=f"{client.command_prefix}bal (user)", inline=False)
            embed.add_field(name="Description:", value=f"This command returns the specified user's balance."
                                                       f"\nNote, if no user is specified, it will return the author's balance.", inline=False)
            embed.add_field(name="Example: ", value=f"{client.command_prefix}bal {client.user.mention}", inline=False)
            await ctx.send(content=None, embed=embed)
        else:
            await ctx.send(f"Unknown command, cannot help")

@client.command()
async def tictactoe(ctx, user2:discord.User, diff='hard'):
    channel = ctx.channel
    author = ctx.author.name
    user1 = ctx.author

    board = [[':white_large_square:',':white_large_square:',':white_large_square:'],
             [':white_large_square:',':white_large_square:',':white_large_square:'],
             [':white_large_square:',':white_large_square:',':white_large_square:']]
    message = ''
    for row in board:
        message += "".join(row) + '\n'

    if not user2.bot:
        await ctx.send(f'{user2.mention} do you accept the challenge? Yes or No: ')
        def check(m):
            return (m.content.lower() == 'yes' or m.content.lower() == 'no') and m.channel == channel and m.author.name == user2.name
        msg = await client.wait_for('message', check=check)
        msg = msg.content

    if not user2.bot:
        if msg == 'no':
            await ctx.send(f'{user1.mention}, your challenge has been denied!')
            return None
        else:
            await ctx.send(f'{user1.mention}, your challenge has been accepted!')

    win = False
    turn = 0

    def check_win(pos):
        if pos[0] != ':white_large_square:':
            if pos[0]==pos[1] and pos[1]==pos[2]:
                return pos[0], True
        return None, False

    def check_win_bot(boards):
            for pos in boards:
                if pos[0] != ':white_large_square:':
                    if pos[0]==pos[1] and pos[1]==pos[2]:
                        return pos[0]
            return False

    def sep_board(board):
        checks = [[board[0][0], board[1][1], board[2][2]],
                  [board[0][2], board[1][1], board[2][0]],
                  [board[0][0], board[1][0], board[2][0]],
                  [board[0][1], board[1][1], board[2][1]],
                  [board[0][2], board[1][2], board[2][2]],
                  [board[0][0], board[0][1], board[0][2]],
                  [board[1][0], board[1][1], board[1][2]],
                  [board[2][0], board[2][1], board[2][2]]]

        return checks

    def full(board):
        op = True
        for i in board:
            if ':white_large_square:' in i:
                op = False

        return op

    def make_move(board, x, y):
        fl = []
        for thing in board:
            for thin in thing:
                fl.append(thin)

        if fl.count(':white_large_square:') % 2 == 1:
            board[x][y] = ':x:'
        else:
            board[x][y] = ':o:'

        return board

    def make_board():
        board = []
        rows = [0,0,0]
        for i in range(3):
            board.append(list(rows))

        return board

    def best_move(board, diff):
        bestMove = None
        best_score = -999999999999999999

        board = board
        for i in range(3):
            for j in range(3):
                if board[i][j] == ':white_large_square:':
                    board = make_move(board, i,j)
                    score = nextMove(False, ':o:', board, 1, 1, diff)
                    board[i][j] = ':white_large_square:'
                    if score > best_score:
                        best_score = score
                        bestMove = (i, j)
        board = make_move(board, bestMove[0], bestMove[1])
        return board

    def nextMove(max_turn, symbol, board, layer, o_layer, diff):
        if check_win_bot(sep_board(board)) != False:
            return 1 if check_win_bot(sep_board(board)) == symbol else -1
        elif full(board):
            return 0

        if diff.lower() == 'hard':
            depth = 100
        elif diff.lower() == 'medium':
            depth = 4
        elif diff.lower() == 'easy':
            depth = 2
        elif diff.lower() == 'baby':
            depth = 1
        else:
            depth = 100

        if layer - o_layer == depth:
            if check_win_bot(sep_board(board)) != False:
                return 1 if check_win_bot(sep_board(board)) == symbol else -1
            else:
                return 0

        scores = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == ':white_large_square:':
                    board = make_move(board,i ,j)
                    scores.append(nextMove(not max_turn, symbol, board, layer+1, o_layer, diff))
                    board[i][j] = ':white_large_square:'

        return max(scores) if max_turn else min(scores)

    while not win and 'white_large_square' in message:
        msg = await ctx.send(message)

        turn = -turn + 1
        if turn == 1:
            user_going = user1
        else:
            user_going = user2

        if not user2.bot or turn == 1:
            numbers = {1:'1️⃣',
                       2:'2️⃣',
                       3:'3️⃣',
                       4:'4️⃣',
                       5:'5️⃣',
                       6:'6️⃣',
                       7:'7️⃣',
                       8:'8️⃣',
                       9:'9️⃣'}

            for i in range(3):
                for j in range(3):
                    if board[i][j] == ':white_large_square:':
                        emote = numbers[3*i+j+1]
                        await msg.add_reaction(emote)

            move, user = await client.wait_for('reaction_add',
                                               check=lambda move, user: move.emoji in '1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣' and user.name == user_going.name)

            reverse_numbers = {'1️⃣':1,
                               '2️⃣':2,
                               '3️⃣':3,
                               '4️⃣':4,
                               '5️⃣':5,
                               '6️⃣':6,
                               '7️⃣':7,
                               '8️⃣':8,
                               '9️⃣':9}
            choice = reverse_numbers[move.emoji] - 1
            row = choice // 3
            col = choice % 3

            if turn == 1:
                board[row][col] = ':x:'
            else:
                board[row][col] = ':o:'
        else:
            board = best_move(board, diff)

        message = ''
        for row in board:
            message += "".join(row) + '\n'

        checks = sep_board(board)

        for check in checks:
            outcome, win = check_win(check)

            if win:
                break

    await ctx.send(message)
    if win:
        await ctx.send(f'{user_going.mention} has won!')
    else:
        await ctx.send(f'Game has ended in a draw!')

#Test command
@client.command()
async def test(ctx):
    if ctx.author.name == 'The Joker':
        return 1
    await eco_give(ctx, -100)


# -----------------
# Currency commands
# -----------------


# Admin commands


@client.command(pass_context=True)
async def eco_give(ctx, user:discord.Member, money, *code):
    if len(code) > 0: code = code[0]
    else: code = 1
    if ctx.message.author.guild_permissions.administrator or ctx.author.name in ['Cluck'] or code == 0:
        user_id = user.id
        conn = connect('currency.db')
        c = conn.cursor()
        c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
        user_info = c.fetchone()
        c.execute("UPDATE currency SET user_balance=? WHERE user_id=?", (user_info[1] + float(money), user_id))
        conn.commit()
        if float(money) >= 0:
            await ctx.send(f"{user.mention}, {money} Karma Coin(s) have been given to you, your balance is now {float(user_info[1] + float(money))}")
        else:
            await ctx.send(f"{user.mention}, {-money} Karma Coin(s) have been taken from you, your balance is now {float(user_info[1] + float(money))}")
    else:
        await ctx.send(f'You do not have permission to do this')


@client.command(pass_context=True)
async def eco_set(ctx, user:discord.Member, money):
    if ctx.message.author.guild_permissions.administrator or ctx.author.name in ['Cluck']:
        user_id = user.id
        conn = connect('currency.db')
        c = conn.cursor()
        c.execute("UPDATE currency SET user_balance=? WHERE user_id=?", (money, user_id))
        conn.commit()
        await ctx.send(f"{user.mention}'s balance is now {money}")
    else:
        await ctx.send(f'You do not have permission to do this')


# User commands


# Returns the specified player's balance, if not specified, returns the author's balance
@client.command(pass_context=True)
async def bal(ctx, user=None):
    if len(ctx.message.mentions) > 0:
        user = ctx.message.mentions[0]
    if not user:
        user_id = ctx.author.id
        conn = connect('currency.db')
        c = conn.cursor()
        c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
        user_info = c.fetchone()
        await ctx.send(f"{ctx.message.author.mention} your balance is {user_info[1]}")
    else:
        try:
            user_id = user.id
            conn = connect('currency.db')
            c = conn.cursor()
            c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
            user_info = c.fetchone()
            await ctx.send(f"{user.mention}'s bal is {user_info[1]}")
        except:
            await ctx.send(f"Invalid user")


# Pays the specified user, money is taken away from the author
@client.command()
async def pay(ctx, user=None, money=None, test=None):
    try:
        money = int(money)
    except:
        pass
    if user == None or money == None or test != None:
        await ctx.send(f"Invalid use of command, use {client.command_prefix}help for more information")
    elif type(money) not in [int, float]:
        await ctx.send(f"Invalid use of command, use {client.command_prefix}help for more information")
    elif len(ctx.message.mentions) == 0:
        await ctx.send(f"Invalid use of command, use {client.command_prefix}help for more information")
    elif money <= 0:
        await ctx.send(f"You can only pay values greater than 0")
    elif len(ctx.message.mentions) == 1:
        user = ctx.message.mentions[0]
        user_id = ctx.author.id
        conn = connect('currency.db')
        c = conn.cursor()
        c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
        user_info = c.fetchone()
        if user_info[1] >= money:
            await eco_give(ctx, user, float(money), 0)
            await eco_give(ctx, ctx.author, -float(money), 0)
        else:
            await ctx.send(f"You do not have enough money to do this")


@client.command()
async def daily(ctx):
    user_id = ctx.message.author.id
    conn = connect('currency.db')
    c = conn.cursor()
    c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
    user_info = c.fetchone()
    if user_info[4] + 86400 < time():
        c.execute("UPDATE currency SET user_last_daily=?, user_balance=? WHERE user_id=?", (time(), user_info[1] + 500, user_id))
        conn.commit()
        conn.close()
        await ctx.send(f"You have claimed your daily reward, your balance is now {user_info[1] + 500}")
    else:
        time_until_next = round(user_info[4] + 86400 - time())
        times = {'hours':time_until_next//3600, 'minutes':(time_until_next%3600)//60, 'seconds':(time_until_next%3600%60)}
        await ctx.send(f"You have used already your daily in the past 24 hours, time until next use: {times['hours']} hours, {times['minutes']} minutes, {times['seconds']} seconds")


@client.command()
async def weekly(ctx):
    user_id = ctx.message.author.id
    conn = connect('currency.db')
    c = conn.cursor()
    c.execute("SELECT * FROM currency WHERE user_id=?", (user_id,))
    user_info = c.fetchone()
    if user_info[5] + 604800 < time():
        print(user_info[5], user_info[5] + 604800, time())
        c.execute("UPDATE currency SET user_last_weekly=?, user_balance=? WHERE user_id=?", (time(), user_info[1] + 5000, user_id))
        conn.commit()
        conn.close()
        await ctx.send(f"You have claimed your weekly reward, your balance is now {user_info[1] + 5000}")
    else:
        time_until_next = round(user_info[5] + 604800 - time())
        times = {'days':time_until_next//86400, 'hours':(time_until_next%86400)//3600, 'minutes':(time_until_next%86400%3600)//60, 'seconds':(time_until_next&86400%3600%60)}
        await ctx.send(f"You have used already your weekly in the past 7 days, time until next use: {times['days']} days, {times['hours']} hours, {times['minutes']} minutes, {times['seconds']} seconds")


@client.command()
async def slots(ctx, money=0):
    if not money == None:
        numbers = [':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:', ":cherries:"]
        result = [f'{random.choice(numbers)}', f'{random.choice(numbers)}', f'{random.choice(numbers)}']
        if result[0] == result[1] == result[2]:
            await eco_give(ctx, ctx.message.author, int(money)*5, 0)
            await ctx.send(f'You have won slots, you have gained {int(money)*5} credits')
        await ctx.send(result)


# -----------
# Run the bot
# -----------

if __name__ == '__main__':
    client.run('secret')
