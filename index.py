# 导入需要的库
from flask_caching import Cache
from flask_restful import Api, Resource, reqparse
from requests_html import HTMLSession
from flask import Flask, Response, request, url_for
from flask.config import Config

# 创建一个Flask应用对象
app = Flask(__name__)

# 创建一个配置对象，用于管理应用的配置
config = Config(app.root_path)

# 从config.py文件中加载配置
config.from_pyfile('config.py')

# 把配置对象赋值给应用对象
app.config.from_object(config)

# 创建一个缓存对象，用于缓存应用的数据
cache = Cache(app)

# 创建一个session对象，用于发送请求
session = HTMLSession()
agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
session.headers.update({'User-Agent': agent})

# 创建一个api对象，用于定义路由
api = Api(app)

# 创建一个解析器对象，用于解析请求参数
parser = reqparse.RequestParser()
parser.add_argument('page', type=int, default=1, help='The page number')
parser.add_argument('per_page', type=int, default=10, help='The number of items per page')
parser.add_argument('url', type=str, help='The detail url')


# 定义一个资源类，用于抓取图片列表
class ScrapeImages(Resource):

    # 使用缓存装饰器，缓存60秒的结果
    @cache.cached(timeout=60)
    def get(self):
        # 使用解析器对象来获取请求参数
        args = parser.parse_args()
        page = args['page']
        per_page = args['per_page']

        # 如果参数不合法，返回错误信息
        if page < 1 or per_page < 1:
            return {'error': 'Invalid parameters'}

        # 定义一个空列表，用于存储图片数据
        image_data = []

        # 循环遍历每一页
        for page_number in range(page, page + per_page):
            # 拼接目标网址
            url = f"https://asigirl.com/album/page/{page_number}"
            # 发送请求，获取响应
            response = session.get(url, verify=True)
            # 如果响应成功，解析响应内容
            if response.status_code == 200:
                # 循环遍历每个图片卡片
                for card in response.html.find('div.oxy-post'):
                    # 获取图片的链接，缩略图和标题
                    image_link = card.find('a', first=True).attrs['href']
                    image_thum = 'https:' + card.find('img', first=True).attrs['src']
                    image_title = card.find(
                        'h3.infinity-post-title', first=True).text
                    # 把图片数据添加到列表中
                    image_data.append({
                        'title': image_title,
                        'link': image_link,
                        'thumbnail': image_thum,
                    })

        # 返回一个JSON响应
        return Response(image_data)


# 定义一个资源类，用于抓取图片详情
class ScrapeDetails(Resource):

    # 使用缓存装饰器，缓存60秒的结果
    @cache.cached(timeout=60)
    def get(self):
        # 使用解析器对象来获取请求参数
        args = parser.parse_args()
        detail_url = args['url']

        # 如果参数为空，返回错误信息
        if detail_url is None:
            return {'error': 'Missing detail_url parameter'}

        # 发送请求，获取响应
        response = session.get(detail_url, verify=True)
        # 如果响应成功，解析响应内容
        if response.status_code == 200:
            # 定义一个空列表，用于存储图片数据
            images = []
            # 循环遍历每个图片标签
            for a_tag in response.html.find('a.asigirl-item'):
                # 获取图片的下载链接和缩略图
                download_link = a_tag.attrs['href']
                display_img = 'https:' + a_tag.find('img', first=True).attrs['src']
                # 把图片数据添加到列表中
                images.append({
                    'link': download_link,
                    'thumbnail': display_img,
                })

            # 返回一个JSON响应
            return Response({'images': images})
        else:
            # 如果响应失败，返回错误信息
            return {'error': 'Invalid detail_url'}


# 把资源类和路由关联起来
api.add_resource(ScrapeImages, '/scrape')
api.add_resource(ScrapeDetails, '/details')

# 如果是主模块，运行应用
if __name__ == '__main__':
    app.run()
