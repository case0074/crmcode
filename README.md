# OpenPhone to Monday.com Sync

Synchronizes contact data between OpenPhone exports and Monday.com boards.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file with your credentials:
   ```env
   MONDAY_API=your_monday_api_key_here
   OPENPHONE_EMAIL=your_openphone_email
   OPENPHONE_PASSWORD=your_openphone_password
   ```

3. (Optional) For Gmail integration, add `credentials.json` from Google Cloud Console

## Usage

Run the main script:
```bash
python mondaywrite.py
```

## Configuration

Update `BOARD_ID` in `mondaywrite.py` to match your Monday.com board.
