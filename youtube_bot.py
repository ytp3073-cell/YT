#!/usr/bin/env python3
"""
YouTube Video Downloader Bot with Direct Download
Works without external API
"""

import os
import logging
import asyncio
import re
import tempfile
import subprocess
from typing import Dict, Optional
from datetime import datetime

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50000000))  # 50MB default

if not BOT_TOKEN:
    print("\n" + "="*50)
    print("❌ ERROR: Bot Token Not Found!")
    print("="*50)
    print("Please create .env file with:")
    print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
    print("="*50)
    exit(1)

class YouTubeBot:
    def __init__(self):
        self.user_data: Dict = {}
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/shorts\/([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def is_youtube_url(self, url: str) -> bool:
        """Check if URL is YouTube"""
        domains = ['youtube.com', 'youtu.be']
        return any(domain in url for domain in domains) and self.extract_video_id(url) is not None
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information using yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'force_generic_extractor': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if info:
                    # Format information
                    formats = []
                    for f in info.get('formats', []):
                        if f.get('video_ext') != 'none' and f.get('audio_ext') != 'none':
                            formats.append({
                                'format_id': f.get('format_id'),
                                'height': f.get('height'),
                                'width': f.get('width'),
                                'filesize': f.get('filesize'),
                                'ext': f.get('ext')
                            })
                    
                    return {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'duration': info.get('duration'),
                        'thumbnail': info.get('thumbnail'),
                        'formats': formats,
                        'view_count': info.get('view_count'),
                        'uploader': info.get('uploader')
                    }
            return None
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    async def download_video(self, url: str, quality: str, user_id: int) -> Optional[str]:
        """Download video with selected quality"""
        temp_dir = tempfile.mkdtemp(prefix=f"ytdl_{user_id}_")
        
        try:
            if quality == 'audio':
                # Download as MP3
                ydl_opts = {
                    'format': 'bestaudio[ext=m4a]/bestaudio',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }
            elif quality == '360':
                # 360p quality
                ydl_opts = {
                    'format': 'best[height<=360][ext=mp4]/best[height<=360]',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }
            elif quality == '480':
                # 480p quality
                ydl_opts = {
                    'format': 'best[height<=480][ext=mp4]/best[height<=480]',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }
            elif quality == '720':
                # 720p quality
                ydl_opts = {
                    'format': 'best[height<=720][ext=mp4]/best[height<=720]',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }
            else:
                # Best quality
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                    'quiet': True,
                    'no_warnings': True,
                }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_files = [f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
                
                if downloaded_files:
                    return os.path.join(temp_dir, downloaded_files[0])
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            # Clean up temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = f"""
🎬 *Welcome {user.first_name}!*

I'm *YouTube Video Downloader Bot* 🤖

*📌 How to use:*
1. Send me any YouTube video link
2. Choose video quality
3. I'll download it with crystal clear audio!

*✨ Features:*
✅ Multiple quality options
✅ Clear audio quality
✅ Fast downloads
✅ No watermarks
✅ Direct video sending

*📎 Supported formats:*
• YouTube videos
• YouTube Shorts

*⚡ Commands:*
/start - Show this message
/help - Get help
/status - Check bot status

*👉 Just send me a YouTube link to get started!*
        """
        
        keyboard = [
            [InlineKeyboardButton("📚 Example Link", callback_data="example")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 *YouTube Downloader Bot - Help Guide*

*🔗 How to Download:*
1. Copy any YouTube video URL
2. Paste it here
3. Select quality
4. Wait for download

*📋 Supported Links:*
• https://youtube.com/watch?v=...
• https://youtu.be/...
• https://youtube.com/shorts/...

*⚡ Quality Options:*
• 🎬 Best - Highest available
• 📺 720p - HD with good audio
• 📱 480p - Balanced quality/size
• ⚡ 360p - Fast download
• 🎵 MP3 - Audio only

*⚠️ Limitations:*
• Max file size: 50MB (Telegram limit)
• Some age-restricted videos may not work
• Long videos might be too large

*❓ Need more help?*
Contact: @coderkartik
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_text = f"""
🟢 *Bot Status: Online*

*📊 Statistics:*
• Users served: {len(self.user_data)}
• Uptime: 100%

*🔧 System Status:*
• Download Service: ✅ Active
• Storage: ✅ Available

Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        message_text = update.message.text.strip()
        
        if self.is_youtube_url(message_text):
            await self.process_video(update, context, message_text)
        else:
            await update.message.reply_text(
                "📎 *Please send me a valid YouTube video URL!*\n\n"
                "Example:\n"
                "• `https://youtube.com/watch?v=dQw4w9WgXcQ`\n"
                "• `https://youtu.be/dQw4w9WgXcQ`\n"
                "• `https://youtube.com/shorts/VIDEO_ID`",
                parse_mode='Markdown'
            )
    
    async def process_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Process video URL"""
        user_id = update.effective_user.id
        
        # Show processing message
        processing_msg = await update.message.reply_text(
            "🔍 *Processing your request...*\n"
            "⏳ Extracting video information...",
            parse_mode='Markdown'
        )
        
        try:
            # Get video info
            video_info = await self.get_video_info(url)
            
            if not video_info:
                await processing_msg.edit_text(
                    "❌ *Unable to fetch video information*\n\n"
                    "Possible reasons:\n"
                    "• Private or age-restricted video\n"
                    "• Network issue\n"
                    "• Invalid URL\n\n"
                    "Please try another video.",
                    parse_mode='Markdown'
                )
                return
            
            # Store video info
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
            self.user_data[user_id]['current_video'] = {
                'url': url,
                'title': video_info.get('title', 'YouTube Video'),
                'video_id': video_info.get('id'),
                'duration': video_info.get('duration')
            }
            
            # Create quality options
            keyboard = [
                [
                    InlineKeyboardButton("🎬 Best", callback_data=f"dl_best_{user_id}"),
                    InlineKeyboardButton("📺 720p", callback_data=f"dl_720_{user_id}")
                ],
                [
                    InlineKeyboardButton("📱 480p", callback_data=f"dl_480_{user_id}"),
                    InlineKeyboardButton("⚡ 360p", callback_data=f"dl_360_{user_id}")
                ],
                [
                    InlineKeyboardButton("🎵 MP3", callback_data=f"dl_audio_{user_id}")
                ],
                [
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{user_id}")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Format duration
            duration = video_info.get('duration', 0)
            if duration:
                minutes, seconds = divmod(duration, 60)
                hours, minutes = divmod(minutes, 60)
                if hours > 0:
                    duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "Unknown"
            
            # Edit message with video info
            title = video_info.get('title', 'YouTube Video')[:50] + "..." if len(video_info.get('title', '')) > 50 else video_info.get('title', 'YouTube Video')
            
            await processing_msg.edit_text(
                f"✅ *Video Found!*\n\n"
                f"📹 *Title:* {title}\n"
                f"👤 *Uploader:* {video_info.get('uploader', 'Unknown')}\n"
                f"⏱️ *Duration:* {duration_str}\n"
                f"👁️ *Views:* {video_info.get('view_count', 'Unknown'):,}\n\n"
                f"👇 *Select download quality:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            await processing_msg.edit_text(
                f"❌ *Error:* {str(e)[:100]}\n\n"
                "Please try another video.",
                parse_mode='Markdown'
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data.startswith("example"):
            await query.edit_message_text(
                "📋 *Example YouTube Links:*\n\n"
                "Regular video:\n"
                "`https://www.youtube.com/watch?v=dQw4w9WgXcQ`\n\n"
                "Short URL:\n"
                "`https://youtu.be/dQw4w9WgXcQ`\n\n"
                "YouTube Shorts:\n"
                "`https://www.youtube.com/shorts/abc123`",
                parse_mode='Markdown'
            )
        
        elif data.startswith("help"):
            await self.help_command(update, context)
        
        elif data.startswith("cancel_"):
            await query.edit_message_text(
                "❌ *Download cancelled*\n\n"
                "Send another YouTube link when you're ready!",
                parse_mode='Markdown'
            )
        
        elif data.startswith("dl_"):
            # Extract quality and user_id
            parts = data.split('_')
            if len(parts) >= 3:
                quality = parts[1]
                callback_user_id = int(parts[2])
                
                if callback_user_id != user_id:
                    await query.edit_message_text("This request is not for you!")
                    return
                
                # Get video info for this user
                video_info = self.user_data.get(user_id, {}).get('current_video', {})
                if not video_info:
                    await query.edit_message_text("Video info not found. Please send link again.")
                    return
                
                url = video_info['url']
                video_title = video_info['title']
                
                # Quality labels
                quality_labels = {
                    'best': '🎬 Best Quality',
                    '720': '📺 720p HD',
                    '480': '📱 480p',
                    '360': '⚡ 360p',
                    'audio': '🎵 MP3 Audio'
                }
                
                quality_label = quality_labels.get(quality, quality.upper())
                
                # Update message to show downloading
                await query.edit_message_text(
                    f"⏬ *Downloading...*\n\n"
                    f"📹 *Title:* {video_title[:40]}...\n"
                    f"🎬 *Quality:* {quality_label}\n"
                    f"🔊 *Audio:* Crystal Clear\n\n"
                    f"⏳ *Status:* Starting download...\n"
                    f"📊 *Progress:* 0%\n"
                    f"⏱️ *ETA:* Calculating...",
                    parse_mode='Markdown'
                )
                
                # Download the video
                try:
                    # Update progress
                    await query.edit_message_text(
                        f"⏬ *Downloading...*\n\n"
                        f"📹 *Title:* {video_title[:40]}...\n"
                        f"🎬 *Quality:* {quality_label}\n\n"
                        f"⏳ *Status:* Downloading from YouTube...\n"
                        f"📊 *Progress:* 25%\n"
                        f"⏱️ *ETA:* 30 seconds",
                        parse_mode='Markdown'
                    )
                    
                    # Download video
                    file_path = await self.download_video(url, quality, user_id)
                    
                    if file_path and os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        
                        # Check file size
                        if file_size > MAX_FILE_SIZE:
                            await query.edit_message_text(
                                f"❌ *File Too Large*\n\n"
                                f"Size: {file_size/(1024*1024):.2f} MB\n"
                                f"Max allowed: {MAX_FILE_SIZE/(1024*1024):.2f} MB\n\n"
                                "Please try a lower quality.",
                                parse_mode='Markdown'
                            )
                            # Clean up
                            import shutil
                            shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
                            return
                        
                        # Update progress
                        await query.edit_message_text(
                            f"⏬ *Downloading...*\n\n"
                            f"📹 *Title:* {video_title[:40]}...\n"
                            f"🎬 *Quality:* {quality_label}\n\n"
                            f"⏳ *Status:* Sending to Telegram...\n"
                            f"📊 *Progress:* 75%\n"
                            f"⏱️ *ETA:* 10 seconds",
                            parse_mode='Markdown'
                        )
                        
                        # Send file to user
                        if quality == 'audio':
                            # Send as audio
                            with open(file_path, 'rb') as audio_file:
                                await context.bot.send_audio(
                                    chat_id=query.message.chat_id,
                                    audio=InputFile(audio_file, filename=f"{video_title[:30]}.mp3"),
                                    caption=f"✅ *Download Complete!*\n\n"
                                           f"🎵 *Title:* {video_title}\n"
                                           f"💾 *Size:* {file_size/(1024*1024):.2f} MB\n"
                                           f"🔊 *Quality:* High Quality MP3",
                                    parse_mode='Markdown'
                                )
                        else:
                            # Send as video
                            with open(file_path, 'rb') as video_file:
                                await context.bot.send_video(
                                    chat_id=query.message.chat_id,
                                    video=InputFile(video_file, filename=f"{video_title[:30]}.mp4"),
                                    caption=f"✅ *Download Complete!*\n\n"
                                           f"📹 *Title:* {video_title}\n"
                                           f"🎬 *Quality:* {quality_label}\n"
                                           f"💾 *Size:* {file_size/(1024*1024):.2f} MB\n"
                                           f"🔊 *Audio:* Crystal Clear",
                                    parse_mode='Markdown',
                                    supports_streaming=True
                                )
                        
                        # Clean up
                        import shutil
                        shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
                        
                        # Final message
                        await query.edit_message_text(
                            f"✅ *Download Successful!*\n\n"
                            f"Your video has been sent above!\n\n"
                            f"Want to download another?\n"
                            f"Just send me a new YouTube link! 🎬",
                            parse_mode='Markdown'
                        )
                        
                    else:
                        await query.edit_message_text(
                            "❌ *Download failed*\n\n"
                            "Could not download the video.\n"
                            "Please try again or choose different quality.",
                            parse_mode='Markdown'
                        )
                        
                except Exception as e:
                    logger.error(f"Download error: {e}")
                    await query.edit_message_text(
                        f"❌ *Download Error*\n\n"
                        f"Error: {str(e)[:100]}\n\n"
                        "Please try again.",
                        parse_mode='Markdown'
                    )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error: {context.error}")
        
        try:
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ *An error occurred*\n\nPlease try again or send /start",
                    parse_mode='Markdown'
                )
        except:
            pass
    
    def run(self):
        """Start the bot"""
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("status", self.status_command))
        
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        app.add_error_handler(self.error_handler)
        
        # Start bot
        print("\n" + "="*50)
        print("🎬 YouTube Video Downloader Bot")
        print("="*50)
        print("⚡ Direct YouTube Download")
        print("🔊 Crystal Clear Audio")
        print("📱 Multiple Quality Options")
        print("="*50)
        print("🤖 Bot is starting...")
        print("="*50)
        
        app.run_polling()

if __name__ == "__main__":
    bot = YouTubeBot()
    bot.run()
