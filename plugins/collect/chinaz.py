# -*-* coding:UTF-8
import re
import lxml.etree


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["http://mtool.chinaz.com", "http://micp.chinaz.com"],
        "description": "站长之家查询",
        "datetime": "2021-12-27"
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='http://mtool.chinaz.com/Tool/SubDomain/',
            params={'host': self.target.value},
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            return {
                'SubdomainList': [{'subdomain': _} for _ in dom.xpath('//td[@name="subhost"]//text()')]
            }

    def icp(self) -> dict:
        r = self.request(
            method='get',
            url='http://micp.chinaz.com/Handle/AjaxHandler.ashx',
            params={'query': self.target.value, 'action': 'GetBeiansl', 'type': 'num'},
        )
        if r.status_code == 200:
            result = re.findall('SiteLicense:"(.*?)",SiteName:"(.*?)",MainPage:"(.*?)"', r.text)
            if result:
                result = [{'icp': _[0], 'company': _[1], 'subdomain': _[2]} for _ in result]
                return {
                    'ICPList': [dict(t) for t in set([tuple(d.items()) for d in result])]
                }
