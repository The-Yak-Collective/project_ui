#discord bot to act as UI for projects based on jordans(?) idea that we have a message for each project
#use PROJECT_UI_DISCORD_KEY as an env variable - the key for discord bot. needs read/write permission to channels

#from discord.ext import tasks, commands
import discord
import asyncio
import os
import time
import datetime
import emoji

from dotenv import load_dotenv
from discord.ext import commands

from discord_project_ui import * #including bot

HOMEDIR="/home/yak"


load_dotenv(HOMEDIR+"/"+'.env')
TWEAK_CHAN=705512721847681035 #temporary

@bot.event #needed since it takes time to connect to discord
async def on_ready(): 
    print('We have logged in as {0.user}'.format(bot),  bot.guilds)
    return

#probbaly change to a "is_check()" type function
def allowed(x,y): #is x allowed to play with item created by y
#permissions - some activities can only be done by yakshaver, etc. or by person who initiated action
    if x==y: #same person. setting one to zero will force role check
        return True
    mid=bot.guilds[0].get_member(message.author.id)
    r=[x.name for x in mid.roles]
    if 'yakshaver' in r or 'yakherder' in r: #for now, both roles are same permissions
        return True
    return False


#@bot.event #seems event eats the events that command uses. but it is not really needed, either
# fix is to add await bot.process_commands(message) at the end
async def don_message(message): 
    if message.author == bot.user:
        return #ignore own messages to avoid loops

    dmtarget=await dmchan(message.author.id) #build backchannel to user, so we can choose to not answer in general channel
    if message.content.startswith("$project_uihelp"):
        s='''
$project_uihelp               this message
$project_uitest               a test message
maybe !!! is correct prefeix. maybe bottest

        '''
        await splitsend(message.channel,s,True)
        return
    return

@bot.command(name='uitest', help='also a test response')
async def project_uitest(ctx):
    s='this is a test response from project_ui bot in bot mode'
    print('got here')
    await splitsend(ctx.message.channel,s,False)
    return
    
@commands.command(name='bottest', help='shows a test message')
async def bottest(ctx):
    s='this is a another test response from project_ui bot in bot mode'
    print('and got here')
    await splitsend(ctx.message.channel,s,False)
    return


print("added:",bot.add_command(bottest))#just to see if it works


@bot.command(name='listchans', help='list project channels')
async def listchans(ctx):
    x=bot.guilds[0].channels
    s=[d for d in x if (d.category and d.category.name=="projects")]
    s1=[d.catagory.name for d in x if d.category]
    print('got to listchans', x,s, s1)
    await splitsend(ctx.message.channel,s,False)
    return
    
@bot.event
async def on_raw_reaction_add(x):
    print('got raw reaction',x, x.channel_id,x.message_id,x.emoji,x.user_id)
    s='got a reaction {} for user {}'.format(x.emoji.name, x.user_id)
    tweak_chan=bot.get_channel(TWEAK_CHAN)
    await splitsend(tweak_chan,s,False)
    c=bot.guilds[0].get_channel(x.channel_id)
    m=await c.fetch_message(x.message_id)
    em=emoji.emojize(":fishing_pole:")
    await m.add_reaction(em)
    em=emoji.emojize(":grinning_face:")
    await m.add_reaction(em)
    return
    


async def dmchan(t):
#create DM channel betwen bot and user
    target=bot.get_user(t)
    if (not target): 
        print("unable to find user and create dm",flush=True)
    return target
    target=target.dm_channel
    if (not target): 
        print("need to create dm channel",flush=True)
        target=await bot.get_user(t).create_dm()
    return target

async def splitsend(ch,st,codeformat):
#send messages within discord limit + optional code-type formatting
    if len(st)<1900: #discord limit is 2k and we want some play)
        if codeformat:
            await ch.send('```'+st+'```')
        else:
            await ch.send(st)
    else:
        x=st.rfind('\n',0,1900)
        if (x<0):
            x=1900
        if codeformat:
            await ch.send('```'+st[0:x]+'```')
        else:
            await ch.send(st[0:x])
        await splitsend(ch,st[x+1:],codeformat)

discord_token=os.getenv('PROJECT_UI_DISCORD_KEY')
bot.run(discord_token) 
