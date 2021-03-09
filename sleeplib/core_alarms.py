# hf3672 SmartSleep Philips library
# to retrieve and set alarms
 
import logging
import requests
from requests.adapters import HTTPAdapter
import json


class Alarms(object):

    def __init__(self, host="192.168.1.1",
                 weekdays=['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']):
        self.rs = requests.session()
        self.rs.verify = False
        HTTPopts = HTTPAdapter(max_retries=0)
        self.rs.mount("https://" + host, HTTPopts)
        self.producturi = "/di/v1/products/1/"
        self.url = "https://" + host + self.producturi
        self.wualm = {"snztm": 9, "aenvs": {}, "aalms": {}, "prfsh": 0}
        self.aenvs = {'prfen': [bool() for i in range(16)],
                      'prfvs': [bool() for i in range(16)],
                      'pwrsv': [int() for i in range(16)]}
        self.aenvs['prfen'][0] = False
        self.aenvs['prfen'][1] = False
        self.aalms = {'ayear': [int() for i in range(16)],
                      'amnth': [int() for i in range(16)],
                      'alday': [int() for i in range(16)],
                      'daynm': [int(0xfe) for i in range(16)],
                      'almhr': [int() for i in range(16)],
                      'almmn': [int() for i in range(16)]}
        self.anxday = [None]
        self.anxday += weekdays
        self.mask2idx = []
        j = 1
        for i in range(7):
            j <<= 1
            self.mask2idx.append(j)

    def _get(self, urifunc):
        urlfunc = self.url + urifunc
        try:
            req = self.rs.get(urlfunc, timeout=5)
        except requests.ConnectionError:
            raise
        except requests.ConnectTimeout:
            raise
        except requests.HTTPError:
            raise
        logging.debug("_get: {}:{}".format(req.status_code, req.content))
        if req.status_code != 200:
            req.raise_for_status()
        return req.json()

    def _put(self, urifunc, data):
        urlfunc = self.url + urifunc
        try:
            req = self.rs.put(urlfunc, json=data, timeout=10)
        except requests.ConnectionError:
            raise
        except requests.ConnectTimeout:
            raise
        except requests.HTTPError:
            raise
        logging.debug("_put: {}:{}".format(req.status_code, req.content))
        if req.status_code != 200:
            req.raise_for_status()
        return req.status_code

    # returns a list of human readable days name and enabled flag
    # against the natural or'ed field
    def _daysAnded(self, daynm):
        days = []

        idx = 0
        for day in self.mask2idx:
            test = daynm & day
            if test:
                days.append([self.anxday[idx % 7 + 1], True])
            else:
                days.append([self.anxday[idx % 7 + 1], False])
            idx += 1

        return days

    # returns an int with all days
    # from a list of human readable days name
    # 1 = Monday is the starts
    def _daysOred(self, days):
        daynm = int()
        for day in days:
            iday = self.anxday.index(day)
            daynm |= pow(2, iday)
        return daynm

    def getAlarms(self):
        alarms = []
        idx = 0
        try:
            self.aenvs = self._get('wualm/aenvs')
            self.aalms = self._get('wualm/aalms')
        except:
            raise
        for enabled in self.aenvs['prfen']:
            alarm = {'index': idx}
            alarm['enabled'] = enabled
            for key in self.aalms:
                if key == 'daynm':
                    alarm[key] = self._daysAnded(self.aalms[key][idx])
                else:
                    alarm[key] = self.aalms[key][idx]
            alarms.append(alarm)
            del alarm
            idx += 1
        return alarms

    def setAlarms(self, alarms_struct):
        idx = 0
        exit = 200
        for alarm in alarms_struct:
            idx += 1
            prfwu = {}
            prfwu['prfnr'] = idx
            prfwu['prfen'] = alarm['enabled']
            prfwu['ayear'] = alarm['year']
            prfwu['amnth'] = alarm['mnth']
            prfwu['alday'] = alarm['lday']
            prfwu['daynm'] = self._daysOred(alarm['daynm'])
            prfwu['almhr'] = alarm['lmhr']
            prfwu['almmn'] = alarm['lmmn']
            try:
                iexit = self._put('wualm/prfwu', prfwu)
                exit += iexit
            except:
                logging.exception("issue setting alarm #{}".format(idx))
                raise
        if exit % 200 != 0:
            logging.error("setAlarms, last put returned {}".format(iexit))
        return exit
