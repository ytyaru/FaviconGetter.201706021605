import dataset
import os.path
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import base64
import FaviconCssWriter
import WebServiceData
import Database
class IndexHtmlWriter:
    def __init__(self):
        self.__charset = 'utf-8'
        self.__db_accesser = Database.DatabaseAccesser()
        self.__css_writer = FaviconCssWriter.FaviconCssWriter()
    
    @property
    def Charset(self):
        return self.__charset;
    
    def Run(self):
        inner_html = ''
        for data in self.__db_accesser.Loads():
            self.__css_writer.Add(data.Classname, data.DataUri)
            inner_html += self.__GetIconHtml(data)
        self.__css_writer.Write()
        self.__WriteHtml(inner_html)
        
    def __GetIconHtml(self, data):
        return '<a href="{href}" title="{title}"><i class="base64-icon {class_name}"></i></a>'.format(
            href=data.Url,
            title=data.Title,
            class_name=data.Classname)
    
    def __WriteHtml(self, inner_html):
        with open('index.html', mode='w', encoding='utf-8') as f:
            html = '<html><head><meta charset="{charset}"><link rel="stylesheet" href="{css_path}"></head><body>{i}</body></html>'.format(
                charset=self.Charset,
                css_path=self.__css_writer.CssPath,
                i=inner_html)
            f.write(html)


if __name__ == '__main__':
    w = IndexHtmlWriter()
    w.Run()
