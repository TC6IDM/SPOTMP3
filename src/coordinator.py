from typing import Dict, List, Tuple
from pathlib import Path
import logging

from src.downloaders.base import BaseDownloader
from src.utils import read_links  # Returns dict["spotify": [...], ...]
from src.downloaders.spotify import SpotifyDownloader
from src.downloaders.soundcloud import SoundCloudDownloader
from src.downloaders.youtube import YouTubeDownloader
from src.models import Song

class Coordinator:
    def __init__(self, output_dir: Path, logger: logging.Logger, 
                 spotify_client_id: str, spotify_client_secret: str):
        self.output_dir = output_dir
        self.logger = logger
        self.spotify_client_id = spotify_client_id
        self.spotify_client_secret = spotify_client_secret

    def _get_downloader(self, provider: str) -> 'BaseDownloader':
        """Factory for provider-specific downloaders."""
        if provider == "spotify":
            return SpotifyDownloader(self.output_dir, self.logger, self.spotify_client_id, self.spotify_client_secret)
        elif provider == "soundcloud":
            return SoundCloudDownloader(self.output_dir, self.logger)
        elif provider == "youtube":
            return YouTubeDownloader(self.output_dir, self.logger)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def process_provider(self, provider: str, links: List[str]) -> int:
        """Process one provider's links (like spotify_main)."""
        if not links:
            self.logger.info(f"ℹ️ No {provider} links")
            return 0
        
        self.logger.info(f"🎯 Starting {len(links)} {provider} playlists...")
        downloader = self._get_downloader(provider)
        exit_code = 0
        
        for i, link in enumerate(links, 1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"[{provider.upper()} {i}/{len(links)}] {link.split('?')[0]}")
            
            code, errors_file = downloader.download(link)
            if code != 0:
                exit_code = code
                self.logger.warning(f"Failed (code {code})")
            
            playlist_name = downloader.fetch_metadata_image(link)

            # Provider-specific post-processing
            missing = downloader.cleanup(playlist_name)
            # if missing:
            #     self.logger.info(f"⚠️ {len(missing)} missing tracks")
            
            # Parse errors if file exists
            # if errors_file.exists(): parse_errors(errors_file, ...)
        
        self.logger.info(f"✅ {provider} complete (exit: {exit_code})")
        return exit_code

    def process_all(self, input_file: Path) -> int:
        """Unified entry: process all providers sequentially."""
        links_by_provider = read_links(input_file, self.logger)
        exit_code = 0
        
        # Your original order: soundcloud -> youtube -> spotify
        for provider in ["soundcloud", "youtube", "spotify"]:
            provider_exit = self.process_provider(provider, links_by_provider.get(provider, []))
            if provider_exit != 0:
                exit_code = provider_exit  # Fail fast
        
        return exit_code
