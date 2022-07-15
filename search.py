import argparse
import datetime
import telethon

from configparser import ConfigParser
from telethon import TelegramClient


config = ConfigParser()
config.read('config.ini')

api_id = config['DEFAULT']['api_id']
api_hash = config['DEFAULT']['api_hash']
session_name = config['DEFAULT']['session_name']
client = TelegramClient(session_name, api_id, api_hash)


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

    args = parser.parse_args()

    return args


async def main():
    args = get_args()

    dialogs = await client.get_dialogs(
        limit=None,
    )

    for dialog in dialogs:
        entity = dialog.entity

        if dialog.is_channel:
            if args.skip_channel:
                continue
        elif dialog.is_group:
            if args.skip_group:
                continue
        else:
            if args.skip_user:
                continue

        messages = await client.get_messages(
            entity,
            limit=50,
            offset_date=None,     # Offset date (messages previous to this date will be retrieved).
                                  # If None, from newest message. Exclusive.
            offset_id=0,          # Offset message ID (only messages previous to the given ID will be retrieved). Exclusive.
        )

        for message in messages:
            if not isinstance(message, telethon.tl.patched.Message):
                continue

            if args.search_text in message.message:
                print(dialog.title, message.date)
                print(message.message)

            if isinstance(message.media, telethon.tl.types.MessageMediaWebPage):
                webpage = message.media.webpage

                if isinstance(webpage, telethon.tl.types.WebPageEmpty):
                    continue

                if webpage.title and args.search_text in webpage.title \
                   or webpage.description and args.search_text in webpage.description:
                    print(dialog.title, message.date)
                    print(message.message)


client.start()
client.loop.run_until_complete(main())
