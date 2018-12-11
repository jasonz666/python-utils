# encoding:utf-8

# Windows 10 系统恢复重置电脑之后
# 被删除的应用程序列表保存在一个 html 文件里
# 这里提取 html 文件里的应用名称列表

from lxml import etree

app_list_html = './已删除的应用.html'

html_fd = open(app_list_html, 'r', encoding='UTF-16')
parser = etree.HTMLParser()
html_tree = etree.parse(html_fd, parser)

tag_tr = html_tree.getroot()[2][0][1][1]
for child in tag_tr.iter():
    if child.tag == 'td' and child.attrib.get('class') == 'Regular':
        for text in child.itertext():
            print(text)
