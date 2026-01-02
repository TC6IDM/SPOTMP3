import os
import re
import subprocess
import sys
import logging
from pathlib import Path

SPOTIFY_PREFIX = "https://open.spotify.com/"

def setup_logging(output_dir: Path):
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
    line = line.strip()
    if not line:
        return ""
    # 1) Markdown [text](url) → capture url in ()
    m = re.match(r".*\((https?://open\.spotify\.com/[^\s)]+)\)", line)
    if m:
        return m.group(1)
    # 2) Already plain spotify URL
    if line.startswith(SPOTIFY_PREFIX):
        return line
    return ""

def read_spotify_links(input_path: Path, logger: logging.Logger) -> list[str]:
    links = []
    try:
        with input_path.open("r", encoding="utf-8") as f:
            for raw in f:
                url = clean_url(raw)
                if url:
                    links.append(url)
        logger.info(f"✅ Parsed {len(links)} Spotify links")
        for i, link in enumerate(links, 1):
            logger.info(f"   {i}. {link.split('?')[0]}")
        return links
    except Exception as e:
        logger.info(f"❌ Failed to read links: {e}")
        return []

def run_spotdl_for_link(link: str, output_dir: Path, logger: logging.Logger) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean command for logging
    cmd = [
        "spotdl",
        # 🎵 AUDIO FALLBACKS (tries in order until success)
        "--audio", "youtube-music",    # 1️⃣ Best quality
        "--audio", "youtube",          # 2️⃣ Most reliable  
        "--audio", "soundcloud",       # 3️⃣ Official releases
        "--audio", "piped",            # 4️⃣ Privacy-focused YT
        "--audio", "bandcamp",         # 5️⃣ Indie/direct
        "--audio", "piped",            # 4️⃣ Privacy-focused YT
        "--audio", "soundcloud",       # 3️⃣ Official releases
        "--audio", "youtube",          # 2️⃣ Most reliable  
        "--audio", "youtube-music",    # 1️⃣ Best quality

        # 📝 LYRICS FALLBACKS (always tries all, embeds best)
        "--lyrics", "genius",          # 1️⃣ Most accurate
        "--lyrics", "musixmatch",      # 2️⃣ Official Spotify sync
        "--lyrics", "azlyrics",        # 3️⃣ Fallback text
        "--lyrics", "synced",          # 4️⃣ Timed lyrics (LRC)
        "--lyrics", "azlyrics",        # 3️⃣ Fallback text
        "--lyrics", "musixmatch",      # 2️⃣ Official Spotify sync
        "--lyrics", "genius",          # 1️⃣ Most accurate

        # 🎛️ Core settings
        "--bitrate", "320k",
        "--format", "mp3",
        "--threads", "4",
        "--overwrite", "skip",
        "--print-errors",
        "--save-errors", "errors.txt",
        
        # 📁 Clean output
        "--output", "{list-name}/{list-position} {title} - {artists}.{output-ext}",
        "download",
        link,
    ]
    
    logger.info(f"🎵 Downloading: {link.split('?')[0]}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    env = os.environ.copy()
    try:
        proc = subprocess.run(cmd, env=env, cwd=str(output_dir), 
                            capture_output=False, text=True, timeout=3600)
        if proc.returncode == 0:
            logger.info(f"✅ Playlist complete: {output_dir}")
        else:
            logger.info(f"⚠️  Playlist finished with code {proc.returncode}")
        return proc.returncode
    except subprocess.TimeoutExpired:
        logger.info("⏰ Download timed out after 1 hour")
        return 1
    except Exception as e:
        logger.info(f"💥 SpotDL error: {e}")
        return 1

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_file> <output_dir>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    
    logger = setup_logging(output_dir)
    
    if not input_file.is_file():
        logger.info(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    links = read_spotify_links(input_file, logger)
    if not links:
        logger.info("❌ No Spotify playlist links found")
        sys.exit(1)

    logger.info(f"🎯 Starting {len(links)} playlists...")
    
    exit_code = 0
    for i, link in enumerate(links, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"[{i}/{len(links)}] Processing playlist...")
        code = run_spotdl_for_link(link, output_dir, logger)
        if code != 0:
            exit_code = code
            logger.info(f"Playlist {i} failed (code {code})")

    logger.info(f"\n🎉 Complete! Final exit code: {exit_code}")
    logger.info(f"📁 Files in: {output_dir}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
