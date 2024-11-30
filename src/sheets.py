key_path = './secrets/sheet-reader-key.json'
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
    for sheet_name in ['AIKATAULU','JOUKKUEET','NHL','TEMPLATE']:
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
        ranges.append(f'{name}!A5:J30')
        metadata_rows.append(row)

    # Request to batch get values from multiple ranges
    response = service.spreadsheets().values().batchGet(
        spreadsheetId=spreadsheet_id,
        ranges=ranges,
        valueRenderOption='UNFORMATTED_VALUE'
    ).execute()

    goals = []
    for value_range, metadata in zip(response['valueRanges'], metadata_rows):
        metadata['game_state'] = value_range['values'][23][3]
        for i, row in enumerate(value_range.get('values', [])[:20]):
            if len(row) > 0:
                row_data = {
                    'scoring_team':'KOTI',
                    'scorer':row[0],
                    'ass_1': row[1],
                    'ass_2': row[2],
                    'n_goals': i + 1
                }

                row_data.update(metadata)
                goals.append(row_data)

                row_data = {
                    'scoring_team':'VIERAS',
                    'scorer':row[5],
                    'ass_1': row[6],
                    'ass_2': row[7],
                    'n_goals': i + 1
                }
                row_data.update(metadata)
                goals.append(row_data)
    goals = pd.DataFrame(goals)
    goals = goals[goals.scorer != '']
    return pd.DataFrame(metadata_rows), goals


def read_data(range_name):
    data = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name, valueRenderOption='UNFORMATTED_VALUE').execute()
    return pd.DataFrame(data['values'][1:], columns=data['values'][0])
    