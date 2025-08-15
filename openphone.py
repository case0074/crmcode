import os
import re
import time
import base64
import requests
import zipfile
import datetime
import pandas as pd
from datetime import timezone
from urllib.parse import urlparse, unquote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
import dotenv
dotenv.load_dotenv()
# Configuration
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
sender_email = "op@openphone.com"
OPENPHONE_EMAIL =os.getenv("OPENPHONE_EMAIL")  # Move to environment variables
OPENPHONE_PASSWORD = os.getenv("OPENPHONE_PASSWORD")         # Move to environment variables

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    
    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as error:
        print(f"Error creating Gmail service: {error}")
        return None

def extract_openphone_export_link(service, msg_id):
    try:
        msg = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        parts = msg['payload'].get('parts', [])
        body = ''
        for part in parts:
            if part['mimeType'] in ['text/plain', 'text/html']:
                data = part['body']['data']
                body += base64.urlsafe_b64decode(data).decode('utf-8')
        
        link_pattern = r'https://opstatics\.s3\.us-west-2\.amazonaws\.com/exports/[^\s]+\.zip\?[^\s]+'
        match = re.search(link_pattern, body)
        return match.group(0) if match else None
        
    except Exception as e:
        print(f"Error extracting link: {e}")
        return None




def download_and_extract_export(url, output_dir='openphone_exports'):
    try:
        os.makedirs(output_dir, exist_ok=True)
        parsed = urlparse(url)
        filename = unquote(os.path.basename(parsed.path)) or f"export_{int(time.time())}.zip"
        filepath = os.path.join(output_dir, filename)
        
        print(f"Downloading export file...")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        
        extract_path = os.path.join(output_dir, filename.replace('.zip', ''))
        os.makedirs(extract_path, exist_ok=True)
        
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        print(f"Export extracted to: {extract_path}")
        return extract_path
        
    except Exception as e:
        print(f"Download/extract error: {e}")
        return None

def request_openphone_export():
    driver = webdriver.Chrome()
    try:
        # 1. LOGIN TO OPENPHONE
        driver.get("https://my.openphone.com/login")
        wait = WebDriverWait(driver, 50)
        
        button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Email & password']]")))
        button.click()
        
        driver.find_element(By.ID, "username").send_keys(OPENPHONE_EMAIL)
        wait.until(EC.element_to_be_clickable((By.NAME, "action"))).click()
        
        driver.find_element(By.ID, "password").send_keys(OPENPHONE_PASSWORD)
        wait.until(EC.element_to_be_clickable((By.NAME, "action"))).click()
        
        # 2. REQUEST DATA EXPORT
        settings_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/settings"]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", settings_link)
        settings_link.click()
        
        general_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/settings/company"]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", general_link)
        general_link.click()
        
        contacts_label = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[./input[@id='contacts']]")))
        contacts_label.click()
        
        export_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-sentry-element='Button'][data-sentry-source-file='DataExport.tsx']")
        ))
        
        # Scroll to the button and wait a bit
        driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
        time.sleep(2)
        
        # Try to click using JavaScript to avoid interception
        try:
            driver.execute_script("arguments[0].click();", export_button)
        except:
            # Fallback to regular click
            export_button.click()
        
        time.sleep(10)
        print("Export requested successfully")
        
    finally:
        driver.quit()

def request_openphone_messages_export():
    driver = webdriver.Chrome()
    try:
        # 1. LOGIN TO OPENPHONE
        driver.get("https://my.openphone.com/login")
        wait = WebDriverWait(driver, 10)
        
        button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='Email & password']]")))
        button.click()
        
        driver.find_element(By.ID, "username").send_keys(OPENPHONE_EMAIL)
        wait.until(EC.element_to_be_clickable((By.NAME, "action"))).click()
        
        driver.find_element(By.ID, "password").send_keys(OPENPHONE_PASSWORD)
        wait.until(EC.element_to_be_clickable((By.NAME, "action"))).click()
        
        # 2. REQUEST DATA EXPORT
        wait = WebDriverWait(driver, 30)
        settings_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/settings"]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", settings_link)
        settings_link.click()
        
        general_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="/settings/company"]')))
        driver.execute_script("arguments[0].scrollIntoView(true);", general_link)
        general_link.click()
        
        contacts_label = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[./input[@id='messages']]")))
        contacts_label.click()
        
        export_button = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[data-sentry-element='Button'][data-sentry-source-file='DataExport.tsx']")
        ))
        
        # Scroll to the button and wait a bit
        driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
        time.sleep(2)
        
        # Try to click using JavaScript to avoid interception
        try:
            driver.execute_script("arguments[0].click();", export_button)
        except:
            # Fallback to regular click
            export_button.click()
        
        time.sleep(10)
        print("Export requested successfully")
        
    finally:
        driver.quit()


def check_for_message_export_email():
    service = get_gmail_service()
    if not service:
        return False
    
    print("Checking for export email...")
    now = datetime.datetime.now(timezone.utc)
    start_time = now - datetime.timedelta(minutes=50)
    
    attempts = 0
    while attempts < 6:  # Check for 3 minutes (30s intervals)
        results = service.users().messages().list(
            userId='me',
            q=f"from:{sender_email} after:{int(start_time.timestamp())}",
            maxResults=1
        ).execute()
        
        if messages := results.get('messages', []):
            msg_id = messages[0]['id']
            if export_url := extract_openphone_export_link(service, msg_id):
                download_and_extract_export(export_url)
                return True
        
        attempts += 1
        time.sleep(30)
    
    return False



def check_for_export_email():
    service = get_gmail_service()
    if not service:
        return False
    
    print("Checking for export email...")
    now = datetime.datetime.now(timezone.utc)
    start_time = now - datetime.timedelta(minutes=50)
    
    attempts = 0
    while attempts < 6:  # Check for 3 minutes (30s intervals)
        results = service.users().messages().list(
            userId='me',
            q=f"from:{sender_email} after:{int(start_time.timestamp())}",
            maxResults=1
        ).execute()
        
        if messages := results.get('messages', []):
            msg_id = messages[0]['id']
            if export_url := extract_openphone_export_link(service, msg_id):
                download_and_extract_export(export_url)
                return True
        
        attempts += 1
        time.sleep(30)
    
    return False


def format_contacts():
    try:
        
        #id,userId,firstName,lastName,company,sharedWith,phone_number_1,phone_number_2,email_1,custom_1_Address,custom_2_Address,custom_3_Number
        # Find the most recent export directory
        cur_directory = Path(__file__).parent
        exports_dir = cur_directory / "openphone_exports"
        
        # Get the most recent export folder
        export_folders = sorted(exports_dir.glob("*/"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not export_folders:
            print("No export folders found in openphone_exports")
            return False
        
        latest_export = export_folders[0]
        contacts_file = next(latest_export.glob("*contacts.csv"), None)
        
        if not contacts_file:
            print(f"No contacts CSV found in {latest_export}")
            return False
        
        # Read and format the contacts
        df = pd.read_csv(contacts_file, usecols=['firstName', 'lastName','phone_number_1','phone_number_2'])
        df.columns = ['First', 'Last', 'Phone1', 'Phone2']  # Rename columns
        
        # Clean phone numbers (remove non-digit characters)
        df['Phone1'] = df['Phone1'].str.replace(r'\D+', '', regex=True)

        # Save formatted contacts
        output_path = cur_directory / "formatted_contacts.csv"
        df.to_csv(output_path, index=False)
        print(f"Formatted contacts saved to {output_path}")
        
        return True
        
    except Exception as e:
        print(f"Error formatting contacts: {e}")
        return False


def main():
    # 1. Request export from OpenPhone    format_contacts()
    request_openphone_export()
    check_for_export_email()
    check_for_message_export_email()
if __name__ == "__main__":
    main()