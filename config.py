import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('8343715238:AAEsxvZN7A2R8lssEn8lIqdLp_sxRZ2YtKY')
    ADMIN_USER_ID = int(os.getenv('7558715645', 0))
    
    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', 'https://coderkartik.great-site.net/youtube/api/index.php')
    
    # Download Settings
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 2000000000))  # 2GB
    
    # Quality Settings
    QUALITY_OPTIONS = {
        'best': {
            'label': '🎬 Best Quality',
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'description': 'Highest available quality'
        },
        '720p': {
            'label': '📺 720p HD',
            'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
            'description': 'HD Quality (1280x720)'
        },
        '480p': {
            'label': '📱 480p Medium',
            'format': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
            'description': 'Medium Quality (854x480)'
        },
        '360p': {
            'label': '⚡ 360p Fast',
            'format': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]',
            'description': 'Fast Download (640x360)'
        },
        'audio': {
            'label': '🎵 Audio Only (MP3)',
            'format': 'bestaudio[ext=m4a]',
            'description': 'Audio only - Best quality'
        }
    }
    
    # Supported domains
    SUPPORTED_DOMAINS = [
        'youtube.com',
        'youtu.be',
        'youtube-nocookie.com',
        'm.youtube.com'
    ]
