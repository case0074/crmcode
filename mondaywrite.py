import csv
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import dotenv
import requests
from openphone import (
    check_for_export_email, 
    download_and_extract_export, 
    extract_openphone_export_link, 
    get_gmail_service, 
    format_contacts, 
    request_openphone_messages_export, 
    request_openphone_export
)

# Load environment variables
dotenv.load_dotenv()

# Configuration
class Config:
    #Configuration settings for the Monday.com integration.
    API_KEY = os.getenv('MONDAY_API')
    API_URL = "https://api.monday.com/v2"
    BOARD_ID = 9551098786
    
    # Column IDs for Monday.com board
    COLUMN_IDS = {
        'phone1': 'phone_mkt3jq7b',
        'phone2': 'phone_mkt347kq', 
        'date_created': 'date_mkt4rd5k',
        'last_activity': 'date_mkt4rfsf'
    }
    
    # File paths
    EXPORTS_DIR = Path("openphone_exports")
    FORMATTED_CONTACTS_FILE = 'formatted_contacts.csv'

class MondayAPI:
    #Handles all Monday.com API interactions.
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
    
    def make_request(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        #Make a GraphQL request to Monday.com API
        payload = {
            "query": query,
            "variables": variables
        }
        
        print("Sending GraphQL Request with Payload:")
        print(json.dumps(payload, indent=2))
        
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        return response.json()
    
    def get_board_columns(self, board_id: int) -> List[Dict[str, str]]:
        #Get column information for a board
        query = '''
        query ($boardId: [ID!]) {
          boards(ids: $boardId) {
            id
            name
            columns {
              id
              title
              type
            }
          }
        }
        '''
        variables = {"boardId": [str(board_id)]}
        result = self.make_request(query, variables)
        
        if 'data' in result and result['data']['boards']:
            return result['data']['boards'][0]['columns']
        return []
    
    def get_contacts(self, board_id: int) -> List[Dict[str, Any]]:
        #Fetch all contacts from a Monday.com board.
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
        result = self.make_request(query, variables)
        
        contacts = []
        if 'data' in result and result['data']['boards']:
            board_data = result['data']['boards'][0]
            if (board_data and 'items_page' in board_data and 
                board_data['items_page'] and 'items' in board_data['items_page']):
                
                for item in board_data['items_page']['items']:
                    contact = {
                        'id': item['id'],
                        'name': item['name'],
                    }
                    for col in item['column_values']:
                        if col['id'] == Config.COLUMN_IDS['phone1']:
                            contact['phone1'] = PhoneUtils.normalize_phone(col['text'])
                        elif col['id'] == Config.COLUMN_IDS['phone2']:
                            contact['phone2'] = PhoneUtils.normalize_phone(col['text'])
                    contacts.append(contact)
        
        return contacts
    
    def update_contact_activity(self, board_id: int, contact_id: str, 
                               date_created: datetime, last_activity: datetime) -> Dict[str, Any]:
        #Update both date created and last activity for a contact
        date_created_str = date_created.strftime('%Y-%m-%d')
        last_activity_str = last_activity.strftime('%Y-%m-%d')

        query = '''
        mutation ($itemId: ID!, $columnVals: JSON!) {
          change_multiple_column_values(item_id: $itemId, board_id: %d, column_values: $columnVals) {
            id
          }
        }
        ''' % board_id
        
        column_values = {
            Config.COLUMN_IDS['date_created']: {"date": date_created_str},
            Config.COLUMN_IDS['last_activity']: {"date": last_activity_str}
        }
        
        variables = {
            "itemId": str(contact_id),
            "columnVals": json.dumps(column_values)
        }
        
        result = self.make_request(query, variables)
        print(f"Updated contact {contact_id}: {result}")
        return result
    
    def update_contact_last_activity(self, board_id: int, contact_id: str, 
                                   last_activity: datetime) -> Dict[str, Any]:
        #Update only the last activity date for existing contacts.
        last_activity_str = last_activity.strftime('%Y-%m-%d')

        query = '''
        mutation ($itemId: ID!, $columnVals: JSON!) {
          change_multiple_column_values(item_id: $itemId, board_id: %d, column_values: $columnVals) {
            id
          }
        }
        ''' % board_id
        
        column_values = {
            Config.COLUMN_IDS['last_activity']: {"date": last_activity_str}
        }
        
        variables = {
            "itemId": str(contact_id),
            "columnVals": json.dumps(column_values)
        }
        
        result = self.make_request(query, variables)
        print(f"Updated last activity for contact {contact_id}: {result}")
        return result
    
    def add_new_contact(self, board_id: int, first_name: str, last_name: str, 
                       phone1: str, phone2: str, date_created: datetime, 
                       last_activity: datetime) -> Dict[str, Any]:
        #Add a new contact to Monday.com with all information.
        date_created_str = date_created.strftime('%Y-%m-%d')
        last_activity_str = last_activity.strftime('%Y-%m-%d')
        
        # Create contact name
        contact_name = f"{first_name} {last_name}".strip()
        if not contact_name:
            contact_name = f"Contact {phone1}"
        
        # Use phone1 as phone2 if phone2 doesn't exist
        if not phone2 and phone1:
            phone2 = phone1
        
        # Format phone numbers
        formatted_phone1 = PhoneUtils.format_phone_for_monday(phone1)
        formatted_phone2 = PhoneUtils.format_phone_for_monday(phone2)
        
        query = '''
        mutation ($boardId: ID!, $itemName: String!, $columnVals: JSON!) {
          create_item(board_id: $boardId, item_name: $itemName, column_values: $columnVals) {
            id
            name
          }
        }
        '''
        
        column_values = {
            Config.COLUMN_IDS['phone1']: {"phone": formatted_phone1, "countryShortName": "US"} if formatted_phone1 else None,
            Config.COLUMN_IDS['phone2']: {"phone": formatted_phone2, "countryShortName": "US"} if formatted_phone2 else None,
            Config.COLUMN_IDS['date_created']: {"date": date_created_str},
            Config.COLUMN_IDS['last_activity']: {"date": last_activity_str}
        }
        
        # Remove None values
        column_values = {k: v for k, v in column_values.items() if v is not None}
        
        variables = {
            "boardId": str(board_id),
            "itemName": contact_name,
            "columnVals": json.dumps(column_values)
        }
        
        result = self.make_request(query, variables)
        print(f"Added new contact '{contact_name}': {result}")
        
        # Debug information
        print(f"DEBUG - Full payload sent to Monday.com:")
        print(f"  Board ID: {board_id}")
        print(f"  Contact Name: {contact_name}")
        print(f"  Column Values: {json.dumps(column_values, indent=2)}")
        
        return result

class PhoneUtils:
    #Utility functions for phone number handling.
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        #Normalize phone number to last 10 digits.
        if not phone:
            return ""
        digits = ''.join(filter(str.isdigit, phone))
        return digits[-10:] if len(digits) >= 10 else digits
    
    @staticmethod
    def format_phone_for_monday(phone: str) -> Optional[str]:
        #Format phone number for Monday.com API (+1 format).
        if not phone:
            return None
        digits = ''.join(filter(str.isdigit, str(phone)))
        if len(digits) >= 10:
            us_number = digits[-10:]
            return f"+1{us_number}"
        return phone

class ActivityProcessor:
    #Handles processing of message activity data.
    
    @staticmethod
    def build_activity_map(messages_csv_path: str) -> Dict[str, Dict[str, datetime]]:
        #Build activity map from messages CSV file.
        activity = {}
        
        try:
            with open(messages_csv_path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    created_at_str = row.get('createdAt')
                    
                    if not created_at_str:
                        continue
                    
                    try:
                        date = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing date '{created_at_str}': {e}. Skipping row.")
                        continue
                    
                    for col in ['to', 'from']:
                        phone = PhoneUtils.normalize_phone(row[col])
                        if not phone:
                            continue
                        activity.setdefault(phone, []).append(date)
        except FileNotFoundError:
            print(f"Messages CSV file not found: {messages_csv_path}")
            return {}
        except Exception as e:
            print(f"Error processing messages CSV: {e}")
            return {}
        
        # Calculate min and max date for each phone number
        final_activity_map = {}
        for phone, dates in activity.items():
            if dates:
                final_activity_map[phone] = {
                    'date_created': min(dates),
                    'last_activity': max(dates)
                }
        
        return final_activity_map

class ContactManager:
    #Manages contact data operations.
    
    @staticmethod
    def load_formatted_contacts() -> Dict[str, Dict[str, str]]:
        #Load contacts from formatted_contacts.csv.
        contacts = {}
        
        try:
            with open(Config.FORMATTED_CONTACTS_FILE, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    phone1_raw = row.get('Phone1', '')
                    phone2_raw = row.get('Phone2', '')
                    
                    phone1_clean = ''.join(filter(str.isdigit, str(phone1_raw)))
                    phone2_clean = ''.join(filter(str.isdigit, str(phone2_raw)))
                    
                    phone1 = phone1_clean[-10:] if len(phone1_clean) >= 10 else phone1_clean
                    phone2 = phone2_clean[-10:] if len(phone2_clean) >= 10 else phone2_clean
                    
                    contact_info = {
                        'first_name': row.get('First', ''),
                        'last_name': row.get('Last', ''),
                        'phone1': phone1,
                        'phone2': phone2
                    }
                    
                    if phone1:
                        contacts[phone1] = contact_info
                    if phone2:
                        contacts[phone2] = contact_info
                        
        except FileNotFoundError:
            print(f"{Config.FORMATTED_CONTACTS_FILE} not found")
        except Exception as e:
            print(f"Error loading formatted contacts: {e}")
        
        return contacts
    
    @staticmethod
    def get_monday_phones_set(monday_contacts: List[Dict[str, Any]]) -> Set[str]:
        #Create a set of all phone numbers already in Monday.com.
        monday_phones = set()
        
        for contact in monday_contacts:
            for phone_field in ['phone1', 'phone2']:
                phone = contact.get(phone_field)
                if phone:
                    phone_digits = ''.join(filter(str.isdigit, phone))
                    if len(phone_digits) >= 10:
                        monday_phones.add(phone_digits[-10:])
        
        return monday_phones

class ExportManager:
    #Manages OpenPhone export operations
    
    @staticmethod
    def get_latest_export_messages_file() -> Optional[str]:
        #Find the most recent export folder and return the messages CSV path.
        if not Config.EXPORTS_DIR.exists():
            print("No openphone_exports directory found!")
            return None
        
        export_folders = [f for f in Config.EXPORTS_DIR.iterdir() if f.is_dir()]
        if not export_folders:
            print("No export folders found in openphone_exports!")
            return None
        
        latest_export = max(export_folders, key=lambda x: x.stat().st_mtime)
        print(f"Using latest export folder: {latest_export.name}")
        
        messages_file = next(latest_export.glob("*messages.csv"), None)
        if not messages_file:
            print(f"No messages CSV found in {latest_export}")
            return None
        
        return str(messages_file)

class MondaySync:
    #Main synchronization orchestrator.
    
    def __init__(self):
        if not Config.API_KEY:
            raise ValueError("MONDAY_API environment variable not set")
        
        self.api = MondayAPI(Config.API_KEY, Config.API_URL)
    
    def print_board_info(self):
        #Print board column information for debugging
        columns = self.api.get_board_columns(Config.BOARD_ID)
        print("Column IDs for your board:")
        for col in columns:
            print(f"Title: {col['title']} | ID: {col['id']} | Type: {col['type']}")
    
    def sync_contacts(self):
        #Main synchronization process
        # Get fresh data from OpenPhone
        print("Requesting fresh data from OpenPhone...")
        format_contacts()
        
        # Get latest export messages file
        messages_csv = ExportManager.get_latest_export_messages_file()
        if not messages_csv:
            return
        
        print(f"Using messages file: {messages_csv}")
        
        # Build activity map
        print("Building activity map...")
        activity_map = ActivityProcessor.build_activity_map(messages_csv)
        print(f"Activity map built with {len(activity_map)} unique phone numbers.")
        
        # Load formatted contacts
        print("Loading formatted contacts...")
        formatted_contacts = ContactManager.load_formatted_contacts()
        print(f"Loaded {len(formatted_contacts)} contacts from {Config.FORMATTED_CONTACTS_FILE}")
        
        # Fetch Monday.com contacts
        print(f"Fetching existing contacts from Monday.com board ID: {Config.BOARD_ID}...")
        monday_contacts = self.api.get_contacts(Config.BOARD_ID)
        print(f"Fetched {len(monday_contacts)} contacts from Monday.com.")
        
        # Get existing phone numbers
        monday_phones = ContactManager.get_monday_phones_set(monday_contacts)
        print(f"Total unique phone numbers in Monday.com: {len(monday_phones)}")
        
        # Debug: Show existing contacts
        print("\nExisting contacts in Monday.com:")
        for contact in monday_contacts:
            print(f"  - {contact['name']}")
        
        # Process each Monday.com contact
        print(f"\nProcessing {len(monday_contacts)} contacts from Monday.com...")
        
        for contact in monday_contacts:
            self._process_contact(contact, formatted_contacts, activity_map)
        
        print("\nProcessing complete!")
    
    def _process_contact(self, contact: Dict[str, Any], formatted_contacts: Dict[str, Dict[str, str]], 
                        activity_map: Dict[str, Dict[str, datetime]]):
        #Process a single contact from Monday.com
        contact_name = contact['name']
        contact_id = contact['id']
        
        # Normalize phone numbers
        contact_phone1 = PhoneUtils.normalize_phone(contact.get('phone1', ''))
        contact_phone2 = PhoneUtils.normalize_phone(contact.get('phone2', ''))
        
        print(f"\nProcessing Monday contact: '{contact_name}' (ID: {contact_id})")
        print(f"  Phone1: {contact.get('phone1', 'N/A')} -> normalized: {contact_phone1}")
        print(f"  Phone2: {contact.get('phone2', 'N/A')} -> normalized: {contact_phone2}")
        
        # Check if contact exists in formatted contacts
        found_in_formatted = contact_phone1 and contact_phone1 in formatted_contacts
        
        if found_in_formatted:
            print(f"  Found in formatted contacts via phone1: {contact_phone1}")
            self._update_existing_contact(contact_id, contact_phone1, activity_map)
        else:
            print(f"  NOT found in formatted contacts - creating new contact")
            self._create_new_contact(contact_name, contact, activity_map)
    
    def _update_existing_contact(self, contact_id: str, phone1: str, 
                               activity_map: Dict[str, Dict[str, datetime]]):
        #Update activity for existing contact.
        if phone1 in activity_map:
            activity_data = activity_map[phone1]
            last_activity = activity_data['last_activity']
            print(f"  Found activity for phone1 {phone1}: {last_activity}")
            print(f"  Updating last activity...")
            self.api.update_contact_last_activity(Config.BOARD_ID, contact_id, last_activity)
        else:
            print(f"  No activity found for this contact")
    
    def _create_new_contact(self, contact_name: str, contact: Dict[str, Any], 
                          activity_map: Dict[str, Dict[str, datetime]]):
        #Create a new contact.
        contact_phone1 = PhoneUtils.normalize_phone(contact.get('phone1', ''))
        
        if contact_phone1 and contact_phone1 in activity_map:
            activity_data = activity_map[contact_phone1]
            date_created = activity_data['date_created']
            last_activity = activity_data['last_activity']
            print(f"  Using activity data: created={date_created}, last={last_activity}")
        else:
            current_date = datetime.now()
            date_created = current_date
            last_activity = current_date
            print(f"  No activity data found, using current date")
        
        self.api.add_new_contact(
            Config.BOARD_ID,
            contact_name,
            "",
            contact.get('phone1', ''),
            contact.get('phone2', ''),
            date_created,
            last_activity
        )

def main():
    #Main entry point
    try:
        sync = MondaySync()
        sync.print_board_info()
        sync.sync_contacts()
    except ValueError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()