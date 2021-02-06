# -*- coding: utf-8 -*-

import sys
import logging
import re
from logging import StreamHandler
import peewee
import bs4

from simplelib.common import threadpool

from simplelib.httpclient import restclient

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
stream_handler = StreamHandler(stream=sys.stdout)
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(filename)s: %(message)s')
stream_handler.setFormatter(formatter)
LOG.addHandler(stream_handler)

BT_HOME_HREF = 'www.88btbtt.com'

SCORE_REG = r'(豆瓣评分(.*\d+ from .*\d+ users))'


DB = peewee.SqliteDatabase(BT_HOME_HREF.replace(".", '_') + '.db')


class BaseModel(peewee.Model):
    class Meta:
        database = DB

    id = peewee.PrimaryKeyField()


class Video(BaseModel):
    tid = peewee.DoubleField()
    type = peewee.CharField(100)
    date = peewee.CharField(100)
    location = peewee.CharField(100)
    classification = peewee.CharField(100)
    resolution = peewee.CharField(100)
    score = peewee.CharField(100)
    title = peewee.TextField()


def deal_page(page_href):
    LOG.info("current page href is %s", page_href)
    client = restclient.RestClient('https', BT_HOME_HREF, 443, timeout=180)
    resp = client.get(page_href)
    soup = bs4.BeautifulSoup(str(resp.content, 'utf-8'),
                             features="html.parser")
    result_set = soup.find_all(name='td',
                               attrs={'class': "subject", 'valign': 'middle'})
    for result in result_set:
        if result.find_all(name='span', attrs={'class': 'icon icon-top-3'}):
            LOG.warning("skip top tables")
            continue
        a_list = result.find_all(name='a')
        if not a_list:
            continue
        movie_info, score, tid = [], '', 0
        span_set = result.find_all(name='span',
                                   attrs={'class': 'icon icon-post-blue'})
        if not span_set:
            span_set = result.find_all(name='span',
                                       attrs={'class': 'icon icon-post-grey'})
        if span_set:
            tid = span_set[0].get('tid')

        for ele in a_list:
            if not ele.get_text():
                continue
            movie_info.append(ele.get_text())

        selected = Video.filter(tid=tid).select()
        if selected.count() >= 1:
            LOG.debug("skip save video %s, tid=%s", movie_info[-1], tid)
            continue

        resp = client.get('/' + a_list[-1].get("href"))
        matches = re.findall(SCORE_REG, str(resp.content, 'utf-8'))
        if matches:
            score = matches[0][1].strip()
        if len(movie_info) < 6:
            LOG.warning('video info may be not correct: %s', movie_info)
            continue
        new_video = Video(tid=tid, score=score,
                          type=movie_info[0],
                          date=movie_info[1],
                          location=movie_info[2],
                          classification=movie_info[3],
                          resolution=movie_info[4],
                          title=movie_info[5])
        new_video.save()
        LOG.info("saved %s %-25s %s", tid, score, ' '.join(movie_info))

    return resp.content


def main():
    Video.create_table()
    pool = threadpool.ThreadPool(10)
    page = 1
    while True:
        next_href = '/index-index-page-{0}.htm'.format(page)
        pool.spawn(deal_page, (next_href,))
        page += 1


if __name__ == '__main__':
    main()
