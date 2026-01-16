import json
import os
import re
import subprocess
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
from spotdl.utils import spotify
import urllib.request

from src.coordinator import Coordinator
from src.utils import get_spotify_creds, setup_logging

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_file> <output_dir>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    load_dotenv()
    
    logger = setup_logging(output_dir)
    
    if not input_file.is_file():
        logger.info(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    # Init coordinator with creds
    client_id, client_secret = get_spotify_creds(logger)
    coord = Coordinator(output_dir, logger, client_id, client_secret)

    # Process all providers (handles soundcloud/youtube/spotify internally)
    exit_code = coord.process_all(input_file)
    sys.exit(exit_code)
    
if __name__ == "__main__":
    main()


