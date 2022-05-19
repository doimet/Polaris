# -*-* coding:UTF-8
import contextlib


class Plugin(Base):
    __info__ = {
        "name": "ip2url",
        "description": "IP转换成Url",
        "references": ["-"],
    }

    def ip(self) -> dict:
        with contextlib.suppress(Exception):
            r = self.request(method='get', url=f"http://{self.target.value}")
            return {"url": str(r.url)}
