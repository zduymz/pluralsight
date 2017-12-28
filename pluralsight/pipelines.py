# -*- coding: utf-8 -*-
import os
import scrapy
from scrapy.pipelines.media import MediaPipeline
from scrapy.http import Request
from pluralsight.settings import OUTPUT_DIR


class PluralsightPipeline(MediaPipeline):

    def get_media_requests(self, item, info):
        if item['link']:
            video_url = item['link']
            return Request(
                url=video_url,
                method='GET',
                meta={
                    'module_title': item['module_title'],
                    'video_title': item['title']
                }
            )

    def media_downloaded(self, response, request, info):
        module = request.meta['module_title']
        video = request.meta['video_title'] + '.mp4'
        path = os.path.join(OUTPUT_DIR, module)
        if not os.path.isdir(path):
            os.makedirs(path)

        print "Start downloading %s - %s " % (module, video)

        with open(os.path.join(path, video), "wb") as f:
            f.write(response.body)

        print "Download complete %s - %s" % (module, video)

    def media_failed(self, failure, request, info):
        item = request.meta['title']
        print "MyFilePipeline download failed %s for %s" % (request.url, item['title'])
