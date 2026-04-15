#!/bin/bash
# Optional: set NVM_DIR if claude is managed via nvm
# export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
cd ~/pocketclaude
python3 bot.py >> ~/pocketclaude/bot.log 2>&1
