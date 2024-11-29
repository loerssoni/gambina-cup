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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = html.Div([
    dcc.Interval(id='update-interval', interval=15000000, n_intervals=0),  # Update every 5 seconds
    html.H1("Gambina Cup", style={"text-align": "center", "font-size":"30px"}),

    # Games list
    html.Div(id="games-list", style={"margin": "20px"}),

    html.H2("Standings", style={"margin-top": "40px"}),
    html.Div(id="standings-table", style={"margin": "20px"}),

    html.H2("Points Leaders", style={"margin-top": "40px"}),
    html.Div(id="points-leaders-table", style={"margin": "20px"}),
])

# Callback to update all data
@app.callback(
    [Output("games-list", "children"),
     Output("standings-table", "children"),
     Output("points-leaders-table", "children")],
    [Input("update-interval", "n_intervals")]
)
def update_data(n):
    # Generate games list
    games_list = []
    live = data.get_live()
    games_list.append(layouts.get_games_elements(live))

    upcoming = data.get_upcoming()
    games_list.append(layouts.get_games_elements(upcoming))
    

    ended = data.get_ended()
    games_list.append(layouts.get_games_elements(ended))

    # # Generate standings table
    # standings_table = dbc.Table.from_dataframe(
    #     standings_df, striped=False, bordered=False, hover=True, style={"margin": "10px"}
    # )

    # # Generate points leaders table
    # points_leaders_table = dbc.Table.from_dataframe(
    #     points_leaders_df, striped=False, bordered=False, hover=True, style={"margin": "10px"}
    # )

    return games_list, [], []


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
