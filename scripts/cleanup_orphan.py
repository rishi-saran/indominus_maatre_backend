import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

uid = 'de81cd9b-0b1d-4b6b-9662-eddf8fa8d209'
r1 = client.table('profiles').delete().eq('id', uid).execute()
r2 = client.table('users').delete().eq('id', uid).execute()
print('profiles deleted:', r1.data)
print('users deleted:', r2.data)
