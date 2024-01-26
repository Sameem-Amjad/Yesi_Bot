import discord
from discord.ext import commands
import re
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access environment variables
token = os.getenv('TOKEN')
prefix = os.getenv('PREFIX')

# Now you can use 'token' and 'prefix' in your script

intents = discord.Intents.default()
intents.message_content = True  # Enable message-related events, including message content

bot = commands.Bot(command_prefix=prefix, intents=intents)

# Cooldown durations in seconds
PREMIUM_COOLDOWN = 1800  # 30 minutes
BASIC_COOLDOWN = 7200    # 2 hours

# Define the roles that can use the command
PREMIUM_ROLE = "Premium Ai Buyer"
BASIC_ROLE = "Basic Ai Buyer"

# Cooldown mapping to store user cooldowns
cooldowns = {}

def read_ping_values():
    ping_values = {}
    with open('pings.txt', 'r') as ping_file:
        for line in ping_file:
            parts = line.strip().split()
            if parts:
                ping_match = re.match(r'\[?(\d+)[\+\]]?', parts[0])
                if ping_match:
                    ping = int(ping_match.group(1))
                    coordinates = re.findall(r'(\d+\.\d+)[XY]', line)
                    if len(coordinates) == 2:
                        pred_x, pred_y = map(float, coordinates)
                        ping_values[ping] = {"pred_x": pred_x, "pred_y": pred_y}
    return ping_values
def update_config_file(ping_value):
    print(ping_value)
    config_path = 'for custom.cfg'

    # Read existing data from config.cfg
    with open(config_path, 'r') as config_file:
        config_lines = config_file.readlines()

    # Find and update pred_x and pred_y values
    for i, line in enumerate(config_lines):
        if 'pred_x' in line:
            config_lines[i] = f'pred_x = "{ping_value["pred_x"]}"\n'
        elif 'pred_y' in line:
            config_lines[i] = f'pred_y = "{ping_value["pred_y"]}"\n'

    # Write the updated data back to config.cfg
    with open(config_path, 'w') as config_file:
        config_file.writelines(config_lines)
def is_premium(ctx):
    return discord.utils.get(ctx.author.roles, name=PREMIUM_ROLE) is not None

def is_basic(ctx):
    return discord.utils.get(ctx.author.roles, name=BASIC_ROLE) is not None

def get_cooldown(ctx):
    if is_premium(ctx):
        return PREMIUM_COOLDOWN
    elif is_basic(ctx):
        return BASIC_COOLDOWN
    else:
        return 0

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
@bot.event
async def on_message(message):
    # Check if the message is from a bot to avoid processing own messages
    if message.author.bot:
        return

    # Authorization check
    if not (is_premium(message) or is_basic(message)):
        await message.channel.send(content="You are not a Basic or premium user.")
        return

    # Print the content of the message
    print(f"Message received: {message.content}")

    # Process commands or perform other actions here
    await bot.process_commands(message)

@bot.command(name='gen')
@commands.check_any(commands.check(is_premium), commands.check(is_basic))
@commands.cooldown(1, 1, commands.BucketType.user)  # Use a default cooldown, will be overridden by the custom cooldown
async def generate_config(ctx, ping_value: int):
    try:
        print("Sameem")
        await bot.get_command('gen').reset_cooldown(ctx)
        if not (is_premium(ctx) or is_basic(ctx)):
            await ctx.send(content="You are not authorized to use this command.")
            return

        ping_values = read_ping_values()

        if ping_value in ping_values:
            data_for_ping_value = ping_values[ping_value]

            update_config_file(data_for_ping_value)

            # Save the updated file
            file_path = 'for_custom.cfg'
            with open(file_path, 'w') as updated_config_file:
                for key, value in data_for_ping_value.items():
                    updated_config_file.write(f"{key} = {value}\n")

            # Send the updated file in a direct message to the user
            await ctx.author.send(content=f"Configuration file updated with ping {ping_value}",
                                  file=discord.File(file_path, filename='for_custom.cfg'))

            await ctx.send(content=f"Configuration file sent to your DM. Cooldown: {get_cooldown(ctx)} seconds")
        else:
            await ctx.send(content=f"Error: Ping {ping_value} not found in pings.txt")

    except commands.CommandOnCooldown as e:
        await ctx.send(f"Command on cooldown. Please wait {round(e.retry_after)} seconds.")
    except Exception as e:
        print(f"Error: {str(e)}")
        await ctx.send(content=f"Error: {str(e)}")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run(token)
