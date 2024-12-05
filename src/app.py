import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd

from game_data import GameData
import playoff_bracket
import layouts

data = GameData()

# Convert standings and points leaders data to DataFrames
standings_df = pd.DataFrame()
points_leaders_df = pd.DataFrame()

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA])
app.title = "Gambina Cup scoreboard"


# Layout
app.layout = html.Div([
    dbc.Container(
        children=[
            dcc.Interval(id='update-interval', interval=30000, n_intervals=0),
            # Games and Standings side by side
            dbc.Row(
                children=[
                    
                    dbc.Col([
                            html.H4("Ottelut", style={"text-align": "center", "font-size":"24px", "margin":"0px"}),
                            html.Div(children=layouts.games_list, style={"margin": "5px"}),
                            html.H4("Pistepörssi", style={"text-align": "center", "font-size":"24px", "margin":"0px"}),
                            dbc.Card(layouts.points_tabs_total, style={"text-align": "center", "margin": "5px",
                                "background-color":"white", "border-radius":"6px"}),
                           
                        ],  
                        xs=12, md=7  # Full width on mobile, half width on medium+
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Div([layouts.standings_tabs], style={"text-align": "center", "margin": "5px"}),
                            ]
                        ),
                        xs=12, md=5  # Full width on mobile, half width on medium+
                    ),
                ],
                style={"marginBottom": "0px"}
            )
        ],
        fluid=True
    )],
)

# Callback to update all data
@app.callback(
    [Output("games-ongoing", "children"),
     Output("games-upcoming", "children"),
     Output("games-ended", "children"),
     Output("standings-tables", "children"),
     Output("poff-bracket-container", "children"),
     Output("final-standings-container", "children"),
     Output("tab-points-regular", "children"),
     Output("tab-goals-regular", "children"),
     Output("tab-assists-regular", "children"),
     Output("tab-show-all-regular", "children"),
     Output("tab-points-post", "children"),
     Output("tab-goals-post", "children"),
     Output("tab-assists-post", "children"),
     Output("tab-show-all-post", "children")],
    [Input("update-interval", "n_intervals")]
)
def update_data(n):
    # Generate games list
    data.refresh_data()
    live = layouts.get_games_elements(data.get_live())
    upcoming = layouts.get_games_elements(data.get_upcoming())
    ended = layouts.get_games_elements(data.get_ended())
    
    standings_tables = []
    # Generate standings table
    for group, g_standings in data.render_standings().items():
        group_table = dbc.Table.from_dataframe(
            g_standings, striped=False, 
            bordered=False, hover=True, style={"margin": "10px"}
        )
        standings_tables += [
            html.Strong(group, style={'display':'flex','justifyContent':'center',
                        'margin':'5px', 'fontSize':'18'}),
            html.Div([group_table]),
        ]

    poff_bracket = playoff_bracket.get_playoff_bracket(data.render_playoff_games())

    points_tables = []
    for season_type in ['regular', 'post']:
        for k in ['points','goals','assists','show-all']:
            points_df = data.render_points(k, season_type)
            points_tables.append(dbc.Table.from_dataframe(
                points_df, striped=False, bordered=False, hover=True, style={"margin": "0px"}
            ))

    final_standings_table = dbc.Table.from_dataframe(
        data.render_final_standings(), striped=False, 
        bordered=False, hover=True, style={"margin": "10px"}
    )

    outputs = [live, upcoming, ended, standings_tables, poff_bracket, final_standings_table]
    outputs = outputs + points_tables
    return outputs

# set app server to variable for deployment
server = app.server

# set app callback exceptions to true
app.config.suppress_callback_exceptions = True

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
