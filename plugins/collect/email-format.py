# -*-* coding:UTF-8
import lxml.etree


class Plugin(Base):
    __info__ = {
        "name": "email-format",
        "description": "电子邮件查询",
        "references": ["https://www.email-format.com"],
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
