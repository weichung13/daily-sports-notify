"""HTTP collection and deterministic normalization of FotMob match data."""
import json
import time
from datetime import datetime, time as day_time, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo('Asia/Taipei')
COMPETITIONS = json.loads(Path(__file__).with_name('competitions.json').read_text())
ENDPOINT = 'https://www.fotmob.com/api/data/matches'


def fetch_day(day):
    params = urlencode({'date': day.strftime('%Y%m%d'), 'timezone': 'Asia/Taipei',
                        'ccode3': 'TWN', 'includeNextDayLateNight': 'false'})
    request = Request(f'{ENDPOINT}?{params}', headers={
        'Accept': 'application/json', 'User-Agent': 'daily-sports-notify/1.0'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
            validate_payload(payload, day)
            return payload
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)


def validate_payload(payload, day):
    if (not isinstance(payload, dict)
            or payload.get('date') != day.strftime('%Y%m%d')
            or not isinstance(payload.get('leagues'), list)):
        raise ValueError(f'FotMob 回傳日期或資料結構異常：{day}')


def normalize(payloads, day, competitions=None):
    competitions = COMPETITIONS if competitions is None else competitions
    start = datetime.combine(day, day_time.min, TAIPEI)
    end = start + timedelta(days=1, hours=4)
    matches = {}
    for payload in payloads:
        for league in payload['leagues']:
            league_id = str(league.get('primaryId') or league['id'])
            if league_id not in competitions:
                continue
            for match in league['matches']:
                status = match['status']
                raw_time = status.get('utcTime')
                if not raw_time:
                    raise ValueError(f'FotMob 比賽 {match.get("id")} 缺少開賽時間')
                kickoff = datetime.fromisoformat(raw_time.replace('Z', '+00:00'))
                if kickoff.tzinfo is None:
                    raise ValueError('FotMob 開賽時間缺少時區')
                kickoff = kickoff.astimezone(TAIPEI)
                if not start <= kickoff <= end:
                    continue
                reason = status.get('reason') or {}
                if status.get('cancelled'):
                    label = '取消'
                elif 'postpon' in str(reason).lower():
                    label = '延期'
                elif status.get('finished'):
                    label = '已結束'
                elif status.get('started'):
                    label = '進行中'
                else:
                    label = reason.get('short', '')
                matches[str(match['id'])] = {
                    'id': str(match['id']), 'kickoff': kickoff,
                    'competition': competitions[league_id],
                    'home': match['home']['name'], 'away': match['away']['name'],
                    'status': label,
                }
    return sorted(matches.values(), key=lambda m: (m['kickoff'], m['id']))


def fetch_schedule(day):
    # Fetch both local dates; do not depend on FotMob's late-night cutoff.
    return normalize([fetch_day(day), fetch_day(day + timedelta(days=1))], day)


def format_schedule(day, matches):
    lines = [f'⚽ {day:%m月%d日} 足球賽程', '台灣時間（Asia/Taipei）', '主隊 vs 客隊']
    for offset in (0, 1):
        target = day + timedelta(days=offset)
        lines.append(f'\n【{target:%Y-%m-%d}' + (' 凌晨 00:00–04:00】' if offset else '】'))
        selected = [m for m in matches if m['kickoff'].date() == target]
        if not selected:
            lines.append('沒有比賽')
        for match in selected:
            suffix = f' [{match["status"]}]' if match['status'] else ''
            lines.append(f'• {match["kickoff"]:%H:%M} {match["home"]} vs '
                         f'{match["away"]}（{match["competition"]}）{suffix}')
    lines.append('\n資料來源：FotMob https://www.fotmob.com/')
    return '\n'.join(lines)
