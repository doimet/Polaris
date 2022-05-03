# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "name": "Crt",
        "description": "证书查询子域名",
        "references": ["https://crt.sh"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://crt.sh/?q={self.target.value}'
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            result = dom.xpath('//table[position()>1]//tr[position()>2]/td[not(@style)]/text()')
            return {
                'SubdomainList': [{'subdomain': _} for _ in result]
            }
