from __future__ import print_function


import os.path

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv('GOOGLE_API_KEY')

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

SAMPLE_SPREADSHEET_ID = '17pno9beqULzAC3QXDHC8yLwOD7HS9QM6qhh2UX_muZw'
SAMPLE_RANGE_NAME = 'Sheet1!A1:E'


def main():
    creds = service_account.Credentials.from_service_account_file('google_credentials.json', scopes=SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, 
                                    range=SAMPLE_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        print('content:')
        for row in values:
            print(row)
    except HttpError as err:
        print(err)

if __name__ == '__main__':
    main()



