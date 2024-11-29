import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc


def get_games_elements(games):
    games_elements = []

    header = dbc.Row(
            children=[
                dbc.Col(html.Strong(games[0]['game_state'], style={'display':'flex','justifyContent':'center',
                'fontSize': '14px', 'margin':'5px'}), width=12),
            ],
            style={'marginBottom': '5px'}
    )
    games_elements.append(header)
    
    by_series = {}

    for game in games:
        score_style = {'display': 'flex', 'justifyContent': 'center', 'fontSize':'14px'}
        by_series[game['SARJA']] = by_series.get(game['SARJA'], []) + [dbc.Row(
            children=[
                dbc.Col(game['KOTI'], width=4, style=score_style),
                dbc.Col(game['score'], width=4, style=score_style),
                dbc.Col(game['VIERAS'], width=4, style=score_style),
            ],
            style={'marginBottom': '1px'}
        ),]
        score_style.update({'fontSize':'14px'})
        by_series[game['SARJA']] = by_series.get(game['SARJA']) + [
        dbc.Row(
            children=[
                dbc.Col(game['record_home'], width=4, style=score_style),
                dbc.Col(game['record_h2h'], width=4, style=score_style),
                dbc.Col(game['record_away'], width=4, style=score_style),
            ],
            style={'marginBottom': '2px'}
        )]

    for series_type, children in by_series.items():

        card_contents = [dbc.Row(
            children=[
                dbc.Col(html.Strong(series_type, style={'display':'flex', 'margin':'5px','justifyContent':'center','fontSize': '12px'}), width=12),
            ],
            style={'margin':'0px'}
        )] + [c for c in children]

        game_element = dbc.Card(
            children=[
                dbc.CardBody(
                    children=card_contents, style={'padding':'0px'}
                ),
            ],
            style={
                'margin': '2px',
                'padding': '0px',
                'fontSize': '11px',
                'borderRadius': '2px'
            }
            )
        games_elements.append(game_element)

    return html.Div(
        children=games_elements,
        style={"margin": "2px"}
    )