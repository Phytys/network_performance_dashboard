############################################################################
# By Glenn Landgren, https://www.linkedin.com/in/glenn-landgren/

# Big thanks to Plotly Dash Community

## Before starting:
# Create environment
# Install modules Dash, Plotly and Pandas, E.g pip or conda install ..

#############################################################################

# Import tools/ modules
from datetime import date, datetime, timedelta
import math
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go


## IMPORT DATA

# Get csv file of delay performante data
df = pd.read_csv("csv_table.csv")
df["DateTime"] = pd.to_datetime(df["DateTime"])
df.set_index("DateTime", inplace=True)


## DASH APP

# Styling
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
colors = {
    'background': '#ffffff',
    'text': '#002266' 
}

# Create app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# App Layout
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(children='[ Delay Dashboard ]', style={
            'textAlign': 'center',
            'color': colors['text']
            }
    ),
    html.Div(children='Example of an Interactive Dashboard by Plotly Dash', style={
        'textAlign': 'center',
        'color': colors['text']
    }),
    html.Br(),
    html.H4(children='RTT Performance Toplist', style={
            'textAlign': 'center',
            'color': colors['text']
            }
    ),
    # Date input to bubble graph, callback #1
    dcc.DatePickerRange(                             
        id='date-picker-range',
        min_date_allowed=datetime(2020, 8, 24),
        max_date_allowed=datetime(2020, 8, 31),
        initial_visible_month=datetime(2020, 8, 31),
        start_date=datetime(2020, 8, 24).date(),
        end_date=datetime(2020, 8, 31).date()
    ),
    html.Br(),
    # The output from callback #1 will be rendered here (bubble graph)
    dcc.Graph(                          
        id='rtt-performance-toplist',
    ),
    html.Br(),
    ##
    html.H4(children='Router Timline Graph', style={
            'textAlign': 'center',
            'color': colors['text']
            }
    ),
    # Text input to line graph (router id), callback #2
    html.Div(dcc.Input(                             
        id='input-on-submit', type='text', value="Router_43")),
    # Submit button for line graph , callback #2
    html.Button('Submit', id='submit-val', n_clicks=0),
    html.Div(id='container-button-basic',
             children='Enter Router id and press submit'
    ),
    # The output from callback #2 will be rendered here (line graph)
    dcc.Graph(                                     
        id='router-graph',
    ),
    # Days slider input to line graph (router id), callback #2
    dcc.Slider(                                    
        id="days-slider-router",
        min=0,
        max=90,
        step=None,
        marks={
            1: '1 Day',
            7: '7 Days',
            30: '30 Days',
            60: '60 Days',
            90: '60 Days',
        },
        value=90
    ),

])

## Callback #1 - a bubble graph that shows worst performing routers


@app.callback(
    Output('rtt-performance-toplist', 'figure'),
    [Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date')
     ])
def update_rtt_figure(start_date, end_date):
    # Create a new DataFrame based on date filtering (dff)
    dff = df.loc[(df.index >= start_date) & (df.index <= end_date)]

    dff = dff.groupby(["Subnet_Id", "Router_Id"]).agg(
        MinDelay=pd.NamedAgg(
            column="MinDelay(ms)", aggfunc="min"),
        MeanDelay=pd.NamedAgg(
            column="MeanDelay(ms)", aggfunc="mean"),
        MaxDelay=pd.NamedAgg(
            column="MaxDelay(ms)", aggfunc="max"),
        # Get std dev for selected time period
        StdMeanDelay=pd.NamedAgg(
            column="MeanDelay(ms)", aggfunc="std"), 
        Router=pd.NamedAgg(
            column="Router_Id", aggfunc="last")
    )
    dff = dff.reset_index()
    dff = dff.round(1)

    # Using plotly template

    hover_text = []
    bubble_size = []

    # We wante the the hover-info-box to contain router id and counter values, the graph is interactive
    for _, row in dff.iterrows():
        hover_text.append(("<b>Router ID: </b>{router}<br>" +
                           "Min Delay: {min_delay}<br>" +
                           "Mean Delay: {mean_delay}<br>" +
                           "Std_Mean Delay: {std_mean_delay}<br>" +
                           "Max Delay: {max_delay}").format(router=row["Router"],
                                                            min_delay=row["MinDelay"],
                                                            mean_delay=row["MeanDelay"],
                                                            std_mean_delay=row["StdMeanDelay"],
                                                            max_delay=row["MaxDelay"]))
        bubble_size.append(math.sqrt(row["StdMeanDelay"]))

    dff["text"] = hover_text
    dff["size"] = bubble_size
    sizeref = 2.*max(dff["MaxDelay"])/(100**2)

    # Create dictionary with dataframes for each Subnet
    Subnet_names = dff.Subnet_Id.unique().tolist()
    subnet_data = {Subnet_Id: dff.query("Subnet_Id == '%s'" % Subnet_Id)
                   for Subnet_Id in Subnet_names}

    # Create figure
    fig = go.Figure()
    # Add traces to plot
    for Subnet_names, Subnet_Id in subnet_data.items():
        fig.add_trace(go.Scatter(
            x=Subnet_Id["MeanDelay"], y=Subnet_Id["StdMeanDelay"],
            name=Subnet_names, text=Subnet_Id["text"],
            marker_size=Subnet_Id["MaxDelay"],
        ))

    # Tune marker appearance and layout
    fig.update_traces(mode="markers", marker=dict(sizemode="area",
                                                  sizeref=sizeref, line_width=2))
    # Update the layout, title etc
    fig.update_layout(
        title="RTT Delay Performance in 'Your' Router Network",
        xaxis=dict(
            title="Mean RTT (ms)",
            gridcolor="white",
            type="log",
            gridwidth=2,
        ),
        yaxis=dict(
            title="Std dev Mean RTT (ms)",
            gridcolor="white",
            type="log",
            gridwidth=2,
        ),
        paper_bgcolor="rgb(255, 255, 255)",
        plot_bgcolor="rgb(243, 243, 243)",
    )

    return fig


## Cllback #2 - router line graph that show delay performance


@app.callback(
    Output('router-graph', 'figure'),
    [Input('days-slider-router', 'value'),
     Input('submit-val', 'n_clicks')],
    [dash.dependencies.State('input-on-submit', 'value')]
)
def update_rtt_graph(selected_days, n_clicks, router):
    # Filter on amount of days back in time
    d = datetime.today() - timedelta(days=selected_days)
    # Create a new DataFrame based on date filtering (dff)
    dff = df.loc[df.index >= d]
    # filter on router id
    dff = dff.loc[dff["Router_Id"] == router]

    # Create figure and add traces
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dff.index, y=dff["MinDelay(ms)"],
                             mode='lines',
                             name='MinDelay(ms)'))
    fig.add_trace(go.Scatter(x=dff.index, y=dff["MeanDelay(ms)"],
                             mode='lines',
                             name='MeanDelay(ms)'))
    fig.add_trace(go.Scatter(x=dff.index, y=dff["MaxDelay(ms)"],
                             mode='lines+markers', name='"MaxDelay(ms)"'))

    # Add title
    fig.update_layout(
        title_text="RTT delay performance for: {}".format(router))
    # Set x-axis title
    fig.update_xaxes(title_text="Time")
    # Set y-axes titles
    fig.update_yaxes(title_text="Round Trip Time (ms)", type="log")

    return fig

# Run App
if __name__ == '__main__':
    app.run_server(debug=True)
    # Served at http://localhost:8050/

    # NOTE You can serve on a windows server by using e.g. "Waitress" Module