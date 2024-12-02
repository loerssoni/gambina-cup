import dash
import dash_bootstrap_components as dbc
from dash import html

def get_playoff_bracket(playoff_games):
    bracket_inputs = {}
    for step in playoff_games.index.levels[0].unique():
        bracket_inputs[step] = {}
        step_games = playoff_games.loc[step]
        for i, name in enumerate(step_games.index.get_level_values('name')):
            name_step_games = step_games.loc[name]
            if len(name_step_games.shape) != 1:
                bracket_inputs[step][i] = []
            else:
                home_team = name_step_games['team_home']
                home_wins = name_step_games['wins_home']
                away_team = name_step_games['team_away']
                away_wins = name_step_games['wins_away']

                if (home_wins == '3') or (home_wins == '1' and 'Pronssiottelu' in name):
                    home_team = html.Strong(home_team)
                    home_wins = html.Strong(home_wins)
                elif (away_wins == '3') or (away_wins == '1' and 'Pronssiottelu' in name):
                    away_team = html.Strong(away_team)
                    away_wins = html.Strong(away_wins)

                bracket_inputs[step][i] = [
                        html.Div([
                            html.Span(home_team, style={"margin-right": "10px", "font-size": "14px"}),
                            html.Span(home_wins, style={"font-size": "14px", "text-align":"right"})
                        ], style={"display": "block", "text-align": "right"}),
                        html.Div([
                            html.Span(away_team, style={"margin-right": "10px", "font-size": "14px"}),
                            html.Span(away_wins, style={"font-size": "14px"})
                        ], style={"display": "block", "text-align": "right"}),
                ]

    
    
    bracket = html.Div(
        className="container grid",
        children=[
            html.Div(
                className="round",
                children=[
                    html.Div(
                        className="round",
                        children=[
                            html.Div(className="match", children=bracket_inputs['Puolivälierät'][0]),
                            html.Div(className="link"),
                            html.Div(className="match", children=bracket_inputs['Puolivälierät'][1]),
                        ]
                    ),
                    html.Div(
                        className="round",
                        children=[
                            html.Div(className="match", children=bracket_inputs['Puolivälierät'][2]),
                            html.Div(className="link"),
                            html.Div(className="match", children=bracket_inputs['Puolivälierät'][3]),
                        ]
                    ),
                ]
            ),
            html.Div(
                className="round justify-space-around",
                children=[
                    html.Div(className="match", children=bracket_inputs['Välierät'][0]),
                    html.Div(className="link"),
                    html.Div(className="match", children=bracket_inputs['Välierät'][1]),
                ]
            ),
            html.Div(
                className="final-round",
                children=[
                    html.Strong("Finaali"),
                    html.Div(className="match", children=bracket_inputs['Finaali'][0]),
                    html.Strong("Pronssiottelu"),
                    html.Div(className="match", children=bracket_inputs['Pronssiottelu'][0]),
                ]
            ),
            html.Div(
                className="round",
                children=[
                    html.Div(className="match", children=bracket_inputs['Valdemar'][0]),
                ]
            ),
            
        ]
        )
    return bracket