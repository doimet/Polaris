# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["https://www.email-format.com"],
        "description": "电子邮件查询",
        "datetime": "2022-02-22"
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://www.email-format.com/d/{self.target.value}/#'
        )
        if r.status_code == 200:
            dom = lxml.etree.HTML(r.content)
            match = dom.xpath('//table[@id="domain_address_container"]//tr//div[@class="fl"]/text()')
            if match:
                return {
                    'EmailList': [{'email': _.strip()} for _ in match]
                }
