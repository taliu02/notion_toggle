import os
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_PAGE_ID = os.environ["NOTION_PAGE_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
IMGUR_CLIENT_ID = os.environ["IMGUR_CLIENT_ID"]
PDF_PATH = os.environ["PDF_PATH"]
AWS_ACCESS_KEY = os.environ["AWS_ACCESS_KEY"]
AWS_SECRET_KEY = os.environ["AWS_SECRET_KEY"]
