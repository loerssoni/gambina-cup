import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc


def get_games_elements(games):
    games_elements = []
    
    by_series = {}

    for game in games:
        team_style = {'display': 'flex', 'justifyContent': 'center', 'fontSize':'16px', 'alignItems':'stretch'}
        score_style = {'display': 'flex', 'justifyContent': 'center', 'alignItems':'end', 'fontSize':'20px'}

        by_series[game['SARJA']] = by_series.get(game['SARJA'], []) + [dbc.Row(
            children=[
                dbc.Col(html.Strong(game['KOTI']), width=4, style=team_style),
                dbc.Col(html.Strong(game['score']), width=4, style=score_style),
                dbc.Col(html.Strong(game['VIERAS']), width=4, style=team_style),
            ],
            style={'marginBottom': '1px', 'alignItems':'center'}
        ),]
        if game['record_h2h'] == '':
            score_subitem = game['SARJA']
        else:
            score_subitem = game['record_h2h']
        record_style = {'display': 'flex', 'justifyContent': 'center', 'fontSize':'14px'}
        by_series[game['SARJA']] = by_series.get(game['SARJA']) + [
        dbc.Row(
            children=[
                dbc.Col(game['record_home'], width=4, style=record_style),
                dbc.Col(score_subitem, width=4, style=record_style),
                dbc.Col(game['record_away'], width=4, style=record_style),
            ],
            style={'marginBottom': '2px'}
        )]

    for series_type, children in by_series.items():
        card_contents = [c for c in children]

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
                'borderRadius': '6px'
            }
            )
        games_elements.append(game_element)

    return html.Div(
        children=games_elements,
        style={"margin": "2px"}
    )

# Define the table component
def get_points_table(data, rows_to_show=3):
    # Slice data to show a limited number of rows by default
    limited_data = data.head(rows_to_show)

    return dash_table.DataTable(
        id="points-table",
        columns=[{"name": col, "id": col} for col in data.columns],
        data=limited_data.to_dict("records"),  # Limited data
        style_table={"overflowX": "auto", "margin":"2px"},
        style_as_list_view=True,
        style_cell={"padding": "5px", "textAlign": "left"},
        style_header={"fontWeight": "bold"},
        sort_action="native",  # Enables column sorting
        page_action="none",  # Show all rows at once (no pagination)
        row_selectable="multi",  # Optional: allow row selection
    )