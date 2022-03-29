# -*-* coding:UTF-8
import re


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "收集网站标题",
    }

    def url(self) -> dict:
        r = self.request(method='get', url=self.target.value)
        match = re.search('<title>(.*?)</title>', r.text, re.IGNORECASE)
        title = match.group(1).strip() if match else '-'
        return {
            '网站信息': {
                '网址': self.target.value,
                '网站标题': title,
                '响应大小': r.length,
                '状态码': r.status_code,
            }
        }
