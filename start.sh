#!/bin/bash
export NVM_DIR="/c/Users/Arklok/.nvm"
[ -s "/nvm.sh" ] && . "/nvm.sh"
cd ~/telegram-pc-bot
python3 bot.py >> ~/telegram-pc-bot/bot.log 2>&1
