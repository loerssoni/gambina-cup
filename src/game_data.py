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

def get_base_standings(team_goals):
    # Aggregate data by team and sarja
    standings = team_goals.groupby(['sarja', 'team'])[['goals', 'opponent_goals', 'regulation_wins', 
            'goal_diff', 'wins', 'losses','extra_points','points']].sum().reset_index() 
    standings['games'] = team_goals.groupby(['sarja', 'team'])['goals'].count().reset_index(drop=True)
    
    # Add ranking by points within each sarja
    standings['rank'] = standings.groupby('sarja')['points'].rank(method='min', ascending=False).astype(int) 
    standings = standings.sort_values(by=['sarja', 'rank']).reset_index(drop=True)
    return standings

def break_ties(shared_games, original_standings):
    # get new standings
    tiebreak_standings = get_base_standings(shared_games)

    # Break ties by points between tied teams
    tiebreak = tiebreak_standings['rank'].astype(int)
    if tiebreak.nunique() != 1:
        return tiebreak
    
    print('Games')
    tiebreak = tiebreak_standings['games'].rank(method='min', ascending=True)    
    if tiebreak.nunique() != 1:
        return tiebreak

    print('Goal diff')
    # if still all ties, check goal diff between tied teams
    tiebreak = tiebreak_standings['goal_diff'].rank(method='min', ascending=False)
    if tiebreak.nunique() != 1:
        return tiebreak

    print('Goals')
    # if still all ties, check goals scoted between tied teams
    tiebreak = tiebreak_standings['goals'].rank(method='min', ascending=False)
    if tiebreak.nunique() != 1:
        return tiebreak

    print('Regulation wins')
    # if still all ties, check regulation wins for entire group
    tiebreak = rank_sarjateams['regulation_wins'].rank(method='min', ascending=False)
    if tiebreak.nunique() != 1:
        return tiebreak

    print('Goal differential')
    tiebreak = rank_sarjateams['goal_diff'].rank(method='min', ascending=False)
    if tiebreak.nunique() != 1:
        return tiebreak

    print('Goals')
    tiebreak = rank_sarjateams['goals'].rank(method='min', ascending=False)
    if tiebreak.nunique() != 1:
        return tiebreak

    return None

def run_tiebreak(standings, team_goals):
    for sarja in standings.sarja.unique():
        sarjateams = standings.loc[standings.sarja == sarja].copy()
        iters = 0
        while sarjateams['rank'].nunique() != len(sarjateams['rank']):
            for rank in sarjateams['rank'].unique():
                rank_teams = sarjateams.loc[sarjateams['rank'] == rank]

                if len(rank_teams) > 1:
                    filtered = (team_goals.sarja == sarja)
                    filtered = filtered & (team_goals['team'].isin(rank_teams.team))
                    filtered = filtered & (team_goals['opponent_team'].isin(rank_teams.team))
                    shared_games = team_goals.loc[filtered]

                    print('Breaking ties for rank ', rank)

                    tiebreak = break_ties(shared_games, standings)
                    if tiebreak is None:
                        break
                    sarjateams['tiebreak_rank'] = sarjateams['rank'].copy()

                    rank_filter = sarjateams['rank'] == rank
                    sarjateams.loc[rank_filter, 'tiebreak_rank'] = sarjateams.loc[rank_filter, 'tiebreak_rank'] + tiebreak.values - 1

                    sarjateams['rank'] = sarjateams['tiebreak_rank'].copy()
            iters += 1
            if iters > 100:
                break
        standings.loc[standings.sarja == sarja, 'rank'] = sarjateams['rank']
    return standings

def get_standings(games, goals):

    games_ended = games.loc[games.game_state == 'PÄÄTTYNYT'].copy()
    games_long = pd.melt(games_ended, ['SARJA', 'name'],['KOTI','VIERAS'], value_name='scoring_team')
    team_goals = goals.groupby(['SARJA', 'name','scoring_team'], as_index=False).agg({'scorer':'count','overtime':'max'})
    team_goals = games_long.merge(team_goals, how='left', on=['SARJA', 'name', 'scoring_team']).drop('variable', axis=1)
    team_goals.columns = ['sarja','game','team','goals','overtime']
    team_goals['goals'] = team_goals['goals'].fillna(0)


    # Add opponent goals
    team_goals['opponent_team'] = team_goals.groupby(['game'])['team'].transform(lambda x: x[::-1].values)
    team_goals['opponent_goals'] = team_goals.groupby(['game'])['goals'].transform(lambda x: x[::-1].values)
    team_goals['goal_diff'] = team_goals['goals'] - team_goals['opponent_goals'] 

    # Add Wins, Losses (including OT Losses), OT Losses, and Points
    team_goals['wins'] = (team_goals['goals'] > team_goals['opponent_goals']).astype(int) 
    team_goals['regulation_wins'] = (team_goals['wins'] == 1)&(team_goals['overtime'] == 0).astype(int)
    team_goals['losses'] = (team_goals['goals'] < team_goals['opponent_goals']).astype(int) 
    team_goals['extra_points'] = ((team_goals['goals'] < team_goals['opponent_goals']) & (team_goals['overtime'] == 1)).astype(int) 
    team_goals['points'] = (team_goals['wins'] * 2) + team_goals['extra_points']
 
    standings = get_base_standings(team_goals)

    # Add rank back to the original DataFrame
    team_goals = team_goals.merge(standings[['sarja', 'team', 'rank']], on=['sarja', 'team'], how='left')
    team_goals['opponent_team'] = team_goals['opponent_team'].astype(str)
    team_goals = team_goals.merge(standings[['sarja', 'team', 'rank']], 
                                  left_on=['sarja', 'opponent_team'], 
                                  right_on=['sarja', 'team'], how='left', suffixes=('', '_opp'))
    standings = run_tiebreak(standings, team_goals)
    
    # finally ensure that all teams are present
    all_teams = pd.melt(games, id_vars='SARJA', value_vars=['KOTI','VIERAS'])[['SARJA','value']].drop_duplicates()
    all_teams.columns = ['sarja','team']
    standings = all_teams.merge(standings, how='left')
    standings[standings.columns[2:]] = standings[standings.columns[2:]].fillna(0).astype(int)
    standings.loc[standings['rank'] == 0, 'rank'] = standings.groupby('sarja')['rank'].transform('max') + 1
    return standings.sort_values('rank')


def get_player_stats(players, goals, teams, games, season):

    if season == 'regular':
        goals = goals[goals['SARJA'].str.contains('lohko')].copy()
    elif season == 'post':
        goals = goals[~goals['SARJA'].str.contains('lohko')].copy()
        
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
    games_filter = games.game_state == 'PÄÄTTYNYT'
    if season == 'regular':
        games_filter = games_filter & (games.SARJA.str.contains('lohko'))
    elif season == 'post':
        games_filter = games_filter & (~games.SARJA.str.contains('lohko'))
        
    games_played = pd.concat([
        games[games_filter].merge(players, right_on='Pelaaja', left_on='KOTI')[['name','Player']],
        games[games_filter].merge(players, right_on='Pelaaja', left_on='VIERAS')[['name','Player']]
    ]).Player.value_counts()
    games_played.name = 'games_played'

    players = players.join(games_played, on='Player')


    return players

def get_players(goals, teams, games):

    players = read_players()

    player_stats = {}
    for season_type in ['regular', 'post']:
        player_stats[season_type] = get_player_stats(players, goals, teams, games, season_type)

    return player_stats

def get_scoreboard(games, goals, standings, teams):
    games_long = pd.melt(games, ['SARJA', 'name'],['KOTI','VIERAS'], value_name='scoring_team')
    team_goals = goals.groupby(['SARJA', 'name','scoring_team'], as_index=False).agg({'scorer':'count','overtime':'max'})
    team_goals = games_long.merge(team_goals, how='left', on=['SARJA', 'name', 'scoring_team']).drop('variable', axis=1)
    team_goals.columns = ['sarja','game','team','goals','overtime']
    team_goals['goals'] = team_goals['goals'].fillna(0)


    scoreboard = games[['SARJA','name','KOTI', 'VIERAS', 'game_state']].merge(team_goals, how='left', left_on=['SARJA','name', 'KOTI'], 
                                                                    right_on=['sarja','game','team'])\
        .merge(team_goals, how='left', left_on=['SARJA','name', 'VIERAS'], right_on=['sarja','game','team'], suffixes = ('_home','_away'))
    scoreboard['overtime'] = scoreboard.overtime_home.fillna(False)
    scoreboard = scoreboard[['SARJA', 'name','game_state', 'team_home','goals_home','overtime', 'team_away', 'goals_away']].copy()
    scoreboard[['goals_home', 'goals_away']] = scoreboard[['goals_home', 'goals_away']].fillna(0)
    scoreboard['series'] = scoreboard['name'].str[:-2]
    scoreboard.loc[scoreboard.series.str.endswith('lohko'), 'series'] = scoreboard.loc[scoreboard.series.str.endswith('lohko'), 'series'].str[-7:]
    scoreboard['winner'] = scoreboard.apply(
        lambda row: row['team_home'] if row['goals_home'] > row['goals_away'] else 
                    (row['team_away'] if row['goals_away'] > row['goals_home'] else 'TIE'), 
        axis=1
    )
    scoreboard = scoreboard \
            .merge(standings, how='left', left_on=['team_home', 'SARJA'], right_on=['team','sarja'])\
            .merge(standings, how='left', left_on=['team_away', 'SARJA'], right_on=['team','sarja'], suffixes=('_home_s','_away_s'))
    stcols = ['wins_home_s','losses_home_s','extra_points_home_s', 'wins_away_s','losses_away_s','extra_points_away_s']
    scoreboard[stcols] = scoreboard[stcols].fillna(0).astype(int)

    scoreboard['score'] = scoreboard['goals_home'].astype(int).astype(str) + ' - ' + scoreboard['goals_away'].astype(int).astype(str)
    scoreboard.loc[scoreboard.overtime, 'score'] += ' (JA)'
    
    scoreboard['record_home'] = '(' + scoreboard['wins_home_s'].astype(int).astype(str) + ' - ' \
        + scoreboard['losses_home_s'].astype(int).astype(str) + ' - ' \
        + scoreboard['extra_points_home_s'].astype(int).astype(str) + ')'
    scoreboard['record_away'] = '(' + scoreboard['wins_away_s'].astype(int).astype(str) + ' - ' \
        + scoreboard['losses_away_s'].astype(int).astype(str) + ' - '  \
        + scoreboard['extra_points_away_s'].astype(int).astype(str) + ')'
    scoreboard['record_h2h'] = '(' + scoreboard['wins_home_s'].astype(int).astype(str) + ' - ' + scoreboard['wins_away_s'].astype(int).astype(str) + ')'
    scoreboard['record_h2h'] = np.select([scoreboard.SARJA.str.endswith('lohko').values], [['' for i in range(len(scoreboard))]], scoreboard.record_h2h)
    scoreboard['record_home'] = np.select([scoreboard.SARJA.str.endswith('lohko')], [scoreboard.record_home], '')
    scoreboard['record_away'] = np.select([scoreboard.SARJA.str.endswith('lohko')], [scoreboard.record_away], ['' for i in range(len(scoreboard))])

    scoreboard = scoreboard.merge(teams, left_on='team_home', right_on='Pelaaja').merge(teams, left_on='team_away', right_on='Pelaaja', suffixes=('_KOTI','_VIERAS'))
    scoreboard['playercard_home'] = scoreboard['team_home'] + ' (' + scoreboard['Joukkue_KOTI'] + ')'
    scoreboard['playercard_away'] = scoreboard['team_away'] + ' (' + scoreboard['Joukkue_VIERAS'] + ')'
    return scoreboard

class GameData():
    def __init__(self):
        self.refresh_data()
    
    def refresh_data(self):
        self.teams = read_teams()
        self.schedule = read_schedule()
        self.games, self.goals = sheets.read_game_data(self.schedule)
        self.standings = get_standings(self.games, self.goals)
        self.scoreboard = get_scoreboard(self.games, self.goals, self.standings, self.teams)
        self.players = get_players(self.goals, self.teams, self.games)

    
    def render_scoreboard(self, scoreboard):
        render_cols = ['SARJA','team_home','team_away', 'score',
                'record_home','record_away', 'record_h2h', 'game_state']
        return scoreboard[render_cols].to_dict(orient='records')
    
    def get_live(self):
        scoreboard = self.scoreboard.loc[(self.scoreboard.game_state == 'KÄYNNISSÄ')]
        return self.render_scoreboard(scoreboard)

    def get_ended(self):
        scoreboard = self.scoreboard.loc[(self.scoreboard.game_state == 'PÄÄTTYNYT')].iloc[-4:]
        return self.render_scoreboard(scoreboard)
    
    def get_upcoming(self):
        scoreboard = self.scoreboard.loc[(self.scoreboard.game_state == 'TULOSSA')].iloc[:2]
        return self.render_scoreboard(scoreboard)
    
    def render_points(self, mode='points', season='regular'):
        output = self.players[season][['Player', 'games_played', 'goal_scorers', 'assists', 'points', 'Pelaaja']].copy()
        output.columns = ['Pelaaja','O','M','S','P', 'Joukkue']
        output[['O','M','S','P']] = output[['O','M','S','P']].fillna(0).astype(int)
        if mode == 'goals':
            output = output.sort_values(['M','O'], ascending=[False, True])
        elif mode == 'assists':
            output = output.sort_values(['S','O'], ascending=[False, True])
        else:
            output = output.sort_values(['P','M','O'], ascending=[False, False, True])  
        
        if mode != 'show-all':
            output = output.iloc[:5]
        return output
        

    def render_standings(self):
        input_cols = ['rank', 'team', 'games', 'wins', 'extra_points', 'losses', 'points']

        group_a = self.standings.loc[self.standings.sarja == 'A-lohko', input_cols]
        group_b = self.standings.loc[self.standings.sarja == 'B-lohko', input_cols]
        
        group_a.columns = ['Sija','Joukkue', 'O', 'V', 'LP', 'T', 'P']
        group_b.columns = ['Sija','Joukkue', 'O', 'V', 'LP', 'T', 'P']
        return group_a, group_b

    def render_playoff_games(self):
        playoff_games = self.games.loc[~self.games.SARJA.str.contains('lohko')].copy()
        playoff_games.columns = ['sarja','home', 'away','arena','name','game_state']
        playoff_games['name'] = playoff_games['name'].str[:-2]

        playoff_games = pd.melt(playoff_games, id_vars=['sarja', 'name'], value_vars=['home', 'away'], 
                                value_name='team', ignore_index=False).sort_index()
        playoff_games = playoff_games[~playoff_games.drop('variable', axis=1).duplicated(keep='first')].copy()
        playoff_games = playoff_games.merge(self.standings, how='left', on=['sarja', 'team'])
        playoff_games = playoff_games.sort_values(['sarja', 'name','variable'], ascending=[True, True, False])
        playoff_games = playoff_games.pivot(index=['sarja','name'], columns=['variable'], values=['team','wins'])
        playoff_games.columns = ['_'.join(s) for s in playoff_games.columns]
        playoff_games = playoff_games
        
        playoff_games = playoff_games.astype(str)
        games_mapping = {
            'Puolivälierät': 4,
            'Välierät': 2,
            'Finaali': 1,
            'Pronssiottelu': 1,
            'Valdemar': 1
        }
        games_index = []
        for series, n in games_mapping.items():
            for i in range(n):
                sarjagames = playoff_games[playoff_games.index.get_level_values('sarja') == series]
                if len(sarjagames) < i+1:
                    games_index.append({
                        'sarja':series,
                        'name': str('')
                    })
                else:
                    games_index.append({
                        'sarja':series,
                        'name': sarjagames.index.get_level_values('name')[i]
                    })
        playoff_games = pd.DataFrame(games_index).set_index(['sarja', 'name'])\
            .merge(playoff_games, how='left', left_index=True, right_index=True).fillna('')
        playoff_games = playoff_games.sort_values(['sarja', 'name'], ascending=[True, False])
        return playoff_games
