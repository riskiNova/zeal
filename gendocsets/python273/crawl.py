import sqlite3
import os

from lxml.html import parse

os.unlink('index.sqlite')
conn = sqlite3.connect('index.sqlite')
c = conn.cursor()

c.execute('CREATE TABLE things (id integer primary key, type text, name text, path text, parent integer)')

tree = parse('py-modindex.html')

modules = {}
modfiles = set()

for tbl in tree.xpath('//table[@class="indextable modindextable"]'):
    for tr in tbl.findall('tr'):
        a = tr.findall('td')[1].find('a')
        if a is None: continue
        modname = a.find('tt').text
        c.execute('INSERT INTO things(type, name, path) values("module", ?, ?)', (modname, a.attrib['href']))
        modules[modname] = c.lastrowid
        modfiles.add(a.attrib['href'].split('#')[0])


def parseClass(class_id, url, tree):
    for dl in tree.xpath('dd/dl[@class="method" or @class="function"]'):
        url = fname
        if dl.xpath('dt/@id'):
            url += '#'+dl.xpath('dt/@id')[0]
        c.execute('INSERT INTO things(type, name, path, parent) values("member", ?, ?, ?)',
            (dl.xpath('dt/tt[@class="descname"]/text()')[0], url, class_id))


for fname in modfiles:
    tree = parse(fname)
    for cls in tree.xpath('//dl[@class="class"]'):
        header = cls.find('dt')
        url = fname
        modname = cls.xpath('dt/tt[@class="descclassname"]/text()')[0][:-1]
        # missing modules
        if modname.startswith('email.mime.'): modname = 'email.mime'
        if modname == 'multiprocessing.queues': modname = 'multiprocessing'
        modid = modules[modname]
        if 'id' not in header.attrib:
            continue
        url += '#' + header.attrib['id']
        c.execute('INSERT INTO things(type, name, path, parent) values("class", ?, ?, ?)', 
            (cls.xpath('dt/tt[@class="descname"]/text()')[0], url, modid))
        parseClass(c.lastrowid, fname, cls)
    
    # non-method functions:
    for function in tree.xpath('//dl[@class="function"]'):
        # ignore methods with class="function"
        if function.getparent().getparent().attrib.get('class') == 'class': continue
        # ctypes.html - callable (ugh.)
        if function.getparent().getparent().getparent().getparent().attrib.get('class') == 'class': continue
        header = function.find('dt')
        url = fname
        from lxml.etree import tostring
        modname = function.xpath('dt/tt[@class="descclassname"]/text()')
        if modname:
            modname = modname[0][:-1]
        else:
            # ctypes prototype
            continue
        # missing modules
        if modname == 'ctypes.util': modname = 'ctypes'
        modid = modules[modname]
        if 'id' not in header.attrib:
            continue
        url += '#' + header.attrib['id']
        c.execute('INSERT INTO things(type, name, path, parent) values("function", ?, ?, ?)', 
            (function.xpath('dt/tt[@class="descname"]/text()')[0], url, modid))


std_classes = {}
def get_std_class(name, href):
    if name not in std_classes:
        c.execute('INSERT INTO things(type, name, path) values("class", ?, ?)', 
            (name, href))
        std_classes[name] = c.lastrowid
    return std_classes[name]


tree = parse('library/stdtypes.html')
for method in tree.xpath('//dl[@class="method"]'):
    url = 'library/stdtypes.html'
    if method.xpath('dt/@id'):
        url += '#'+method.xpath('dt/@id')[0]
    classname = method.xpath('dt/tt[@class="descclassname"]/text()')
    if classname:
        classname = classname[0][:-1]
    else:
        classname = method.getparent().getparent().find('dt').find('tt').text
    c.execute('INSERT INTO things(type, name, path, parent) values("member", ?, ?, ?)',
        (method.xpath('dt/tt[@class="descname"]/text()')[0], url,
         get_std_class(classname, url)))

conn.commit()
conn.close()
