#!/bin/bash

# Name of notebook to deploy
NAME=app

# Convert notebook to py script
# We skip all cells tagged 'skip-app' to speed up startup time
jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags="('skip-app',)"  --to script $NAME.ipynb

# Make sure the files exists (otherwise all workers try to create it at the same time)
python ./prefetch.py
# To avoid having to fetch the data each time, make sure the /root/.vaex/file-cache directory
# is persistent (setup Directory Mappings in Dash Enterprise)

# Depending on notebook metadata, command above may output a .txt file
# If so, change extension to .py
if [ -f $NAME.txt ]; then
   mv $NAME.txt $NAME.py
fi

# Serve app
gunicorn app:server --workers 4 -t 240
