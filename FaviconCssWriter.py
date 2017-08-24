class FaviconCssWriter:
    def __init__(self):
        self.__css = """@charset "utf-8";
.base64-icon {
    display: inline-block;
}
a .base64-icon:hover {
    display: inline-block;
    width: 32px;
    height: 32px;
    background-size: 32px 32px;
    /* ニアレストネイバー法 https://developer.mozilla.org/ja/docs/Web/CSS/image-rendering */
   image-rendering: -moz-crisp-edges;         /* Firefox */
   image-rendering: -o-crisp-edges;         /* Opera */
   image-rendering: -webkit-optimize-contrast;/* Webkit (非標準の名前) */
   image-rendering: crisp-edges;
   -ms-interpolation-mode: nearest-neighbor;  /* IE (非標準プロパティ) */
   /* 半透明マウスカーソル http://www.tagindex.com/stylesheet/page/cursor.html */
   cursor: url(half_alpha_mouse_cursor.png), default;
}
"""

    @property
    def CssPath(self):
        return 'favicon.css'

    def Write(self):
        with open(self.CssPath, mode='w', encoding='utf-8') as f:
            f.write(self.__css)

    def Add(self, name, base64_str, width=16, height=16):
        if not name or not base64_str:
            return
        self.__css += ".base64-icon.{name} ".format(name=name)
        self.__css += "{" + "\n"
        self.__css += """    width: {width}px;
    height: {height}px;
    background-size: {width}px {height}px;
    background-image: url({base64_str});""".format(width=width, height=height, base64_str=base64_str)
        self.__css += "\n" + "}"
