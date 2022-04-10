# -*-* coding:UTF-8
import dns.zone
import dns.resolver


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "name": "域传送",
        "references": ["-"],
        "description": "通过域传送获取子域名",
    }

    def domain(self) -> dict:
        result = []
        resolver = dns.resolver.Resolver()
        answers = resolver.query(self.target.value, 'NS')
        for name_server in [str(answer) for answer in answers]:
            try:
                xfr = dns.query.xfr(where=name_server, zone=self.target.value, timeout=5.0, lifetime=10.0)
                zone = dns.zone.from_xfr(xfr)
                names = zone.nodes.keys()
                for name in names:
                    full_domain = str(name) + '.' + self.target.value
                    result.append(full_domain)
            except:
                pass
        return {'SubdomainList': [{'subdomain': _} for _ in result]}
