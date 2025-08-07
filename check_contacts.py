import csv
from datetime import datetime
import json
import os
import dotenv
import requests

# Load environment variables from .env file
dotenv.load_dotenv()

# Monday.com API credentials
API_KEY = os.getenv('MONDAY_API')
API_URL = "https://api.monday.com/v2"

def make_monday_request(query, variables):
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "query": query,
        "variables": variables
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def fetch_monday_contacts(board_id):
    query = '''
    query ($boardId: [ID!]) {
      boards(ids: $boardId) {
        id
        name
        items_page (limit: 500) {
            items {
                id
                name
                column_values {
                    id
                    text
                }
            }
        }
      }
    }
    '''
    variables = {"boardId": [str(board_id)]}
    result = make_monday_request(query, variables)
    contacts = []
    
    if 'data' in result and result['data']['boards']:
        board_data = result['data']['boards'][0]
        if board_data and 'items_page' in board_data and board_data['items_page'] and 'items' in board_data['items_page']:
            for item in board_data['items_page']['items']:
                contact = {
                    'id': item['id'],
                    'name': item['name'],
                }
                for col in item['column_values']:
                    if col['id'] == 'phone_mkt3jq7b':
                        contact['phone1'] = col['text']
                    elif col['id'] == 'phone_mkt347kq':
                        contact['phone2'] = col['text']
                contacts.append(contact)
    return contacts

def main():
    BOARD_ID = 9551098786
    
    print("Fetching contacts from Monday.com...")
    monday_contacts = fetch_monday_contacts(BOARD_ID)
    
    print(f"\nTotal contacts in Monday.com: {len(monday_contacts)}")
    
    # Look for Kelly Keith specifically
    print("\nSearching for Kelly Keith...")
    kelly_contacts = []
    for contact in monday_contacts:
        name_lower = contact['name'].lower()
        if 'kelly' in name_lower and 'keith' in name_lower:
            kelly_contacts.append(contact)
            print(f"FOUND: {contact['name']} (ID: {contact['id']})")
            print(f"  Phone1: {contact.get('phone1', 'N/A')}")
            print(f"  Phone2: {contact.get('phone2', 'N/A')}")
    
    if not kelly_contacts:
        print("No Kelly Keith found in Monday.com")
    
    # Show all contact names
    print("\nAll contact names in Monday.com:")
    for contact in monday_contacts:
        print(f"  - {contact['name']}")

if __name__ == "__main__":
    main() 