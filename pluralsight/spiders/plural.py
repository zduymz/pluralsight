# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.http import Request, FormRequest
from pluralsight.items import PluralsightItem
import json
import os
import time


class PluralSpider(scrapy.Spider):
    name = 'plural'
    allowed_domains = ['pluralsight.com']
    start_urls = ['https://app.pluralsight.com/id?']
    login_page = 'https://app.pluralsight.com/id?'
    course_page = 'https://app.pluralsight.com/player/functions/rpc'
    video_link = 'https://app.pluralsight.com/video/clips/viewclip'

    # def parse(self, response):
    #     pass

    def start_requests(self):
        # create output directory
        output_dir = self.settings['OUTPUT_DIR'];
        if output_dir == '':
            output_dir = 'output'
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        # login
        self.username = self.settings['PS_USERNAME']
        self.password = self.settings['PS_PASSWORD']
        yield Request(
            url=self.login_page,
            callback=self.do_login,
            dont_filter=True,
        )

    def do_login(self, response):
        return FormRequest.from_response(
            response,
            formid='signInForm',
            formdata={
                'Username': self.username,
                'Password': self.password
            },
            callback=self.get_course_info,
        )

    def debug_output(self, response):
        with open("/tmp/debug.html", 'w') as f:
            f.write(response.body)

    def get_course_info(self, response):
        headers = {
            'authority': 'app.pluralsight.com',
            'dnt': '1',
            'accept': '*/*',
            'content-type': 'application/json;charset=UTF-8',
            'pragma': 'no-cache'
        }
        course_payload = '{"fn":"bootstrapPlayer","payload":{"courseId":"' + \
            self.settings['COURSE_NAME'] + '"}}'
        return Request(
            url=self.course_page,
            method='POST',
            headers=headers,
            body=course_payload,
            callback=self.parse_course_info,
        )

    def parse_course_info(self, response):
        headers = {
            'authority': 'app.pluralsight.com',
            'dnt': '1',
            'accept': '*/*',
            'content-type': 'application/json;charset=UTF-8',
            'pragma': 'no-cache'
        }

        data = json.loads(response.body)
        if data.has_key('payload') and \
                data['payload'].has_key('course') and \
                data['payload']['course'].has_key('modules'):
            for course_module in data['payload']['course']['modules']:
                for clip in course_module['clips']:
                    module_payload = '{{"author":"{0}","includeCaptions":false,"clipIndex":{1},"courseName":"{2}","locale": "en","moduleName":"{3}","mediaType":"mp4","quality":"1280x720"}}'.format(course_module['author'],
                        clip['index'],
                        data['payload']['course']['name'],
                        course_module['name'])

                    # HTTP ERROR 429
                    time.sleep(0.1)

                    yield Request(
                        meta = {
                            'module_title': str(clip['moduleIndex']) + ' ' + course_module['title'],
                            'clip_title': str(clip['index']) + ' ' + clip['title']
                        },
                        url=self.video_link,
                        method='POST',
                        headers=headers,
                        body=module_payload,
                        callback=self.handle_video_link,
                    )


    def handle_video_link(self, response):
        item = PluralsightItem()
        body = json.loads(response.body)
        # need to improve how to get link
        item['module_title'] = response.meta['module_title']
        item['title'] = response.meta['clip_title']
        item['link'] = body['urls'][0]['url']
        yield item