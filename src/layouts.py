import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc


def get_games_elements(games):
    games_elements = []
    
    by_series = {}

    for game in games:
        team_style = {'display': 'flex', 'justifyContent': 'center', 'fontSize':'16px', 'alignItems':'stretch'}
        score_style = {'display': 'flex', 'justifyContent': 'center', 'alignItems':'end', 'fontSize':'20px'}

        by_series[game['SARJA']] = by_series.get(game['SARJA'], []) + [
            dbc.Row(
                children=[
                    dbc.Col(html.Strong(game['team_home']), width=4, style=team_style),
                    dbc.Col(html.Strong(game['score']), width=4, style=score_style),
                    dbc.Col(html.Strong(game['team_away']), width=4, style=team_style),
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
                dbc.Row(
                    dbc.Col(series_type, width=12, style={'fontSize':'14px','textAlign':'center'})
                ),
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

    return games_elements

el_ongoing = dbc.Accordion(
    [   dbc.AccordionItem(
            id = 'games-ongoing',
            title=html.Strong("KÄYNNISSÄ", style={'display':'flex','justifyContent':'center',
                'margin':'2px'}),
        )
    ],
    always_open=True
)

el_upcoming = dbc.Accordion(
    [   
        dbc.AccordionItem(
            id = 'games-upcoming',
            title=html.Strong("TULOSSA", style={'display':'flex','justifyContent':'center',
                'margin':'2px'})
        ),
        dbc.AccordionItem(
            id='games-ended',
            title=html.Strong("PÄÄTTYNYT", style={'display':'flex','justifyContent':'center',
                'margin':'2px'})
        )
    ],
    start_collapsed=True
)

games_list = [
    el_ongoing,
    el_upcoming
]


standings_elements = [
    html.Strong("A-lohko", style={'display':'flex','justifyContent':'center',
                'margin':'5px', 'fontSize':'18'}),
    html.Div(id='a-table'),
    html.Strong("B-lohko", style={'display':'flex','justifyContent':'center',
                'margin':'5px', 'fontSize':'18'}),
    html.Div(id='b-table')
]

playoff_elements = [
    html.Div(id='poff-bracket-container'),
]

final_standings_elements = [
    html.Div(id='final-standings-container')
]

standings_tabs = dbc.Tabs(
        [
            dbc.Tab(
                label="Sarjataulukko",
                tab_id="tab-sarjataulukko",
                children=standings_elements,
                label_style = {"margin": "3px", "padding":"3px 10px 3px 10px"}
            ),
            dbc.Tab(
                label="Pudotuspelit",
                tab_id="tab-playoffs",
                children=playoff_elements,
                label_style = {"margin": "3px", "padding":"3px 10px 3px 10px"}
            ),
            dbc.Tab(
                label="Lopputulokset",
                tab_id="tab-final-standings",
                children=final_standings_elements,
                label_style = {"margin": "3px", "padding":"3px 10px 3px 10px"}
            )
        ],
        id="standings-tabs",  # Optional: to handle tab switching callbacks
        active_tab="tab-sarjataulukko",
    )

points_tables = {
    'Pisteet':'points',
    'Maalit':'goals',
    'Syötöt':'assists',
    'Näytä kaikki':'show-all'
}

points_tabs = {}
for season_type in ['regular', 'post']: 
    points_tabs[season_type] = [
        dbc.Tab(
            label=label,
            id=f"tab-{id}-{season_type}",
            label_style = {"margin": "3px", "padding":"3px 10px 3px 10px"}
        ) for label, id in points_tables.items()
    ]

tabs_of_tabs = [
    dbc.Tab(dbc.Tabs(
            points_tabs['regular'],
            id="points-tabs-regular",  # Optional: to handle tab switching callbacks
            active_tab="tab-points-regular",
            style={"border-radius":"6px", "background-color":"white"}
    ),
    label="Runkosarja", 
    id = "regular-season-tab"),
    dbc.Tab(dbc.Tabs(
            points_tabs['post'],
            id="points-tabs-post",  # Optional: to handle tab switching callbacks
            active_tab="tab-points-post",
            style={"border-radius":"6px", "background-color":"white"}
    ),
    label="Playoffs", 
    id = "post-season-tab")   
]

points_tabs_total = dbc.Tabs(
    tabs_of_tabs,
    active_tab="regular-season-tab",
    style={"border-radius":"6px", "background-color":"white"}
)
