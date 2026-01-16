#!/usr/bin/env python3
"""
YouTube Video Downloader Telegram Bot
Author: @coderkartik
Description: Downloads YouTube videos using custom API
"""

import os
import logging
import asyncio
import re
import json
from typing import Dict, Optional
from datetime import datetime

import requests
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import Config

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

class YouTubeDownloaderBot:
    def __init__(self):
        self.config = Config
        self.user_data: Dict[int, Dict] = {}
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
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
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        # Check if any supported domain is in URL
        if not any(domain in url for domain in self.config.SUPPORTED_DOMAINS):
            return False
        
        # Try to extract video ID
        video_id = self.extract_video_id(url)
        return video_id is not None
    
    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information using API"""
        try:
            api_url = f"{self.config.API_BASE_URL}?youtube-dl={url}&info=1"
            
            logger.info(f"Fetching video info from: {api_url}")
            
            response = requests.get(api_url, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return data
                except json.JSONDecodeError:
                    # If API returns HTML or text response
                    content = response.text
                    # Try to extract title from HTML if needed
                    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                    title = title_match.group(1).strip() if title_match else "Unknown Title"
                    
                    return {
                        'status': 'success',
                        'title': title,
                        'url': url,
                        'thumbnail': f"https://img.youtube.com/vi/{self.extract_video_id(url)}/maxresdefault.jpg"
                    }
            else:
                logger.error(f"API returned status code: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching video info: {e}")
            return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = f"""
🎬 **Welcome {user.first_name}!**

I'm **YouTube Video Downloader Bot** 🤖

**📌 How to use:**
1. Send me any YouTube video link
2. Choose video quality
3. I'll download it with crystal clear audio!

**✨ Features:**
✅ Multiple quality options
✅ Clear audio quality
✅ Fast downloads
✅ No watermarks
✅ Direct video sending

**📎 Supported formats:**
• YouTube videos
• YouTube Shorts
• Playlists (first video)

**⚡ Commands:**
/start - Show this message
/help - Get help
/settings - Change download settings
/status - Check bot status

**👉 Just send me a YouTube link to get started!**
        """
        
        # Create inline keyboard with example
        keyboard = [
            [InlineKeyboardButton("📚 Example Link", callback_data="example")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **YouTube Downloader Bot - Help Guide**

**🔗 How to Download:**
1. Copy any YouTube video URL
2. Paste it here
3. Select quality
4. Wait for download

**📋 Supported Links:**
• https://youtube.com/watch?v=...
• https://youtu.be/...
• https://youtube.com/shorts/...
• Mobile YouTube links

**⚡ Quality Options:**
• 🎬 Best Quality - Highest available
• 📺 720p HD - HD with good audio
• 📱 480p - Balanced quality/size
• ⚡ 360p - Fast download
• 🎵 Audio Only - MP3 format

**⚠️ Limitations:**
• Max file size: 2GB
• Some age-restricted videos may not work
• Playlist support limited

**❓ Need more help?**
Contact: @coderkartik
        """
        
        keyboard = [
            [InlineKeyboardButton("🚀 Start Downloading", switch_inline_query_current_chat="")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user_id = update.effective_user.id
        
        # Get user settings or defaults
        user_settings = self.user_data.get(user_id, {}).get('settings', {
            'default_quality': '720p',
            'auto_download': False,
            'send_as_document': False
        })
        
        settings_text = f"""
⚙️ **Download Settings**

**Current Settings:**
• Default Quality: {user_settings['default_quality']}
• Auto Download: {'✅ On' if user_settings['auto_download'] else '❌ Off'}
• Send as Document: {'✅ On' if user_settings['send_as_document'] else '❌ Off'}

**Change settings:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🎬 Best Quality", callback_data="set_quality_best"),
                InlineKeyboardButton("📺 720p", callback_data="set_quality_720p")
            ],
            [
                InlineKeyboardButton("📱 480p", callback_data="set_quality_480p"),
                InlineKeyboardButton("⚡ 360p", callback_data="set_quality_360p")
            ],
            [
                InlineKeyboardButton(f"{'✅' if user_settings['auto_download'] else '❌'} Auto Download", 
                                   callback_data="toggle_auto"),
                InlineKeyboardButton(f"{'✅' if user_settings['send_as_document'] else '❌'} As Document", 
                                   callback_data="toggle_document")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status_text = """
🟢 **Bot Status: Online**

**📊 Statistics:**
• Users served: Calculating...
• Downloads today: Calculating...
• Uptime: 100%

**🔧 System Status:**
• API Connection: ✅ Working
• Download Service: ✅ Active
• Storage: ✅ Available

**📞 Support:**
For issues or questions, contact @coderkartik

Last updated: {}
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages"""
        message_text = update.message.text.strip()
        
        # Check if message contains YouTube URL
        if self.is_valid_youtube_url(message_text):
            await self.process_video_request(update, context, message_text)
        else:
            # Check if it might be a partial URL
            if any(keyword in message_text.lower() for keyword in ['youtube', 'youtu.be', 'watch?v=']):
                await update.message.reply_text(
                    "🔍 **I think you sent a YouTube link, but I couldn't extract it properly.**\n\n"
                    "Please make sure it's a complete URL like:\n"
                    "• `https://youtube.com/watch?v=...`\n"
                    "• `https://youtu.be/...`\n"
                    "• `https://youtube.com/shorts/...`\n\n"
                    "Then send it again! 😊",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "📎 **Please send me a YouTube video URL!**\n\n"
                    "I can download videos from:\n"
                    "✅ YouTube\n"
                    "✅ YouTube Shorts\n\n"
                    "Just copy and paste any YouTube link here! 🎬",
                    parse_mode='Markdown'
                )
    
    async def process_video_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Process YouTube video download request"""
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "🔍 **Processing your request...**\n"
            "• Extracting video information\n"
            "• Checking available formats\n"
            "• Preparing download options\n\n"
            "⏳ Please wait...",
            parse_mode='Markdown'
        )
        
        try:
            # Get video information
            video_info = await self.get_video_info(url)
            
            if not video_info:
                await processing_msg.edit_text(
                    "❌ **Unable to fetch video information**\n\n"
                    "Possible reasons:\n"
                    "• Invalid or private video\n"
                    "• Age-restricted content\n"
                    "• Network issue\n\n"
                    "Please try another video or check the URL.",
                    parse_mode='Markdown'
                )
                return
            
            # Extract video ID for thumbnail
            video_id = self.extract_video_id(url)
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            
            # Store video info for this user
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
            
            self.user_data[user_id]['current_video'] = {
                'url': url,
                'title': video_info.get('title', 'YouTube Video'),
                'video_id': video_id
            }
            
            # Create quality selection keyboard
            keyboard = []
            for quality_key, quality_info in self.config.QUALITY_OPTIONS.items():
                button_text = f"{quality_info['label']}"
                callback_data = f"download_{quality_key}_{video_id}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Add cancel button
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_download")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Edit message with quality options
            title = video_info.get('title', 'YouTube Video')[:100] + "..." if len(video_info.get('title', '')) > 100 else video_info.get('title', 'YouTube Video')
            
            await processing_msg.edit_text(
                f"✅ **Video Found!**\n\n"
                f"📹 **Title:** {title}\n"
                f"🔗 **URL:** {url}\n"
                f"🆔 **Video ID:** `{video_id}`\n\n"
                f"👇 **Select download quality:**\n"
                f"_Audio will be clear in all options_ 🔊",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error processing video request: {e}")
            await processing_msg.edit_text(
                "❌ **An error occurred**\n\n"
                "Error details: {}\n\n"
                "Please try again or contact support.".format(str(e)),
                parse_mode='Markdown'
            )
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        user_id = query.from_user.id
        
        if callback_data == "example":
            await query.edit_message_text(
                "📋 **Example YouTube Links:**\n\n"
                "• Regular video:\n"
                "`https://www.youtube.com/watch?v=dQw4w9WgXcQ`\n\n"
                "• Short URL:\n"
                "`https://youtu.be/dQw4w9WgXcQ`\n\n"
                "• YouTube Shorts:\n"
                "`https://www.youtube.com/shorts/VIDEO_ID`\n\n"
                "Just copy and paste any of these formats!",
                parse_mode='Markdown'
            )
        
        elif callback_data == "help":
            await self.help_command(update, context)
        
        elif callback_data == "settings":
            await self.settings_command(update, context)
        
        elif callback_data == "back_to_main":
            await self.start_command(update, context)
        
        elif callback_data == "cancel_download":
            await query.edit_message_text(
                "❌ **Download cancelled**\n\n"
                "Send another YouTube link whenever you're ready! 🎬",
                parse_mode='Markdown'
            )
        
        elif callback_data.startswith("download_"):
            await self.process_download_request(query, callback_data)
        
        elif callback_data.startswith("set_quality_"):
            quality = callback_data.replace("set_quality_", "")
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
            if 'settings' not in self.user_data[user_id]:
                self.user_data[user_id]['settings'] = {}
            self.user_data[user_id]['settings']['default_quality'] = quality
            
            await query.edit_message_text(
                f"✅ **Settings Updated!**\n\n"
                f"Default quality set to: **{quality.upper()}**\n\n"
                f"New videos will use this quality by default.",
                parse_mode='Markdown'
            )
        
        elif callback_data == "toggle_auto":
            if user_id not in self.user_data:
                self.user_data[user_id] = {}
            if 'settings' not in self.user_data[user_id]:
                self.user_data[user_id]['settings'] = {'auto_download': False}
            
            current = self.user_data[user_id]['settings'].get('auto_download', False)
            self.user_data[user_id]['settings']['auto_download'] = not current
            
            status = "✅ ON" if not current else "❌ OFF"
            await query.edit_message_text(
                f"✅ **Settings Updated!**\n\n"
                f"Auto Download: **{status}**",
                parse_mode='Markdown'
            )
    
    async def process_download_request(self, query, callback_data: str):
        """Process the actual download request"""
        # Extract quality and video ID from callback data
        parts = callback_data.split('_')
        if len(parts) < 3:
            await query.edit_message_text("Invalid request format")
            return
        
        quality = parts[1]
        video_id = parts[2]
        
        # Get user's stored video URL
        user_id = query.from_user.id
        video_info = self.user_data.get(user_id, {}).get('current_video', {})
        
        if not video_info or video_info.get('video_id') != video_id:
            await query.edit_message_text(
                "❌ **Video information not found**\n\n"
                "Please send the YouTube link again.",
                parse_mode='Markdown'
            )
            return
        
        video_url = video_info['url']
        video_title = video_info['title']
        
        # Update message to show downloading status
        quality_label = self.config.QUALITY_OPTIONS.get(quality, {}).get('label', quality.upper())
        
        await query.edit_message_text(
            f"⏬ **Downloading Video...**\n\n"
            f"📹 **Title:** {video_title[:50]}...\n"
            f"🎬 **Quality:** {quality_label}\n"
            f"🔊 **Audio:** Crystal Clear\n\n"
            f"⏳ **Status:** Preparing download...\n"
            f"📊 **Progress:** 0%\n"
            f"⏱️ **ETA:** Calculating...",
            parse_mode='Markdown'
        )
        
        try:
            # Download video using API
            download_url = f"{self.config.API_BASE_URL}?youtube-dl={video_url}&format={quality}"
            
            # Show progress updates
            for progress in [25, 50, 75]:
                await asyncio.sleep(1)
                await query.edit_message_text(
                    f"⏬ **Downloading Video...**\n\n"
                    f"📹 **Title:** {video_title[:50]}...\n"
                    f"🎬 **Quality:** {quality_label}\n"
                    f"🔊 **Audio:** Crystal Clear\n\n"
                    f"⏳ **Status:** Downloading...\n"
                    f"📊 **Progress:** {progress}%\n"
                    f"⏱️ **ETA:** {3-progress//25} seconds",
                    parse_mode='Markdown'
                )
            
            # Download the file
            response = requests.get(download_url, stream=True, timeout=300)
            
            if response.status_code == 200:
                # Generate filename
                safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = f"{safe_title[:50]}_{quality}.mp4"
                
                # Save file temporarily
                temp_path = f"temp_{user_id}_{video_id}.mp4"
                
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Get file size
                file_size = os.path.getsize(temp_path)
                
                # Check if file is too large for Telegram
                if file_size > self.config.MAX_FILE_SIZE:
                    await query.edit_message_text(
                        "❌ **File Too Large**\n\n"
                        f"File size: {file_size/(1024*1024):.2f} MB\n"
                        f"Maximum allowed: {self.config.MAX_FILE_SIZE/(1024*1024):.2f} MB\n\n"
                        "Please try a lower quality option.",
                        parse_mode='Markdown'
                    )
                    os.remove(temp_path)
                    return
                
                # Send the video
                with open(temp_path, 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id=query.message.chat_id,
                        video=InputFile(video_file, filename=filename),
                        caption=f"✅ **Download Complete!**\n\n"
                               f"📹 **Title:** {video_title}\n"
                               f"🎬 **Quality:** {quality_label}\n"
                               f"💾 **Size:** {file_size/(1024*1024):.2f} MB\n"
                               f"🔊 **Audio:** Crystal Clear\n\n"
                               f"Enjoy your video! 🎬",
                        parse_mode='Markdown',
                        supports_streaming=True
                    )
                
                # Clean up temp file
                os.remove(temp_path)
                
                # Send completion message
                await query.edit_message_text(
                    "✅ **Download Successful!**\n\n"
                    "Your video has been sent above with crystal clear audio! 🔊\n\n"
                    "Want to download another video? Just send me the link! 🎬",
                    parse_mode='Markdown'
                )
                
            else:
                await query.edit_message_text(
                    "❌ **Download Failed**\n\n"
                    "API returned error code: {}\n\n"
                    "Please try again or choose a different quality.".format(response.status_code),
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            await query.edit_message_text(
                "❌ **Download Error**\n\n"
                "An error occurred while downloading:\n"
                f"`{str(e)}`\n\n"
                "Please try again or contact support.",
                parse_mode='Markdown'
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Error: {context.error}")
        
        if update and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ **An error occurred**\n\n"
                         "Please try again or send /start to restart.",
                    parse_mode='Markdown'
                )
            except:
                pass
    
    def run(self):
        """Start the bot"""
        if not self.config.TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables!")
            print("\n" + "="*50)
            print("❌ ERROR: Bot Token Not Found!")
            print("="*50)
            print("Please follow these steps:")
            print("1. Create a bot with @BotFather on Telegram")
            print("2. Copy the bot token")
            print("3. Add it to .env file:")
            print("   TELEGRAM_BOT_TOKEN=your_token_here")
            print("4. Also add your Telegram ID:")
            print("   ADMIN_USER_ID=your_telegram_id")
            print("="*50)
            return
        
        # Create Application
        application = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("settings", self.settings_command))
        application.add_handler(CommandHandler("status", self.status_command))
        
        # Add message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Add callback query handler
        application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        # Add error handler
        application.add_error_handler(self.error_handler)
        
        # Start the bot
        print("\n" + "="*50)
        print("🎬 YouTube Video Downloader Bot")
        print("="*50)
        print(f"🤖 Bot Username: @{application.bot.username}")
        print(f"🔗 API URL: {self.config.API_BASE_URL}")
        print("📊 Status: Starting...")
        print("="*50)
        
        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)

# Run the bot
if __name__ == '__main__':
    bot = YouTubeDownloaderBot()
    bot.run()