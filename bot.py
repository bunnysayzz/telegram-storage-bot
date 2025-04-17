import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from dotenv import load_dotenv

import database as db
from healthcheck import run_health_server

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add console output for better debugging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Conversation states
CHOOSING_CATEGORY, CREATE_CATEGORY, WAITING_FOR_CATEGORY_NAME, CHOOSING_FILE, MAIN_MENU = range(5)

def set_bot_commands(updater):
    """Set the bot commands menu in Telegram."""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Open the main menu"),
        BotCommand("files", "Browse your stored files"),
        BotCommand("categories", "Manage your categories"),
        BotCommand("delete", "Delete a category"),
        BotCommand("help", "Show help information"),
    ]
    updater.bot.set_my_commands(commands)

def get_main_menu_keyboard():
    """Return the main menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📂 Browse Files", callback_data='menu_files'),
            InlineKeyboardButton("📁 Categories", callback_data='menu_categories')
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data='help'),
            InlineKeyboardButton("🗑 Delete Category", callback_data='menu_delete')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def start_command(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask for user's choice."""
    user = update.effective_user
    
    # Reset user data
    context.user_data.clear()
    
    welcome_message = (
        f"👋 Hello {user.first_name}! Welcome to your personal storage bot!\n\n"
        f"📚 *WHAT I CAN DO FOR YOU:*\n"
        f"• Store and organize your files in categories\n"
        f"• Retrieve your files whenever you need them\n"
        f"• Help you manage your file collection\n\n"
        f"🔧 *HOW TO USE ME:*\n"
        f"• Send me any file (documents, photos, videos, etc.)\n"
        f"• Use the menu buttons below to navigate\n"
        f"• Use /help to see detailed instructions\n\n"
        f"Ready to get started? Choose an option below or simply send me any file!"
    )
    
    update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

def show_menu(update: Update, context: CallbackContext) -> None:
    """Show the main menu."""
    query = update.callback_query
    
    # Handle both command and callback query
    if query:
        query.answer()
        query.edit_message_text(
            text="📱 *Main Menu*\n\nWhat would you like to do?",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    else:
        update.message.reply_text(
            text="📱 *Main Menu*\n\nWhat would you like to do?",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    return MAIN_MENU

def handle_menu_selection(update: Update, context: CallbackContext) -> int:
    """Handle menu button selection."""
    query = update.callback_query
    query.answer()
    
    action = query.data.replace('menu_', '')
    
    if action == 'files':
        return browse_files_from_query(update, context)
    elif action == 'categories':
        return show_categories_from_query(update, context)
    elif action == 'delete':
        return delete_categories_from_query(update, context)
    else:
        # Default action
        return MAIN_MENU

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        '📚 *STORAGE BOT HELP GUIDE*\n\n'
        '🤖 *ABOUT THIS BOT*\n'
        'This bot helps you store and organize files into categories so you can access them anytime.\n\n'
        
        '📋 *COMMANDS*\n'
        '• `/start` - Start the bot and see the welcome message\n'
        '• `/menu` - Open the main menu with all options\n'
        '• `/files` - Browse all your stored files by category\n'
        '• `/categories` - Manage your file categories\n'
        '• `/delete` - Delete unwanted categories\n'
        '• `/help` - Show this help information\n\n'
        
        '📁 *STORING FILES*\n'
        '1. Send any file (photo, video, document, audio) to the bot\n'
        '2. Select an existing category or create a new one\n'
        '3. The file will be stored in that category for later access\n'
        '4. You can send multiple files in sequence to the same category\n\n'
        
        '🔍 *BROWSING & RETRIEVING FILES*\n'
        '1. Use `/files` or the "Browse Files" button\n'
        '2. Select a category to view its files\n'
        '3. Files will be displayed in pages of 10 items\n'
        '4. Use the navigation buttons to move between pages\n'
        '5. Use the "Add Files" button to upload more files to the current category\n\n'
        
        '📊 *MANAGING CATEGORIES*\n'
        '• Create: Use "Create New Category" or send files to a new category\n'
        '• Browse: Use `/files` to see all your categories with file counts\n'
        '• Delete: Use `/delete` to remove unwanted categories\n\n'
        
        '⚠️ *IMPORTANT NOTES*\n'
        '• Files are securely stored on Telegram servers\n'
        '• There may be a short delay when first messaging the bot after inactivity\n'
        '• Send /start anytime to restart the conversation\n\n'
        
        'Need more help? Contact the developer @azharsayzz'
    )
    
    update.message.reply_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

def help_from_query(update: Update, context: CallbackContext) -> int:
    """Show help from a callback query."""
    query = update.callback_query
    
    help_text = (
        '📚 *STORAGE BOT HELP GUIDE*\n\n'
        '🤖 *ABOUT THIS BOT*\n'
        'This bot helps you store and organize files into categories so you can access them anytime.\n\n'
        
        '📋 *COMMANDS*\n'
        '• `/start` - Start the bot and see the welcome message\n'
        '• `/menu` - Open the main menu with all options\n'
        '• `/files` - Browse all your stored files by category\n'
        '• `/categories` - Manage your file categories\n'
        '• `/delete` - Delete unwanted categories\n'
        '• `/help` - Show this help information\n\n'
        
        '📁 *STORING FILES*\n'
        '1. Send any file (photo, video, document, audio) to the bot\n'
        '2. Select an existing category or create a new one\n'
        '3. The file will be stored in that category for later access\n'
        '4. You can send multiple files in sequence to the same category\n\n'
        
        '🔍 *BROWSING & RETRIEVING FILES*\n'
        '1. Use `/files` or the "Browse Files" button\n'
        '2. Select a category to view its files\n'
        '3. Files will be displayed in pages of 10 items\n'
        '4. Use the navigation buttons to move between pages\n'
        '5. Use the "Add Files" button to upload more files to the current category\n\n'
        
        '📊 *MANAGING CATEGORIES*\n'
        '• Create: Use "Create New Category" or send files to a new category\n'
        '• Browse: Use `/files` to see all your categories with file counts\n'
        '• Delete: Use `/delete` to remove unwanted categories\n\n'
        
        '⚠️ *IMPORTANT NOTES*\n'
        '• Files are securely stored on Telegram servers\n'
        '• There may be a short delay when first messaging the bot after inactivity\n'
        '• Send /start anytime to restart the conversation\n\n'
        
        'Need more help? Contact the developer @azharsayzz'
    )
    
    query.edit_message_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

def get_back_to_menu_button():
    """Get a keyboard with just a back button."""
    return InlineKeyboardMarkup([[InlineKeyboardButton("« Back to Menu", callback_data="back_to_menu")]])

def show_categories_from_query(update: Update, context: CallbackContext) -> int:
    """Show categories from a callback query."""
    query = update.callback_query
    user_id = update.effective_user.id
    categories = db.get_user_categories(user_id)
    
    buttons = []
    # Add existing categories
    for category in categories:
        buttons.append([InlineKeyboardButton(category, callback_data=f'category_{category}')])
    
    # Add option to create a new category
    buttons.append([InlineKeyboardButton("➕ Create New Category", callback_data='create_new_category')])
    
    # Add back button
    buttons.append([InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    query.edit_message_text(
        '📋 *Your Categories*\n\nSelect a category or create a new one:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return CHOOSING_CATEGORY

def show_categories(update: Update, context: CallbackContext) -> int:
    """Show the user's categories and option to create a new one."""
    user_id = update.effective_user.id
    categories = db.get_user_categories(user_id)
    
    buttons = []
    # Add existing categories
    for category in categories:
        buttons.append([InlineKeyboardButton(category, callback_data=f'category_{category}')])
    
    # Add option to create a new category
    buttons.append([InlineKeyboardButton("➕ Create New Category", callback_data='create_new_category')])
    
    # Add back button
    buttons.append([InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    update.message.reply_text(
        '📋 *Your Categories*\n\nSelect a category or create a new one:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return CHOOSING_CATEGORY

def handle_category_selection(update: Update, context: CallbackContext) -> int:
    """Handle category selection from inline keyboard."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'back_to_menu':
        return show_menu(update, context)
    
    if query.data == 'create_new_category':
        query.edit_message_text(
            text="✏️ *New Category*\n\nPlease send me the name for your new category:",
            parse_mode='Markdown',
            reply_markup=get_back_to_menu_button()
        )
        return WAITING_FOR_CATEGORY_NAME
    
    # User selected an existing category
    category_name = query.data.replace('category_', '')
    context.user_data['current_category'] = category_name
    
    query.edit_message_text(
        text=f"📁 *Category: {category_name}*\n\n"
             f"Send me files to add to this category, or use the buttons below.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📂 View Files", callback_data=f'browse_{category_name}')],
            [InlineKeyboardButton("✅ Done", callback_data='done')],
            [InlineKeyboardButton("« Back to Categories", callback_data='back_to_categories')]
        ])
    )
    return CHOOSING_FILE

def create_new_category(update: Update, context: CallbackContext) -> int:
    """Create a new category with the name provided by the user."""
    user_id = update.effective_user.id
    category_name = update.message.text.strip()
    
    # Create the new category
    db.create_category(user_id, category_name)
    
    update.message.reply_text(
        f"✅ Category '*{category_name}*' created successfully!\n\n"
        f"Send me files to add to this category, or use the buttons below.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Done", callback_data='done')],
            [InlineKeyboardButton("« Back to Categories", callback_data='back_to_categories')]
        ])
    )
    
    context.user_data['current_category'] = category_name
    return CHOOSING_FILE

def save_file(update: Update, context: CallbackContext) -> int:
    """Save a file to the selected category."""
    user_id = update.effective_user.id
    message = update.message
    
    # Check if we are in a category selection flow
    if 'current_category' in context.user_data:
        category = context.user_data['current_category']
    else:
        # If not in a flow, show categories to select from
        keyboard = []
        categories = db.get_user_categories(user_id)
        
        # Create inline keyboard with categories
        buttons = []
        for category in categories:
            buttons.append([InlineKeyboardButton(category, callback_data=f'category_{category}')])
        
        buttons.append([InlineKeyboardButton("➕ Create New Category", callback_data='create_new_category')])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        
        update.message.reply_text(
            '📂 *Store File*\n\nPlease select a category for this file:',
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
        
        # Save the message ID so we can forward it later
        context.user_data['pending_file_id'] = update.message.message_id
        context.user_data['pending_file_chat_id'] = update.message.chat.id
        return CHOOSING_CATEGORY
    
    # Forward the message to the channel
    channel_id = os.getenv("CHANNEL_ID")
    forwarded_msg = message.forward(chat_id=channel_id)
    
    # Determine the file type
    file_type = None
    file_name = None
    
    if message.photo:
        file_type = "photo"
    elif message.video:
        file_type = "video"
        if message.video.file_name:
            file_name = message.video.file_name
    elif message.document:
        file_type = "document"
        if message.document.file_name:
            file_name = message.document.file_name
    elif message.audio:
        file_type = "audio"
        if message.audio.file_name:
            file_name = message.audio.file_name
    elif message.voice:
        file_type = "voice"
    elif message.animation:
        file_type = "animation"
        if message.animation.file_name:
            file_name = message.animation.file_name
    else:
        file_type = "unknown"
    
    # Save file info to the database
    db.add_file_to_category(
        user_id=user_id,
        category=category,
        message_id=forwarded_msg.message_id,
        file_type=file_type,
        file_name=file_name
    )
    
    # Track number of files uploaded in this session
    if 'files_uploaded' not in context.user_data:
        context.user_data['files_uploaded'] = 0
    context.user_data['files_uploaded'] += 1
    
    # Update existing confirmation message if it exists, otherwise send a new one
    confirmation_text = f"✅ *{context.user_data['files_uploaded']} file(s) saved* to category '*{category}*'!\n\n"
    confirmation_text += f"Send more files or use the buttons below."
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Done", callback_data='done')],
        [InlineKeyboardButton("« Back to Categories", callback_data='back_to_categories')]
    ])
    
    if 'last_confirmation_message_id' in context.user_data and context.user_data['last_confirmation_message_id']:
        try:
            # Try to edit the existing confirmation message
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=context.user_data['last_confirmation_message_id'],
                text=confirmation_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            return CHOOSING_FILE
        except Exception as e:
            logger.error(f"Error updating confirmation message: {e}")
            # If editing fails, we'll send a new message below
    
    # Send a new confirmation message and track its ID
    sent_message = update.message.reply_text(
        confirmation_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )
    context.user_data['last_confirmation_message_id'] = sent_message.message_id
    
    return CHOOSING_FILE

def handle_file_menu(update: Update, context: CallbackContext) -> int:
    """Handle menu actions in file selection mode."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'done':
        if 'current_category' in context.user_data:
            del context.user_data['current_category']
        
        # Reset file upload counter
        if 'files_uploaded' in context.user_data:
            del context.user_data['files_uploaded']
        
        # Clear last confirmation message ID
        if 'last_confirmation_message_id' in context.user_data:
            del context.user_data['last_confirmation_message_id']
        
        query.edit_message_text(
            "✅ *Done!*\n\nWhat would you like to do next?",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif query.data == 'back_to_categories':
        # Remove current category
        if 'current_category' in context.user_data:
            del context.user_data['current_category']
        
        # Reset file upload counter
        if 'files_uploaded' in context.user_data:
            del context.user_data['files_uploaded']
        
        # Clear last confirmation message ID
        if 'last_confirmation_message_id' in context.user_data:
            del context.user_data['last_confirmation_message_id']
        
        # Show categories
        return show_categories_from_query(update, context)
    
    # Handle "Back to Browse" button
    elif query.data.startswith('browse_'):
        category_name = query.data.replace('browse_', '')
        
        # Reset file upload counter
        if 'files_uploaded' in context.user_data:
            del context.user_data['files_uploaded']
        
        # Clear last confirmation message ID
        if 'last_confirmation_message_id' in context.user_data:
            del context.user_data['last_confirmation_message_id']
        
        # Go back to browsing the category
        return handle_browse_selection(update, context)
    
    return CHOOSING_FILE

def done(update: Update, context: CallbackContext) -> int:
    """Exit the conversation."""
    if 'current_category' in context.user_data:
        del context.user_data['current_category']
    
    # Reset file upload counter
    if 'files_uploaded' in context.user_data:
        del context.user_data['files_uploaded']
    
    # Clear last confirmation message ID
    if 'last_confirmation_message_id' in context.user_data:
        del context.user_data['last_confirmation_message_id']
    
    update.message.reply_text(
        "✅ *Done!*\n\nWhat would you like to do next?",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

def browse_files_from_query(update: Update, context: CallbackContext) -> int:
    """Browse files by category from a callback query."""
    query = update.callback_query
    user_id = update.effective_user.id
    categories = db.get_user_categories(user_id)
    
    if not categories:
        # If no categories exist, suggest creating one
        query.edit_message_text(
            "📂 *Browse Files*\n\nYou don't have any categories yet. Would you like to create one?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Create New Category", callback_data='create_new_category')],
                [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
            ])
        )
        return CHOOSING_CATEGORY
    
    buttons = []
    for category in categories:
        # Get file count for this category
        files = db.get_files_in_category(user_id, category)
        file_count = len(files)
        buttons.append([InlineKeyboardButton(f"{category} ({file_count})", callback_data=f'browse_{category}')])
    
    # Add option to create a new category
    buttons.append([InlineKeyboardButton("➕ Create New Category", callback_data='create_new_category')])
    
    # Add back button
    buttons.append([InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    query.edit_message_text(
        '📂 *Browse Files*\n\nSelect a category to view files:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

def browse_files(update: Update, context: CallbackContext) -> None:
    """Browse files by category."""
    user_id = update.effective_user.id
    categories = db.get_user_categories(user_id)
    
    if not categories:
        # If no categories exist, suggest creating one
        update.message.reply_text(
            "📂 *Browse Files*\n\nYou don't have any categories yet. Would you like to create one?",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Create New Category", callback_data='create_new_category')],
                [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
            ])
        )
        return CHOOSING_CATEGORY
    
    buttons = []
    for category in categories:
        # Get file count for this category
        files = db.get_files_in_category(user_id, category)
        file_count = len(files)
        buttons.append([InlineKeyboardButton(f"{category} ({file_count})", callback_data=f'browse_{category}')])
    
    # Add option to create a new category
    buttons.append([InlineKeyboardButton("➕ Create New Category", callback_data='create_new_category')])
    
    # Add back button
    buttons.append([InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    update.message.reply_text(
        '📂 *Browse Files*\n\nSelect a category to view files:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

def handle_browse_selection(update: Update, context: CallbackContext) -> None:
    """Handle browse category selection from inline keyboard."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'back_to_menu':
        return show_menu(update, context)
    
    # Check if this is an add files action
    if query.data.startswith('add_files_'):
        category_name = query.data.replace('add_files_', '')
        return handle_add_files_to_category(update, context, category_name)
    
    # Check if this is a pagination request
    if query.data.startswith('page_'):
        # Extract category name and page number
        _, category_name, page = query.data.split('_')
        page = int(page)
        show_files_page(update, context, category_name, page)
        return
    
    category_name = query.data.replace('browse_', '')
    show_files_page(update, context, category_name, 1)  # Start with page 1

def handle_add_files_to_category(update: Update, context: CallbackContext, category_name: str) -> int:
    """Handle adding files to a specific category."""
    query = update.callback_query
    
    # Set current category in context for file uploads
    context.user_data['current_category'] = category_name
    
    query.edit_message_text(
        text=f"📂 *Adding Files to: {category_name}*\n\n"
             f"Send me files to add to this category. They will be automatically saved to '{category_name}'.\n\n"
             f"You can send multiple files in sequence.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Done", callback_data='done')],
            [InlineKeyboardButton("« Back to Browse", callback_data=f'browse_{category_name}')]
        ])
    )
    return CHOOSING_FILE

def show_files_page(update: Update, context: CallbackContext, category_name: str, page: int) -> None:
    """Show files for a specific page of a category."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get files with pagination
    files, total_pages, total_files = db.get_files_in_category_paginated(
        user_id, category_name, page, page_size=10
    )
    
    if not files:
        query.edit_message_text(
            text=f"📂 *Category: {category_name}*\n\nNo files in this category.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add Files", callback_data=f'add_files_{category_name}')],
                [InlineKeyboardButton("« Back to Categories", callback_data='menu_files')],
                [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
            ])
        )
        return
    
    # Create pagination navigation buttons
    nav_buttons = []
    
    # Add page navigation if more than one page
    if total_pages > 1:
        pag_buttons = []
        if page > 1:
            pag_buttons.append(InlineKeyboardButton("« Prev", callback_data=f'page_{category_name}_{page-1}'))
        
        pag_buttons.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data=f'ignore'))
        
        if page < total_pages:
            pag_buttons.append(InlineKeyboardButton("Next »", callback_data=f'page_{category_name}_{page+1}'))
        
        nav_buttons.append(pag_buttons)
    
    # Add "Add Files" button
    nav_buttons.append([InlineKeyboardButton("➕ Add Files", callback_data=f'add_files_{category_name}')])
    
    # Add back buttons
    nav_buttons.append([InlineKeyboardButton("« Back to Categories", callback_data='menu_files')])
    nav_buttons.append([InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')])
    
    # Display page information
    start_idx = (page - 1) * 10 + 1
    page_info = f"📂 *Category: {category_name}*\n\n"
    page_info += f"Showing files {start_idx}-{start_idx + len(files) - 1} of {total_files}\n"
    page_info += f"Page {page} of {total_pages}\n\n"
    page_info += "Sending files...\n"
    
    query.edit_message_text(
        text=page_info,
        parse_mode='Markdown'
    )
    
    # Copy each file from the channel to the user with numbering
    channel_id = os.getenv("CHANNEL_ID")
    
    for i, file_info in enumerate(files):
        try:
            # Create a caption with the file number
            file_number = start_idx + i
            file_caption = f"File #{file_number} of {total_files}"
            
            # Add filename if available
            if "file_name" in file_info:
                file_caption += f"\nFilename: {file_info['file_name']}"
            
            # Use copy_message with caption instead of forward_message
            context.bot.copy_message(
                chat_id=update.effective_user.id,
                from_chat_id=channel_id,
                message_id=file_info["message_id"],
                caption=file_caption
            )
        except Exception as e:
            logger.error(f"Error copying message: {e}")
            context.bot.send_message(
                chat_id=update.effective_user.id,
                text=f"Error retrieving file #{start_idx + i}: {e}"
            )
    
    # Send a follow-up message with navigation buttons
    context.bot.send_message(
        chat_id=update.effective_user.id,
        text=f"✅ Showing files {start_idx}-{start_idx + len(files) - 1} of {total_files} from *{category_name}*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(nav_buttons)
    )

def delete_category_command(update: Update, context: CallbackContext) -> None:
    """Show categories to delete from the /delete command."""
    user_id = update.effective_user.id
    categories = db.get_user_categories(user_id)
    
    if not categories:
        update.message.reply_text(
            "🗑 *Delete Category*\n\nYou don't have any categories to delete.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    buttons = []
    for category in categories:
        buttons.append([InlineKeyboardButton(category, callback_data=f'delete_{category}')])
    
    # Add back button
    buttons.append([InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    update.message.reply_text(
        '🗑 *Delete Category*\n\nSelect a category to delete:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def delete_categories_from_query(update: Update, context: CallbackContext) -> int:
    """Show delete categories screen from a query callback."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get all categories for this user
    categories = db.get_user_categories(user_id)
    
    if not categories:
        query.edit_message_text(
            "🗑 *Delete Category*\n\nYou don't have any categories to delete.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    buttons = []
    for category in categories:
        buttons.append([InlineKeyboardButton(category, callback_data=f'delete_{category}')])
    
    # Add back button
    buttons.append([InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    query.edit_message_text(
        '🗑 *Delete Category*\n\nSelect a category to delete:',
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return MAIN_MENU

def handle_delete_selection(update: Update, context: CallbackContext) -> None:
    """Handle delete category selection."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'back_to_menu':
        return show_menu(update, context)
    
    category_name = query.data.replace('delete_', '')
    user_id = update.effective_user.id
    
    # Delete the category
    success = db.delete_category(user_id, category_name)
    
    if success:
        query.edit_message_text(
            text=f"✅ Category '*{category_name}*' has been deleted.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
            ])
        )
    else:
        query.edit_message_text(
            text=f"❌ Failed to delete category '*{category_name}*'.",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("« Back to Menu", callback_data='back_to_menu')]
            ])
        )

def handle_text_input(update: Update, context: CallbackContext) -> None:
    """Handle text input that's not part of a conversation."""
    # Show the menu as fallback
    show_menu(update, context)

def handle_pending_file(update: Update, context: CallbackContext) -> int:
    """Handle the pending file after category selection."""
    if 'pending_file_id' in context.user_data and 'pending_file_chat_id' in context.user_data:
        # Try to forward the pending file from its original message
        file_id = context.user_data['pending_file_id']
        chat_id = context.user_data['pending_file_chat_id']
        
        try:
            # First, let the user know we're processing their file
            update.callback_query.edit_message_text(
                f"Processing your file to category '{context.user_data['current_category']}'..."
            )
            
            # Then ask them to send the file again
            context.bot.send_message(
                chat_id=chat_id,
                text=f"Please send the file again to save it to category '{context.user_data['current_category']}'."
            )
            
            # Clean up the pending file data
            del context.user_data['pending_file_id']
            del context.user_data['pending_file_chat_id']
            
            return CHOOSING_FILE
        except Exception as e:
            logger.error(f"Error handling pending file: {e}")
            context.bot.send_message(
                chat_id=chat_id,
                text="There was an error processing your file. Please send it again."
            )
    
    return CHOOSING_FILE

def main() -> None:
    """Start the bot."""
    # Initialize the database
    db.init_db()
    
    # Print environment variables for debugging (masking sensitive values)
    logger.info(f"Environment variables:")
    logger.info(f"IS_DOCKER: {os.environ.get('IS_DOCKER')}")
    logger.info(f"RENDER: {os.environ.get('RENDER')}")
    logger.info(f"PORT: {os.environ.get('PORT')}")
    logger.info(f"HEALTH_PORT: {os.environ.get('HEALTH_PORT')}")
    logger.info(f"RENDER_EXTERNAL_URL: {os.environ.get('RENDER_EXTERNAL_URL')}")
    logger.info(f"BOT_TOKEN set: {'Yes' if os.environ.get('BOT_TOKEN') else 'No'}")
    logger.info(f"CHANNEL_ID set: {'Yes' if os.environ.get('CHANNEL_ID') else 'No'}")
    
    # Start health check server if running in Docker/Render
    if os.environ.get('IS_DOCKER') == 'true' or os.environ.get('RENDER') == 'true':
        run_health_server()
        logger.info("Health check server started")
    
    # Create the Updater and pass it your bot's token
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("No BOT_TOKEN environment variable found! Exiting...")
        return
    
    updater = Updater(bot_token)
    
    # Log bot information
    try:
        bot_info = updater.bot.get_me()
        logger.info(f"Bot connected successfully: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"Failed to get bot information: {e}")
        logger.error("Please check your BOT_TOKEN")
        return
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Set up the commands menu
    try:
        set_bot_commands(updater)
        logger.info("Bot commands set successfully")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {e}")
    
    # Basic commands
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("menu", show_menu))
    
    # File browsing
    dispatcher.add_handler(CommandHandler("files", browse_files))
    
    # Category deletion
    dispatcher.add_handler(CommandHandler("delete", delete_category_command))
    
    # Conversation handler for categories and file storage
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("categories", show_categories),
            CommandHandler("menu", show_menu),
            CommandHandler("files", browse_files),
            CallbackQueryHandler(show_menu, pattern='^back_to_menu$'),
            CallbackQueryHandler(help_from_query, pattern='^help$'),
            CallbackQueryHandler(handle_menu_selection, pattern='^menu_'),
            CallbackQueryHandler(handle_browse_selection, pattern='^browse_'),
            CallbackQueryHandler(handle_browse_selection, pattern='^add_files_'),
            CallbackQueryHandler(handle_browse_selection, pattern='^page_'),
            CallbackQueryHandler(handle_delete_selection, pattern='^delete_'),
            MessageHandler(
                Filters.photo | Filters.video | Filters.document | 
                Filters.audio | Filters.voice | Filters.animation,
                save_file
            ),
        ],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(help_from_query, pattern='^help$'),
                CallbackQueryHandler(handle_menu_selection, pattern='^menu_'),
                CallbackQueryHandler(handle_browse_selection, pattern='^browse_'),
                CallbackQueryHandler(handle_browse_selection, pattern='^add_files_'),
                CallbackQueryHandler(handle_browse_selection, pattern='^page_'),
                CallbackQueryHandler(handle_delete_selection, pattern='^delete_'),
            ],
            CHOOSING_CATEGORY: [
                CallbackQueryHandler(handle_category_selection),
            ],
            WAITING_FOR_CATEGORY_NAME: [
                MessageHandler(Filters.text & ~Filters.command, create_new_category),
                CallbackQueryHandler(show_menu, pattern='^back_to_menu$'),
            ],
            CHOOSING_FILE: [
                CommandHandler("done", done),
                CallbackQueryHandler(handle_file_menu),
                MessageHandler(
                    Filters.photo | Filters.video | Filters.document | 
                    Filters.audio | Filters.voice | Filters.animation,
                    save_file
                ),
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("help", help_command),
            CommandHandler("menu", show_menu),
            MessageHandler(Filters.text & ~Filters.command, handle_text_input),
        ],
        allow_reentry=True,
    )
    
    dispatcher.add_handler(conv_handler)
    
    # Delete webhook before starting the bot
    try:
        updater.bot.delete_webhook()
        logger.info("Deleted existing webhook")
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
    
    # Check if we're running on Render
    if os.environ.get('RENDER') == 'true':
        # Get the Render URL from environment
        PORT = int(os.environ.get('PORT', 10000))
        RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')
        
        if RENDER_URL:
            try:
                # Set webhook with proper path
                webhook_url = f"{RENDER_URL}/telegram"
                logger.info(f"Attempting to set webhook to {webhook_url}")
                
                # Set the webhook with more detailed error messages
                webhook_result = updater.bot.set_webhook(url=webhook_url)
                
                if webhook_result:
                    logger.info(f"Successfully set webhook to {webhook_url}")
                    
                    # Verify webhook was set
                    webhook_info = updater.bot.get_webhook_info()
                    logger.info(f"Webhook verification - URL: {webhook_info.url}, Pending updates: {webhook_info.pending_update_count}")
                    
                    # Start webhook server
                    updater.start_webhook(
                        listen="0.0.0.0",
                        port=PORT,
                        url_path="telegram",
                        webhook_url=webhook_url
                    )
                    logger.info(f"Webhook server started on port {PORT}")
                else:
                    raise Exception("Webhook returned False")
                    
            except Exception as e:
                logger.error(f"Failed to set up webhook: {e}")
                # Fallback to polling if webhook setup fails
                logger.info("Falling back to polling mode due to webhook setup failure")
                updater.start_polling()
                logger.info("Polling mode started")
        else:
            # Fallback to polling if RENDER_EXTERNAL_URL is not available
            logger.warning("RENDER_EXTERNAL_URL not found, falling back to polling")
            updater.start_polling()
            logger.info("Polling mode started")
    else:
        # Start the Bot in polling mode
        updater.start_polling()
        logger.info("Bot started successfully in polling mode")
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main() 