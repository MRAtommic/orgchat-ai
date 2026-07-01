import sqlite3
import json
from pathlib import Path

DB_PATH = Path("chat_history.db")

def _get_conn():
    import database
    return database._get_conn()

# --- Notifications Helper Functions ---

def add_notification(username, n_type, title, message, link=None):
    """
    types: 'mention', 'like', 'comment', 'system'
    """
    try:
        conn = _get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO notifications (username, type, title, message, link) VALUES (?, ?, ?, ?, ?)',
                (username, n_type, title, message, link)
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        print(f"Error adding notification: {e}")
        return False

def get_notifications(username, unread_only=False, limit=50):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        query = 'SELECT id, type, title, message, link, is_read, timestamp FROM notifications WHERE username = ?'
        if unread_only:
            query += ' AND is_read = 0'
        query += ' ORDER BY timestamp DESC LIMIT ?'
        
        cursor.execute(query, (username, limit))
        rows = cursor.fetchall()
    finally:
        conn.close()
    
    notifs = []
    for r in rows:
        notifs.append({
            "id": r[0],
            "type": r[1],
            "title": r[2],
            "message": r[3],
            "link": r[4],
            "is_read": r[5],
            "timestamp": r[6]
        })
    return notifs

def mark_notification_read(notif_id):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notif_id,))
        conn.commit()
    finally:
        conn.close()

def mark_all_notifications_read(username):
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET is_read = 1 WHERE username = ?', (username,))
        conn.commit()
    finally:
        conn.close()

def delete_notification(notif_id, username):
    """Delete a single notification, ensuring it belongs to the user."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notifications WHERE id = ? AND username = ?', (notif_id, username))
        conn.commit()
    finally:
        conn.close()

def delete_all_notifications(username):
    """Delete all notifications for a user."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notifications WHERE username = ?', (username,))
        conn.commit()
    finally:
        conn.close()

def admin_clear_all_notifications():
    """Admin only: Permanently delete every single notification for every user."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM notifications')
        count = cursor.rowcount
        conn.commit()
        return count
    finally:
        conn.close()

def notify_users(usernames, n_type, title, message, link=None):
    """
    Broadcast a notification to a list of users efficiently in one transaction.
    """
    try:
        conn = _get_conn()
        try:
            cursor = conn.cursor()
            for user in usernames:
                cursor.execute(
                    'INSERT INTO notifications (username, type, title, message, link) VALUES (?, ?, ?, ?, ?)',
                    (user, n_type, title, message, link)
                )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        print(f"Error in batch notification: {e}")
        return False

def notify_all_except(sender_username, n_type, title, message, link=None):
    """Broadcast a notification to everyone except the sender."""
    import database
    all_users = database.get_all_usernames()
    target_users = [u for u in all_users if u.lower() != sender_username.lower()]
    return notify_users(target_users, n_type, title, message, link)
