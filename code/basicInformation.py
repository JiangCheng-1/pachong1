import requests
from requests.exceptions import RequestException
import re
import csv

headers = {
    'User-Agent': 'Mozilla/5.0(Macintosh;Intel Mac OS X 10_13_3)AppleWebkit/537.36(KHTML,like Gecko)Chrome/65.0.3325.162 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'cookie': r'Path=/; Path=/; gkmlfront_session=eyJpdiI6ImFBZkRiMGpBM1ZnKzVRT0ZyZjd1elE9PSIsInZhbHVlIjoidzdWQXNlaFhsY1BQZG85UmZ6R25nc1JRdWcrMGN6aHRsZUdQbkZQU2s3V2lMejVNZ1g3Rnk4cnJPK1Bua1FuXC8iLCJtYWMiOiIxYjNjODMzNDY2ZDg0ODEzZWViYjk2MTcyZGZmZGQwOGIxOGM3MDBkODBiZGE4ZjU1MDg3MjI4N2M0M2UyM2ZmIn0%3D; front_uc_session=eyJpdiI6IkgxSUJOeXdQT0h3RkxGXC96czRYcHVRPT0iLCJ2YWx1ZSI6IlhZNjYrVkQ0amVuQnVQVUVlWWh5TDZ1VmFnbVFpYXlITzdPeXV2aWJKcmI2U25rZmluZVh1cXJtV3Z1SDV0aFkiLCJtYWMiOiIyYjc5MDYyNGQ4MTI4NjdjZjM2Mzk0NTZlZTkwODA0ZGJiZTQ1NTFlYmM4OWYxYjkyMDk3NDcwYmEyYzMyNzdkIn0%3D'
}


# 获取每一条政策数据的详情页链接
def get_hrefs(base_url1, base_url2):
    href_list = []
    for pageId in range(49):
        if pageId == 0:
            pass
        else:
            url = base_url1 + str(pageId) + base_url2
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    # 将单引号替换成双引号
                    response = response.text.replace('\'', '\"')
                    pattern = re.compile('"classify_theme_name".*?"url":"(.*?)"', re.S)
                    hrefs = re.findall(pattern, response)
                    for href in hrefs:
                        href = href.replace('http', 'https').replace('\\','')
                        href_list.append(href)
            except RequestException as e:
                print('Error', e.args)
    return href_list


# 使用request.get()获取网页
def get_one_page(url):
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            response.encoding = 'utf-8'
            return response.text
        return '页面无反应'
    except RequestException:
        return 'Request出现错误'


# 从网页内容中提取自己想要的信息
def parse_one_page(html):
    # 使用compile函数将正则表达式的字符串形式编译成一个pattern对象
    pattern = re.compile(
        '索引号.*?<span title="(.*?)">'
        '.*?发布机构.*?<span>(.*?)</span>'
        '.*?名称.*?<span.*?title="(.*?)">'
        '.*?发布日期.*?<span>(.*?)</span>'
        '.*?<div class="article-content">(.*?)</div>',
        # 'class="nfw-cms-attachment".*?href="(.*?)"',
        re.S)
    items = re.findall(pattern, html)
    for item in items:
        # 从政策正文文本中获取链接
        p = re.compile('class="nfw-cms-attachment".*?href="(.*?)"', re.S)
        href = re.findall(p, item[4])
        if not href:
            href = ['无附件链接']
        else:
            href = href
        # 对政策正文文本进行清洗（去除非汉字和非数字）
        t = re.sub('([^\u4e00-\u9fa5\u0030-\u0039])', '', item[4])
        # 修改日期格式
        date = re.sub('-','',item[3])
        yield {
            '索引号': item[0].strip(),
            '发布机构': item[1].strip(),
            '政策标题': item[2].strip(),
            '发布日期': int(date),
            '政策正文文本': t,
            '政策正文附件链接': ','.join(href),
        }


def write_to_file(content):
    with open('../data/policies.csv', 'w', encoding='utf-8-sig', newline="") as f:
        writer = csv.writer(f)
        header = ['索引号', '发布机构', '政策标题', '发布日期', '政策正文文本', '政策正文附件链接']
        writer.writerow(header)
        writer.writerows(content)


# 收集特定时间区间内的全部政策信息
def get_period_policies(date1,date2):
    # 获取每条政策数据的详情页链接
    url1 = 'https://www.gd.gov.cn/gkmlpt/api/all/5?page='
    url2 = '&sid=2'
    urls = get_hrefs(url1, url2)
    content_list = []
    for i in urls:
        # 获取每条政策数据的详细内容
        text = get_one_page(i)
        single_list = []
        for j in parse_one_page(text):
            single_list = [j['索引号'], j['发布机构'], j['政策标题'], j['发布日期'],
                           j['政策正文文本'], j['政策正文附件链接']]
        if date1 <= single_list[3] <= date2:
            content_list.append(single_list)
        if single_list[3] < date1:
            break
    write_to_file(content_list)


if __name__ == '__main__':
    get_period_policies(20230628,20230629)
