import os, discord, csv, re, sys
from dotenv import load_dotenv
from discord import app_commands, Client
from discord.ext import tasks
from discord.flags import Intents

from class_checker import Class_Checker

# Prepare constant value from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CREDENTIALS = {
    'SOLAR_ID': os.getenv('SOLAR_ID'),
    'SOLAR_PWD': os.getenv('SOLAR_PWD')
}
GUILD_ID = discord.Object(id=int(os.getenv('GUILD_ID')))

# ? Probably permissions
intents = discord.Intents.default()
intents.message_content = True

# prepare file paths (must be in absolute path)
class_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'classes.csv')
user_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.csv')

# initialize required variables
classes = dict()

# initialize required classes
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
class_checker = Class_Checker(CREDENTIALS)

# ========= HELPER FUNCTIONS =========
def is_registered(interaction: discord.Interaction):
    if interaction.user.id in classes:
        return True
    else:
        return False

# ========= EVENTS =========
@bot.event
async def on_ready():
    # Read registered users
    user_csv_file = open(user_file_path, 'r')
    try:
        for user_id in next(csv.reader(user_csv_file, delimiter=',')):
            classes[int(user_id)] = []
    except StopIteration:
        print("No rows in the CSV file.", file=sys.stderr)
    finally:
        user_csv_file.close()

    # Read registered class information
    class_csv_file = open(class_file_path, 'r')
    for row in csv.DictReader(class_csv_file, delimiter=','):
        class_info = {
            'course_subject': row['course_subject'],
            'course_number': row['course_number'],
            'section_number': row['section_number']
        }
        user_id = row['user_id']
        if user_id in classes:
            classes[user_id].append(class_info)
        else:
            classes[user_id] = [class_info]
    class_csv_file.close()

    # sync the slash commands
    await tree.sync(guild=GUILD_ID)
    print("RUNNING...")

# ========= SLASH COMMANDS =========
@tree.command(name='testing', description='This command is for testing purpose')
async def prompt(interaction: discord.Interaction):
    await interaction.response.send_message("HI THERE")

@tree.command()
async def register(interaction: discord.Interaction):
    user_id = interaction.user.id

    # If user is already registered, prompt the user and return
    if user_id in classes:
        await interaction.response.send_message('Already Registered!')
        return

    # Otherwise, add the user_id as a key to the classes then prompt the user
    classes[user_id] = []
    await interaction.response.send_message('Successfully registered!')

@tree.command()
@app_commands.check(is_registered)
async def request(interaction: discord.Interaction, section_number: str, course_subject: str, course_number: str):
    user_id = interaction.user.id

    # Check if section number is correct
    match = re.search(r'\d{5}', section_number)
    if not match:
        await interaction.response.send_message("Section Number must be 5 numbers!", ephemeral=True)
    
    # Check if course subject is correct
    match = re.search(r'[a-zA-Z]{3}', course_subject)
    if not match:
        await interaction.response.send_message("Course Subject must be 3 alphabets!", ephemeral=True)
    course_subject = course_subject.upper()

    # Check if course number is correct
    match = re.search(r'\d{3}', course_number)
    if not match:
        await interaction.response.send_message("Course Number must be 3 numbers!", ephemeral=True)

    class_info = {
            'course_subject': course_subject,
            'course_number': course_number,
            'section_number': section_number
    }
    classes[user_id].append(class_info)

    await interaction.response.send_message("Successfuly added the class!")

@tree.command()
@app_commands.check(is_registered)
async def show(interaction: discord.Interaction):
    user_id = interaction.user.id

    messages = ""
    for _class in classes[user_id]:
        messages += f"[{_class['section_number']}] {_class['course_subject']} {_class['course_number']}"
    
    if not messages:
        messages = "No courses are requested yet"

    await interaction.response.send_message(messages)

# ========= LOOPS =========
#TODO change class_checker functions into async
# @tasks.loop(seconds=5.0)
# async def notify():
#     # Write the data to the file
#     user_csv_file = open(user_file_path, 'w')
#     if len(classes.keys()) != 0:
#         user_csv_file.write(','.join(str(key) for key in list(classes)))
#     user_csv_file.close()

#     class_csv_file = open(class_file_path, 'w')
#     data = "user_id,section_number,course_subject,course_number\n"
#     for user_id in classes:
#         for _class in classes[user_id]:
#             data += f"{user_id},{_class['section_number']},{_class['course_subject']},{_class['course_number']}\n"
#     class_csv_file.write(data)
#     class_csv_file.close()

#     # check classes for each user
#     class_checker.login()
#     for user_id in classes:
#         # Collect information (heavy task)
#         messages = ""
#         for _class in classes[user_id]:
#             course_subject = _class['course_subject']
#             course_number =  _class['course_number']
#             section_number = _class['section_number']
#             status, instructor = class_checker.find(course_subject,course_number,section_number)
#             messages += f"[{section_number}] {course_subject} {course_number} - {instructor} is now {status}\n"

#         # Send a message if any course is available
#         if messages:
#             messages = "NEW UPDATE!\n\n" + messages
#             user = await bot.fetch_user(int(user_id))  
#             await user.send(messages)
#     class_checker.quit()

# ========= ERROR =========
@request.error
@show.error
async def on_check_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.CheckFailure):
        await interaction.response.send_message("Please register first!")
    else:
        await interaction.response.send_message(f"Error occurred! {error}")

bot.run(TOKEN)