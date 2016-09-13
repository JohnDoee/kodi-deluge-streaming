#!/usr/bin/env python

import hashlib
import os
import shutil
import sys
import tempfile
import zipfile

from xml.etree import ElementTree

# zip file/content
DIST_FOLDER = 'dist'

def read_addon_xml_name():
    tree = ElementTree.parse('addon.xml')
    addon = tree.getroot()
    return addon.attrib['id'], '%(id)s-%(version)s.zip' % addon.attrib

def compress():
    addon_name, filename = read_addon_xml_name()
    my_zip = zipfile.ZipFile(os.path.join(DIST_FOLDER, filename), 'w')
    
    for root, dirs, files in os.walk('.'):
        files = [f for f in files if not f[0] == '.' and os.path.splitext(f)[1] not in ['.pyo', '.pyc']]
        dirs[:] = [d for d in dirs if not d[0] == '.' and d != DIST_FOLDER]
        for f in files:
            if f == 'deploy_addon.py':
                continue
            my_zip.write(os.path.join(root, f), arcname=os.path.join(addon_name, root, f))
    my_zip.close()

def move_file(src, dest):
    path = os.path.split(dest)[0]
    if not os.path.isdir(path):
        os.makedirs(path)
    
    shutil.move(src, dest)

if __name__ == '__main__':
    compress()