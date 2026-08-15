import os
import sys
import secrets

# ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# set temporary strong secret and force DEBUG False
os.environ.setdefault('DJANGO_SECRET_KEY', secrets.token_urlsafe(64))
os.environ['DJANGO_DEBUG'] = 'False'
# load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT + '/.env')
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BetterSelf.settings')

import django
from django.core.management import call_command

django.setup()

print('Running deploy checks with temporary strong secret...')
call_command('check', '--deploy')
print('Done')
