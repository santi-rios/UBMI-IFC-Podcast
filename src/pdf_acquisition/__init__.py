"""PDF acquisition modules for downloading research papers."""

from .direct_download import DirectDownloader
from .paperbot import PyPaperBotWrapper

__all__ = ['DirectDownloader', 'PyPaperBotWrapper']