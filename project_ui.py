#discord bot to act as UI for projects based on jordans(?) idea that we have a message for each project
#use PROJECT_UI_DISCORD_KEY as an env variable - the key for discord bot. needs read/write permission to channels

#logic:
#when run, starts by:
#   deletes all messages in dashboard
#   creates new upcoming message
#   gets list of channels
#   creates new message for each channel based on channel name and "other data sources" if any. for now, none! later, use $proj interface?
#   message includes name, blank text) channel (with #) and role:
#   each "create" also creates a line in the database with channel id and corresponding message id. maybe a list in memory is enough?
#   read existing roles
#   create/match (same first 10 chars or whole thing) a role for each channel and add it to list
#   add three reactions to each message: join and leave and details
#ongoing:
#   if new channel created or deleted or name changed, reboot program
#   if emoji
#       if on a message id in list
#           send a dm to that person, with details, if asked
#           if join, add a role
#           if leave, remove role
#   other commands, for now only test

import discord
import asyncio
import os
import time
import datetime
import emoji
import subprocess


from dotenv import load_dotenv
from discord.ext import tasks, commands

from discord_project_ui import * #including bot

HOMEDIR="/home/yak"

import sqlite3 

class Int_Mess:
    def __init__(id=0,type=None,mess_id=0,update=None,role=None,content="",emoji=[]):
        id=id #ID of the entry; int
        type=type #for now "upcoming" or "project"
        mess_id=mess_id #ID of message in discord; int
        update=update #function to call to update the message
        #reaction=reaction #function to call when a reaction is added (clicked)
        role=role # what role to add or remove
        content=content #contents of the  message; text
        emoji=emoji #list of tuples (emojies strings, function to call) to show at bottom of message. default to green_book red_book eye
    

entries=[]#array of Int_Mess

load_dotenv(HOMEDIR+"/"+'.env')
TWEAK_CHAN=705512721847681035 #temporary
EXP_CHAN=808415505856594001 #dashboard channel id

@bot.event #needed since it takes time to connect to discord
async def on_ready(): 
    print('We have logged in as {0.user}'.format(bot),  bot.guilds)
    await init_bot() 
    return

async def init_bot():
    global entries
    await delete_all_messages()
    entries=[]
    create_upcoming_message()
    x=bot.guilds[0].channels
    chanlist=[d for d in x if (d.category and d.category.name=="Projects")]
    #not done yet - read existing roles and match to channels
    for c in chanlist:
        await create_message(c)
    test_tick.cancel() #hope nothing stays hanging...
    test_tick.start()
    
async def delete_all_messages(): #for now, only bot messages
    c=bot.guilds[0].get_channel(EXP_CHAN)
    def is_me(m):
        return m.author == bot.user
    deleted = await c.purge(limit=20, check=is_me)
    
async def create_message(c): #c is name of channel we are working on
    await splitsend(bot.guilds[0].get_channel(EXP_CHAN),'create message {}'.format(c.name),False)
    #identify role
    #generate content - for now using only local content, later knack or proj
    #generate entry
    #create actual message
    #update message ID
    #adde mojis to message
    pass


@bot.event
async def on_guild_channel_delete(channel):
    await init_bot()
@bot.event
async def on_guild_channel_create(channel):
    await init_bot()
@bot.event
async def on_guild_channel_update(before, after):
    await init_bot()


@tasks.loop(seconds=600.0) #change to larger number as soon as we see this works. there is a rate limit 5 mess per channel in 5 sec
async def test_tick():
    #print ("tick")
    for x in entries:
        await x.update()

def upcoming_contents():
    thecontents="**updated every 10 min, last at** {} (UTC)".format(datetime.datetime.utcnow().strftime("%H:%M %b, %d %Y"))
    out = subprocess.Popen(['python3',HOMEDIR+'/robot/onboarding_robot/upcoming_command.py'], 
           stdout=subprocess.PIPE, 
           stderr=subprocess.STDOUT)
    stdout,stderr = out.communicate()
    thecontents=thecontents+'\n'+str(stdout,"utf-8").replace("\\n",'\n')
    return thecontents
    
async def create_upcoming_message():
    thecontents=upcoming_contents()
    upcoming_mess=Int_Mess(id=0,type="upcoming",update=update_upcoming_message,content=thecontents)
    c=bot.guilds[0].get_channel(EXP_CHAN)
    mess=await splitsend(c,thecontents, False)
    upcoming_mess.mess_id=mess.id
    entries.append(upcoming_mess)
        
async def update_upcoming_message():
    thecontents=upcoming_contents()
    x=[entry for entry in entries if entry.type=="upcoming"]
    x[0].content=thecontents
    c=bot.guilds[0].get_channel(EXP_CHAN)
    mess=await c.fetch_message(x[0].mess_id)
    await mess.edit(content=thecontents)


#@bot.event #seems event eats the events that command uses. but it is not really needed, either
# fix is to add await bot.process_commands(message) at the end

@bot.command(name='uitest', help='a test response')
async def project_uitest(ctx):
    s='this is a test response from project_ui bot in bot mode'
    print('got here')
    await splitsend(ctx.message.channel,s,False)
    return
    

@bot.command(name='listchans', help='list project channels')
async def listchans(ctx):
    x=bot.guilds[0].channels
    s=[d for d in x if (d.category and d.category.name=="Projects")]
    s1=[d.category.name for d in x if d.category]
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
    #change to sending dm accoridng to add/join/details
    return #no need to randomly add emojis on other's messages
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
            return await ch.send('```'+st+'```')
        else:
            return await ch.send(st)
    else:
        x=st.rfind('\n',0,1900)
        if (x<0):
            x=1900
        if codeformat:
            return await ch.send('```'+st[0:x]+'```')
        else:
            return await ch.send(st[0:x])
        return await splitsend(ch,st[x+1:],codeformat)
        
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

discord_token=os.getenv('PROJECT_UI_DISCORD_KEY')
bot.run(discord_token) 
