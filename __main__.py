import sys
import aiohttp
import asyncio
import json
import os
from dotenv import load_dotenv
load_dotenv()

OPENPHONE_API = os.getenv('OPENPHONE_API')
MONDAY_API = os.getenv('MONDAY_API')

async def request_open_phone(api: str, params: dict = {}):
    if not params: params = {}
    while(True):
        try:
            async with session.get(
            f'https://api.openphone.com/v1/{api}',
            params= {
                'maxResults': 100
            } | params,
            headers={
                'Authorization': OPENPHONE_API
            }) as response:
                if not response.ok: continue
                data = await response.json()

                for object in data.get('data'):
                    yield object

                if not data.get('nextPageToken'): break
                params['pageToken'] = data.get('nextPageToken')
        except Exception as e:
            print(e, file=sys.stderr)
            await asyncio.sleep(1)

async def main():
    global session
    async with aiohttp.ClientSession() as session:
        # Only use the first phone number for now
        async for user_phone_number in request_open_phone('phone-numbers'): break

        participant_groups = []
        async for conversation in request_open_phone('conversations', {'phoneNumbers': user_phone_number['id']}):
            participant_groups.append(conversation['participants'])

        calls = []
        messages = []

        async def collect_calls(participants):
            if len(participants) != 1: return
            async for call in request_open_phone('calls', {
                'phoneNumberId': user_phone_number['id'],
                'participants': participants,
                }):
                calls.append(call)
        
        async def collect_messages(participants):
            async for message in request_open_phone('messages', {
                'phoneNumberId': user_phone_number['id'],
                'participants': participants,
                }):
                messages.append(message)

        async with asyncio.TaskGroup() as task_group:
            for participants in participant_groups:
                task_group.create_task(collect_calls(participants))
                task_group.create_task(collect_messages(participants))
        
        with open('outputs/participants.txt', '+w') as file:
            file.write(json.dumps(participant_groups, indent=2))
        with open('outputs/calls.txt', '+w') as file:
            file.write(json.dumps(calls, indent=2))
        with open('outputs/messages.txt', '+w') as file:
            file.write(json.dumps(messages, indent=2))
    
asyncio.run(main())