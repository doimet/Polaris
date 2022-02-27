# -*-* coding:UTF-8
import os
import aiodns


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "references": ["-"],
        "description": "枚举子域名",
        "datetime": "2022-01-01"
    }

    @cli.options('input', desc="设置输入目标", default='{self.target.value}')
    def domain(self, domain):
        with self.async_pool() as execute:
            with open(os.path.join('data', 'subdomain.dict'), encoding='utf-8') as f:
                for line in f:
                    prefix = line.strip()
                    execute.submit(self.custom_task, f'{prefix}.{domain}') if prefix else None
            return {'SubdomainList': execute.result()}

    async def custom_task(self, subdomain):
        self.log.debug(f'enum: {subdomain}')
        resolver = aiodns.DNSResolver(timeout=1)
        # resolver0.nameservers = ['114.114.114.114']
        await resolver.query(subdomain, 'A')
        return {'subdomain': subdomain}
