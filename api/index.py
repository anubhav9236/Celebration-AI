import sys
import os

# Add parent directory to sys.path so modules can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app

# Vercel Serverless Function entry point
# Vercel Python runtime discovers the WSGI 'app' variable
