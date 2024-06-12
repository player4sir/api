from flask_caching import Cache
from flask_restful import Api, Resource
from requests_html import HTMLSession
from flask import Flask, Response, json, request

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
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
        except ValueError:
            return {'error': 'Invalid parameters'}, 400

        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10

        image_data = []
        for page_number in range(page, page + per_page):
            url = f"https://asigirl.com/album/page/{page_number}"
            response = session.get(url, verify=True)
            if response.status_code == 200:
                for card in response.html.find('div.oxy-post'):
                    try:
                        image_link = card.find('a', first=True).attrs['href']
                        image_thum = 'https:' + card.find('img', first=True).attrs['src']
                        image_title = card.find('h3.infinity-post-title', first=True).text
                        image_data.append({
                            'title': image_title,
                            'link': image_link,
                            'thumbnail': image_thum,
                        })
                    except (AttributeError, IndexError) as e:
                        # Handle parsing errors
                        continue
            else:
                return {'error': 'Failed to retrieve data from the source'}, 500

        return Response(
            json.dumps(image_data),
            mimetype='application/json'
        )


class ScrapeDetails(Resource):

    def get(self):
        detail_url = request.args.get('url')

        if detail_url is None:
            return {'error': 'Missing detail_url parameter'}, 400

        response = session.get(detail_url, verify=True)
        if response.status_code == 200:
            images = []
            for a_tag in response.html.find('a.asigirl-item'):
                try:
                    download_link = a_tag.attrs['href']
                    display_img = 'https:' + a_tag.find('img', first=True).attrs['src']
                    images.append({
                        'link': download_link,
                        'thumbnail': display_img,
                    })
                except (AttributeError, IndexError) as e:
                    # Handle parsing errors
                    continue

            return {'images': images}
        else:
            return {'error': 'Invalid detail_url'}, 400


api.add_resource(ScrapeImages, '/scrape')
api.add_resource(ScrapeDetails, '/details')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
