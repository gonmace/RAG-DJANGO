from decouple import config
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.dev')

print("POSTGRES_DB:", config('POSTGRES_DB'))
print("POSTGRES_USER:", config('POSTGRES_USER'))
print("POSTGRES_PASSWORD:", config('POSTGRES_PASSWORD'))
print("POSTGRES_HOST:", config('POSTGRES_HOST'))
print("POSTGRES_PORT:", config('POSTGRES_PORT')) 