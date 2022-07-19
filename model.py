import sqlite3
import os
from dataclasses import asdict
import galnet


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
        self.db = sqlite3.connect(os.environ['VOX_SQLITE_PATH'])
        self.db.execute(SCHEMA)
        self.db.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))

    def check_news(self, news_to_check: galnet.OneNews) -> bool:
        """Check if we have specified news in DB, returns True if we have, False if we don't

        :param news_to_check: galnet news
        :return:
        """

        with self.db:
            sql_result = self.db.execute(CHECK_NEWS_QUERY, (news_to_check.galnet_guid,)).fetchone()['count']
            if sql_result == 0:
                return False

            else:
                return True

    def save_news(self, one_news: galnet.OneNews) -> None:
        with self.db:
            self.db.execute(INSERT_ONE_NEWS_QUERY, asdict(one_news))


model = Model()
