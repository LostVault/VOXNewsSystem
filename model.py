import sqlite3


SCHEMA = """
create table if not exists galnet_ru (
    galnet_guid text,
    galnet_date text,
    news_body text,
    title text,
    published_at text,
    picture_name text,
    inserted default current_timestamp
);"""

CHECK_NEWS_QUERY = """
select count(*) as count
from galnet_ru
where galnet_guid = ?;"""

INSERT_ONE_NEWS_QUERY = """
insert into galnet_ru (galnet_guid, galnet_date, news_body, title, picture_name, published_at)
values (:galnet_guid, :galnet_date, :news_body, :title, :picture_name, :published_at);"""


class Model:
    def __init__(self):
        self.db = sqlite3.connect('galnet_ru.sqlite')
        self.db.execute(SCHEMA)
        self.db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    def check_news(self, galnet_guid: str) -> bool:
        """Check if we have news with specified galnet_guid in DB, returns True if have, False if haven't

        :param galnet_guid: galnet guid to check
        :return:
        """

        with self.db:
            sql_result = self.db.execute(CHECK_NEWS_QUERY, (galnet_guid,)).fetchone()['count']
            if sql_result == 0:
                return False

            else:
                return True

    def save_news(self, one_news: dict) -> None:
        """Takes one news and save it to DB

        :param one_news: data[<int>] from api response
        :return:
        """
        attributes: dict = one_news['attributes']

        if self.check_news(attributes['field_galnet_guid']):  # don't save news if we already saved it
            return

        news_to_insert: dict = {
            'title': attributes['title'],
            'news_body': attributes['body']['value'],
            'galnet_guid': attributes['field_galnet_guid'],
            'galnet_date': attributes['field_galnet_date'],
            'picture_name': attributes['field_galnet_image'],
            'published_at': attributes['published_at']
        }

        with self.db:
            self.db.execute(INSERT_ONE_NEWS_QUERY, news_to_insert)


model = Model()
