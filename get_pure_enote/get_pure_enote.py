# encoding:utf-8
# fileName: get_pure_enote.py
# finishDate: 2018-12-04

###################
## ！！！注意！！！ ##
###################

## 目前此脚本只能处理导入自有道云笔记的印象笔记！
## 无法处理印象笔记网页剪藏笔记，它里面含有更多标签属性如 -evernote-webclip 等！
## 这些属性还没有包含在 original_enote_sample.enex 样本文件里！
## 并且处理其他笔记时，代码中可能有 bug 存在！

##-----------------------------------------------------------------------------
## 在非印象笔记格式的笔记里找出所有不需要的笔记正文里的属性，删除之
## 在印象笔记的导出文件 enex 中 en-note 标签里是笔记正文，内含 HTML 标签
##
## 具体方法是：
## 1、提取非印象笔记格式的每个笔记的每个 en-note 里的所有 HTML 标签和属性
## 2、提取创建自印象笔记的每个笔记的每个 en-note 里的所有 HTML 标签和属性
## 3、把1与2结果中的标签作为字典的键，标签的属性作为字典值，这个字典值是子字典的键
## 4、子字典的键是标签的属性名，子字典的值是列表
## 5、列表元素是标签的属性值，或者是这个属性值里包含的 CSS 属性名
## 6、比较非印象格式的结果中比印象笔记结果中多余的标签属性名或 CSS 属性名
## 7、如果是标签属性名多余，直接删除这个标签的属性
## 8、如果是 CSS 属性多余，把 CSS 属性和它的值替换成空字符串
## 9、如果处理属性后，标签的属性值为空字符串或仅有大于或等于一个空格，则删除该标签的属性
##
## 数据结构举例：
## span 标签作为字典键，span 的 style 属性作为字典值，它也是子字典的键
## style 属性里的 CSS 属性 font-size 作为列表元素，这个列表是 style 子字典的值
## 即 dic['span']['style'][0] == 'font-size'
## 也即 dic -> {'span': {'style': ['font-size']}}
## 标签的属性和属性值形如：<a href="http://example.com">，其中 href 只有一个属性值
## 标签的属性值里的 CSS 属性形如：<span style="font-size: x; font-family: x;">
## 如果标签的属性里只有一个值，而没有 CSS 样式属性，那么列表就只有一个元素
##
## 这个程序最开始用来处理从有道云笔记导入到印象笔记的笔记
##-----------------------------------------------------------------------------

import re, sys, os
from lxml import etree

##-------------
## 函数定义
##-------------

# 用法显示函数
def usage():
    tmp_fn = os.path.basename(sys.argv[0])
    print('用法: python %s "/path/to/待处理文件.enex"\n' % tmp_fn)
    print('\t/path/to/待处理文件.enex 是需要处理格式的印象笔记导出文件路径，必须导出为 enex 文件\n')
    #print('\t比如从网页剪藏的笔记需要简化格式，就导出为 enex 文件作为待处理文件\n')
    print('\t必须用 Python 3.5 或以上版本运行本程序！\n')

##-----------------
## main
##-----------------

# 样本文件定义
enote_fn = 'original_enote_sample.enex'
ynote_fn = ''
new_ynote_fn = ''

# 需要保留而不处理的标签
reserve_tags = (
    'font',
    'en-media',
    'ul',
    'li',
    'table',
    'col',
    'en-todo'
)

# en-note 结点的 CDATA 里的开头两行内容
# 如果包含 DTD 文件的 URL 更新，修改下面 en_doctype 的值
xml_decl = '<?xml version="1.0" encoding="UTF-8"?>\n'
en_doctype = '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">\n\n'

# 版本判断
py_ver = sys.version_info.major + (sys.version_info.minor / 10)
if py_ver < 3.5:
    usage()
    exit(1)

# 从命令行获取文件
if len(sys.argv) != 2:
    usage()
    exit(1)
else:
    ynote_fn = sys.argv[1]
    new_ynote_fn = sys.argv[1] + '.new.enex'

# 文件判断
if os.access(sys.argv[1], os.F_OK) and os.access(sys.argv[1], os.R_OK):
    pass
else:
    print('ERROR: %s: file not found or unreadable.' % sys.argv[1])
    exit(1)

# 文件夹可写判断
if not os.access(os.path.dirname(sys.argv[1]), os.W_OK):
    print('ERROR: %s: directory unwritable.' % os.path.dirname(sys.argv[1]))
    exit(1)

# 样本文件判断
enote_fn = os.path.dirname(os.path.abspath(__file__)) + os.sep + enote_fn
if not os.access(enote_fn, os.F_OK):
    print('ERROR: %s: evernote sample file not found.' % enote_fn)
    exit(1)

# 打开文件给 XML 解析器处理
print('INFO: 正在把 enex 文件解析成 xml 文档 ...')
fd_ynote = open(ynote_fn, 'r', encoding='UTF-8')
fd_enote = open(enote_fn, 'r', encoding='UTF-8')

# 定制 XML 解析器，保留 CDATA
xml_parser = etree.XMLParser(strip_cdata=False)

# 解析有道笔记和印象笔记为 XML 元素树
ynote_tree = etree.parse(fd_ynote, xml_parser)
enote_tree = etree.parse(fd_enote, xml_parser)

# 从有道笔记和印象笔记的 XML 文档树找出所有 content 标签
# 每个 content 标签里有一个 CDATA，CDATA 里有一个 en-note 标签
# en-note 标签里是笔记的正文内容，包含 HTML 标签，CSS 样式属性等
# findall 返回一个列表，每个列表元素是一个 content 标签
# findall 以文档顺序搜索，被提取出来的标签修改后放回 CDATA 里顺序不会被打乱
print('INFO: 正在提取 xml 文档里的所有 content 结点 ...')
ynote_content = ynote_tree.findall('.//content')
enote_content = enote_tree.findall('.//content')

# 把所有 content 里的 CDATA 解封装出来形成列表
# 每个解封装出来的内容包含一个 xml 文档声明语句：
# <?xml version="1.0" encoding="UTF-8"?>
# 然后包含一个 doctype 语句，来定义 en-note 文档：
# <!DOCTYPE en-note SYSTEM "xxx.dtd">
# 最后才是 en-note 标签，它里面是笔记正文
print('INFO: 正在解封装 content 结点里的 CDATA ...')
ynote_en_note = [en_note.text for en_note in ynote_content]
enote_en_note = [en_note.text for en_note in enote_content]

# 定义 HTML 解析器，用于把 CDATA 里的内容解析成 HTML 文档
html_parser = etree.HTMLParser()

# 把有道笔记和印象笔记的 en-note 标签解析成 HTML 元素树的列表
print('INFO: 正在将 CDATA 解析成 html 文档 ...')
ynote_html_root = [etree.fromstring(en_note.encode(), html_parser)
                   for en_note in ynote_en_note]
enote_html_root = [etree.fromstring(en_note.encode(), html_parser)
                   for en_note in enote_en_note]

# 在已解析成 HTML 的 en-note 元素（结点）的列表里提取所有标签
# 返回一个列表，列表每个元素是一个子列表
# 一个子列表里的所有元素表示一个 en-note 结点里的所有标签（结点）
print('INFO: 正在提取笔记正文里的所有标签 ...')
ynote_all_tags = [root.findall('.//') for root in ynote_html_root]
enote_all_tags = [root.findall('.//') for root in enote_html_root]

# 构造标签字典
tag_ynote_dict = {}
tag_enote_dict = {}

# 标记字典
# 如果值为1，表示应该比较标签的属性名
# 如果值为2，表示应该比较标签属性值里的 CSS 属性名
tag_ynote_dict_flag = {}

# ynote_all_tags 是一个列表，它的元素是一个子列表 en_note
print('INFO: 正在处理笔记正文里的所有标签 ...')
for en_note in ynote_all_tags:
    # en_note 是一个子列表，它的元素是笔记正文中的标签
    for elem in en_note:
        # 如果字典没有这个 key，才创建新字典
        # 防止下次 for 迭代把之前的字典内容覆盖掉
        if elem.tag not in tag_ynote_dict:
            tag_ynote_dict[elem.tag] = {}
            tag_ynote_dict_flag[elem.tag] = {}
        # elem.attrib 返回的是所有属性组成的字典
        # 字典键是属性名，字典值是属性值
        for attr in elem.attrib:
            list1 = elem.attrib[attr].split(';')
            # 有冒号的是 CSS 属性，且一般 CSS 属性里不会有超链接
            if ':' in elem.attrib[attr] and '://' not in elem.attrib[attr]:
                tag_ynote_dict_flag[elem.tag][attr] = 2
                list2 = [s.split(':') for s in list1]
            else:
                tag_ynote_dict_flag[elem.tag][attr] = 1
                list2 = [[s, ''] for s in list1]
            # 为了防止覆盖之前的列表，也要先判断
            if attr not in tag_ynote_dict[elem.tag]:
                tag_ynote_dict[elem.tag][attr] = []
            # 应该用 append 方法追加列表元素
            for s in list2:
                if s[0] and s[0].strip() not in tag_ynote_dict[elem.tag][attr]:
                    tag_ynote_dict[elem.tag][attr].append(s[0].strip())

for en_note in enote_all_tags:
    for elem in en_note:
        if elem.tag not in tag_enote_dict:
            tag_enote_dict[elem.tag] = {}
        for attr in elem.attrib:
            list1 = elem.attrib[attr].split(';')
            if ':' in elem.attrib[attr] and '://' not in elem.attrib[attr]:
                list2 = [s.split(':') for s in list1]
            else:
                list2 = [[s, ''] for s in list1]
            if attr not in tag_enote_dict[elem.tag]:
                tag_enote_dict[elem.tag][attr] = []
            for s in list2:
                if s[0] and s[0].strip() not in tag_enote_dict[elem.tag][attr]:
                    tag_enote_dict[elem.tag][attr].append(s[0].strip())

# 创建需删除属性的标记字典
tag_ynote_dict_del = {}
for key_tag in tag_ynote_dict:
    for key_attr in tag_ynote_dict[key_tag]:
        for idx in range(len(tag_ynote_dict[key_tag][key_attr])):
            if key_tag not in tag_ynote_dict_del:
                tag_ynote_dict_del[key_tag] = {}
            if key_attr not in tag_ynote_dict_del[key_tag]:
                tag_ynote_dict_del[key_tag][key_attr] = []
            tag_ynote_dict_del[key_tag][key_attr].append(
                [tag_ynote_dict[key_tag][key_attr][idx], 0])

# 开始比较需要去除的属性
for key_tag in tag_ynote_dict:
    if key_tag in reserve_tags:
        continue
    for key_attr in tag_ynote_dict[key_tag]:
        if tag_ynote_dict_flag[key_tag][key_attr] == 1:
            if key_attr not in tag_enote_dict[key_tag]:
                # 列表里第一个值是标签属性值或者标签属性值里的 CSS 属性名
                # 列表第二个值是如何处理属性的标记，有如下值：
                # 0，属性无需处理
                # 2，需要把 CSS 属性名和它的值一起替换成空字符串
                # 1，需要把这个属性值的属性名，即标签的属性名直接删除
                tag_ynote_dict_del[key_tag][key_attr][0] = [
                    tag_ynote_dict_del[key_tag][key_attr][0][0], 1]
        if tag_ynote_dict_flag[key_tag][key_attr] == 2:
            css_index = 0
            for css_attr in tag_ynote_dict[key_tag][key_attr]:
                if key_attr in tag_enote_dict[key_tag]:
                    if css_attr not in tag_enote_dict[key_tag][key_attr]:
                        tag_ynote_dict_del[key_tag][key_attr][css_index] = [
                            tag_ynote_dict_del[key_tag][key_attr][css_index][0], 2]
                else:
                    tag_ynote_dict_del[key_tag][key_attr][css_index] = [
                        tag_ynote_dict_del[key_tag][key_attr][css_index][0], 1]
                css_index += 1

# 提取 HTML 文档里的 en-note 结点
ynote_note_node = [root.findall('.//en-note') for root in ynote_html_root]

# 开始修改属性
print('INFO: 正在修改不需要的标签属性 ...')
for en_note in ynote_note_node:
    for child in en_note[0].findall('.//'):
        for attr in child.attrib:
            for idx in range(len(tag_ynote_dict_del[child.tag][attr])):
                if tag_ynote_dict_del[child.tag][attr][idx][1] == 1:
                    child.attrib.pop(attr, True)
                    break
                if tag_ynote_dict_del[child.tag][attr][idx][1] == 2:
                    exp = re.compile(tag_ynote_dict_del[child.tag][attr][idx][0] + r'[^;]+; *')
                    child.attrib[attr] = exp.sub('', child.attrib[attr])

# 删除值为空的标签属性
for en_note in ynote_note_node:
    for child in en_note[0].findall('.//'):
        for attr in child.attrib:
            # 如果属性值为空或者仅包含一个或以上空格，才删除这个属性
            if child.attrib[attr] == "" or re.compile(r'^ +$').findall(child.attrib[attr]):
                child.attrib.pop(attr, True)
                break

# 封装 en-note 结点到 CDATA 里
print('INFO: 正在重新封装 CDATA ...')
for idx in range(len(ynote_note_node)):
    ynote_content[idx].text = etree.CDATA(
        xml_decl + en_doctype + etree.tostring(ynote_note_node[idx][0]).decode())

# 修改完成，写入文件
print('INFO: 正在保存结果到新文件 ...')
new_ynote_fn = os.path.abspath(new_ynote_fn)
with open(new_ynote_fn, 'w', encoding='UTF-8') as fd:
    # 写回 xml 文档声明和 doctype 声明
    head = xml_decl + ynote_tree.docinfo.doctype + '\n'
    fd.write(head)
    # 写回 enex 文件时，先把 xml 文档树序列化，并用 utf-8 编码
    fd.write(etree.tostring(ynote_tree.getroot(), encoding='UTF-8').decode())

# 关闭文件
fd_ynote.close()
fd_enote.close()
print('INFO: 新文件: %s' % new_ynote_fn)
print('INFO: 全部完成！')