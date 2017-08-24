import os.path
import dataset
import urllib.parse
import urllib.request
import requests
from bs4 import BeautifulSoup
import base64
import collections
class WebServiceData:
    def __init__(self):
        self.__charset = 'utf-8'
        self.__url = None
        self.__title = None
        self.__base64 = None
        self.__content = None
        self.__file_name = None
        self.__extension = None    

    @property
    def Charset(self):
        return self.__charset
    @property
    def Url(self):
        return self.__url
    @property
    def Title(self):
        return self.__title
    @property
    def Content(self):
        return self.__content
    @property
    def Base64(self):
        return self.__base64
    @property
    def DataUri(self):
        return "data:{mime};base64,{value}".format(mime=self.__GetMimeType(), value=self.Base64)
    @property
    def Filename(self):
        return self.__file_name
    @property
    def Extension(self):
        return self.__extension
    @property
    def Classname(self):
        return urllib.parse.urlparse(self.Url).netloc.replace('.', '_')

    """
    インスタンスの状態をセットする。
    from: URL, HTTP.Get
    """
    def Get(self, url):
        self.__GetUrl(url)
        soup = self.__GetSoupForRequests()
        self.__GetTitle(soup)
        self.__GetFavicon(self.__GetFaviconUrl(self.Url, self.__GetFaviconElement(soup)))

    def __GetSoupForUrllib(self):
        return BeautifulSoup(urllib.request.urlopen(self.Url), 'lxml')
    def __GetSoupForRequests(self):
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:52.0) Gecko/20100101 Firefox/52.0'}
        r = requests.get(self.Url, headers=headers)
        if self.__charset != str(r.encoding):
            r.encoding = r.apparent_encoding
        return BeautifulSoup(r.text, 'lxml')

    def __GetTitle(self, soup):
        title = soup.find('title')
        if title:
            self.__title = ''.join(soup.find('title').stripped_strings)
        else:
            self.__title = urllib.parse.urlparse(self.Url).netloc

    """
    インスタンスの状態をセットする。
    from: DB, OrderedDict
    @param {dataset.Database.Table} serviceはDbTable.Serviceクラスで生成したテーブルのレコード。
    @param {dataset.Database.Table} faviconはDbTable.Faviconクラスで生成したテーブルのレコード。
    """
    def Load(self, service:collections.OrderedDict, favicon:collections.OrderedDict):
        self.__url = service['Url']
        self.__title = service['Title']
        self.__content = favicon['Content']
        self.__base64 = base64.b64encode(favicon['Content']).decode(self.Charset)
        self.__extension = favicon['Extension']
        self.__file_name = self.Classname + '.' + self.Extension
    
    """
    各画像形式ファイルを出力する。
    先にGet(),またはLoad()しておくこと。
    """
    def Write(self, path=None):
        if None is self.__content:
            print('Get()またはLoad()してください。')
            return
        out_path = self.Filename
        if None is not path:
            if path.strip().endswith('/'):
                print('ファイルパスを指定してください。: {0}'.format(path))
            file_name, ext = os.path.splitext(os.path.basename(path))
            if ext[1:] != self.Extension:
                print('指定された拡張子は {0} ですが、実物のファイルの拡張子は {1} です。'
                    '拡張子 {1} として作成します。'.format(ext[1:], self.Extension))
                ext = '.' + self.Extension
            if '' == file_name.strip():
                file_name = 'favicon'
                print('ファイル名が空文字または空白文字のみです。'
                    'ファイル名 {0} として作成します。'.format(file_name))
            file_path = file_name + ext
            if '' != os.path.dirname(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
            out_path = os.path.join(os.path.dirname(path), file_path)
        print('*******: {0}'.format(out_path))
        with open(out_path, 'wb') as f:
            f.write(self.Content)

    def __GetUrl(self, url):
        u = urllib.parse.urlparse(url)
        self.__url = urllib.parse.urlunparse(u).replace(u.path, '')
        return self.__url

    def __GetFavicon(self, fav_url:str):
        self.__content = requests.get(fav_url).content
        self.__base64 = base64.b64encode(self.Content).decode(self.Charset)
        self.__file_name = os.path.basename(urllib.parse.urlparse(fav_url).path)
        self.__extension = os.path.splitext(self.Filename)[1][1:]
        # svgはテキスト。pngなどはバイナリ。DBではBLOB型。HTML出力するときはbase64。

    def __GetFaviconElement(self, soup):
        link = soup.find('link', rel='mask-icon') # Chrome,Safari="mask-icon"
        if not link:
            link = soup.find('link', rel='icon') # IE="shortcut icon", Firefox="icon"
        if not link:
            print('Faviconを設定するHTML要素が存在しません。デフォルト値の"{base_url}/favicon.ico"に存在する可能性があります。')
            link = None
        return link

    def __GetFaviconUrl(self, url, link):
        if link:
            if '' == urllib.parse.urlparse(link.get('href')).scheme:
                return urllib.parse.urljoin(url, link.get('href'))
            else:
                return link.get('href')
        else:
            return urllib.parse.urljoin(url, 'favicon.ico')

    def __GetMimeType(self):
        mime_top = 'image/'
        if ('ico' == self.Extension.lower() or
            'png' == self.Extension.lower() or
            'gif' == self.Extension.lower() or
            'jpeg' == self.Extension.lower()):
            return mime_top + self.Extension.lower()
        if 'jpg' == self.Extension.lower():
            return mime_top + 'jpeg'
        if 'svg' == self.Extension.lower():
            return mime_top + 'svg+xml'
        return mime_top + self.Extension.lower()
