import vaex
import os
# Open the main data
taxi_path = 's3://vaex/taxi/yellow_taxi_2009_2015_f32_app.hdf5?anon=true'
# override the path, e.g. $ export TAXI_PATH=/data/taxi/yellow_taxi_2012_zones.hdf5
taxi_path = os.environ.get('TAXI_PATH', taxi_path)
df = vaex.open(taxi_path)
# for demo purposes, only use first 100 million rows
df = df[:100_000_000]

# Make sure the data is cached locally
used_columns = ['pickup_longitude',
                'pickup_latitude',
                'dropoff_longitude',
                'dropoff_latitude',
                'total_amount',
                'pickup_hour'
               ]
for col in used_columns:
    print(f'Making sure column "{col}" is cached...')
    df.nop(col, progress=True)