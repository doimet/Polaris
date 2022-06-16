# -*-* coding:UTF-8


class Plugin(Base):
    __info__ = {
        "name": "ICP备案查询网",
        "description": "备案查询",
        "references": ["https://api.vvhan.com"],
    }

    def domain(self) -> dict:
        r = self.request(
            method='get',
            url=f'https://api.vvhan.com/api/icp?url={self.target.value}',
            timeout=15
        )
        if r.status_code == 200:
            info = r.json()['info']
            return {
                "ICPInfo": {
                    "name": info["name"],
                    "icp": info["icp"],
                    "nature": info["nature"],
                },
                "WebInfo": {
                    "title": info["title"]
                }
            }
