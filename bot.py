import os
import logging
import asyncio
import aiohttp
import replicate
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from io import BytesIO
import base64

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class IcifiedBot:
    def __init__(self, telegram_token: str, replicate_token: str):
        self.telegram_token = telegram_token
        self.replicate_token = replicate_token
        
        # Initialize Replicate client
        os.environ["REPLICATE_API_TOKEN"] = replicate_token
        self.replicate_client = replicate.Client(api_token=replicate_token)
        
        # Bot application
        self.app = Application.builder().token(telegram_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup bot command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = """
🔥 Welcome to the ICIFIED Bot! 💎

Transform any photo into a luxurious masterpiece with:
• Diamond-encrusted watches ⌚💎
• Shiny diamond grillz 😁✨
• Maintains original style and lighting

Simply send me a photo and I'll ice it out for you!

Commands:
/help - Show this help message
/start - Start the bot

Just send a photo to get started! 📸
        """
        
        keyboard = [
            [InlineKeyboardButton("🔥 Send Photo to Ice Out! 📸", callback_data="send_photo")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 ICIFIED Bot Help 💎

How to use:
1. Send me any photo
2. Wait for processing (30-60 seconds)
3. Receive your icified masterpiece!

Features:
• Adds luxury diamond watch to left wrist
• Adds diamond grillz to teeth
• Preserves original lighting and background
• Works with portraits, selfies, and character images

Tips for best results:
• Use clear, well-lit photos
• Face should be visible for grillz
• Arms/hands visible for watch placement
• Higher resolution = better results

Send a photo to try it out! 🔥
        """
        await update.message.reply_text(help_text)
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming photos"""
        try:
            # Send processing message
            processing_msg = await update.message.reply_text(
                "🔥 Icifying your photo... This may take 30-60 seconds! 💎\n\n"
                "Adding:\n• Diamond watch ⌚💎\n• Diamond grillz 😁✨"
            )
            
            # Get the photo
            photo = update.message.photo[-1]  # Get highest resolution
            photo_file = await photo.get_file()
            
            # Download photo to memory
            photo_bytes = BytesIO()
            await photo_file.download_to_memory(photo_bytes)
            photo_bytes.seek(0)
            
            # Process the image
            result_url = await self.process_image(photo_bytes)
            
            if result_url:
                # Download processed image
                processed_image = await self.download_image(result_url)
                
                # Send result
                await update.message.reply_photo(
                    photo=processed_image,
                    caption="🔥 Your photo has been ICIFIED! 💎✨\n\nShare your iced out masterpiece! 🎯"
                )
                
                # Delete processing message
                await processing_msg.delete()
            else:
                await processing_msg.edit_text(
                    "❌ Sorry, something went wrong processing your image. Please try again!"
                )
                
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await update.message.reply_text(
                "❌ Error processing your photo. Please try again or contact support."
            )
    
    async def process_image(self, image_bytes: BytesIO) -> str:
        """Process image through Replicate API"""
        try:
            # Convert image to base64 for API
            image_b64 = base64.b64encode(image_bytes.getvalue()).decode()
            data_url = f"data:image/jpeg;base64,{image_b64}"
            
            # Use a working image generation model (FLUX for better results)
            output = await asyncio.to_thread(
                self.replicate_client.run,
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": "person with luxury diamond watch on wrist and diamond grillz teeth, ice out, jewelry, bling, expensive, high quality, photorealistic, luxury lifestyle",
                    "image": data_url,
                    "width": 768,
                    "height": 768,
                    "num_inference_steps": 4,
                    "guidance_scale": 3.5
                }
            )
            
            # Return the first output URL
            if output and len(output) > 0:
                return output[0]
            return None
            
        except Exception as e:
            logger.error(f"Error in Replicate API call: {e}")
            return None
    
    async def download_image(self, url: str) -> BytesIO:
        """Download image from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                image_data = await response.read()
                return BytesIO(image_data)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "send_photo":
            await query.edit_message_text(
                "📸 Send me a photo to ice out! \n\n"
                "I'll add diamond grillz and a luxury watch while maintaining "
                "the original style and lighting. 💎🔥"
            )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Icified Bot...")
        self.app.run_polling()


# Main execution
if __name__ == "__main__":
    # Environment variables
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")
    
    # Debug logging
    print("🔍 Debug Info:")
    print(f"Telegram token exists: {bool(TELEGRAM_TOKEN)}")
    print(f"Telegram token length: {len(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else 0}")
    print(f"Replicate token exists: {bool(REPLICATE_TOKEN)}")
    print(f"Replicate token length: {len(REPLICATE_TOKEN) if REPLICATE_TOKEN else 0}")
    
    if not TELEGRAM_TOKEN or not REPLICATE_TOKEN:
        print("❌ Missing required environment variables!")
        print("Please set:")
        print("- TELEGRAM_BOT_TOKEN")
        print("- REPLICATE_API_TOKEN")
        exit(1)
    
    # Create and run bot
    try:
        print("🚀 Creating bot...")
        bot = IcifiedBot(TELEGRAM_TOKEN, REPLICATE_TOKEN)
        print("✅ Bot created successfully!")
        print("🔥 Starting bot...")
        bot.run()
    except Exception as e:
        print(f"❌ Error creating/running bot: {e}")
        import traceback
        traceback.print_exc()
