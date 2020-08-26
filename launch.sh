#!/bin/bash

# Name of notebook to deploy
NAME=app

# Convert notebook to py script
# We skip all cells tagged 'skip-app' to speed up startup time
jupyter nbconvert --TagRemovePreprocessor.remove_cell_tags="('skip-app',)"  --to script $NAME.ipynb

# make sure the files exists (otherwise all workers try to create it at the same time)
python -c "import vaex; df = vaex.open('s3://vaex/taxi/yellow_taxi_2009_2015_f32_app.hdf5?anon=true')"

# Depending on notebook metadata, command above may output a .txt file
# If so, change extension to .py
if [ -f $NAME.txt ]; then
   mv $NAME.txt $NAME.py
fi

# Serve app
gunicorn app:server --workers 4 -t 240
