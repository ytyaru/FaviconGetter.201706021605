from abc import ABCMeta, abstractmethod
import os
import os.path
import dataset
import urllib.parse
import datetime
import collections
import WebServiceData
import traceback
class DatabaseAccesser:
    def __init__(self, path='./db/'):
        dbc = DatabaseConnector()
        self.__services = dbc.Connect(Services(), path)
        self.__favicons = dbc.Connect(Favicons(), path)
        self.__old_favicons = dbc.Connect(OldFavicons(), path)
        self.__dbs = [self.__services, self.__favicons, self.__old_favicons]

    def DbBegin(self):
        [x.begin() for x in self.__dbs]
    def DbCommit(self):
        [x.commit() for x in self.__dbs]
    def DbRollback(self):
        [x.rollback() for x in self.__dbs]

    # https://teratail.com/questions/52151
    def __Transact(func):
        def wrapper(self, *args, **kwargs):
            try:
                self.DbBegin()
                ret = func(self, *args, **kwargs)
                self.DbCommit()
                print('DBにコミットしました。')
                return ret
            except:
                import traceback
                traceback.print_exc()
                self.DbRollback()
                print('DBをロールバックしました。')
        return wrapper
        
    """
    DBにある全データを1つずつ返す。
    """
    def Loads(self) -> WebServiceData.WebServiceData:
        for record in self.__services['Services']:
            data = WebServiceData.WebServiceData()
            data.Load(record, self.__favicons['Favicons'].find_one(ServiceId=record['Id']))
            yield data

    """
    DBにあるデータのうち指定URLと一致したデータを返す。
    """
    def Load(self, url:str) -> WebServiceData.WebServiceData:
        return self.__LoadFromUrl(url)
        
    """
    DBにあるデータのうち指定URLと一致したデータを返す。なければHTTP.Getして存在すればDBへInsertRevisionする。
    """
    def LoadGet(self, url:str) -> WebServiceData.WebServiceData:
        return self.__LoadFromUrl(url, self.InsertRevision)
    
    def __LoadFromUrl(self, url:str, if_none=None) -> WebServiceData.WebServiceData:
        data = WebServiceData.WebServiceData()
        record = self.__services.find_one(Url=url)
        if None is record:
            if None is if_none:
                return
            else:
                if_none(url) # self.InsertRevision, self.Upsert, self.Insert
        data.Load(record, self.__favicons['Favicons'].find_one(ServiceId=record['Id'])['Content'])
        return data
    
    """
    DBへ挿入する。
    """
    @__Transact
    def Insert(self, data:WebServiceData.WebServiceData):
        service_record = self.__services['Services'].find_one(Url=data.Url)
        if None is not service_record:
            print('Insert 既存のため挿入中止します。: {0}'.format(data.Url))
            return
        self.__InsertService(data)
        self.__InsertFavicon(data)
        print('Insert 挿入しました。: {0}'.format(url))
        
    """
    DBへ挿入する。
    """""
    @__Transact
    def InsertGet(self, url:str):
        service_record = self.__services['Services'].find_one(Url=url)
        if None is not service_record:
            print('InsertGet 既存のため挿入中止します: {0}'.format(url))
            return
        data = WebServiceData.WebServiceData()
        data.Get(url)
        self.__InsertService(data)
        self.__InsertFavicon(data)
        print('InsertGet 挿入しました。: {0}'.format(url))
    
    def __InsertFromUrl(self, url:str, if_none=None):
        service_record = self.__services['Services'].find_one(Url=url)
        if None is not service_record:
            print('すでに存在しています。: {0}'.format(url))
            return
        if_none(url) # WebServiceData.Get, 
        self.__InsertService(data)
        self.__InsertFavicon(data)
    
    """
    DBへ挿入する。既存なら更新する。
    """""
    @__Transact
    def Upsert(self, url:str):
        data = WebServiceData.WebServiceData()
        data.Get(url)
        service_record = self.__services['Services'].find_one(Url=url)
        if None is service_record:
            self.__InsertService(data)
            self.__InsertFavicon(data)
            print('Upsert 挿入しました。: {0}'.format(url))
        else:
            self.__UpdateService(data)
            self.__UpdateFavicon(data)
            print('Upsert 更新しました。: {0}'.format(url))
    
    """
    DBへ挿入する。内容が変わっていたらOldFaviconテーブルに古いレコードを挿入する。
    """""
    @__Transact
    def InsertRevision(self, url:str):
        data = WebServiceData.WebServiceData()
        data.Get(url)
        service_record = self.__services['Services'].find_one(Url=url)
        if None is service_record:
            self.__InsertService(data)
            self.__InsertFavicon(data)
            print('InsertRevision 挿入しました。: {0}'.format(url))
        else:
            self.__UpdateService(data)
            favicon_record = self.__favicons['Favicons'].find_one(ServiceId=service_record['Id'])
            print('InsertRevision 更新しました。: {0}'.format(url))
            if data.Content != favicon_record['Content']:
                self.__InsertRevisionFavicon(favicon_record, service_record['Id'])
                self.__UpdateFavicon(data, service_record['Id'])
                print('InsertRevision 古いファビコンをOldFaviconに登録しました。: {0}'.format(url))

    """
    DBに挿入する。
    """
    def __InsertService(self, data:WebServiceData.WebServiceData):
        self.__services['Services'].insert(dict(
            Url=data.Url,
            Title=data.Title,
            Updated="{0:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
        ))

    """
    DBに挿入する。
    """
    def __InsertFavicon(self, data:WebServiceData.WebServiceData, service_id=None):
        if None is service_id:
            service_id = self.__services['Services'].find_one(Url=data.Url)['Id']
        self.__favicons['Favicons'].insert(dict(
            ServiceId=service_id,
            Extension=data.Extension,
            Content=data.Content
        ))

    """
    DBに挿入する。
    """
    def __InsertOldFavicon(self, data:WebServiceData.WebServiceData, service_id=None):
        if None is service_id:
            service_id = self.__services['Services'].find_one(Url=data.Url)['Id']
        self.__old_favicons['OldFavicons'].insert(dict(
            ServiceId=service_id,
            Extension=data.Extension,
            Content=data.Content,
            Inserted="{0:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
        ))
    
    """
    DBに挿入する。
    """
    def __InsertRevisionFavicon(self, record:collections.OrderedDict, service_id=None):
        if None is service_id:
            service_id = self.__services['Services'].find_one(Url=record['Url'])['Id']
        self.__old_favicons['OldFavicons'].insert(dict(
            ServiceId=service_id,
            Extension=record['Extension'],
            Content=record['Content'],
            Inserted="{0:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
        ))
    
    """
    レコードを更新する。
    """
    def __UpdateService(self, data:WebServiceData.WebServiceData):
        self.__services['Services'].update(dict(
            Url=data.Url,
            Title=data.Title,
            Updated="{0:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now())
        ), ['Url'])

    """
    レコードを更新する。
    """
    def __UpdateFavicon(self, data:WebServiceData.WebServiceData, service_id):
        if None is service_id:
            service_id = self.__services['Services'].find_one(Url=data.Url)['Id']
        self.__favicons['Favicons'].update(dict(
            ServiceId=service_id,
            Extension=data.Extension,
            Content=data.Content
        ), ['ServiceId'])
    
class DatabaseConnector():
    def __init__(self):
        self.__db = None
        self.__tables = []
        self.__extension = 'db'
        self.__file_name = self.__class__.__name__ + '.' + self.__extension

    """
    DBに接続する。DBファイルがないなら作成しテーブルを作成する。
    @param {Database.__Database} databaseは__Database継承クラス。このDatabaseを開く。
    @param {str} path_dirはDBファイルを作成するディレクトリ。
    """
    def Connect(self, database, path_dir=None):
        path = self.__GetDbFilePath(database, path_dir)
        if not(os.path.isfile(path)):
            self.__CreateFile(path)
        db = dataset.connect('sqlite:///' + path)
        if database.Name not in db:
            db.query(database.CreateTableString)
        return db

    def __GetDbFilePath(self, database, path):
        if path:
            return os.path.abspath(os.path.join(path, database.Filename))
        else:
            return os.path.join(os.path.abspath(os.path.dirname(__file__)), database.Filename)

    def __CreateFile(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as f:
            pass
        print('ディレクトリやファイルを作成しました。: {0}'.format(path))

class Database(metaclass=ABCMeta):
    def __init__(self):
        self.__db = None
        self.__extension = 'db'
        self.__file_name = self.__class__.__name__ + '.' + self.__extension
    @property
    def Extension(self):
        return self.__extension
    @property
    def Filename(self):
        return self.__file_name
    # クラス名をDBファイル名にも使う
    @property
    def Name(self):
        return self.__class__.__name__
    @property
    @abstractmethod
    def CreateTableString(self):
        return self.__tables

class Services(Database):
    def __init__(self):
        super().__init__()

    @Database.CreateTableString.getter
    def CreateTableString(self):
        return """create table "Services" (
    "Id"                integer primary key,
    "Url"               text unique not null,
    "Title"             text, -- HTMLのtitle要素テキストノード値。
    "Updated"           text  -- 最終更新日時
);
"""

class Favicons(Database):
    def __init__(self):
        super().__init__()
    
    @Database.CreateTableString.getter
    def CreateTableString(self):
        return """create table "Favicons" (
    "Id"                integer primary key,
    "ServiceId"         integer unique not null, -- unique。1サービスあたり1ファビコン。
    "Extension"         text, -- ファイル拡張子。小文字でico,png,gif,jpg,svg。
    "Content"           blob -- ファビコンの画像内容。ico,png,gif,jpg,svgの内容。（BASE64文字列ではない）
);
"""
# 外部キー制約を加えたかったが、別ファイルDBテーブルには設定できない仕様
# FOREIGN KEY ("ServiceId") REFERENCES  "WebServices"("Id")
    
class OldFavicons(Database):
    def __init__(self):
        super().__init__()

    @Database.CreateTableString.getter
    def CreateTableString(self):
        return """create table "OldFavicons" (
    "Id"                integer primary key,
    "ServiceId"         integer not null, -- uniqueにはしない。複数バージョンを含みうるから。
    "Extension"         text, -- ファイル拡張子。小文字でico,png,gif,jpg,svg。
    "Content"           blob, -- ファビコンの画像内容。ico,png,gif,jpg,svgの内容。（BASE64文字列ではない）
    "Inserted"          text -- 挿入日付。バージョン。
);
"""
# 外部キー制約を加えたかったが、別ファイルDBテーブルには設定できない仕様
# FOREIGN KEY ("ServiceId") REFERENCES  "WebServices"("Id")

