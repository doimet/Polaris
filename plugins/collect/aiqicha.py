# -*-* coding:UTF-8
import json
import re
import urllib.parse


class Plugin(Base):
    __info__ = {
        "author": "doimet",
        "name": "爱企查",
        "references": ["https://aiqicha.baidu.com"],
        "description": "爱企查企业信息查询",
    }

    @cli.options('company', help="设置公司名称", default='{self.target.value}')
    @cli.options('ua', help="设置User-Agent", default='{self.config.aiqicha.ua}')
    @cli.options('cookies', help="认证cookie", default='{self.config.aiqicha.cookie}')
    def company(self, company, ua, cookies) -> dict:
        if not cookies or not ua:
            raise Exception('missing cookies or ua parameter')
        self.log.debug(f'start collect company base info')
        url = f'https://aiqicha.baidu.com/s?q={urllib.parse.quote(company)}&t=0'
        r = self.request(
            method='get',
            url=url,
            headers={
                'Cookie': cookies,
                'Referer': url,
                'User-Agent': ua,
            }
        )

        match = re.search(r'"resultList":(.*?),"totalNumFound', r.text)
        if match:
            data = json.loads(match.group(1))
            if data:
                pid = data[0]['pid']
                with self.async_pool() as execute:
                    execute.submit(self.custom_collect_base_info, pid)
                    execute.submit(self.custom_collect_app_info, pid)
                    execute.submit(self.custom_collect_holds_info, pid)
                    execute.submit(self.custom_collect_branch_info, pid)
                    execute.submit(self.custom_collect_invest_info, pid)
                    execute.submit(self.custom_collect_icp_info, pid)
                    company_info = {k: v for one in execute.result() for k, v in one.items()}
                    return {'CompanyInfo': company_info}

    async def custom_collect_base_info(self, pid):
        r = await self.async_http(
            method='get',
            url=f'https://aiqicha.baidu.com/company_detail_{pid}'
        )

        if r.status_code == 200:
            base_info = {}
            match = re.findall(r'email":"(.*?)"', r.text)
            if match:
                base_info['email'] = match[0] if len(set(match)) == 1 else match
            match = re.findall('telephone":"(.*?)"', r.text)
            if match:
                base_info['telephone'] = match[0] if len(match) == 1 else match
            match = re.findall('addr":"(.*?)"', r.text)
            if match:
                base_info['address'] = match[0].encode().decode('unicode_escape')
            match = re.findall('website":"(.*?)"', r.text)
            if match:
                base_info['subdomain'] = match[0] if len(match) == 1 else match
            return {"base_info": base_info}

    async def custom_collect_holds_info(self, pid):
        self.log.debug(f'start collect company holds info')
        page, holds_info, page_total = 1, [], 0
        while True:
            r = await self.async_http(
                method='get',
                url=f'https://aiqicha.baidu.com/detail/holdsajax?p=1&size=100&pid={pid}',
                headers={
                    'Referer': f'https://aiqicha.baidu.com/company_detail_{pid}'
                }
            )
            if r.status_code == 200:
                resp = r.json()
                page_total = resp['data']['pageCount']
                if page != resp['data']['page']:
                    break
                for i in resp['data']['list']:
                    holds_info.append({"company": i['entName'], "proportion": i['proportion']})
                if page == page_total:
                    break
                page += 1
            else:
                break
        return {"holds_info": holds_info}

    async def custom_collect_branch_info(self, pid):
        self.log.debug(f'start collect company branch info')
        page, branch_info, page_total = 1, [], 0
        while True:
            r = await self.async_http(
                method='get',
                url=f'https://aiqicha.baidu.com/detail/branchajax?p=1&size=100&pid={pid}',
                headers={
                    'Referer': f'https://aiqicha.baidu.com/company_detail_{pid}'
                }
            )
            if r.status_code == 200:
                resp = r.json()
                page_total = resp['data']['pageCount']
                if page != resp['data']['page']:
                    break
                for i in resp['data']['list']:
                    branch_info.append({"company": i['entName']})
                if page == page_total:
                    break
                page += 1
            else:
                break
        return {"branch_info": branch_info}

    async def custom_collect_invest_info(self, pid):
        self.log.debug(f'start collect company invest info')
        page, invest_info, page_total = 1, [], 0
        while True:
            r = await self.async_http(
                method='get',
                url=f'https://aiqicha.baidu.com/detail/investajax?p=1&size=100&pid={pid}',
                headers={
                    'Referer': f'https://aiqicha.baidu.com/company_detail_{pid}'
                }
            )
            if r.status_code == 200:
                resp = r.json()
                page_total = resp['data']['pageCount']
                if page != resp['data']['page']:
                    break
                for i in resp['data']['list']:
                    invest_info.append({"company": i['entName'], 'proportion': i['regRate']})
                if page == page_total:
                    break
                page += 1
            else:
                break
        return {"invest_info": invest_info}

    async def custom_collect_app_info(self, pid):
        self.log.debug(f'start collect company app info')
        page, app_info, page_total = 1, [], 0
        while True:
            r = await self.async_http(
                method='get',
                url=f'https://aiqicha.baidu.com/c/appinfoAjax?p={page}&size=100&pid={pid}',
                headers={
                    'Referer': f'https://aiqicha.baidu.com/company_detail_{pid}'
                }
            )
            if r.status_code == 200:
                resp = r.json()
                page_total = resp['data']['pageCount']
                if page != resp['data']['page']:
                    break
                for i in resp['data']['list']:
                    app_info.append({"name": i['name'], 'classify': i['classify'], 'description': i['logoBrief']})
                if page == page_total:
                    break
                page += 1
            else:
                break
        return {"app_info": app_info}

    async def custom_collect_icp_info(self, pid):
        self.log.debug(f'start collect company icp info')
        page, icp_info, page_total = 1, [], 0
        while True:
            r = await self.async_http(
                method='get',
                url=f'https://aiqicha.baidu.com/detail/icpinfoajax?p={page}&pid={pid}',
                headers={
                    'Referer': f'https://aiqicha.baidu.com/company_detail_{pid}'
                }
            )
            if r.status_code == 200:
                resp = r.json()
                page_total = resp['data']['pageCount']
                if page != resp['data']['page']:
                    break
                for i in resp['data']['list']:
                    icp_info.append({"site": i['siteName'], "domains": i['domain'], "icp": i['icpNo']})
                if page == page_total:
                    break
                page += 1
            else:
                break
        return {"icp_info": icp_info}
