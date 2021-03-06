# hf3672 SmartSleep Philips library
# to retrieve and set alarms
# (actually just retrieve, because the device don't want my updates
#  and it responds with {"error": "Timeout"} or {"error": "Out of memory"})
 
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
        headers = {'Content-Type': 'application/json'}
        urlfunc = self.url + urifunc
        try:
            req = self.rs.put(urlfunc, data=data, headers=headers, timeout=30)
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
        for alarm in alarms_struct:
            self.aenvs['prfen'][idx] = alarm['enabled']
            self.aalms['ayear'][idx] = alarm['year']
            self.aalms['amnth'][idx] = alarm['mnth']
            self.aalms['alday'][idx] = alarm['lday']
            self.aalms['daynm'][idx] = self._daysOred(alarm['daynm'])
            self.aalms['almhr'][idx] = alarm['lmhr']
            self.aalms['almmn'][idx] = alarm['lmmn']
            idx += 1
        data1 = {"snztm": 9, "aenvs": self.aenvs, "aalms": self.aalms, "prfsh": 0}
        data2 = {"snztm": 9, "aenvs": self.aenvs, "aalms": {}, "prfsh": 0}
        data_str = json.dumps(data1)
        data_str = data_str.replace(' ', '')
        aalms = json.dumps(self.aalms).replace(' ', '')
        aenvs = json.dumps(self.aenvs).replace(' ', '')
        try:
            #exit = self._put('wualm/aenvs', self.aenvs)
            exit = self._put('wualm', data_str)
            #exit = self._put('wualm/aalms', aalms_str)
            #exit = self._put('wualm/aenvs', aenvs_str)
        except:
            raise
        if exit != 200:
            logging.info("setAlarms, put returned {}".format(exit))
        return exit
