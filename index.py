from flask_caching import Cache
from flask_restful import Api, Resource, reqparse
from requests_html import HTMLSession
from flask import Flask, Response, json, request # 你需要导入request模块，否则会报错
# from requests import request

app = Flask(__name__)
# 配置缓存
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
# 创建一个session对象，用于发送请求
session = HTMLSession()
agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
session.headers.update({'User-Agent': agent})
# 创建一个api对象，用于定义路由
api = Api(app)


class ScrapeImages(Resource):

    def get(self):
        # 你需要使用request.args.get方法来获取参数，而不是直接使用request.args
        page = request.args.get('page', 1)
        per_page = request.args.get('per_page', 10)

        if page is None or page < 1:
            page = 1
        if per_page is None or per_page < 1:
            per_page = 10

        image_data = []
        for page_number in range(page, page + per_page):
            url = f"https://asigirl.com/album/page/{page_number}"
            response = session.get(url, verify=True)
            if response.status_code == 200:
                for card in response.html.find('div.oxy-post'):
                    image_link = card.find('a', first=True).attrs['href']
                    image_thum = 'https:' + card.find('img', first=True).attrs['src']
                    image_title = card.find(
                        'h3.infinity-post-title', first=True).text
                    image_data.append({
                        'title': image_title,
                        'link': image_link,
                        'thumbnail': image_thum,
                    })

        return Response(
            json.dumps(image_data),
            mimetype='application/json',
            headers={'Content-Type': 'application/json; charset=utf-8'},
        )


class ScrapeDetails(Resource):

    def get(self):
        detail_url = request.args.get('url')

        if detail_url is None:
            return {'error': 'Missing detail_url parameter'}

        response = session.get(detail_url, verify=True)
        if response.status_code == 200:
            images = []
            for a_tag in response.html.find('a.asigirl-item'):
                download_link = a_tag.attrs['href']
                display_img = 'https:' + a_tag.find('img', first=True).attrs['src']
                images.append({
                    'link': download_link,
                    'thumbnail': display_img,
                })

            return {'images': images}
        else:
            return {'error': 'Invalid detail_url'}


api.add_resource(ScrapeImages, '/scrape')
api.add_resource(ScrapeDetails, '/details')

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0',port=8080)
