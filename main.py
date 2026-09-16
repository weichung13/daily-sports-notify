"""Daily FotMob football schedule; preview by default, --send to notify LINE."""
import argparse
import json
import os
from datetime import date, datetime
from urllib.request import Request, urlopen

from fotmob import TAIPEI, fetch_schedule, format_schedule


def send_to_line(message):
    token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    user = os.environ.get('LINE_USER_ID')
    if not token or not user:
        raise ValueError('缺少 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID')
    chunks, chunk = [], ''
    for line in message.splitlines(keepends=True):
        if len(line) > 4500:
            raise ValueError('單行訊息過長')
        if len(chunk) + len(line) > 4500:
            chunks.append(chunk)
            chunk = ''
        chunk += line
    if chunk:
        chunks.append(chunk)
    for offset in range(0, len(chunks), 5):
        data = {'to': user, 'messages': [
            {'type': 'text', 'text': text} for text in chunks[offset:offset + 5]]}
        request = Request('https://api.line.me/v2/bot/message/push',
                          data=json.dumps(data).encode(), headers={
                              'Content-Type': 'application/json',
                              'Authorization': f'Bearer {token}'})
        with urlopen(request, timeout=30) as response:
            response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', type=date.fromisoformat,
                        default=datetime.now(TAIPEI).date())
    parser.add_argument('--send', action='store_true', help='發送 LINE（預設僅預覽）')
    args = parser.parse_args()
    message = format_schedule(args.date, fetch_schedule(args.date))
    print(message)
    if args.send:
        send_to_line(message)
        print('LINE 發送成功')


if __name__ == '__main__':
    main()
