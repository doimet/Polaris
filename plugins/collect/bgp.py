# -*-* coding:UTF-8
import re
import lxml.etree


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "name": "BGP",
        "references": ["https://bgp.he.net"],
        "description": "BGP查询",
    }

    def ip(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://bgp.he.net/ip/{self.target.value}',
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            match = dom.xpath('//div[@id="ipinfo"]/table/tbody/tr/td//text()')
            if match:
                return {
                    "IpInfo": {
                        "asn": match[0],
                        "segment": match[1],
                        "isp": match[2]
                    }
                }
