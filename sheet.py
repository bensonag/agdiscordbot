from __future__ import print_function


import os.path
from typing import Sequence
import pytz
from datetime import datetime
import discord
import log

from typing import Union
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# https://docs.google.com/spreadsheets/d/17pno9beqULzAC3QXDHC8yLwOD7HS9QM6qhh2UX_muZw/edit#gid=0 
SAMPLE_SPREADSHEET_ID = '17pno9beqULzAC3QXDHC8yLwOD7HS9QM6qhh2UX_muZw'
RANGE_NAME = 'Sheet1!A2:F'


class Sheet():
    def __init__(self, logger: log.Logger):
        self._logger = logger
        creds = service_account.Credentials.from_service_account_file('google_creds.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        self.sheet = service.spreadsheets()

    def update_wl_list(self, members: Sequence[discord.Member]):
        """Write all WLed users to the sheet.

        For un-recorded user, [user.id, user.name, , timestamp] will be reocrded.
        If any existing user is not shown in the passed users list, it will be removed.
        """
        new = [self._member_to_row(member) for member in members]
        new = self._sort_by_id(new)

        old = self._all_sheeted_users()
        updated_rows = self._remove_invalid_entries(old, new)
        updated_rows = self._add_new_entries(updated_rows, new)

        self._write(updated_rows)

    def _remove_invalid_entries(self, old, new):
        new_wl_ids = set(row[0] for row in new)
        for i in range(len(old) - 1, -1, -1): # Remove in reserve order
            if old[i][0] not in new_wl_ids:
                self._logger.info(f'Removed user({old[i]}) since they no longer has whitelist role')
                old.pop(i)
            elif i != 0 and old[i][0] == old[i-1][0]:
                self._logger.warning(f'Removed row ({old[i]}) due to duplication')
                old.pop(i)
        return old

    def _member_to_row(self, member: discord.Member) -> Sequence:
        return [str(member.id), member.name, '', '']

    def _add_new_entries(self, old: Sequence[Sequence], new: Sequence[Sequence]):
        i = 0  # index for old
        for j in range(len(new)):
            if i == len(old) or old[i][0] != new[j][0]: # if no such ID
                old.insert(i, new[j])
                self._update_timestamp(old, i)
                self._logger.info(f'Add new User({new[j]})')
            else:
                if old[i][1] != new[j][1]:  # If name is different, update name
                    self._logger.warning(f'Update User({old[i][0]})\'s name from {old[i][1]} to {new[j][1]}')
                    self._update_timestamp(old, i)
                    old[i][1] = new[j][1]
            i = i + 1
        return old
    
    def add_one_entry(self, member: discord.Member):
        old = self._all_sheeted_users()
        if self._find_same_id(old, member.id) != None:
            self._logger.warning(f'User ({member.id}. {member.name}) already exists!')
            return

        member = self._member_to_row(member)
        self._logger.info(f'Add new User({member})')
        old.append(member)
        self._update_timestamp(old, len(old) - 1)
        updated = self._sort_by_id(old)
        self._write(updated)
    
    def remove_one_entry(self, member: discord.Member):
        sheeted_members = self._all_sheeted_users()
        index = self._find_same_id(sheeted_members, member.id)
        if index is None:
            self._logger.warning(f'No User ({member.id}. {member.name}) exists! Deletion aborted')
            return
        deleted_row = sheeted_members.pop(index)
        self._logger.info(f'Removed User ({deleted_row})')
        self._write(sheeted_members)
    
    def record_address(self, member: discord.Member, addr: str):
        sheeted_members = self._all_sheeted_users()
        index = self._find_same_id(sheeted_members, member.id)
        if index is None:
            sheeted_members.append(self._member_to_row(member))
            index = len(sheeted_members) - 1
        sheeted_members[index][2] = addr
        self._logger.info(f'Updated User ({sheeted_members[index]})')
        self._update_timestamp(sheeted_members, index)
        updated = self._sort_by_id(sheeted_members)
        self._write(updated)

    def _find_same_id(self, rows: Sequence[Sequence], target_id: Union[int, str]) -> Union[None, int]:
        target_id = str(target_id)
        for i in range(len(rows)):
            if rows[i][0] == target_id:
                return i
        return None
            
    def _update_timestamp(self, rows, index):
        while len(rows[index]) < 4:
            rows[index].append('')
        rows[index][3] = self._current_time()

    def _all_sheeted_users(self) -> Sequence[Sequence]:
        try:
            result = self.sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                                        range=RANGE_NAME).execute()
        except HttpError as err:
            self._logger.error(err)
        
        values = result.get('values', [])
        sorted_values = self._sort_by_id(values)
        return sorted_values

    def _sort_by_id(self, rows):
        return sorted(rows, key=lambda row: row[0])

    def _write(self, values):
        values.append([''] * 4)
        values.append([''] * 4) # add some blank rows to override existing rows
        body = {'values': values}
        result = self.sheet.values().update(
            spreadsheetId=SAMPLE_SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption='RAW', body=body
        ).execute()
        self._logger.info(f'Write completed: {result}')

    def _current_time(self):
        return datetime.now(pytz.timezone('US/Eastern')).strftime("%Y:%m:%d %H:%M:%S")


# if __name__ == '__main__':
    # sheet = Sheet()
    # sheet.read_simple()
    # sheet.write()
    # sheet.current_time()


# TODO: log to google cloud stakedrive
