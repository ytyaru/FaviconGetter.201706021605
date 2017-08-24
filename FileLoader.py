import dataset
import os.path
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import base64
import FaviconCssWriter
import WebServiceData
import Database
class FileLoader:
    def __init__(self):
        self.__charset = 'utf-8'
        self.__db_access = Database.DatabaseAccesser()
    def Run(self, path='url.txt'):
        with open(path, mode='r', encoding='utf-8') as f:
            for line in f.read().split('\n'):
                if '' == line.strip():
                    continue
                print(line)
#                data = WebServiceData.WebServiceData()
#                data.Get(line)
#                self.__db_access.Insert(data)

                self.__db_access.InsertGet(line)
#                self.__db_access.Upsert(line)
#                self.__db_access.InsertRevision(line)


if __name__ == '__main__':
    loader = FileLoader()
    loader.Run()
