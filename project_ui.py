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
    def __init__(self, id=0,name=None,type=None,mess_id=0,update=None,role=None,content=None,emoji=None,chan=None):
        self.id=id #ID of the entry; int
        self.name=name # name of teh project/message
        self.type=type #for now "upcoming" or "project"
        self.mess_id=mess_id #ID of message in discord; int
        self.update=update #function to call to update the message
        #reaction=reaction #function to call when a reaction is added (clicked)
        self.role=role # what role to add or remove
        self.content=content #contents of the  message; text
        self.emoji=emoji #list of tuples (emojies strings, function to call) to show at bottom of message. default to green_book red_book eye
        self.chan=chan
    

entries=[]#array of Int_Mess
message_channels=set()

load_dotenv(HOMEDIR+"/"+'.env')
TWEAK_CHAN=705512721847681035 #temporary
EXP_CHAN=808415505856594001 #dashboard channel id

@bot.event #needed since it takes time to connect to discord
async def on_ready(): 
    print('We have logged in as {0.user}'.format(bot),  bot.guilds)
    await init_bot() 
    return

async def init_bot():
    global entries,message_channels
    await delete_all_messages()
    entries=[]
    message_channels=set()
    await create_upcoming_message()
    x=bot.guilds[0].channels
    chanlist=[d for d in x if (d.category and d.category.name=="Projects")]
    #not done yet - read existing roles and match to channels
    for c in chanlist:
        await create_message(c)
    test_tick.cancel() #hope nothing stays hanging...
    test_tick.start()
    
async def delete_all_messages(): #for now, only bot messages
    def is_me(m):
        return m.author == bot.user
    c=bot.guilds[0].get_channel(EXP_CHAN) # switch to below the ###
    deleted = await c.purge(limit=20, check=is_me)
    return
    ###for when we actually use more channels
    for x in message_channels:
        deleted = await x.purge(limit=20, check=is_me)
    
async def create_message(c): #c is name of channel we are working on
    thec=bot.guilds[0].get_channel(EXP_CHAN)
    message_channels.add(thec)
    #await splitsend(thec,'create message {}'.format(c.name),False)
    #identify role
    #generate content - for now using only local content, later knack or proj
    thecontents="project **{0}**\n{1}\n<#{2}>".format(c.name,"no details yet",c.id)
    #generate entry
    proj_mess=Int_Mess(id=0,type="project",name=c.name,update=update_project_message,content=thecontents,emoji=[(":bell:",join_project,emoji.emojize(":bell:")),(":bell_with_slash:",leave_project,emoji.emojize(":bell_with_slash:")),(":eye:",detail_project,emoji.emojize(":eye:"))],chan=thec)
    mess=await splitsend(thec,thecontents, False)
    proj_mess.mess_id=mess.id
    entries.append(proj_mess)
    #add mojis to message
    for x in proj_mess.emoji:
        em=x[2]
        await mess.add_reaction(em)
    pass

async def update_project_message(x):
#will update project contents, when we have real data to show...
    pass
async def join_project(x):
    print("join ",x.name)
#try to join
    pass
async def leave_project(x):
#try to leave
    print("leave ",x.name)
    pass
async def detail_project(x):
#try to get details
    print("details on ",x.name)
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
        await x.update(x)

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
    c=bot.guilds[0].get_channel(EXP_CHAN)
    upcoming_mess=Int_Mess(id=0,type="upcoming",name="upcoming",update=update_upcoming_message,content=thecontents,chan=c)

    mess=await splitsend(c,thecontents, False)
    upcoming_mess.mess_id=mess.id
    entries.append(upcoming_mess)
        
async def update_upcoming_message(x):#x is message entry,not used here
    thecontents=upcoming_contents()
    x=[entry for entry in entries if entry.type=="upcoming"]
    x[0].content=thecontents
    c=x[0].chan
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
    if (x.user_id == bot.user.id):
        return # this happens while buuilding the messages
    print('got raw reaction',x, x.channel_id,x.message_id,x.emoji,x.user_id)
    whichproj=[p for p in entries if p.mess_id==x.message_id]
    if whichproj==[]:
        print("not on my messages")
        return
    em=[e for e in whichproj[0].emoji if e[2]==x.emoji.name]
    if em==[]:
        print("not right kind of emoji", whichproj[0].emoji)
        return
    em[0][1](whichproj[0])
    await splitsend(tweak_chan,s,False)
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
