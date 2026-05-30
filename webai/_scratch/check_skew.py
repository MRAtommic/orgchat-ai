import sys
sys.path.append('.')
from google.oauth2 import id_token
from google.auth.transport import requests

print("Arguments of verify_oauth2_token:")
import inspect
sig = inspect.signature(id_token.verify_oauth2_token)
print(sig)
