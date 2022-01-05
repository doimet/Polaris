# -*-* coding:UTF-8
import whois


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "获取域名whois信息",
        "datetime": "2021-12-27"
    }

    def domain(self) -> dict:
        info = whois.whois(self.target.value)
        return {
            'DomainInfo': {
                '联系人': info['name'] or '-',
                '邮箱账号': info['emails'] or '-',
                '注册商': info['registrar'] or '-',
                '域名服务器': ', '.join(info['name_servers'] or [])
            }
        }
