from scrapy.selector import Selector
from scrapy.spider import Spider
from rer.items import RerScrappersItem
from scrapy import log
import time
import datetime


STATIONS_FILE = '/root/scrapers/rer/sncf_stations_list.txt'

f = open(STATIONS_FILE, 'r')
urls = [s.rstrip() for s in f]

class SncfSpider(Spider):
    name = 'sncf'
    allowed_domains = ['transilien.com']
    start_urls = urls

    def parse(self, response):
        sel = Selector(response)
        if response.url not in self.start_urls:
            self.log('Url (%s) not in list.' % response.url, level=log.ERROR)
            self.log('Origin url : %s' % response.request.url, level=log.ERROR)
        else:
            lines = sel.xpath('//tr[@class=""]//a/img/@alt').extract()
            lines += sel.xpath('//tr[@class="odd"]//a/img/@alt').extract()

            raw_missions = sel.xpath('//tr[@class=""]//a[@class="arrets_desservis"]/@href').extract()
	    missions = []
	    for raw_mission in raw_missions:
	        ind = raw_mission.find('numeroTrain=') + len('numeroTrain=')
	        missions.append(raw_mission[ind:ind + 6])

            raw_missions = sel.xpath('//tr[@class="odd"]//a[@class="arrets_desservis"]/@href').extract()
	    for raw_mission in raw_missions:
	        ind = raw_mission.find('numeroTrain=') + len('numeroTrain=')
	        missions.append(raw_mission[ind:ind + 6])

            status = 'Inconnu'
            time = datetime.datetime.now()
            station = sel.xpath('//div[@class="h1"]/h1/text()')[0].extract()

            for n in xrange(len(lines)):
                if lines[n] == 'A':
                    i = RerScrappersItem()

                    i['time'] = time
                    i['full_mission'] = missions[n]
                    i['station'] = station
                    i['status'] = status

                    yield i

		    self.log('%s : parsed' % i['station'], level=log.DEBUG)


            #yield response.request
