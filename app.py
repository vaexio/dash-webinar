#!/usr/bin/env python
# coding: utf-8

# # Implementing the Dashboard components
# 
# ### Key points to remember:
# - Dash is functional, every user interaction should trigger a callback
# - Dash callbacks should not modify the data

# In[18]:


import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html

from jupyter_dash import JupyterDash

import plotly.express as px
import plotly.graph_objs as go

import numpy as np

import vaex

import os
in_dash_enterprise = "DASH_APP_NAME" in os.environ


# ### Load the data

# In[2]:


if in_dash_enterprise:
    df = vaex.open('s3://vaex/taxi/yellow_taxi_2009_2015_f32_app.hdf5?anon=true')
else:
    df = vaex.open('/data/taxi/yellow_taxi_2009_2015_f32_app.hdf5')


# ### Create the selection

# In[3]:


def create_selection(hours=None):
    selection = None  # Initial state - no selection
    df_copy = df.copy()  # This creates a shallow copy which only references the original data 
    
    if hours:
        hour_min, hour_max = hours
        if hour_min > 0:
            df_copy.select(hour_min <= df_copy.pickup_hour, mode='and')
            selection = True
        if hour_max < 23:
            df_copy.select(df_copy.pickup_hour <= hour_max, mode='and')
            selection = True
    
    return df_copy, selection


# In[4]:


df_copy, selection = create_selection(hours=None)
df_copy.count(selection=selection, progress='widget')


# In[5]:


df_copy, selection = create_selection(hours=[12, 15])
df_copy.count(selection=selection, progress='widget')


# ### Compute heatmap data

# In[6]:


def compute_heatmap_data(hours, heatmap_limits):
    df_copy, selection =  create_selection(hours=hours)
    heatmap_data_array = df_copy.count(binby=[df_copy.pickup_longitude, df_copy.pickup_latitude],
                                       selection=selection,
                                       limits=heatmap_limits,
                                       shape=256,
                                       array_type='xarray')
    return heatmap_data_array


# In[7]:


heatmap_limits_initial = [[-74.05, -73.75], [40.58, 40.90]]

data_array = compute_heatmap_data(hours=None, heatmap_limits=heatmap_limits_initial)
data_array


# ### Create the heatmap figure

# In[8]:


def create_figure_heatmap(data_array, heatmap_limits, trip_start=None, trip_end=None):

    # Do the layout of the figure
    legend = go.layout.Legend(orientation='h',
                              x=0.0,
                              y=0.05,
                              font={'color': 'azure'},
                              bgcolor='royalblue',
                              itemclick=False,
                              itemdoubleclick=False)
    
    margin = go.layout.Margin(l=0, r=0, b=0, t=30)
    
    layout = go.Layout(height=600, 
                       title=None,
                       margin=margin,
                       legend=legend,
                       xaxis=go.layout.XAxis(title='Longitude', range=heatmap_limits[0]),
                       yaxis=go.layout.YAxis(title='Latitude', range=heatmap_limits[1]))

    # The actual figure
    fig = px.imshow(np.log1p(data_array).T, origin='lower')
    fig.layout = layout
    
    # add markers for the points clicked
    def add_point(x, y, **kwargs):
        fig.add_trace(go.Scatter(x=[x], y=[y], marker_color='azure', marker_size=8, mode='markers', showlegend=True, **kwargs))
    
    if trip_start:
        add_point(trip_start[0], trip_start[1], name='Trip start', marker_symbol='circle')
    
    if trip_end:
        add_point(trip_end[0], trip_end[1], name='Trip end', marker_symbol='x')

    return fig


# In[9]:


trip_start_initial = -73.78223, 40.64438 # JFK
trip_end_initial = -73.99, 40.75  # Manhatten

create_figure_heatmap(data_array=data_array, 
                      heatmap_limits=heatmap_limits_initial, 
                      trip_start=trip_start_initial, 
                      trip_end=trip_end_initial)


# ### Compute trip details

# In[10]:


def compute_trip_details(hours=None, trip_start=None, trip_end=None):
    df_copy, selection = create_selection(hours=hours)
    
    # Radius around which to select trips
    # One mile is ~0.0145 deg; and in NYC there are approx 20 blocks per mile
    # We will select a radius of 3 blocks
    r = 0.0145 / 20 * 3
    pickup_long, pickup_lat = trip_start
    dropoff_long, dropoff_lat = trip_end
    
    selection_pickup = (df_copy.pickup_longitude - pickup_long)**2 + (df_copy.pickup_latitude - pickup_lat)**2 <= r**2
    selection_dropoff = (df_copy.dropoff_longitude - dropoff_long)**2 + (df_copy.dropoff_latitude - dropoff_lat)**2 <= r**2
    
    df_copy.select(selection_pickup & selection_dropoff, mode='and')
    selection = True  # After this step, selection is alwasy True; one always has an origin and destination
    
    return {'counts': df_copy.count(selection=selection),
            'counts_fare': df_copy.count(binby=[df_copy.total_amount], selection=selection, limits=[0, 50], shape=25),
           }


# In[11]:


# %%time
trip_details = compute_trip_details(hours=None, trip_start=trip_start_initial, trip_end=trip_end_initial)
trip_details


# In[12]:


# %%time
trip_details = compute_trip_details(hours=[7, 10], trip_start=trip_start_initial, trip_end=trip_end_initial)
trip_details


# ### Create histograms 

# In[13]:


def create_histogram_figure(counts, title=None, xlabel=None, ylabel=None):
    
    # Create the bar figure
    x = df.bin_centers(expression=df.total_amount, limits=[0, 50], shape=25)
    bars = px.bar(x=x, y=counts, color_discrete_sequence=['royalblue'] * 25)
    
    
    # Layout
    title = go.layout.Title(text=title, x=0.5, y=1, font={'color': 'black'})
    margin = go.layout.Margin(l=0, r=0, b=0, t=30)
    legend = go.layout.Legend(orientation='h',
                              bgcolor='rgba(0,0,0,0)',
                              x=0.5,
                              y=1,
                              itemclick=False,
                              itemdoubleclick=False)
    layout = go.Layout(height=230,
                       margin=margin,
                       legend=legend,
                       title=title,
                       xaxis=go.layout.XAxis(title=xlabel),
                       yaxis=go.layout.YAxis(title=ylabel),
                       plot_bgcolor="#F9F9F9",
                       paper_bgcolor="#F9F9F9")
                       
    
    # Now calculate the most likely value (peak of the histogram)
    peak = np.round(x[np.argmax(counts)], 2)

    return go.Figure(data=bars, layout=layout), peak


# In[14]:


fig, peak = create_histogram_figure(counts=trip_details['counts_fare'], 
                                    title='Fare amount', xlabel='Fare amount', ylabel='Number of trips')
fig


# In[15]:


peak


# ## Let us build a Dash application!
# 
# Instantiate the App

# In[16]:


app = JupyterDash(__name__, external_stylesheets=[])


# Define the app layout

# In[19]:


app.layout = html.Div(className='app-body', children=[
    # Stores
    dcc.Store(id='map_clicks', data=0),
    dcc.Store(id='trip_start', data=trip_start_initial),
    dcc.Store(id='trip_end', data=trip_end_initial),
    dcc.Store(id='heatmap_limits', data=heatmap_limits_initial),

    # Control panel
    html.Div(className="row", id='control-panel', children=[
        html.Div(className="four columns pretty_container", children=[
            html.Label('Select pick-up hours'),
            dcc.RangeSlider(id='hours',
                            value=[0, 23],
                            min=0, max=23,
                            marks={i: str(i) for i in range(0, 24, 3)})
        ]),
    ]),

    # Visuals
    html.Div(className="row", children=[
             html.Div(className="seven columns pretty_container", children=[
                dcc.Markdown(children='_Click on the map to select trip start and destination._'),
                dcc.Graph(id='heatmap_figure',
                          figure=create_figure_heatmap(data_array,
                                                       heatmap_limits_initial,
                                                       trip_start_initial,
                                                       trip_end_initial))
             ]),
             html.Div(className="five columns pretty_container", children=[
                dcc.Graph(id='trip_summary_amount_figure'),
                dcc.Markdown(id='trip_summary_md')
             ]),
    ]),
])


# ### Define user interactions via callbacks
# 
# Update the heatmap when data ranges and the hours selection has changed

# In[20]:


@app.callback(Output('heatmap_figure', 'figure'),
              [Input('hours', 'value'),
               Input('heatmap_limits', 'data'),
               Input('trip_start', 'data'),
               Input('trip_end', 'data')],
              prevent_initial_call=True)
def update_heatmap_fiture(hours, heatmap_limits, trip_start, trip_end):
    data_array = compute_heatmap_data(hours, heatmap_limits)
    return create_figure_heatmap(data_array, heatmap_limits, trip_start, trip_end)


# Update the heamap data range given some user interaction

# In[21]:


@app.callback(Output('heatmap_limits', 'data'),
              [Input('heatmap_figure', 'relayoutData')],
              [State('heatmap_limits', 'data')],
              prevent_initial_call=True)
def update_limits(relayoutData, heatmap_limits):
    if relayoutData is None:
        raise dash.exceptions.PreventUpdate
    elif relayoutData is not None and 'xaxis.range[0]' in relayoutData:
        heatmap_limits = [[relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']],
                          [relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']]]
    else:
        raise dash.exceptions.PreventUpdate
        if heatmap_limits is None:
            heatmap_limits = heatmap_limits_initial
    return heatmap_limits


# Heatmap click interaction

# In[22]:


@app.callback([Output('map_clicks', 'data'),
               Output('trip_start', 'data'),
               Output('trip_end', 'data')],
              [Input('heatmap_figure', 'clickData')],
              [State('map_clicks', 'data'),
               State('trip_start', 'data'),
               State('trip_end', 'data')])
def click_heatmap_action(click_data_heatmap, map_clicks, trip_start, trip_end):
    if click_data_heatmap is not None:
        click = click_data_heatmap['points'][0]['x'], click_data_heatmap['points'][0]['y']
        if map_clicks % 2 == 0:
            trip_start = click
        else:
            trip_end = click
        map_clicks += 1
    return map_clicks, trip_start, trip_end


# Update the trip statistics based on new trip information

# In[23]:


@app.callback([Output('trip_summary_amount_figure', 'figure'),
               Output('trip_summary_md', 'children')],
              [Input('hours', 'value'),
               Input('trip_start', 'data'),
               Input('trip_end', 'data')])
def update_trip_details(hours, trip_start, trip_end):
    trip_detail_data = compute_trip_details(hours, trip_start, trip_end)

    counts = trip_detail_data['counts']
    counts_fare = trip_detail_data['counts_fare']

    # Trip amount histogram
    fig_fare, peak_fare = create_histogram_figure(counts=counts_fare,
                                                  title=None,
                                                  xlabel='Total fare amount [$]',
                                                  ylabel='Number or rides')
    # Trip summary statistics
    trip_stats = f'''
                    **Trip statistics:**
                    - Number of rides: {counts}
                    - Most likely total trip cost: ${peak_fare}
                  '''


    return fig_fare, trip_stats


# In[24]:


if __name__ == "__main__":
    if in_dash_enterprise:
        app.run_server()
    else:
        app.run_server(mode="jupyterlab", port=8060)


# In[ ]:




