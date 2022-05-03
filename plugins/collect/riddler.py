# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "name": "Riddler",
        "description": "riddler查询",
        "references": ["https://riddler.io"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url='https://riddler.io/search',
            params={'q': f'pld:{self.target.value}'}
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            result = dom.xpath('//tbody/tr/td[@class="col-lg-5 col-md-5 col-sm-5"]/a[position()>1]/text()')
            return {
                'SubdomainList': [{'subdomain': _} for _ in result]
            }
