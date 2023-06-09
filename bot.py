# bot.py
import discord
import logging.handlers
import os
import pytz
import random
import requests
import sqlite3
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging()
logger = logging.getLogger()
load_dotenv()

time = datetime.now(pytz.timezone('US/Central'))
logger.info(f'US Central DateTime {time}')

imdb_api_key = os.getenv("IMDB_API_KEY")
TOKEN = os.getenv("DISCORD_TOKEN")
channel_id = os.getenv("CHANNEL_ID")

client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# https://www.youtube.com/@glowstik/videos < good reference

version = "1.2.69.1"
database = r"C:\github\movie_bot\movie_list.db"
logger.info('attempting db connection')

conn = None
try:
    conn = sqlite3.connect(database)
except Exception as e:
    logger.error("Error in connecting to db")

with conn:
    @client.event
    async def on_ready():
        await client.get_channel(int(channel_id)).send(f"bot is ready. Version: {version}")
        try:
            synced = await client.tree.sync()
            logger.info(f"synced {len(synced)} command(s)")

        except Exception as e:
            print(e)


    @client.tree.command(name="add")
    async def add_movie(interaction: discord.Interaction, movie: str):
        fix_title = movie.title()
        date_time = time.strftime("%d-%m-%Y %H:%M:%S")

        logger.info(f"user {interaction.user} used the add command for this movie {fix_title}")
        await interaction.response.defer()

        curr = conn.cursor()
        curr.execute("SELECT title FROM movie_table WHERE title = ?", [fix_title])
        does_movie_exist = curr.fetchall()

        if does_movie_exist:
            message = f"the movie '{fix_title}' is already on the list. Bitch."

        else:

            url = f'https://imdb-api.com/API/Search/{imdb_api_key}/{fix_title}'

            try:
                request = requests.get(url=url)
                data = request.json()
                logger.info(f"data: {data}")
                imdb_id = data["results"][0]["id"]

            except:
                logger.info(f"no imdb_id for that movie: {movie}")
                imdb_id = None

            message = f"Thank you, {interaction.user.mention}, for adding '{fix_title}' to the list."
            sql = "INSERT INTO movie_table (user_name, insert_date, title, imdb_id) VALUES (?,?,?,?)"
            values = (str(interaction.user), str(date_time), str(fix_title), str(imdb_id))
            logger.info(
                f"Inserting user_name: {interaction.user} "
                f"at this time: {date_time} "
                f"with this movie title: {fix_title} "
                f"with imdb_id: {imdb_id}"
            )
            logger.info(f"SQL insert: {sql} with values: {values}")
            cur = conn.cursor()
            cur.execute(sql, values)
            conn.commit()

        await interaction.followup.send(message)


    @client.tree.command(name="check")
    async def check_for_movie(interaction: discord.Interaction, movie: str):
        fix_title = movie.title()

        logger.info(f"user {interaction.user} used the check command")
        message = f"The movie '{fix_title}' does not exist, add it. Bitch."
        curr = conn.cursor()

        curr.execute("SELECT id, title FROM movie_table WHERE title = ?", [fix_title])

        does_movie_exist = curr.fetchall()

        if does_movie_exist:
            for movie in does_movie_exist:
                message = f"the movie {movie[0]}: {movie[1]} is already on the list. Bitch."
        await interaction.response.send_message(message)


    @client.tree.command(name="watched_list")
    async def watched_movies(interaction: discord.Interaction):
        logger.info(f"user {interaction.user} used the watched_list command")
        curr = conn.cursor()

        curr.execute("SELECT id, user_name, title, removed_date FROM movie_table WHERE watched = 'yes'")

        movie_list = curr.fetchall()
        logger.info("movie_list")
        logger.info(movie_list)

        description = ""
        for movie in movie_list:
            description += f'{movie[0]}: {movie[2]} added by {movie[1]} and removed on {movie[3]}\n\n'

        embed = discord.Embed(title="DMHS Movie Watched List",
                              description=description)
        await interaction.response.send_message(embed=embed)


    @client.tree.command(name="count")
    async def count_list(interaction: discord.Interaction):
        logger.info(f"user {interaction.user} used the count command")
        curr = conn.cursor()

        curr.execute(f"SELECT user_name FROM usernames_table")
        users_from_table = curr.fetchall()
        description = ""

        for user in users_from_table:
            curr.execute("SELECT COUNT(user_name) FROM movie_table WHERE user_name = ?", user)
            totals = curr.fetchall()
            for total in totals:
                description += f'{user[0]}: {total[0]}\n\n'

        embed = discord.Embed(title="User Input Totals",
                              description=description)
        await interaction.response.send_message(embed=embed)


    @client.tree.command(name="list")
    async def list_movies_with_imdb(interaction: discord.Interaction):
        logger.info(f"user {interaction.user} used the list_imdb command")
        curr = conn.cursor()

        curr.execute("SELECT id, user_name, title, imdb_id FROM movie_table WHERE watched IS NULL")
        movie_list = curr.fetchall()

        description = ""
        description_count = 0
        movie_total = len(movie_list)

        page_num = 1
        page_max = (movie_total // 35) + 1

        for movie in movie_list:
            make_link = movie[2]
            if movie[3]:
                make_link = f"[{movie[2]}](https://www.imdb.com/title/{movie[3]}/)"

            description += f'{movie[0]}: {make_link} added by {movie[1]}\n\n'
            description_count = description_count + 1
            footer = f"Page {page_num} of {page_max}"

            if description_count == 35:
                movie_total = movie_total - 35
                description_count = 0
                embed = discord.Embed(title="DMHS Movie List",
                                      description=description)
                embed.set_footer(text=footer)
                description = ""

                if page_num == 1:
                    page_num += 1
                    embed.set_footer(text=footer)
                    await interaction.response.send_message(embed=embed)

                else:
                    page_num += 1
                    embed.set_footer(text=footer)
                    await interaction.followup.send(embed=embed)

            elif movie_total < 35:
                movie_total = movie_total - 1

                if movie_total == 0:
                    page_num += 1
                    embed = discord.Embed(title="DMHS Movie List",
                                          description=description)
                    embed.set_footer(text=footer)
                    await interaction.followup.send(embed=embed)


    @client.tree.command(name="complete_list")
    async def list_all_movies(interaction: discord.Interaction):
        logger.info(f"user {interaction.user} used the complete_list command")

        curr = conn.cursor()
        curr.execute("SELECT id, title, watched FROM movie_table")

        movie_list = curr.fetchall()
        description = ""

        for movie in movie_list:
            watched = "Yes"
            if movie[2] is None:
                watched = "No"

            description += f'{movie[0]}: {movie[1]} | watched: {watched}\n'

        embed = discord.Embed(title="DMHS Movie List",
                              description=description)
        await interaction.response.send_message(embed=embed)


    @client.tree.command(name="random")
    async def select_random(interaction: discord.Interaction):
        logger.info(f"user {interaction.user} used the random command")
        curr = conn.cursor()

        curr.execute("SELECT id FROM movie_table WHERE watched IS NULL")

        movie_ids = curr.fetchall()
        logger.info(f"list of IDs: {movie_ids}")

        movie_ids = [row[0] for row in movie_ids]
        logger.info(f"list of IDs sorted: {movie_ids} ")

        select_random_movie = random.choice(movie_ids)

        curr.execute("SELECT id, user_name, title, imdb_id FROM movie_table WHERE watched IS NULL AND id = ?",
                     [select_random_movie])
        random_movie = curr.fetchall()
        logger.info(f"The chosen movie: {random_movie}")

        description = ""
        for movie in random_movie:
            make_link = movie[2]
            if movie[3]:
                make_link = f"[{movie[2]}](https://www.imdb.com/title/{movie[3]}/)"

            description += f'{movie[0]}: {make_link} added by {movie[1]}\n'

        embed = discord.Embed(title="The random movie selected",
                              description=description)
        await interaction.response.send_message(embed=embed)


    @client.tree.command(name="random_by_user")
    async def select_random_by_user(interaction: discord.Interaction, users: str):
        logger.info(f"user {interaction.user} used the random_by_user command")
        logger.info(f"user names: {users}")
        curr = conn.cursor()

        num_users = len(users.split())

        discord_users = {}
        curr.execute(f"SELECT user_name, discord_id FROM usernames_table")
        users_from_table = curr.fetchall()

        for user in users_from_table:
            discord_users[user[1]] = user[0]

        user_names = "("
        count = 0
        for user in users.split():
            count += 1
            logger.info(f"user: {user}")
            try:
                user_names += "'"
                user_names += discord_users[user]
                if count == num_users:
                    user_names += "'"
                else:
                    user_names += "', "

                logger.info(f"user name found: {discord_users[user]}")

            except:
                logger.info(f"couldn't find a user with that id: {user}")

        user_names += ")"

        logger.info(f"the list of user names: {user_names}")


        try:
            curr.execute(f"SELECT id FROM movie_table WHERE watched IS NULL AND user_name IN {user_names}")
            movie_ids = curr.fetchall()
            logger.info(f"list of IDs: {movie_ids}")

        except:
            await interaction.response.send_message(f"Please make sure to put a space between usernames or "
                                                    f"the command needs a few seconds in between runs.")

        try:
            movie_ids = [row[0] for row in movie_ids]
            logger.info(f"list of IDs sorted: {movie_ids}")

            select_random_movie = random.choice(movie_ids)
            curr.execute("SELECT id, user_name, title, imdb_id FROM movie_table WHERE watched IS NULL AND id = ?",
                         [select_random_movie])
            random_movie = curr.fetchall()
            logger.info(f"The chosen movie: {random_movie}")

            description = ""
            for movie in random_movie:
                make_link = movie[2]
                if movie[3]:
                    make_link = f"[{movie[2]}](https://www.imdb.com/title/{movie[3]}/)"

                description += f'{movie[0]}: {make_link} added by {movie[1]}\n'

            embed = discord.Embed(title="The random movie selected",
                                  description=description)
            await interaction.response.send_message(embed=embed)

        except:
            await interaction.response.send_message(f"Found no movies with those user names, sorry")


    @client.tree.command(name="remove")
    async def remove_movie(interaction: discord.Interaction, movie: int):
        date_time = time.strftime("%d-%m-%Y %H:%M:%S")

        logger.info(f"user {interaction.user} removed {movie} from the list.")
        logger.info(f"Removing {movie} from list")
        cur = conn.cursor()
        cur.execute("UPDATE movie_table SET watched = ?, removed_date = ? WHERE id = ?", ['yes', date_time, movie])
        conn.commit()

        message = f"{interaction.user} removed {movie} from the list at this time {date_time}."

        await interaction.response.send_message(message)


    @client.event
    async def on_message(message):

        if message.author == client.user:
            return

        if 'chow' in message.content.lower():
            chow_quotes = [
                'So long, gayboys!',
                'You wanna make fuck on me?!!',
                'Toodaloo, motherfuckers!',
                "It's funny because he's fat!",
                'CHOW LOVES COCAINE!',
                'Fuck on Chow? Chow fuck on YOU',
                'Oh, your having a bad day? Did you die? But did you die??',

            ]
            response = random.choice(chow_quotes)

        if 'tlsf' in message.content.lower():
            response = "The best streamer, dead or alive."

        await message.channel.send(response)

client.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
