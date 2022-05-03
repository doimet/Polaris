# -*-* coding:UTF-8
import re
import lxml.etree


class Plugin(Base):
    __info__ = {
        "name": "BGP",
        "description": "BGP查询",
        "references": ["https://bgp.he.net"],
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
                    "IPInfo": {
                        "asn": match[0],
                        "segment": match[1],
                        "isp": match[2]
                    }
                }
