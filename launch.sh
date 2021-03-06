#!/bin/bash

# Name of notebook to deploy
NAME=app

# Convert notebook to py script
# We skip all cells tagged 'skip-app' to speed up startup time
jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags="('skip-app',)"  --to script $NAME.ipynb


# To avoid having to fetch the data each time, make sure the /app/.vaex/file-cache directory
# is persistent (setup Directory Mappings in Dash Enterprise)
# But Dash Enterprise cannot map inside /app
# The solution is to map to /vaex-file-cache and link these directories
if [ -d /vaex-file-cache ] && [ ! -d /app/.vaex/file-cache ]; then
    mkdir -p /app/.vaex
    ln -s /vaex-file-cache /app/.vaex/file-cache
fi

# Make sure the files exists (otherwise all workers try to create it at the same time)
python ./prefetch.py

# Depending on notebook metadata, command above may output a .txt file
# If so, change extension to .py
if [ -f $NAME.txt ]; then
   mv $NAME.txt $NAME.py
fi

# Serve app
gunicorn app:server --workers 4 -t 240 --preload
