import asyncio
import discord
import requests
from discord.ext import commands
from time import strftime
from dateutil import parser
from datetime import datetime
import os

prefix = '>'
alarmList2 = {}  # Dictionary of lists of alarms

description = "A simple alarm clock bot.\ntype "+prefix+"help for help."
bot = commands.Bot(command_prefix=prefix, description=description)
client = discord.Client()


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('-'*20)
    await bot.change_presence(activity=discord.Game(name='>help'))


# BEGIN COMMANDS-------------------- คำสั่ง

@bot.command()  # TIME COMMAND
async def time(ctx):
    """displays the current time."""
    time_str = strftime("%H:%M:%S")
    await ctx.send("```"+time_str+"```")
    del time_str

@bot.command()  # BTC COMMAND
async def btc(ctx):
    """displays the current btc."""
    response = requests.get('https://api.coindesk.com/v1/bpi/currentprice.json')
    data = response.json()
    await ctx.send("```" + "Current price is " + data["bpi"]["USD"]["rate"] + " US Dollar" + "```")


@bot.command()  # COVID-19 COMMAND
async def covid(ctx):
    """displays the current covid."""
    response1 = requests.get('https://covid19.ddc.moph.go.th/api/Cases/today-cases-all')
    data1 = response1.json()
    await ctx.send("```" + str(data1[0]['total_case']) + "```")
    print(data1)


# END COMMANDS----------------------

# BEGIN ALIASES--------------------- ชื่อที่ใช้เรียกฟังก์ชัน

@bot.command(pass_context=True)
async def la(ctx):
    """lists all currently active alarms. Short for ListAlarms."""
    await internal_alarmlist(ctx)


@bot.command(pass_context=True)
async def alarm(ctx, time):
    """sets an alarm for the given time / date."""
    await internal_alarm(ctx, time)


@bot.command(pass_context=True)
async def a(ctx, in_time):
    """sets an alarm for the given time / date. Short for alarm."""
    await internal_alarm(ctx, in_time)


@bot.command(pass_context=True)
async def d(ctx, ind):
    """removes the alarm at the given index from the alarmList. Alias of delete."""
    await internal_remove_alarm(ctx, ind)


@bot.command(pass_context=True)
async def rm(ctx, ind):
    """removes the alarm at the given index from the alarmList. Alias of delete."""
    await internal_remove_alarm(ctx, ind)


@bot.command(pass_context=True)
async def delete(ctx, ind):
    """removes the alarm at the given index from the alarmList."""
    await internal_remove_alarm(ctx, ind)


@bot.command(pass_context=True)
async def remove(ctx, ind):
    """removes the alarm at the given index from the alarmList. Alias of delete."""
    await internal_remove_alarm(ctx, ind)


# END ALIASES-----------------------

# BEGIN FUNCTIONS------------------- ฟังก์ชัน
    

async def internal_alarmlist(contx):  # ALARMLIST COMMAND
    """lists all currently active alarms."""
    embed = discord.Embed(title=":alarm_clock:Alarm List", color=0x00ff00)
    embed.set_thumbnail(url="http://cdn.iphonehacks.com/wp-content/uploads/2017/01/alarm-icon-29.png")
    print('Current alarm list:')
    if contx.channel not in alarmList2.keys() or alarmList2[contx.channel] == []:
        await contx.send('no alarms have yet been set in this channel. add one with ' + prefix + 'alarm [time].')
        return
    for i in range(len(alarmList2[contx.channel])):
        embed.add_field(name='#' + str(i + 1) + ':' + str(alarmList2[contx.channel][i].name).split('#', 1)[0],
                        value=str(alarmList2[contx.channel][i].time), inline=True)
        print('#' + str(i + 1) + ':' + str(alarmList2[contx.channel][i].name) + " -> " + str(alarmList2[contx.channel][i].time))
    print('-'*50)
    await contx.send(embed=embed)


async def internal_alarm(contx, inp):  # ALARM COMMAND
    """sets an alarm for the given time / date."""
    try:
        alarm_time = parser.parse(inp)
    except:
        await contx.send(":negative_squared_cross_mark:Please use the Format \"[M-D-Y] H:M:S\".\
__Examples:__\
12-24 10:00 --> 24th Dec of the current year, 10:00:00.\
12:30 --> 12:30, today.\
__if no date is supplied, the current day will be used.__")
        return
    if alarm_time < datetime.now():
        await contx.send('The date / time you supplied is in the past. No alarm has been set.')
        return

    temp = Alarm(contx.author, alarm_time)
    if contx.channel not in alarmList2.keys():
        alarmList2.update({contx.channel: []})

    alarmList2[contx.channel].append(temp)  # add the alarm to the list at the index (channel)
    del temp

    await contx.send(
        ":white_check_mark:" + contx.author.mention + "'s alarm is now set to **" + str(alarm_time.date()) + ", " + str(
            alarm_time.time()) + "**!")


async def internal_remove_alarm(contx, index):
    index = int(index) - 1
    if contx.author == alarmList2[contx.channel][index].name:  # you shouldn't be able to delete other people's alarms
        alarm_time = alarmList2[contx.channel][index].time
        await contx.send(":white_check_mark:Your alarm for **" + str(alarm_time.date()) + ", "
                         + str(alarm_time.time()) + "** has been removed.")
        del alarmList2[contx.channel][index]
        del alarm_time
    else:
        await contx.send("the alarm at the Index you entered does not belong to you.")


# END FUNCTIONS---------------------

# BEGIN CLASSES--------------------- class ที่ใช้เก็บเวลา ที่ผู้ใช้ใช้คำสั่งนาฬิกาปลุก

class Alarm:
    name = None
    time = None

    def __init__(self, usr, t):
        self.name = usr
        self.time = t


# END CLASSES-----------------------

# BEGIN BACKGROUND TASKS------------ การทำงานของนาฬิกาปลุก

async def check_alarms():
    await bot.wait_until_ready()
    while not bot.is_closed():
        for alarmList in alarmList2.values():
            for i in range(len(alarmList)):
                if alarmList[i].time < datetime.now():
                    await alarmList[i].name.create_dm()
                    await alarmList[i].name.dm_channel.send(content=":alarm_clock:Your alarm for **"+str(alarmList[i].time)+"** just rang!")
                    print("alarm of "+str(alarmList[i].name)+" just rang!")
                    alarmList.pop(i)
        await asyncio.sleep(5)  # task runs every 5 seconds


# END BACKGROUND TASKS--------------

bot.loop.create_task(check_alarms())
bot.run('TOKEN')