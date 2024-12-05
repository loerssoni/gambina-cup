key_path = 'secrets/sheet-reader-key.json'
spreadsheet_id = '1VwC-GYUuEjsZr1DqGgeo8Wkv6_Ly6NZjAV07Zeik4ko'


import os
import pandas as pd

from apiclient import discovery
from google.oauth2 import service_account

scopes = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/spreadsheets']
secret_file = os.path.join(os.getcwd(), key_path)


credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
service = discovery.build('sheets', 'v4', credentials=credentials)

def schedule_sheets_update(mode):
    if mode not in ['create','delete']:
        raise ValueError('Invalid mode')
    range_name = 'AIKATAULU!A1:D100'
    template_id = '61864045'
    
    schedule = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name, valueRenderOption='UNFORMATTED_VALUE').execute()
    
    metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    all_sheets = {p['properties']['title']:p['properties']['sheetId'] for p in metadata['sheets']}
    
    n_games = {}
    reqs = []
    
    update_cells = []
    scoreboard_updates = []
    for i, row in enumerate(schedule['values'][1:]):
        if len(row) == 4:
            teams = sorted(row[1:3])
            game_id = f'{teams[0]}{teams[1]}{row[0]}'
            n_games[game_id] = n_games.get(game_id, 0) + 1

            name = f'{game_id}_{n_games[game_id]}'
            update_cells.append((name, True))

            if (mode == 'create'):
                if name not in all_sheets:
                    reqs.append({
                        "duplicateSheet": {
                            "sourceSheetId": template_id,
                            "newSheetName": name,
                        }
                    })
                scoreboard_updates.append([
                    {
                        'range': f'{name}!A2:A2',  # Specify the first range
                        'values': [[row[1]]]
                    },
                    {
                        'range': f'{name}!F2:F2',  # Specify the first range
                        'values': [[row[2]]]
                    }
                ])
                
            elif (mode=='delete' and name in all_sheets):
                reqs.append({
                    f"deleteSheet": {
                        "sheetId": all_sheets[name]
                    }
                })
        else:
            update_cells.append(('', False))

    if len(reqs) > 0:# Execute the batchUpdate request
        body = {"requests": reqs}
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        all_sheets = {p['properties']['title']:p['properties']['sheetId'] for p in metadata['sheets']}
    
   
    cell_updates = []
    if mode == 'create':
        url_base = f"""=HYPERLINK(\"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"""
        names = [r['duplicateSheet']['newSheetName'] for r in reqs]
        for name, update in update_cells:
            if update:
                cell_updates.append([f"""{url_base}?gid={all_sheets[name]}#gid={all_sheets[name]}", "Gamelink")"""])
            else:
                cell_updates.append([""])

    if mode == 'delete':
        cell_updates = [[""] for i in schedule['values']]
    
    body = {
        'values': cell_updates
    }

    response = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="AIKATAULU!E2:E",  # Specify the range
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    if mode == 'create':
        response = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'data':scoreboard_updates, 'valueInputOption':'USER_ENTERED'}
        ).execute()
    
    
    move_requests = []
    for sheet_name in ['JOUKKUEET','NHL','TEMPLATE', 'AIKATAULU']:
        move_requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": all_sheets[sheet_name],
                "index": 0
            },
            "fields": "index"
        }})
    
    request_body_move = {
        "requests": [move_requests]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=request_body_move
    ).execute()

    return

def read_game_data(schedule):
    
    n_games = {}
    metadata_rows = []
    ranges = []
    for row in schedule.to_dict(orient='records'):
        teams = sorted([row['KOTI'], row['VIERAS']])
        game_id = f"{teams[0]}{teams[1]}{row['SARJA']}"
        n_games[game_id] = n_games.get(game_id, 0) + 1

        name = f'{game_id}_{n_games[game_id]}'
        row['name'] = name
        ranges.append(f'{name}!A6:J39')
        metadata_rows.append(row)

    # Request to batch get values from multiple ranges
    response = service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id,
        ranges=ranges,
        valueRenderOption='UNFORMATTED_VALUE'
    ).execute()

    goals = []
    for value_range, metadata in zip(response['valueRanges'], metadata_rows):
        metadata['game_state'] = value_range['values'][6][3]
            
        for i, row in enumerate(value_range.get('values', [])[:34]):
            if len(row) > 0 and row[0] != '':
                
                row_data = {
                    'scoring_team':'KOTI',
                    'scorer':row[0],
                    'ass_1': row[1],
                    'ass_2': row[2],
                    'overtime': i == 33
                }

                row_data.update(metadata)
                goals.append(row_data)
                
            if len(row) > 5 and row[5] != '':
                row_data = {
                    'scoring_team':'VIERAS',
                    'scorer':row[5],
                    'overtime': i == 33
                }

                if len(row) > 6:
                    row_data['ass_1'] = row[6]
                if len(row) > 7:
                    row_data['ass_2'] = row[7]

                row_data.update(metadata)
                goals.append(row_data)
                
    if len(goals) > 0:
        goals = pd.DataFrame(goals)
        goals = goals[goals.scorer != '']
        goals['scoring_team_pos'] = goals.scoring_team.copy()
        goals['scoring_team'] = goals.apply(lambda x: x[x['scoring_team']], axis=1)

    else:
        goals = pd.DataFrame(columns=['name', 'scoring_team_pos', 'scoring_team','scorer','ass_1','ass_2','overtime', 'KOTI','VIERAS','SARJA'])        
        
    return pd.DataFrame(metadata_rows), goals

def get_new_schedule_rows(data):
    n_teams = len(data.games.home.unique())
    series_wins = {
                'Puolivälierät': 3,
                'Valdemar': 1,
                'Sijoitusotteluvälierät': 1,
                'Välierät': 3,
                'Sijoitusottelu 5.': 1,
                'Sijoitusottelu 7.': 1,
                'Pronssiottelu': 1,
                'Finaali': 3,
    }
    games_scheduled = pd.melt(data.games, id_vars='SARJA', value_vars=['KOTI','VIERAS'])
    games_scheduled.columns = ['sarja','var','team']
    games_scheduled = games_scheduled[['sarja','team']].value_counts().reset_index()

    seedings = pd.melt(pd.DataFrame(data.get_seedings()), ignore_index=False).dropna()
    seedings.columns = ['sarja','team']
    seedings = seedings.merge(data.standings[['sarja','team', 'wins','losses']], how='left').set_index(seedings.index)
    seedings = seedings.merge(games_scheduled, how='left').set_index(seedings.index)
    seedings[['wins','losses', 'count']] = seedings[['wins','losses','count']].fillna(0).astype(int)
    seedings['series_wins'] = seedings.sarja.replace(series_wins)
    seedings['required_games'] = seedings['series_wins'] + seedings[['wins','losses']].min(axis=1)

    new_rows = []
    for sarja in seedings.sarja.unique():
        sarja_seeds = seedings.loc[seedings.sarja == sarja]
        if sarja == 'Valdemar' and n_teams == 8:
            pass
        if sarja == 'Valdemar' and n_teams == 9:
            top = sarja_seeds.loc[1, 'team']
            mid = sarja_seeds.loc[2, 'team']
            bot = sarja_seeds.loc[3, 'team']
            new_rows.append([sarja, bot, top, 'Ei valittu'])
            new_rows.append([sarja, mid, bot, 'Ei valittu'])
            new_rows.append([sarja, top, mid, 'Ei valittu'])
            
        else:
            for i in range(6):
                for seed in range(1, len(sarja_seeds)//2 + 1):
                    top_seed = sarja_seeds.loc[seed, 'team']
                    lower_seed = sarja_seeds.loc[len(sarja_seeds) - seed + 1, 'team']
                    if sarja_seeds.loc[seed, 'required_games'] >= i > sarja_seeds.loc[seed, 'count']:
                        if i % 2:    
                            new_rows.append([sarja, top_seed, lower_seed, 'Ei valittu'])
                        else:
                            new_rows.append([sarja, lower_seed, top_seed, 'Ei valittu'])
    return new_rows

def update_schedule():
    from game_data import GameData
    data = GameData()
    new_rows = get_new_schedule_rows(data)

    sheet_name = "AIKATAULU"

    # Read the data from column A to find the first empty row
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A:A"
    ).execute()

    values = response.get('values', [])
    first_empty_row = len(values) + 1 if values else 1

    # Define the range starting from the first empty row
    update_range = f"{sheet_name}!A{first_empty_row}:D"

    # Define the data to write
    body = {
        "values": new_rows
    }

    # # Perform the update
    response = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=update_range,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()

    print("Update response:", response)


def read_data(range_name):
    data = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name, valueRenderOption='UNFORMATTED_VALUE').execute()
    return pd.DataFrame(data['values'][1:], columns=data['values'][0])
    