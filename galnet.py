import aiohttp
import io
import discord


NEWS_ENDPOINT = 'https://cms.zaonce.net/ru-RU/jsonapi/node/galnet_article?sort%5Bsort-published%5D%5Bpath%5D=published_at&sort%5Bsort-published%5D%5Bdirection%5D=DESC&page%5Blimit%5D={limit}'  # noqa
BASE_PICTURES = 'https://hosting.zaonce.net/elite-dangerous/galnet/{picture}.png'


async def get_news(limit: int = 10) -> list[dict]:
    async with aiohttp.ClientSession() as session:
        async with session.get(NEWS_ENDPOINT.format(limit=limit)) as response:
            return (await response.json())['data']


async def get_picture(name: str) -> discord.File:
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_PICTURES.format(picture=name)) as response:
            pic = io.BytesIO(await response.read())
            return discord.File(pic, filename=f'{name}.png')


def russify_date(galnet_date: str) -> str:
    galnet_date_splited = galnet_date.split(' ')
    month = galnet_date_splited[1]
    months_dict = {
        'JAN': 'Янв',
        'FEB': 'Фев',
        'MAR': 'Мар',
        'APR': 'Апр',
        'MAY': 'Май',
        'JUN': 'Июн',
        'JUL': 'Июл',
        'AUG': 'Авг',
        'SEP': 'Сен',
        'OCT': 'Окт',
        'NOV': 'Ноя',
        'DEC': 'Дек'
    }

    russified_month = months_dict.get(month, month)
    galnet_date_splited[1] = russified_month
    return ' '.join(galnet_date_splited)
