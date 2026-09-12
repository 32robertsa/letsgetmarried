import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import yaml
import requests

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = "104DylQBkbN8lhMBEPxg9lDvKhEd2lGt7nAMvZUxjg8g"


def pull(sheetrange):
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("web/token.json"):
    creds = Credentials.from_authorized_user_file("web/token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "web/credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("web/token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = (
        sheet.values()
        .get(spreadsheetId=SPREADSHEET_ID, range=sheetrange)
        .execute()
    )
    values = result.get("values", [])

    return values

  except HttpError as err:
    print(err)
    return None
  
def main():
    guestvalues = pull('Guests')
    registryvalues = pull('Registry')
  
    # Open the file and parse the YAML content
    with open('resources/pullfromsheets.yaml', 'r', encoding='utf-8') as file:
      data = yaml.safe_load(file)

      names = [row['name'] for row in data['invitations']]
      
      for val in guestvalues[1:]:

        extras = val[3].split(', ')

        people = [val[1]]
        if val[2] != '':
          people.append(val[2])
        if extras != ['']:
          people = people + extras

        children = None
        if val[4] in ['Yes', 'yes', 'True', 'true']:
          children = 'invited'
        elif val[4] in ['', 'n/a', 'N/A']:
          children = 'n/a'
        else:
          children = 'not-invited'
          
        row_dct = {
          'name': val[0],
          'people': people,
          'children': children,
        }
        
        if val[0] in names:
          thisrow = [row for row in data['invitations'] if row['name'] == val[0]][0]
          if thisrow == row_dct:
            continue
          data['invitations'].remove(thisrow)
          
        data['invitations'].append(row_dct)

      items = [row['id'] for row in data['registry']]

      for val in registryvalues[1:]:
                
        row_dct = {
          'name': val[0],
          'id': val[1],
          'link': val[2],
          'image': val[3],
          'price': val[4].strip('$'),
        }

        if val[1] in items:
          thisrow = [row for row in data['registry'] if row['id'] == val[1]][0]
          if thisrow == row_dct:
            continue
          data['registry'].remove(thisrow)

        data['registry'].append(row_dct)
        
    with open('resources/pullfromsheets.yaml', 'w', encoding='utf-8') as file:
      yaml.dump(data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
if __name__ == "__main__":
  main()
