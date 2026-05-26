"""
Google OAuth2 Service — Per-User Authentication for Drive & Sheets
==================================================================
Handles the OAuth2 Authorization Code Flow for individual users,
allowing each user to connect their own Google Drive & Sheets.
"""

import os
import json
import logging
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

import database

logger = logging.getLogger(__name__)

# Scopes requested from the user
OAUTH2_SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.file',       # Only files created by this app
    'https://www.googleapis.com/auth/spreadsheets'
]


class GoogleOAuth2Service:
    """Manages per-user Google OAuth2 authorization flows."""

    def __init__(self):
        self.client_id = os.environ.get("GOOGLE_OAUTH2_CLIENT_ID", "")
        self.client_secret = os.environ.get("GOOGLE_OAUTH2_CLIENT_SECRET", "")
        self.redirect_uri = os.environ.get(
            "OAUTH2_REDIRECT_URI",
            "http://localhost:5005/api/auth/google/callback"
        )

        # Try loading from credentials_web.json as fallback
        if not self.client_id or not self.client_secret:
            self._load_from_json()

        if self.client_id and self.client_secret:
            logger.info("✅ Google OAuth2 Service initialized successfully.")
        else:
            logger.warning("⚠️ Google OAuth2 credentials not configured. Per-user login disabled.")

    def _load_from_json(self):
        """Load credentials from credentials_web.json file."""
        json_path = os.path.join(os.path.dirname(__file__), 'credentials_web.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                web_config = data.get("web", {})
                self.client_id = web_config.get("client_id", "")
                self.client_secret = web_config.get("client_secret", "")
                redirect_uris = web_config.get("redirect_uris", [])
                if redirect_uris:
                    self.redirect_uri = redirect_uris[0]
                logger.info(f"📄 Loaded OAuth2 config from credentials_web.json")
            except Exception as e:
                logger.error(f"❌ Failed to load credentials_web.json: {e}")

    @property
    def is_configured(self):
        """Returns True if OAuth2 credentials are properly configured."""
        return bool(self.client_id and self.client_secret)

    def _build_client_config(self):
        """Build the client config dict for google_auth_oauthlib Flow."""
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [self.redirect_uri]
            }
        }

    def get_authorization_url(self, redirect_uri=None, state=None):
        """
        Generate a Google OAuth2 authorization URL for the user to visit.
        Returns: (authorization_url, state, code_verifier)
        """
        if not self.is_configured:
            raise ValueError("Google OAuth2 is not configured. Set GOOGLE_OAUTH2_CLIENT_ID and SECRET.")

        flow = Flow.from_client_config(
            self._build_client_config(),
            scopes=OAUTH2_SCOPES,
            redirect_uri=redirect_uri or self.redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',          # Get a refresh_token
            include_granted_scopes='true',  # Incremental authorization
            prompt='select_account consent', # Always force account selection AND consent to get fresh refresh_token
            state=state
        )

        return authorization_url, state, getattr(flow, 'code_verifier', None)

    def exchange_code_for_token(self, authorization_code, redirect_uri=None, code_verifier=None):
        """
        Exchange an authorization code for access & refresh tokens.
        Returns: {
            'access_token': str,
            'refresh_token': str,
            'token_expiry': str (ISO format),
            'email': str,
            'name': str,
            'picture': str
        }
        """
        if not self.is_configured:
            raise ValueError("Google OAuth2 is not configured.")

        flow = Flow.from_client_config(
            self._build_client_config(),
            scopes=OAUTH2_SCOPES,
            redirect_uri=redirect_uri or self.redirect_uri
        )

        flow.fetch_token(code=authorization_code, code_verifier=code_verifier)
        credentials = flow.credentials

        # Get user info
        user_info = self._get_user_info(credentials)

        # Calculate token expiry
        token_expiry = None
        if credentials.expiry:
            token_expiry = credentials.expiry.isoformat()

        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': token_expiry,
            'email': user_info.get('email', ''),
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', '')
        }

    def _get_user_info(self, credentials):
        """Fetch user profile info from Google People API."""
        try:
            service = build('oauth2', 'v2', credentials=credentials, cache_discovery=False)
            user_info = service.userinfo().get().execute()
            return user_info
        except Exception as e:
            logger.error(f"❌ Failed to get user info: {e}")
            return {}

    def build_user_credentials(self, username):
        """
        Build Google Credentials object from stored tokens for a specific user.
        Auto-refreshes if expired.
        Returns: google.oauth2.credentials.Credentials or None
        """
        token_data = database.get_google_token(username)
        if not token_data:
            return None

        creds = Credentials(
            token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=OAUTH2_SCOPES
        )

        # Check if token is expired and refresh
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save refreshed token
                new_expiry = creds.expiry.isoformat() if creds.expiry else None
                database.save_google_token(
                    username=username,
                    google_email=token_data.get('google_email', ''),
                    access_token=creds.token,
                    refresh_token=creds.refresh_token,
                    token_expiry=new_expiry
                )
                logger.info(f"🔄 Refreshed Google token for user: {username}")
            except Exception as e:
                logger.error(f"❌ Failed to refresh token for {username}: {e}")
                return None

        if not creds.valid:
            # Try refreshing one more time
            try:
                creds.refresh(Request())
                new_expiry = creds.expiry.isoformat() if creds.expiry else None
                database.save_google_token(
                    username=username,
                    google_email=token_data.get('google_email', ''),
                    access_token=creds.token,
                    refresh_token=creds.refresh_token,
                    token_expiry=new_expiry
                )
            except Exception as e:
                logger.error(f"❌ Token invalid and refresh failed for {username}: {e}")
                return None

        return creds

    def build_user_drive_service(self, username):
        """Build a Google Drive API service for a specific user."""
        creds = self.build_user_credentials(username)
        if not creds:
            return None
        try:
            return build('drive', 'v3', credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.error(f"❌ Failed to build Drive service for {username}: {e}")
            return None

    def build_user_sheets_service(self, username):
        """Build a Google Sheets API service for a specific user."""
        creds = self.build_user_credentials(username)
        if not creds:
            return None
        try:
            return build('sheets', 'v4', credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.error(f"❌ Failed to build Sheets service for {username}: {e}")
            return None

    def setup_user_workspace(self, username, google_email):
        """
        Create a personal Spreadsheet and Drive folder for a newly connected user.
        Called once after successful OAuth2 authorization.
        """
        drive_service = self.build_user_drive_service(username)
        sheets_service = self.build_user_sheets_service(username)

        if not drive_service or not sheets_service:
            logger.error(f"❌ Cannot setup workspace for {username}: services unavailable")
            return False

        try:
            # 1. Create a root folder in user's Drive
            folder_meta = {
                'name': 'OrgChat AI — เอกสารบัญชี',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(
                body=folder_meta, fields='id'
            ).execute()
            folder_id = folder.get('id')
            database.set_user_drive_folder_id(username, folder_id)
            logger.info(f"📁 Created Drive folder for {username}: {folder_id}")

            # 2. Create a Spreadsheet in user's Drive
            spreadsheet_body = {
                'properties': {
                    'title': f'OrgChat AI — บัญชีของ {google_email}'
                }
            }
            spreadsheet = sheets_service.spreadsheets().create(
                body=spreadsheet_body, fields='spreadsheetId'
            ).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')

            # Move spreadsheet into the folder
            file_info = drive_service.files().get(
                fileId=spreadsheet_id, fields='parents'
            ).execute()
            previous_parents = ",".join(file_info.get('parents', []))
            drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            database.set_user_spreadsheet_id(username, spreadsheet_id)
            logger.info(f"📊 Created Spreadsheet for {username}: {spreadsheet_id}")

            # 3. Initialize essential sheets with headers (reuse from google_drive_service schema)
            self._init_essential_sheets(sheets_service, spreadsheet_id)

            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup workspace for {username}: {e}")
            return False

    def _init_essential_sheets(self, sheets_service, spreadsheet_id):
        """Initialize essential sheet tabs with standard headers in a new user spreadsheet."""
        essential_sheets = {
            "ใบเสร็จ/ใบกำกับภาษี": [
                "วันที่บันทึก", "เวลาที่บันทึก", "AI Model", "หมวดหมู่",
                "วันที่เอกสาร", "เลขที่เอกสาร", "ร้านค้า/คู่ค้า",
                "เลขประจำตัวผู้เสียภาษี", "สาขา", "ยอดก่อน VAT",
                "VAT", "ยอดรวม VAT", "ยอดสุทธิ", "หัก ณ ที่จ่าย",
                "คำอธิบายรายการ", "หมายเหตุ", "ตามใบกำกับ",
                "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "ผู้ส่ง (LINE User)"
            ],
            "สลิปโอนเงิน": [
                "วันที่บันทึก", "เวลาที่บันทึก", "AI Model", "หมวดหมู่",
                "วันที่โอน", "ผู้โอน", "ยอดเงินสุทธิ",
                "ธนาคารผู้โอน", "หัก ณ ที่จ่าย", "ผู้รับเงิน",
                "ธนาคารผู้รับ", "เลขที่อ้างอิง", "หมายเหตุ",
                "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "ผู้ส่ง (LINE User)"
            ],
            "สรุปกระทบยอด": [
                "วันที่ประมวลผล", "สถานะ", "วันที่เอกสาร",
                "ยอดเงิน", "คู่ค้า/ร้านค้า", "ลิงก์สลิป",
                "ลิงก์ใบกำกับ", "หมายเหตุ", "ผู้ส่ง (LINE User)"
            ],
            "ใบเสนอราคา (สร้างจากระบบ)": [
                "วันที่ทำรายการ", "เลขที่ใบเสนอราคา",
                "ชื่อลูกค้า/บริษัท", "ข้อมูลติดต่อ",
                "ยอดรวมก่อนลด", "ส่วนลด", "ยอดสุทธิ (VAT 7%)",
                "ผู้ออกเอกสาร", "ลิงก์ไฟล์ PDF", "ผู้ส่ง (LINE User)"
            ]
        }

        try:
            # Create sheets (skip Sheet1 which exists by default)
            requests = []
            for title in essential_sheets:
                requests.append({
                    'addSheet': {'properties': {'title': title}}
                })

            if requests:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests}
                ).execute()

            # Add headers to each sheet
            batch_data = []
            for title, headers in essential_sheets.items():
                batch_data.append({
                    'range': f"'{title}'!A1",
                    'values': [headers]
                })

            if batch_data:
                sheets_service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        'valueInputOption': 'RAW',
                        'data': batch_data
                    }
                ).execute()

            # Delete default Sheet1
            try:
                sheet_meta = sheets_service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id
                ).execute()
                for s in sheet_meta.get('sheets', []):
                    if s['properties']['title'] in ['Sheet1', 'ชีต1']:
                        sheets_service.spreadsheets().batchUpdate(
                            spreadsheetId=spreadsheet_id,
                            body={'requests': [{'deleteSheet': {'sheetId': s['properties']['sheetId']}}]}
                        ).execute()
                        break
            except Exception:
                pass

            # Apply Royal Blue header styling to all sheets
            self._style_all_headers(sheets_service, spreadsheet_id)

            logger.info(f"📋 Initialized essential sheets for spreadsheet {spreadsheet_id}")

        except Exception as e:
            logger.error(f"❌ Failed to init essential sheets: {e}")

    def _style_all_headers(self, sheets_service, spreadsheet_id):
        """Apply royal blue + white bold header styling to all sheets."""
        try:
            sheet_meta = sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()

            requests = []
            for s in sheet_meta.get('sheets', []):
                sheet_id = s['properties']['sheetId']
                requests.append({
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {"frozenRowCount": 1}
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                })
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": 26
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.1137, "green": 0.3098, "blue": 0.8471
                                },
                                "textFormat": {
                                    "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                                    "bold": True,
                                    "fontSize": 10,
                                    "fontFamily": "Inter"
                                },
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                })

            if requests:
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests}
                ).execute()

        except Exception as e:
            logger.error(f"❌ Failed to style headers: {e}")

    def build_org_credentials(self, org_id: int):
        """Build Google Credentials from an org's shared token. Auto-refreshes if expired."""
        token_data = database.get_org_google_token(org_id)
        if not token_data:
            return None

        creds = Credentials(
            token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=OAUTH2_SCOPES
        )

        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                new_expiry = creds.expiry.isoformat() if creds.expiry else None
                database.save_org_google_token(
                    org_id=org_id,
                    google_email=token_data.get('google_email', ''),
                    access_token=creds.token,
                    refresh_token=creds.refresh_token,
                    token_expiry=new_expiry,
                    connected_by=token_data.get('connected_by')
                )
            except Exception as e:
                logger.error(f"❌ Failed to refresh org token for org {org_id}: {e}")
                return None

        return creds if creds.valid else None

    def build_credentials(self, username: str = None, org_id: int = None):
        """
        Resolve credentials: org token first (shared), then personal user token.
        Returns (credentials, source) where source is 'org', 'personal', or 'org_admin_personal'.
        """
        import database
        token_data, source = database.resolve_google_token(username, org_id)
        if not token_data:
            return None, 'none'
            
        from google.oauth2.credentials import Credentials as GoogleCredentials
        from google.auth.transport.requests import Request as GoogleRequest
        
        creds = GoogleCredentials(
            token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=OAUTH2_SCOPES
        )
        
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(GoogleRequest())
                new_expiry = creds.expiry.isoformat() if creds.expiry else None
                if source == 'org':
                    database.save_org_google_token(
                        org_id=org_id,
                        google_email=token_data.get('google_email', ''),
                        access_token=creds.token,
                        refresh_token=creds.refresh_token,
                        token_expiry=new_expiry,
                        connected_by=token_data.get('connected_by')
                    )
                else:
                    t_username = token_data.get('username') or username
                    if t_username:
                        database.save_google_token(
                            username=t_username,
                            google_email=token_data.get('google_email', ''),
                            access_token=creds.token,
                            refresh_token=creds.refresh_token,
                            token_expiry=new_expiry
                        )
            except Exception as e:
                logger.error(f"❌ Failed to refresh dynamic Google token ({source}): {e}")
                return None, 'none'
                
        return creds, source

    def setup_org_workspace(self, org_id: int, google_email: str, connected_by: str = None) -> bool:
        """Create a shared Spreadsheet and Drive folder for the org. Called once on connect."""
        creds = self.build_org_credentials(org_id)
        if not creds:
            logger.error(f"❌ Cannot setup org workspace for org {org_id}: no credentials")
            return False

        try:
            drive_service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            sheets_service = build('sheets', 'v4', credentials=creds, cache_discovery=False)

            # Create root folder in org's Google Drive
            org_name = f"org_{org_id}"
            try:
                from database import _get_conn as _db_conn
                conn = _db_conn()
                row = conn.execute("SELECT name FROM organizations WHERE id = ?", (org_id,)).fetchone()
                conn.close()
                if row:
                    org_name = row[0]
            except Exception:
                pass

            folder_meta = {
                'name': f'OrgChat AI — {org_name}',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_service.files().create(body=folder_meta, fields='id').execute()
            folder_id = folder.get('id')
            database.set_org_drive_folder_id(org_id, folder_id)
            logger.info(f"📁 Created org Drive folder for org {org_id}: {folder_id}")

            # Create Spreadsheet
            spreadsheet = sheets_service.spreadsheets().create(
                body={'properties': {'title': f'OrgChat AI — บัญชี {org_name}'}},
                fields='spreadsheetId'
            ).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')

            # Move spreadsheet into the folder
            file_info = drive_service.files().get(fileId=spreadsheet_id, fields='parents').execute()
            previous_parents = ",".join(file_info.get('parents', []))
            drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()

            database.set_org_spreadsheet_id(org_id, spreadsheet_id)
            logger.info(f"📊 Created org Spreadsheet for org {org_id}: {spreadsheet_id}")

            # Initialize sheet tabs
            self._init_essential_sheets(sheets_service, spreadsheet_id)
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup org workspace for org {org_id}: {e}")
            return False

    def is_org_connected(self, org_id: int) -> bool:
        """Check if an org has a shared Google account connected."""
        token_data = database.get_org_google_token(org_id)
        return token_data is not None and bool(token_data.get('refresh_token'))

    def get_org_connection_info(self, org_id: int) -> dict:
        """Get org-level connection info for display."""
        token_data = database.get_org_google_token(org_id)
        if not token_data:
            return {'connected': False, 'email': None, 'spreadsheet_id': None, 'drive_folder_id': None}
        return {
            'connected': True,
            'email': token_data.get('google_email'),
            'spreadsheet_id': token_data.get('spreadsheet_id'),
            'drive_folder_id': token_data.get('drive_folder_id'),
            'connected_by': token_data.get('connected_by'),
            'updated_at': token_data.get('updated_at'),
        }

    def disconnect_org(self, org_id: int) -> bool:
        """Disconnect an org's shared Google account."""
        token_data = database.get_org_google_token(org_id)
        if token_data and token_data.get('access_token'):
            try:
                import requests as http_requests
                http_requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': token_data['access_token']},
                    headers={'content-type': 'application/x-www-form-urlencoded'},
                    timeout=5
                )
            except Exception:
                pass
        database.delete_org_google_token(org_id)
        logger.info(f"🔌 Disconnected org Google account for org {org_id}")
        return True

    def is_user_connected(self, username):
        """Check if a user has connected their personal Google account."""
        token_data = database.get_google_token(username)
        return token_data is not None and token_data.get('refresh_token') is not None

    def get_user_connection_info(self, username):
        """Get personal connection status info for display."""
        token_data = database.get_google_token(username)
        if not token_data:
            return {
                'connected': False,
                'email': None,
                'spreadsheet_id': None,
                'drive_folder_id': None
            }
        return {
            'connected': True,
            'email': token_data.get('google_email'),
            'spreadsheet_id': token_data.get('spreadsheet_id'),
            'drive_folder_id': token_data.get('drive_folder_id'),
            'updated_at': token_data.get('updated_at')
        }

    def disconnect_user(self, username):
        """Disconnect a user's Google account (revoke and delete tokens)."""
        token_data = database.get_google_token(username)
        if token_data and token_data.get('access_token'):
            # Try to revoke the token at Google (best-effort)
            try:
                import requests as http_requests
                http_requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': token_data['access_token']},
                    headers={'content-type': 'application/x-www-form-urlencoded'},
                    timeout=5
                )
            except Exception:
                pass  # Best effort — token will expire anyway

        database.delete_google_token(username)
        logger.info(f"🔌 Disconnected Google account for user: {username}")
        return True


# Singleton instance
oauth2_service = GoogleOAuth2Service()
