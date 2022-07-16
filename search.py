import argparse
import datetime
import logging
import telethon

from configparser import ConfigParser
from telethon import TelegramClient
from time import sleep
from tqdm import tqdm


config = ConfigParser()
config.read('config.ini')

api_id = config['DEFAULT']['api_id']
api_hash = config['DEFAULT']['api_hash']
session_name = config['DEFAULT']['session_name']
client = TelegramClient(session_name, api_id, api_hash)


logging.basicConfig(filename='search.log',
                    filemode='w',
                    format='%(message)s',
                    level=logging.INFO)

logger = logging.getLogger()


def get_args():
    parser = argparse.ArgumentParser(description='Settings.')

    parser.add_argument('--search_text',
                        default='', type=str,
                        help='Text to be searched in current account')
    parser.add_argument('--skip_channel',
                        default=False, type=bool,
                        help='Whether to skip channel when search')
    parser.add_argument('--skip_chat',
                        default=False, type=bool,
                        help='Whether to skip group when search')
    parser.add_argument('--skip_user',
                        default=False, type=bool,
                        help='Whether to skip user and bot when search')

    parser.add_argument('--message_limit_channel',
                        default=50, type=int,
                        help='Number of messages to be retrieved for channel.')
    parser.add_argument('--message_limit_group',
                        default=50, type=int,
                        help='Number of messages to be retrieved for group.')
    parser.add_argument('--message_limit_user',
                        default=50, type=int,
                        help='Number of messages to be retrieved for user and bot.')

    args = parser.parse_args()

    return args


async def main():
    args = get_args()

    dialogs = await client.get_dialogs(
        limit=None,
    )
    dialogs_bar = tqdm(dialogs, bar_format='{desc} ({n_fmt}/{total_fmt})')

    for dialog in dialogs_bar:
        dialogs_bar.set_description_str(f'Searching in dialog: {dialog.name}')
        entity = dialog.entity

        if dialog.is_channel:
            limit = args.message_limit_channel
            if args.skip_channel:
                continue
        elif dialog.is_group:
            limit = args.message_limit_group
            if args.skip_group:
                continue
        else:
            limit = args.message_limit_user
            if args.skip_user:
                continue

        messages = await client.get_messages(
            entity,
            limit=limit,
            offset_date=None,     # Offset date (messages previous to this date will be retrieved).
                                  # If None, from newest message. Exclusive.
            offset_id=0,          # Offset message ID (only messages previous to the given ID will be retrieved). Exclusive.
        )
        messages_bar = tqdm(messages, desc='Progress in dialog', leave=False)

        for message in messages_bar:
            if not isinstance(message, telethon.tl.patched.Message):
                continue

            if args.search_text in message.message:
                logger.info(dialog.title + ' ' + message.date.strftime('%Y-%m-%d %H:%M:%S') )
                logger.info(message.message + '\n')

            if isinstance(message.media, telethon.tl.types.MessageMediaWebPage):
                webpage = message.media.webpage

                if isinstance(webpage, telethon.tl.types.WebPageEmpty):
                    continue

                if webpage.title and args.search_text in webpage.title \
                   or webpage.description and args.search_text in webpage.description:
                    logger.info(dialog.title + ' ' + message.date.strftime('%Y-%m-%d %H:%M:%S') )
                    logger.info(message.message + '\n')

            messages_bar.update(1)
            sleep(0.005)

client.start()
client.loop.run_until_complete(main())
