import sys
import json
import time
import discord
import random
import asyncio

from utils import create_tables, sqlite, http, brawlcalc
from discord.ext import commands

with open("config.json", "r") as f:
    config = json.load(f)


tables = create_tables.creation(debug=True)
if not tables:
    sys.exit(1)


bot = commands.Bot(
    command_prefix=config["prefix"], prefix=config["prefix"],
    command_attrs=dict(hidden=True)
)


class Brawlhalla(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.no_account = "You don't seem to have any account, set one up with `bh!set Your_SteamID64`"
        self.db = sqlite.Database()
        print("Logging in...")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Ready: {self.bot.user} | Servers: {len(self.bot.guilds)}')
        await self.bot.change_presence(
            activity=discord.Activity(type=3, name=config["playing"]),
            status=discord.Status.online
        )

    @commands.command()
    async def ping(self, ctx):
        """ Pong! """
        before = time.monotonic()
        before_ws = int(round(self.bot.latency * 1000, 1))
        message = await ctx.send("Loading...")
        ping = int((time.monotonic() - before) * 1000)
        await message.edit(content=f"🏓 WS: {before_ws}ms  |  REST: {ping}ms")

    @commands.command()
    async def source(self, ctx):
        """ Check out my source code <3 """
        await ctx.send(f"**{ctx.bot.user}** is powered by this source code:\nhttps://github.com/AlexFlipnote/Brawlhalla.py")

    def brawlhalla_account(self, user_id: int):
        """ Fetch BrawlhallaID from DB """
        data = self.db.fetchrow("SELECT * FROM accounts WHERE user_id=?", (user_id,))
        return data["brawlhalla_id"] if data else None

    async def brawlhalla_info(self, brawlhallaid: int, data: str = "info"):
        """ Fetch brawlhalla info from BrawlhallaID """
        if data == "ranked":
            api_url = f'https://api.brawlhalla.com/player/{brawlhallaid}/ranked?api_key={config["brawlhalla_token"]}'
        else:
            api_url = f'https://api.brawlhalla.com/player/{brawlhallaid}/stats?api_key={config["brawlhalla_token"]}'

        try:
            r = await http.get(api_url, res_method="json", no_cache=True)
        except Exception:
            return None
        return r

    @commands.command(name="set")
    async def set_account(self, ctx, *, steamid64: int):
        """ Set your brawlhalla account with SteamID64 """
        try:
            r = await http.get(f"https://api.brawlhalla.com/search?steamid={steamid64}&api_key={config['brawlhalla_token']}", res_method="json")
            failed = False
        except Exception:
            failed = True

        if failed or not r:
            return await ctx.send(
                "The API didn't return any information...\n"
                "If you want to check your SteamID64, visit <https://steamidfinder.com/>"
            )

        account = self.brawlhalla_account(ctx.author.id)
        confirmcode = random.randint(10000, 99999)

        def check_confirm(m):
            if (m.author == ctx.author and m.channel == ctx.channel):
                if (m.content.startswith(str(confirmcode))):
                    return True
            return False

        confirm_msg = await ctx.send(
            f"**If the information under is correct, type `{confirmcode}` to confirm your account.**\n\n"
            f"Brawlhalla ID: {r['brawlhalla_id']}\nSteam profile URL: <http://steamcommunity.com/profiles/{steamid64}>"
        )

        try:
            await self.bot.wait_for('message', timeout=30.0, check=check_confirm)
        except asyncio.TimeoutError:
            await confirm_msg.delete()

        if account:
            self.db.execute(
                "UPDATE accounts SET steamid64=?, brwalhalla_id=? WHERE user_id=?",
                (steamid64, r['brawlhalla_id'], ctx.author.id)
            )
        else:
            self.db.execute("INSERT INTO accounts VALUES (?, ?, ?)", (ctx.author.id, steamid64, r['brawlhalla_id']))

        await ctx.send(f"Done, I have {'updated' if account else 'created'} your account, **{ctx.author.name}**")

    @commands.command(aliases=["info"])
    async def stats(self, ctx):
        """ Check your stats in Brawlhalla """
        account = self.brawlhalla_account(ctx.author.id)
        if not account:
            return await ctx.send(self.no_account)

        r = await self.brawlhalla_info(account)

        lose = r['games'] - r['wins']
        kills = sum([g['kos'] for g in r['legends']])
        deaths = sum([g['falls'] + g['suicides'] for g in r['legends']])

        embed = discord.Embed(colour=ctx.author.top_role.colour.value or 0x000000)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        embed.add_field(name="Name", value=r["name"], inline=True)
        embed.add_field(name="Clan", value=r['clan']['clan_name'] if 'clan' in r else 'No clan', inline=True)
        embed.add_field(name="W/L Ratio", value=f"{r['wins']} / {lose} ({round(r['wins'] / lose, 2)})", inline=True)
        embed.add_field(name="K/D Ratio", value=f"{kills} / {deaths} ({round(kills / deaths, 2)})", inline=True)
        embed.add_field(name="Team kills", value=sum([g['teamkos'] for g in r['legends']]), inline=True)
        await ctx.send(content=f"ℹ Brawlhalla stats to **{r['brawlhalla_id']}**", embed=embed)

    @commands.command()
    async def kills(self, ctx):
        """ Check your kill type stats """
        account = self.brawlhalla_account(ctx.author.id)
        if not account:
            return await ctx.send(self.no_account)

        r = await self.brawlhalla_info(account)

        kill_types = [
            ["Bomb", r['kobomb']],
            ["Mine", r['komine']],
            ["Sidekick", r['kosidekick']],
            ["Snowball", r['kosnowball']],
            ["Spikeball", r['kospikeball']],
            ["Thrown item", sum([g['kothrownitem'] for g in r['legends']])],
            ["Unarmed", sum([g['kounarmed'] for g in r['legends']])],
            ["Weapons", sum([g['koweaponone'] + g['koweapontwo'] for g in r['legends']])],
        ]

        embed = discord.Embed(colour=ctx.author.top_role.colour.value or 0x000000)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        for kill, amount in kill_types:
            embed.add_field(name=kill, value=f"{amount:,}", inline=True)
        await ctx.send(content=f"ℹ Brawlhalla kill methods to **{r['brawlhalla_id']}**", embed=embed)

    @commands.command()
    async def ranked(self, ctx):
        """ Check your ranked stats """
        account = self.brawlhalla_account(ctx.author.id)
        if not account:
            return await ctx.send(self.no_account)

        r = await self.brawlhalla_info(account, data="ranked")
        if not r:
            return await ctx.send("Either you haven't played 10 ranked games or the API returned nothing at all...")

        ftwovstwo = next((g for g in sorted(r["2v2"], key=lambda x: x["rating"], reverse=True)), None)
        lose = r['games'] - r['wins']

        embed = discord.Embed(colour=ctx.author.top_role.colour.value or 0x000000)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        embed.add_field(name="Name", value=f'{r["name"]} ({r["region"]})', inline=False)

        onevone_info = [
            f"**Tier:** {r['tier']} ({r['rating']} / {r['peak_rating']} Peak)",
            f"**Win/Lose Ratio:** {r['wins']} / {lose} ({round(r['wins'] / lose, 2)})"
        ]
        embed.add_field(name="1v1 Ranked", value="\n".join(onevone_info), inline=False)

        if ftwovstwo:
            losetwovstwo = ftwovstwo['games'] - ftwovstwo['wins']
            twovtwo_info = [
                f"**Team:** {ftwovstwo['teamname']}",
                f"**Tier:** {ftwovstwo['tier']} ({ftwovstwo['rating']} / {ftwovstwo['peak_rating']} Peak)",
                f"**W/L Ratio:** {ftwovstwo['wins']} / {losetwovstwo} ({round(ftwovstwo['wins'] / losetwovstwo, 2)})"
            ]
            embed.add_field(name="2v2 Ranked", value="\n".join(twovtwo_info), inline=False)
        else:
            embed.add_field(name="2v2 Ranked", value="No info available yet...", inline=False)

        await ctx.send(content=f"ℹ Brawlhalla ranked stats to **{r['brawlhalla_id']}**", embed=embed)

    @commands.command()
    async def glory(self, ctx):
        """ Check your glory for next season """
        account = self.brawlhalla_account(ctx.author.id)
        if not account:
            return await ctx.send(self.no_account)

        data = await self.brawlhalla_info(account, data="ranked")
        if not data:
            return await ctx.send("Either you haven't played 10 ranked games or the API returned nothing at all...")

        embed = discord.Embed(
            colour=ctx.author.top_role.colour.value or 0x000000,
            description=f"{data['name']}'s estimated Glory and 1v1 rating after the ranked season reset are:"
        )

        embed.set_thumbnail(url=ctx.author.avatar_url)

        try:
            sumall2v2 = sum([g["wins"] for g in data["2v2"]])
            estglory = brawlcalc.GetGloryFromBestRating(data["peak_rating"]) + brawlcalc.GetGloryFromWins(sumall2v2 + data["wins"])
        except IndexError:
            estglory = brawlcalc.GetGloryFromBestRating(data["peak_rating"]) + brawlcalc.GetGloryFromWins(data["wins"])

        findnextelonum = brawlcalc.GetPersonalEloFromOldElo(data["rating"])
        findnexteloname = brawlcalc.GetEloName(findnextelonum)

        embed.add_field(name="Estimated Glory", value=estglory, inline=True)
        embed.add_field(name="Estimated Reset Rating", value=f"{findnextelonum} ({findnexteloname})", inline=True)
        await ctx.send(content=f"ℹ Brawlhalla glory/rating estimation to **{data['brawlhalla_id']}**", embed=embed)


bot.add_cog(Brawlhalla(bot))
bot.run(config["token"])
