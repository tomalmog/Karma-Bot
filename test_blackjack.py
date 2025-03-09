# Import necessary modules
import discord
from discord.ext import commands
import random
from time import time
from _sqlite3 import *


# Define the bot itself
client = commands.Bot(command_prefix='.')


# -------------
# Server Events
# -------------


# Detects if a user has joined the server
@client.event
async def on_member_join(member):
    print(f'{member} has joined the server.')


# Detects if a user has left the server
@client.event
async def on_member_remove(member):
    print(f'{member} has left the server.')


# Detects messages and handles everything leveling based
@client.event
async def on_message(message):
    if message.author.id != "743616910205255791":
        conn = connect('users.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS
                  users (
                  user_id integer,
                  user_exp integer,
                  user_last_message real,
                  user_total_messages integer,
                  user_level integer,
                  user_next_level_exp
                  )""")
        conn.commit()

        user_id = message.author.id
        c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user_information = c.fetchone()

        if not user_information:
            c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (user_id, random.randint(15, 26), time(), 1, 0, 75))
        else:
            user_exp = user_information[1]
            user_last_message = user_information[2]
            user_total_messages = user_information[3]
            user_level = user_information[4]
            user_next_level_exp = user_information[5]
            if user_last_message + 60 < time():
                user_exp += random.randint(15, 26)
                if user_exp >= user_next_level_exp:
                    user_level += 1
                    user_exp -= user_next_level_exp
                    user_next_level_exp *= 1.1
            c.execute("UPDATE users SET user_exp=?, user_last_message=?, user_total_messages=?, user_level=? WHERE user_id=?", (user_exp, time(), user_total_messages + 1, user_level, user_id))

        conn.commit()
        conn.close()


    #--------------
    #Blackjack
    #---------------
    if message.content == '.blackjack':

        channel = message.channel
        author = message.author

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

        cards = ['ace','2','3','4','5','6','7'
            ,'8','9','10','jack','queen','king']

        dealer = []

        dealer.append(random.choice(cards))
        shown = random.choice(cards)
        dealer.append(shown)

        await channel.send(f'Dealer Has {shown} shown')

        hand = [random.choice(cards), random.choice(cards)]

        outcome = ''
        while outcome not in ('lost', 'stand'):

            await channel.send(f'Your hand is {hand} do you hit or stand?')

            def check(m):
                return (m.content == 'hit' or m.content == 'stand') and m.channel == channel

            msg = await client.wait_for('message', check=check)
            message.content = msg

            print(message.content)

            if (message.content).lower() == 'hit':
                hand.append(random.choice(cards))

                if add(hand) > 21:
                    outcome = 'lost'
            elif (message.content).lower() == 'stand':
                outcome = 'stand'

        if outcome == 'lost':
            print("You lose ", hand, dealer, add(hand), add(dealer))

        else:
            while add(dealer) < 17:
                dealer.append(random.choice(cards))

            if add(dealer) > 21 or add(hand) > add(dealer):
                print('You win ', hand, dealer, add(hand), add(dealer))

            elif add(dealer) > add(hand):
                print('You lose ', hand, dealer, add(hand), add(dealer))

            else:
                print('Draw ', hand, dealer, add(hand), add(dealer))

    await client.process_commands(message)
