# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "name": "xhttp",
        "description": "收集网站标题",
        "references": ["-"],
    }

    def url(self) -> dict:
        r = self.request(method='get', url=self.target.value)
        match = re.search('<title>(.*?)</title>', r.text, re.IGNORECASE)
        title = match.group(1).strip() if match else '-'
        return {
            'WebSiteInfo': {
                'url': self.target.value,
                'title': title,
                'size': r.length,
                'code': r.status_code,
            }
        }
