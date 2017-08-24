import os.path
import urllib.parse
import WebServiceData
import dataset

# ネットから取得
url = 'https://www.google.co.jp'
data = WebServiceData.WebServiceData()
data.Get(url)
data.Write() # Google側が作ったファイル名で保存される
data.Write('/tmp/icons/favicon.google.svg') # 指定したパスに保存される

# DBから取得
data2 = WebServiceData.WebServiceData()
db = dataset.connect('sqlite:///' + 'WebServices.sqlite3')
data2.Load(db['Services'].find_one(Url=url))
data2.Write() # DBではファイル名を "{Classname}.{Extension}" とする

