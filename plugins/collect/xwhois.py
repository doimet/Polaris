# -*-* coding:UTF-8
import whois


class Plugin(Base):
    __info__ = {
        "name": "Whois",
        "description": "获取域名whois信息",
        "references": ["-"],
    }

    def domain(self) -> dict:
        info = whois.whois(self.target.value)
        return {
            'DomainInfo': {
                'name': info['name'],
                'email': info['emails'] if info['emails'] and 'abuse' not in info['emails'] else None,
                'registrar': info['registrar'],
                'nameservers': ', '.join(info['name_servers'] or [])
            }
        }
