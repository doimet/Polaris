# -*-* coding:UTF-8
import contextlib


class Plugin(Base):
    __info__ = {
        "name": "subdomain2url",
        "description": "Subdomain转换成Url",
        "references": ["-"],
    }

    def subdomain(self) -> dict:
        with contextlib.suppress(Exception):
            r = self.request(method='get', url=f"http://{self.target.value}")
            return {"url": str(r.url)}
