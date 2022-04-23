from __future__ import print_function


import os.path
from typing import Sequence
import pytz
from datetime import datetime
from dotenv import load_dotenv
import discord

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


load_dotenv()
API_KEY = os.getenv('GOOGLE_API_KEY')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# https://docs.google.com/spreadsheets/d/17pno9beqULzAC3QXDHC8yLwOD7HS9QM6qhh2UX_muZw/edit#gid=0 
SAMPLE_SPREADSHEET_ID = '17pno9beqULzAC3QXDHC8yLwOD7HS9QM6qhh2UX_muZw'
RANGE_NAME = 'Sheet1!A2:F'


class Sheet():
    def __init__(self):
        creds = service_account.Credentials.from_service_account_file('google_creds.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        self.sheet = service.spreadsheets()

    def update_wl_list(self, users: Sequence[discord.Member]):
        """Write all WLed users to the sheet.

        For un-recorded user, [user.id, user.name, , timestamp] will be reocrded.
        If any existing user is not shown in the passed users list, it will be removed.
        """
        new = [[str(user.id), user.name] for user in users]
        new = self._sort_by_id(new)

        old = self._all_sheeted_users()
        updated_rows = self._remove_invalid_entries(old, new)
        updated_rows = self._add_new_entries(updated_rows, new)

        self.write(updated_rows)

    def _remove_invalid_entries(self, old, new):
        new_wl_ids = set(row[0] for row in new)
        for i in range(len(old) - 1, -1, -1): # Remove in reserve order
            if old[i][0] not in new_wl_ids:
                print(f'Removed user({old[i]}) since they no longer has whitelist role')
                old.pop(i)
            elif i != 0 and old[i][0] == old[i-1][0]:
                print(f'Removed row ({old[i]}) due to duplication')
                old.pop(i)
        return old

    def _add_new_entries(self, old, new):
        current_time = self._current_time()
        i = 0  # index for old
        for j in range(len(new)):
            if i == len(old) or old[i][0] != new[j][0]: # if no such ID
                old.insert(i, new[j])
                self._update_timestamp(current_time, old, i)
                print(f'Add new User({new[j]})')
            else:
                if old[i][1] != new[j][1]:  # If name is different, update name
                    print(f'Update User({old[i][0]})\'s Name from {old[i][1]} to {new[j][1]}')
                    self._update_timestamp(current_time, old, i)
                    old[i][1] = new[j][1]
            i = i + 1
        return old
            
    def _update_timestamp(self, current_time, rows, index):
        while len(rows[index]) < 4:
            rows[index].append('')
        rows[index][3] = current_time


    def _all_sheeted_users(self) -> Sequence:
        try:
            result = self.sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                                        range=RANGE_NAME).execute()
        except HttpError as err:
            print(err)
        
        values = result.get('values', [])
        sorted_values = self._sort_by_id(values)
        return sorted_values

    def _sort_by_id(self, rows):
        return sorted(rows, key=lambda row: row[0])

    def write(self, values):
        print(values)
        values.append([''] * 4)
        print(values)
        body = {'values': values}
        result = self.sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption='RAW', body=body
        ).execute()
        print(result)

    def _current_time(self):
        return datetime.now(pytz.timezone('US/Eastern')).strftime("%Y:%m:%d %H:%M:%S")


if __name__ == '__main__':
    sheet = Sheet()
    # sheet.read_simple()
    # sheet.write()
    # sheet.current_time()


"""
Scenario: start
- Read all entries from the sheet
- List all users with WL role, add new users to the sheet

Scenario: When a user is given WL role
- Read all entries from the sheet, and add the user to the ordered list

Scenario: When the user provide address in that channel
- update it to the sheet
"""