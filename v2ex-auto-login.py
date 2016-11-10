#!/usr/bin/env python
#-*- coding: utf-8 -*-
import os
import sys
import time
import logging
import datetime
import requests
import BeautifulSoup
from requests.adapters import HTTPAdapter

V2EX_BASE_URL = 'https://www.v2ex.com'
ACCOUNTS_FILE = './.accounts'
LOG_FILE = '/var/log/v2ex.log'

# configure logger
logger = logging.getLogger("v2ex")
formatter = logging.Formatter('%(name)-12s %(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S',)
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler(sys.stderr)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

class V2EX:
    """
    v2ex auto login and execute daily task get gold coins 
    """

    def __init__(self, username, password):
        self.signin_url = V2EX_BASE_URL + "/signin"
        self.daily_url =  V2EX_BASE_URL + "/mission/daily"
        self.v2ex_url = V2EX_BASE_URL
        self.user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"

        self.headers = {
            "User-Agent": self.user_agent,
            "Referer": self.v2ex_url,
        }
        v2ex_session = {}
        soup = {}
        self.username = username
        self.password = password
        self.v2ex_session = requests.Session()
        self.v2ex_session.mount(self.v2ex_url, HTTPAdapter(max_retries=5))
        self.soup = BeautifulSoup.BeautifulSoup()
        logger.debug("v2ex init")

    def login(self):
        # get login_info random 'once' value
        v2ex_main_req = self.v2ex_session.get(
            self.signin_url,
            headers=self.headers
        )
        v2ex_main_tag = BeautifulSoup.BeautifulSoup(v2ex_main_req.content)
        form_tag = v2ex_main_tag.find(
            'form', attrs={"method": "post", "action": "/signin"}
        )

        name_tag = form_tag.find('input', attrs={"type": "text"})
        name_tag_name = name_tag.get('name')

        passwd_tag = form_tag.find('input', attrs={"type": "password"})
        passwd_tag_name = passwd_tag.get('name')

        login_info = {
            "next": "/",
            name_tag_name: self.username,
            passwd_tag_name: self.password,
        }

        for input_tag in form_tag.findAll('input'):
            tag_name = input_tag.get('name')
            tag_value = input_tag.get('value')
            if input_tag.get('type') in ['text', 'password']:
                continue
            
            if tag_value:
                login_info[tag_name] = tag_value

        self.headers["Referer"] = self.signin_url
        
        # login
        self.v2ex_session.post(
            self.signin_url, 
            data=login_info, 
            headers=self.headers
        )

        
        main_req = self.v2ex_session.get(self.v2ex_url, headers=self.headers)
        self.soup = BeautifulSoup.BeautifulSoup(main_req.content)
        top_tag = self.soup.find('div', attrs={"id": "Top"})
        user_tag = top_tag.find(href="/member/" + self.username)
        if not user_tag:
            logger.debug("v2ex signin failed for %s", self.username)
            return False
        else:
            logger.debug("v2ex signin successed for %s", self.username)
            return True

    def unchecked(self):
        award_tag = self.soup.find(href="/mission/daily")
        if award_tag:
            return True
        else:
            logger.debug("v2ex has already checked in")
            return False

    def checkin(self):
        # get award if haven't got it
        get_award_req = self.v2ex_session.get(
            self.daily_url, 
            headers=self.headers
        )
        get_award_soup = BeautifulSoup.BeautifulSoup(get_award_req.content)
        button_tag = get_award_soup.find('input', attrs={'type': 'button'})
        click_href = button_tag.attrs[3][1]
        first_dot_index = click_href.find("'")
        last_dot_index = click_href.find("'", first_dot_index + 1)
        click_url = self.v2ex_url + click_href[first_dot_index + 1: last_dot_index]

        self.headers["Referer"] = self.daily_url
        award_req = self.v2ex_session.get(click_url, headers=self.headers)

        if award_req.status_code == requests.codes.ok:
            logger.debug("v2ex checkin successfully ! ")
        else:
            logger.debug("v2ex checkin failed with %s", self.username, " ! \n")

    def run(self):
        if self.login():
            if self.unchecked():
                self.checkin()


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
    accounts = [x.split(' ') for x in file('./.accounts') if x.strip() and x[0] != '#' ]

    for username, passwd in accounts:
        logger.info("Run for %s", username)
        v2ex = V2EX(username, passwd)
        v2ex.run()

