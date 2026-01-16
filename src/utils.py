import logging
import os
from pathlib import Path
import re
import sys
from typing import List, Tuple

from src.models import Song


def setup_logging(output_dir: Path) -> logging.Logger:
    """Setup logging to console + file"""
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / "spotdl.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file)
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Started - Logs: {log_file}")
    return logger

def clean_url(line: str) -> str:
    """Spotify + SoundCloud + YouTube (markdown + plain)."""
    if line.startswith("#"):
        return ""
    line = line.strip()
    if not line:
        return ""
    
    # YouTube markdown [text](youtube_url)
    m_yt_md = re.search(r"\((https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s\)\]]+)\)", line)
    if m_yt_md:
        return m_yt_md.group(1)
    
    # YouTube plain URLs
    m_yt = re.search(r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s\)\]]+", line)
    if m_yt:
        return m_yt.group(0)
    
    # SoundCloud
    m_sc = re.search(r"https?://(?:www\.)?soundcloud\.com/[^\s\)\]]+", line)
    if m_sc:
        return m_sc.group(0)
    
    # Spotify markdown [text](song_url)
    m_sp_md = re.search(r"\((https?://(?:open\.)?spotify\.com/[^\s\)\]]+)\)", line)
    if m_sp_md:
        return m_sp_md.group(1)
    
    # Spotify plain URLs (embedded anywhere, trimmed)
    m_sp_plain = re.search(r"https?://(?:open\.)?spotify\.com/[^\s\)\]]+", line)
    if m_sp_plain:
        return m_sp_plain.group(0)
    
    return ""

def read_links(input_path: Path, logger: logging.Logger) -> dict[str, List[str]]:
    """Read ALL links (Spotify + SoundCloud) from input file."""
    links = []
    spotify_links = []
    soundcloud_links = []
    youtube_links = []
    
    try:
        with input_path.open("r", encoding="utf-8") as f:
            for raw in f:
                url = clean_url(raw)
                if url:
                    links.append(url)
                    
                    if "spotify.com" in url:
                        spotify_links.append(url)
                    elif "soundcloud.com" in url:
                        soundcloud_links.append(url)
                    elif "youtube.com" in url or "youtu.be" in url:
                        youtube_links.append(url)

        
        logger.info(f"✅ Parsed {len(links)} total links:")
        logger.info(f"   📀 Spotify: {len(spotify_links)}")
        logger.info(f"   🔊 SoundCloud: {len(soundcloud_links)}")
        logger.info(f"   📺 YouTube: {len(youtube_links)}")
        
        for i, link in enumerate(links, 1):
            kind = "📀 Spotify" if "spotify.com" in link else "🔊 SoundCloud" if "soundcloud.com" in link else "📺 YouTube"
            logger.info(f"   {i}. {kind} {link.split('?')[0]}")
        
        return {
            "all": links,
            "spotify": spotify_links,
            "soundcloud": soundcloud_links,
            "youtube": youtube_links
        }
    except Exception as e:
        logger.error(f"❌ Failed to read links: {e}")
        return {"all": [], "spotify": [], "soundcloud": [], "youtube": []}

def parse_errors(errors_file: Path, logger: logging.Logger, playlist_url: str) -> List[Song]:
    """Parse spotdl errors file for failed songs."""
    failed_songs = []
        
    try:
        with errors_file.open("r", encoding="utf-8") as ef:
            for line in ef:
                line = line.strip()
                if not line or not line.startswith('https://open.spotify.com/track/'):
                    continue
                
                #    def __init__(self, song_url: str, playlist_url: str = None, error: str = "", title: str = "", artists: List[str] = [], playlist: Playlist = None, list_position: str = ""):
                #https://open.spotify.com/track/6bFeIzkzsU45auYW1UUa47 - LookupError: No results found for song: NOTION - Dreams
                if ' - LookupError: No results found for song:' in line:
                    song_link = line.split(' - LookupError: No results found for song:', 1)[0]
                    artists = line.split(' - LookupError: No results found for song:', 1)[1].split(' - ')[0]
                    title = line.split(' - LookupError: No results found for song:', 1)[1].split(' - ')[1]
                    failed_songs.append(Song(song_url=song_link.strip(), playlist_url=playlist_url, error = "LookupError: No results found", title=title.strip(), artists=[a.strip() for a in artists.split(',')]))
                    continue
                
                #https://open.spotify.com/track/2ZXsTQ8d1c75zMEJH0uj1R - KeyError: 'webCommandMetadata'
                if " - KeyError: 'webCommandMetadata'" in line:
                    song_link = line.split(' - KeyError:', 1)[0]
                    failed_songs.append(Song(song_url=song_link.strip(), playlist_url=playlist_url, error = f"KeyError: 'webCommandMetadata'"))
                    continue

                #https://open.spotify.com/track/0PBQS0GycsYJ4yJJRjAIXU - AudioProviderError: YT-DLP download error - https://music.youtube.com/watch?v=ceXJTfuie6k
                if " - AudioProviderError: YT-DLP download error - " in line:
                    song_link = line.split(' - AudioProviderError: YT-DLP download error - ', 1)[0]
                    failed_songs.append(Song(song_url=song_link.strip(), playlist_url=playlist_url, error = "AudioProviderError: YT-DLP download error"))
                    continue
    
    except Exception as e:
        logger.error(f"Failed to parse errors: {e}")
    
    return failed_songs

def get_spotify_creds(logger: logging.Logger) -> Tuple[str, str]:
    """Load and validate Spotify CLIENTID/CLIENT_SECRET from .env or env vars."""
    client_id = os.getenv("CLIENTID")
    client_secret = os.getenv("CLIENTSECRET")
    
    if not client_id or not client_secret:
        logger.error("❌ Missing CLIENTID or CLIENTSECRET in .env")
        raise ValueError("Spotify credentials required")
    
    os.environ["SPOTIFY_CLIENT_ID"] = client_id
    os.environ["SPOTIFY_CLIENT_SECRET"] = client_secret
    logger.info("🔑 Spotify creds loaded")
    return client_id, client_secret