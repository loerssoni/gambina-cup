import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from game_data import GameData
import layouts

data = GameData()

# Convert standings and points leaders data to DataFrames
standings_df = pd.DataFrame()
points_leaders_df = pd.DataFrame()

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.title = "Gambina Cup scoreboard"


# Layout
app.layout = dbc.Container(
        children=[
            dcc.Interval(id='update-interval', interval=30000, n_intervals=0),
            # Games and Standings side by side
            dbc.Row(
                children=[
                    
                    dbc.Col([
                            html.H4("Ottelut", style={"text-align": "center", "font-size":"24px", "margin":"0px"}),
                            html.Div(id="games-list", style={"margin": "5px"}),
                            html.H4("Pistepörssi", style={"text-align": "center", "font-size":"24px", "margin":"0px"}),
                            html.Div(id="points-leaders-table", style={"text-align": "center", "margin": "5px"}),
                        ],  
                        xs=12, md=7  # Full width on mobile, half width on medium+
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.H4("Sarjataulukko", style={"text-align": "center", "fontSize":"24px"}),
                                html.Div(id="standings-table", style={"text-align": "center", "margin": "5px"}),
                            ]
                        ),
                        xs=12, md=5  # Full width on mobile, half width on medium+
                    ),
                ],
                style={"marginBottom": "0px"}
            ),
            # Pistepörssi Section
            dbc.Row(
                children=[
                    dbc.Col(
                        html.Div(
                            [
                               
                            ]
                        ),
                        xs=12, md=8  # Full width on mobile, half width on medium+
                    )
                ],
                style={"marginBottom": "2px"}
            ),
        ],
        fluid=True  # Ensures the layout stretches to screen width
    )

# Callback to update all data
@app.callback(
    [Output("games-list", "children"),
     Output("standings-table", "children"),
     Output("points-leaders-table", "children")],
    [Input("update-interval", "n_intervals")]
)
def update_data(n):
    # Generate games list
    data.refresh_data()

    games_list = [
        dbc.Row(
            children=[
                dbc.Col(html.Strong("KÄYNNISSÄ", style={'display':'flex','justifyContent':'left',
                 'marginLeft':'28px', 'fontSize':'18'}), width=12),
            ],
            style={'marginBottom': '5px'}
    )]
    live = data.get_live()
    games_list.append(layouts.get_games_elements(live))

    
    upcoming = data.get_upcoming()
    ended = data.get_ended()

    el_upcoming = dbc.Accordion(
        [
            dbc.AccordionItem(
                layouts.get_games_elements(upcoming),
                title=html.Strong("TULOSSA", style={'display':'flex','justifyContent':'center',
                 'margin':'2px'})
            ),
            dbc.AccordionItem(
                layouts.get_games_elements(ended),
                title=html.Strong("PÄÄTTYNYT", style={'display':'flex','justifyContent':'center',
                 'margin':'2px'}),
            ),
        ],
        start_collapsed=True
    )
    games_list.append(el_upcoming)


    # # Generate standings table
    group_a, group_b = data.render_standings()

    standings_elements = [
        html.Strong("A-lohko", style={'display':'flex','justifyContent':'center',
                 'margin':'5px', 'fontSize':'18'}),

        dbc.Table.from_dataframe(
            group_a, striped=False, bordered=False, hover=True, style={"margin": "10px"}
        ),

        html.Strong("B-lohko", style={'display':'flex','justifyContent':'center',
                 'margin':'5px', 'fontSize':'18'}),

        dbc.Table.from_dataframe(
            group_b, striped=False, bordered=False, hover=True, style={"margin": "10px"}
        )
    ]

    points_tables = {}
    for k in ['Pisteet','Maalit','Syötöt','Näytä kaikki']:
        points_df = data.render_points(k)
        points_tables[k] = dbc.Table.from_dataframe(
            points_df, striped=False, bordered=False, hover=True, style={"margin": "10px"}
        )

    points_tabs = dbc.Tabs(
            [
                dbc.Tab(
                    label=k,
                    tab_id=f"tab-{k}",
                    children=[
                        points_tables[k]
                    ],
                    label_style = {"margin": "3px", "padding":"3px 10px 3px 10px"}
                ) for k in points_tables
            ],
            id="tabs",  # Optional: to handle tab switching callbacks
            active_tab="tab-Pisteet",
        )

    return games_list, standings_elements, [points_tabs]

# set app server to variable for deployment
srv = app.server

# set app callback exceptions to true
app.config.suppress_callback_exceptions = True

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
