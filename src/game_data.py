import pandas as pd
import numpy as np

import sheets

def read_players():
    range_name = 'NHL!A1:T'  
    return sheets.read_data(range_name)

def read_teams():
    range_name = 'JOUKKUEET!A1:B'  
    return sheets.read_data(range_name)

def read_schedule():
    range_name = 'AIKATAULU!A1:D'
    
    return sheets.read_data(range_name).dropna()

def read_players():
    range_name = 'NHL!A1:T'  
    return sheets.read_data(range_name)


def get_scoreboard(games, goals):
    scores = goals.groupby(['scoring_team', 'SARJA', 'KOTI', 'VIERAS', 'name'], as_index=False)['n_goals'].max()
    scores = scores.pivot(columns='scoring_team', index='name', values='n_goals')

    if len(goals) > 0:
        scoreboard = games.join(scores, on=['name'], rsuffix='_SCORE')
    else:
        scoreboard = games
        scoreboard['KOTI_SCORE'] = 0
        scoreboard['VIERAS_SCORE'] = 0

    scoreboard[['KOTI_SCORE', 'VIERAS_SCORE']] = scoreboard[['KOTI_SCORE', 'VIERAS_SCORE']].fillna(0)
    scoreboard['game_n'] = ''
    scoreboard.loc[~scoreboard['SARJA'].str.contains('lohko'), 'game_n'] = 'Playoffs (Game ' + scoreboard['name'].str.split('_').str[1] + '.)'
    scoreboard['series'] = scoreboard['name'].str[:-2]
    scoreboard.loc[scoreboard.series.str.endswith('lohko'), 'series'] = scoreboard.loc[scoreboard.series.str.endswith('lohko'), 'series'].str[-7:]
    scoreboard['winner'] = scoreboard.apply(
        lambda row: row['KOTI'] if row['KOTI_SCORE'] > row['VIERAS_SCORE'] else 
                    (row['VIERAS'] if row['VIERAS_SCORE'] > row['KOTI_SCORE'] else 'TIE'), 
        axis=1
    )

    return scoreboard

def get_standings(scoreboard):    # Transform to long-form and count victories as before
    long_df = pd.melt(
        scoreboard.loc[scoreboard.game_state == 'PÄÄTTYNYT'], 
        id_vars=["series", "winner", "KOTI_SCORE", "VIERAS_SCORE"], 
        value_vars=["KOTI", "VIERAS"],
        value_name="team"
    )
    
    long_df['win'] = long_df['team'] == long_df['winner']
    long_df['tie'] = long_df['winner'] == 'TIE'
    long_df['loss'] = (~long_df['win'])&(~long_df['tie'])
    long_df['goalsfor'] = 0
    long_df.loc[long_df.variable == 'KOTI', 'goalsfor'] += long_df.loc[long_df.variable == 'KOTI', 'KOTI_SCORE']
    long_df.loc[long_df.variable == 'VIERAS', 'goalsfor'] += long_df.loc[long_df.variable == 'VIERAS', 'VIERAS_SCORE']
    long_df['goalsaga'] = 0
    long_df.loc[long_df.variable == 'KOTI', 'goalsaga'] += long_df.loc[long_df.variable == 'KOTI', 'VIERAS_SCORE']
    long_df.loc[long_df.variable == 'VIERAS', 'goalsaga'] += long_df.loc[long_df.variable == 'VIERAS', 'KOTI_SCORE']
    long_df['games'] = 1
    standings = long_df.groupby(['series','team'], as_index=False)[['games', 'win','tie','loss']].sum()
    standings['points'] = standings['win'] * 2 + standings['tie']

    base = scoreboard[['series','KOTI']]
    base.columns = ['series','team']
    base2 = scoreboard[['series','VIERAS']]
    base2.columns = base.columns
    base = pd.concat([base, base2]).drop_duplicates()
    final = base.merge(standings, how='left', on=['series','team'])
    
    final =  final.fillna(0).sort_values(['series', 'points', 'win','games'], ascending=[True, False, False, True]).reset_index(drop=True)
    final['position'] = final.groupby('series').cumcount()  + 1
    final = final.set_index(['series', 'team']).astype(int).reset_index().astype(str)
    return final

def get_players(goals, teams, games):

    players = read_players()
    points_data = {}
    points_data['goal_scorers'] = goals.scorer.value_counts()
    points_data['assist1'] = goals.ass_1.value_counts()
    points_data['assist2'] = goals.ass_2.value_counts()
    points_data = pd.DataFrame(points_data).fillna(0)
    points_data['assists'] = points_data[['assist1','assist2']].sum(1)
    points_data['points'] = points_data[['goal_scorers','assist1','assist2']].sum(1)
    points_data = points_data.loc[points_data.index != '']
    players = players.join(points_data, on='Player')
    players[points_data.columns] = players[points_data.columns].fillna(0)
    players = players.merge(teams, left_on='Team', right_on='Joukkue', how='inner')
    players['Joukkue'] = players.Player + '\n(' + players.Joukkue + ')'
    games_played = pd.concat([
        games[games.game_state == 'PÄÄTTYNYT'].merge(players, right_on='Pelaaja', left_on='KOTI')[['name','Player']],
        games[games.game_state == 'PÄÄTTYNYT'].merge(players, right_on='Pelaaja', left_on='VIERAS')[['name','Player']]
    ]).Player.value_counts()
    games_played.name = 'games_played'

    players = players.join(games_played, on='Player')

    return players

def scoreboard_standings(scoreboard, standings, teams):
    scoreboard = scoreboard \
            .merge(standings, left_on=['KOTI', 'series'], right_on=['team','series'])\
            .merge(standings, left_on=['VIERAS', 'series'], right_on=['team','series'], suffixes=('_home','_away'))
    scoreboard['score'] = scoreboard['KOTI_SCORE'].astype(int).astype(str) + ' - ' + scoreboard['VIERAS_SCORE'].astype(int).astype(str)
    scoreboard['record_home'] = '(' + scoreboard['win_home'].astype(int).astype(str) + ' - ' + scoreboard['loss_home'].astype(int).astype(str) + ' - ' + scoreboard['tie_home'].astype(int).astype(str) + ')'
    scoreboard['record_away'] = '(' + scoreboard['win_away'].astype(int).astype(str) + ' - ' + scoreboard['loss_away'].astype(int).astype(str) + ' - ' + scoreboard['tie_away'].astype(int).astype(str) + ')'
    scoreboard['record_h2h'] = '(' + scoreboard['win_home'].astype(int).astype(str) + ' - ' + scoreboard['win_away'].astype(int).astype(str) + ')'
    scoreboard['record_h2h'] = np.select([scoreboard.SARJA.str.endswith('lohko').values], [['' for i in range(len(scoreboard))]], scoreboard.record_h2h)
    scoreboard['record_home'] = np.select([scoreboard.SARJA.str.endswith('lohko')], [scoreboard.record_home], '')
    scoreboard['record_away'] = np.select([scoreboard.SARJA.str.endswith('lohko')], [scoreboard.record_away], ['' for i in range(len(scoreboard))])
    
    scoreboard = scoreboard.merge(teams, left_on='KOTI', right_on='Pelaaja').merge(teams, left_on='VIERAS', right_on='Pelaaja', suffixes=('_KOTI','_VIERAS'))
    scoreboard['playercard_home'] = scoreboard['KOTI'] + ' (' + scoreboard['Joukkue_KOTI'] + ')'
    scoreboard['playercard_away'] = scoreboard['VIERAS'] + ' (' + scoreboard['Joukkue_VIERAS'] + ')'
    return scoreboard

class GameData():
    def __init__(self):
        sheets.schedule_sheets_update('create')
        self.refresh_data()
    
    def refresh_data(self):
        self.teams = read_teams()
        self.schedule = read_schedule()
        self.games, self.goals = sheets.read_game_data(self.schedule)
        self.scoreboard = get_scoreboard(self.games, self.goals)
        self.standings = get_standings(self.scoreboard)
        self.scoreboard = scoreboard_standings(self.scoreboard, self.standings, self.teams)
        self.players = get_players(self.goals, self.teams, self.games)

    
    def render_scoreboard(self, scoreboard):
        render_cols = ['SARJA','KOTI','VIERAS',
                'AREENA', 'score', 'Joukkue_KOTI', 'Joukkue_VIERAS',
                'record_home','record_away', 'record_h2h', 'game_state']
        return scoreboard[render_cols].to_dict(orient='records')
    
    def get_live(self):
        scoreboard = self.scoreboard.loc[(self.scoreboard.game_state == 'KÄYNNISSÄ')]
        return self.render_scoreboard(scoreboard)

    def get_ended(self):
        scoreboard = self.scoreboard.loc[(self.scoreboard.game_state == 'PÄÄTTYNYT')].iloc[:4]
        return self.render_scoreboard(scoreboard)
    
    def get_upcoming(self):
        scoreboard = self.scoreboard.loc[(self.scoreboard.game_state == 'TULOSSA')].iloc[:2]
        return self.render_scoreboard(scoreboard)
    
    def render_points(self, mode='Pisteet'):
        output = self.players[['Player', 'games_played', 'goal_scorers', 'assists', 'points', 'Pelaaja']].copy()
        output.columns = ['Pelaaja','Ottelut','Maalit','Syötöt','Pisteet', 'Joukkue']
        
        if mode == 'Maalit':
            output = output.sort_values(['Maalit','Ottelut'], ascending=[False, True])
        elif mode == 'Syötöt':
            output = output.sort_values(['Syötöt','Ottelut'], ascending=[False, True])
        else:
            output = output.sort_values(['Pisteet','Maalit','Ottelut'], ascending=[False, False, True])  
        
        if mode != 'Näytä kaikki':
            output = output.iloc[:5]
        return output
        

    def render_standings(self):
        input_cols = ['team','games', 'win', 'tie', 'loss', 'points']

        group_a = self.standings.loc[self.standings.series == 'A-lohko', input_cols]
        group_b = self.standings.loc[self.standings.series == 'B-lohko', input_cols]
        
        group_a.columns = [' ', 'G', 'W', 'T', 'L', 'P']
        group_b.columns = [' ', 'G', 'W', 'T', 'L', 'P']
        return group_a, group_b
