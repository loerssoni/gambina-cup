import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc


def get_games_elements(games):
    games_elements = []

    element_style = {
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justifyContent': 'center',
        'height': 'auto',
        'textAlign': 'center',
        'fontFamily': 'Arial, sans-serif',
        'margin': '1px',
        'padding': '1px',
        'fontSize': '11px'  # Reduce the global font size
    }
    games_elements.append(html.Div(
                    children=[
                        html.Strong(games[0]['game_state'], style={'flex': '1', 'fontsize':'20px'}),
                    ], style=element_style
    ))
    for game in games:
        game_element = html.Div(
            style=element_style,
            children=[
                html.Div(
                    style={'display': 'flex', 'width': '60%', 'justifyContent': 'space-between', 'fonsize':'14px'},
                    children=[
                        html.Strong(game['SARJA'], style={'flex': '1'}),
                    ]
                ),
                                # Row 1
                html.Div(
                    style={'display': 'flex', 'width': '60%', 'justifyContent': 'space-between'},
                    children=[
                        html.Div(game['playercard_home'], style={'flex': '1'}),
                        html.Div(game['score'], style={'flex': '1'}),
                        html.Div(game['playercard_away'], style={'flex': '1'}),
                    ]
                ),
                # Row 2
                html.Div(
                    style={
                        'display': 'flex', 
                        'width': '60%', 
                        'justifyContent': 'space-between',
                        'marginTop': '2px', 
                        'fontSize': '9px'
                    },
                    children=[
                        html.Div(game['record_home'], style={'flex': '1'}),
                        html.Div(game['record_h2h'], style={'flex': '1'}),
                        html.Div(game['record_away'], style={'flex': '1'}),
                    ]
                ),
            ]
        )

        games_elements.append(game_element)
    return html.Div(
        children=games_elements,
        style={"margin":"30px"}
    )
