import dataclasses
import typing

import aiohttp
import io
import discord


NEWS_ENDPOINT = 'https://cms.zaonce.net/ru-RU/jsonapi/node/galnet_article?sort%5Bsort-published%5D%5Bpath%5D=published_at&sort%5Bsort-published%5D%5Bdirection%5D=DESC&page%5Blimit%5D={limit}'  # noqa
BASE_PICTURES = 'https://hosting.zaonce.net/elite-dangerous/galnet/{picture}.png'

FIRST_SECTION_TEMPLATE = """⠀
```fix
{title}
{date}
``````
{body}
```""".strip()

FOLLOWING_SECTION_TEMPLATE = """
```
{body}
```""".strip()


@dataclasses.dataclass
class OneNews:
    title: str
    news_body: str  # original body
    galnet_guid: str
    galnet_date: str
    picture_name: str
    published_at: str
    picture: discord.File = None
    body: str = dataclasses.field(init=False)  # body after replace('\n', '\n\n')

    def __post_init__(self):
        self.galnet_date = russify_date(self.galnet_date)
        self.body = self.news_body.replace('\r\n', '\n')\
            .replace('\n\n', '\n')\
            .replace('\n', '\n\n')
        # .replace('\n\n', '\n') required for normalization, see, for example, 'HIP 22460 получает жизненно важные ресурсы' 07 JUL 3308

    def plain_text_len(self) -> int:
        return len(self.title) + len(self.galnet_date) + len(self.body) + \
               len(FIRST_SECTION_TEMPLATE.format(title='', date='', body=''))

    async def download_picture(self):
        self.picture = await get_picture(self.picture_name)


async def get_news(limit: int = 10) -> list[OneNews]:
    news: list[OneNews] = list()
    async with aiohttp.ClientSession() as session:
        async with session.get(NEWS_ENDPOINT.format(limit=limit)) as response:
            for dict_news in (await response.json())['data']:
                attributes: dict = dict_news['attributes']
                news.append(
                    OneNews(
                        title=attributes['title'],
                        news_body=attributes['body']['value'],
                        galnet_guid=attributes['field_galnet_guid'],
                        galnet_date=attributes['field_galnet_date'],
                        picture_name=attributes['field_galnet_image'],
                        published_at=attributes['published_at']
                    )
                )

            return news


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


async def format_news(one_news: OneNews) -> typing.Iterable[dict[str, str | discord.File]]:
    """Returns iterable of arguments for channel.send() coro"""

    await one_news.download_picture()

    if one_news.plain_text_len() < 2000:  # Simple case
        msg = FIRST_SECTION_TEMPLATE.format(title=one_news.title, date=one_news.galnet_date, body=one_news.body)
        return {'content': msg, 'file': one_news.picture},

    # And complicated case with message splitting up to 2 parts
    result: list[dict[str, str | discord.File]] = []
    body_splited = one_news.body.splitlines(keepends=True)
    header_part = FIRST_SECTION_TEMPLATE.format(title=one_news.title, date=one_news.galnet_date, body='{body}')
    header_body = str()
    i = 0
    for part in body_splited:
        if len(header_part + part + header_body) < 2000:
            i += 1
            header_body += part

        else:
            break

    header_part = header_part.format(body=header_body)
    result.append({'content': header_part})
    body_splited = body_splited[i:]

    if len(FOLLOWING_SECTION_TEMPLATE.format(body=''.join(body_splited))) < 2000:
        last_part = FOLLOWING_SECTION_TEMPLATE.format(body=''.join(body_splited))
        result.append({'content': last_part, 'file': one_news.picture})
        return result

    # And more complicated case with >3 parts, TODO: test it
    i = 0
    following_part_body = ''
    for following_part in body_splited:
        if len(following_part + following_part_body + FOLLOWING_SECTION_TEMPLATE.format(body='')) <= 2000:
            following_part_body += following_part
            i += 1

        else:
            following_msg = FOLLOWING_SECTION_TEMPLATE.format(body=following_part_body)
            result.append({'content': following_msg})
            i = 0
            following_part_body = ''

    result[-1]['file'] = one_news.picture
    return result
