# Telegram Storage Bot

A Telegram bot that allows users to store and organize files, media, and documents into categories, and access them anytime.

**Try it now: [@Commit](https://t.me/Commit)**

## Features

- Store any type of file (photos, videos, documents, audio, voice messages, animations)
- Organize files into custom categories
- Browse and retrieve files by category
- Create and delete categories

## Setup

### Prerequisites

- Python 3.7 or higher
- A Telegram Bot Token (created via @BotFather)
- A private Telegram channel where the bot is an admin

### Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/telegram-storage-bot.git
cd telegram-storage-bot
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Configure your environment variables for:
   - `BOT_TOKEN`: Get from @BotFather
   - `CHANNEL_ID`: ID of your private channel (usually starts with -100)
   - `CHANNEL_FIRST_MESSAGE_ID`: ID of the first message in your channel (usually 2)

4. Run the bot:
```bash
python bot.py
```

## Docker Deployment

### Running with Docker

1. Make sure you have Docker installed on your system.

2. Build the Docker image:
```bash
docker build -t telegram-storage-bot .
```

3. Create a data directory for persistent storage:
```bash
mkdir -p data
```

4. Run the container:
```bash
docker run -d --name telegram-bot \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --restart unless-stopped \
  telegram-storage-bot
```

### Using Docker Compose

1. Simply run:
```bash
docker-compose up -d
```

## Deploying to Render

### Option 1: Deploy via Dashboard

1. Create a new Web Service on Render.

2. Connect your GitHub repository.

3. Choose "Docker" as the environment.

4. Configure the following environment variables in the Render dashboard:
   - `BOT_TOKEN=your_bot_token`
   - `CHANNEL_ID=your_channel_id`
   - `CHANNEL_FIRST_MESSAGE_ID=2`

5. Set these additional options:
   - Set the port to `10000`
   - Enable disk persistence with at least 1GB mounted at `/app/data`

6. Deploy the service.

### Option 2: Deploy via render.yaml

1. Push your code to a GitHub repository.

2. Add your environment variables to the `render.yaml` file (uncomment and fill in the values).

3. Go to the Render dashboard and choose "Blueprint" deployment.

4. Connect your repository and Render will automatically configure the service.

### Important Notes for Render

- The bot will automatically run in webhook mode when deployed on Render, making it more responsive.
- The bot includes a health check server on port 8080 that Render uses to determine if the service is running.
- Make sure to use disk persistence for the `/app/data` directory to maintain your database between deployments.
- The free tier of Render spins down after periods of inactivity, which may affect your bot's response time.

## Usage

After starting the bot with `/start`, you can interact with it using the following commands:

### Available Commands

- `/start` - Initialize the bot and see the welcome message
- `/menu` - Open the main menu with all available options
- `/files` - Browse your stored files by category
- `/categories` - Manage your file categories
- `/delete` - Delete unwanted categories
- `/help` - Show detailed help information

### Storing Files

1. **Direct Method**:
   - Simply send any file (photo, video, document, audio, voice message, animation) to the bot
   - Choose a category from the list or create a new one
   - The file will be stored in the selected category

2. **From Categories Menu**:
   - Use `/categories` command
   - Select an existing category or create a new one
   - Send files to add them to the category
   - Click "Done" when finished

3. **From Browsing Interface**:
   - While browsing files, use the "Add Files" button
   - Send files to add them to the current category
   - Click "Done" when finished or "Back to Browse" to return to viewing files

### Browsing and Retrieving Files

1. Use the `/files` command or the "Browse Files" button in the main menu
2. Select a category to view its files
3. The bot will display files in pages of 10 items with:
   - File number and name
   - Navigation controls (Previous/Next page)
   - "Add Files" button to add more files to the current category
4. Use the pagination controls to navigate between pages if you have more than 10 files

### Managing Categories

- **Creating Categories**:
  - Use "Create New Category" option in the categories menu
  - Enter a name for your new category
  - Or, send a file and select "Create New Category" when prompted

- **Browsing Categories**:
  - Use `/files` command to see all categories with file counts
  - Select a category to view its contents

- **Deleting Categories**:
  - Use `/delete` command
  - Select the category you want to delete
  - Confirmation will be shown when deleted successfully

### Session Management

- Use the "Done" button to complete the current operation and return to the main menu
- Use "Back" buttons to navigate to previous screens
- Send `/start` at any time to reset the conversation

### Important Notes

- Files are securely stored on Telegram servers
- The bot uses inline buttons for navigation, making it easy to use
- When deployed on Render's free tier, the bot may experience a slight delay (30-60 seconds) when receiving the first message after a period of inactivity
- Subsequent messages will be processed quickly once the service is running

## License

MIT 