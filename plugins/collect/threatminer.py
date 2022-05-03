# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "name": "ThreatMiner",
        "description": "threatminer查询",
        "references": ["https://www.threatminer.org"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='https://www.threatminer.org/getData.php',
            params={'e': 'subdomains_container', 'q': self.target.value, 't': 0, 'rt': 10}
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            if dom:
                result = dom.xpath('//tbody//a/text()')
                return {
                    'SubdomainList': [{'subdomain': _} for _ in result]
                }
