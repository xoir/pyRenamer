# -*- coding: utf-8 -*-

"""
filetools.py - Functions for operating on files for the pyRenamer mass file
renamer

Copyright © 2016 Thomas Freeman <tfree87@users.noreply.github.com>
Copyright © 2006-2008 Adolfo González Blázquez <code@infinicode.org>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""


# Global Imports
import os
import glob
import re
import sys
import time
from datetime import datetime
import random
import unicodedata
from gettext import gettext as _

STOP = False

def set_stop(stop):
    """ Set stop var to see if ther's no need to keep reading files """
    global STOP
    STOP = stop


def get_stop():
    return STOP


def escape_pattern(pattern):
    """ Escape special chars on patterns, so glob doesn't get confused """
    pattern = pattern.replace('[', '[[]')
    return pattern


def get_file_listing(dir, mode, pattern=None):
    """ Returns the file listing of a given directory. It returns only files.
    Returns a list of [file,/path/to/file] """

    filelist = []

    if  pattern == (None or ''):
        listaux = os.listdir(dir)
    else:
        if dir != '/': dir += '/'
        dir = escape_pattern(dir + pattern)
        listaux = glob.glob(dir)

    listaux.sort(key=str.lower)
    for elem in listaux:
        if STOP: return filelist
        if mode == 0:
            # Get files
            if not os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        elif mode == 1:
            # Get directories
            if os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        elif mode == 2:
            # Get files and directories
            filelist.append([os.path.basename(elem),os.path.join(dir,elem)])
        else:
            # Get files
            if not os.path.isdir(os.path.join(dir,elem)):
                filelist.append([os.path.basename(elem),os.path.join(dir,elem)])

    return filelist


def get_file_listing_recursive(dir, mode, pattern=None):
    """ Returns the file listing of a given directory recursively.
    It returns only files. Returns a list of [file,/path/to/file] """

    filelist = []

    # Get subdirs
    for root, dirs, files in os.walk(dir, topdown=False):
        if STOP: return filelist
        for directory in dirs:
            if STOP: return filelist
            elem = get_file_listing(os.path.join(root, directory), mode, pattern)
            for i in elem:
                if STOP: return filelist
                filelist.append(i)

    # Get root directory files
    list = get_file_listing(dir, mode, pattern)
    for i in list:
        filelist.append(i)

    return filelist


def get_dir_listing(dir):
    """ Returns the subdirectory listing of a given directory. It returns only directories.
     Returns a list of [dir,/path/to/dir] """

    dirlist = []

    listaux = os.listdir(dir)
    listaux.sort(key=str.lower)
    for elem in listaux:
        if STOP: return dirlist
        if os.path.isdir(os.path.join(dir,elem)): dirlist.append([os.path.basename(elem),os.path.join(dir,elem)])

    return dirlist


def get_new_path(name, path):
    """ Remove file from path, so we have only the dir"""
    dirpath = os.path.split(path)[0]
    if dirpath != '/': dirpath += '/'
    return dirpath + name


def replace_spaces(name, path, mode):
    """ if mode == 0: ' ' -> '_'
        if mode == 1: '_' -> ' '
        if mode == 2: '_' -> '.'
        if mode == 3: '.' -> ' '
        if mode == 4: ' ' -> '-'
        if mode == 5: '-' -> ' ' """

    name = str(name)
    path = str(path)

    if mode == 0:
        newname = name.replace(' ', '_')
    elif mode == 1:
        newname = name.replace('_', ' ')
    elif mode == 2:
        newname = name.replace(' ', '.')
    elif mode == 3:
        newname = name.replace('.', ' ')
    elif mode == 4:
        newname = name.replace(' ', '-')
    elif mode == 5:
        newname = name.replace('-', ' ')

    newpath = get_new_path(newname, path)
    return str(newname), str(newpath)


def replace_capitalization(name, path, mode):
    """ 0: all to uppercase
    1: all to lowercase
    2: first letter uppercase
    3: first letter uppercase of each word """
    name = str(name)
    path = str(path)

    if mode == 0:
        newname = name.upper()
    elif mode == 1:
        newname = name.lower()
    elif mode == 2:
        newname = name.capitalize()
    elif mode == 3:
        #newname = name.title()
        newname = ' '.join([x.capitalize() for x in name.split()])

    newpath = get_new_path(newname, path)
    return str(newname), str(newpath)


def replace_with(name, path, orig, new):
    """ Replace all occurences of orig with new """
    newname = name.replace(orig, new)
    newpath = get_new_path(newname, path)

    return str(newname), str(newpath)


def replace_accents(name, path):
    """ Remove accents, umlauts and other locale symbols from words 

    For instance: 'áàäâăÁÀÄÂĂéèëêěÉÈËÊĚíìïîĭÍÌÏÎĬóòöôŏÓÒÖÔŎúùüûůÚÙÜÛŮšŠčČřŘžŽýÝ'
    becomes:      'aaaaaAAAAAeeeeeEEEEEiiiiiIIIIIoooooOOOOOuuuuuUUUUUsScCrRzZyY'
    
    Standard ASCII characters don't change, such as:
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-`!@#$%^&*(){}[]:;.<>,'
    """
    name = str(name)
    path = str(path)


    newname = ''.join((c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn'))

    newpath = get_new_path(newname, path)
    return str(newname), str(newpath)


def replace_duplicated(name, path):
    """ Remove duplicated symbols """

    name = str(name)
    path = str(path)

    symbols = ['.', ' ', '-', '_']

    newname = name[0]
    for c in name[1:]:
        if c in symbols:
            if newname[-1] != c:
                newname += c
        else:
            newname += c

    newpath = get_new_path(newname, path)
    return str(newname), str(newpath)


def rename_using_patterns(name, path, pattern_ini, pattern_end, count):
    """ This method parses te patterns given by the user and stores the new filename
    on the treestore. Posibble patterns are:

    {#} Numbers
    {L} Letters
    {C} Characters (Numbers & letters, not spaces)
    {X} Numbers, letters, and spaces
    {@} Trash
    """
    name = str(name)
    path = str(path)

    pattern = pattern_ini
    newname = pattern_end

    pattern = pattern.replace('.','\.')
    pattern = pattern.replace('[','\[')
    pattern = pattern.replace(']','\]')
    pattern = pattern.replace('(','\(')
    pattern = pattern.replace(')','\)')
    pattern = pattern.replace('?','\?')
    pattern = pattern.replace('{#}', '([0-9]*)')
    pattern = pattern.replace('{L}', '([a-zA-Z]*)')
    pattern = pattern.replace('{C}', '([\S]*)')
    pattern = pattern.replace('{X}', '([\S\s]*)')
    pattern = pattern.replace('{@}', '(.*)')

    try:
        repattern = re.compile(pattern)
    except:
        print('Error: could not compile pattern')
        return None, None
        
    try:
        groups = repattern.search(name).groups()

        for i in range(len(groups)):
            newname = newname.replace('{'+repr(i+1)+'}',groups[i])
    except:
        return None, None

    # Replace {num} with item number.
    # If {num2} the number will be 02
    # If {num3+10} the number will be 010
    count = repr(count)
    cr = re.compile("{(num)([0-9]*)}"
                    "|{(num)([0-9]*)(\+)([0-9]*)}")
    try:
        cg = cr.search(newname).groups()
        if len(cg) == 6:

            if cg[0] == 'num':
                # {num2}
                if cg[1] != '': count = count.zfill(int(cg[1]))
                newname = cr.sub(count, newname)

            elif cg[2] == 'num' and cg[4] == '+':
                # {num2+5}
                if cg[5] != '': count = str(int(count)+int(cg[5]))
                if cg[3] != '': count = count.zfill(int(cg[3]))

        newname = cr.sub(count, newname)
    except:
        pass

    # Replace {dir} with directory name
    dir = os.path.dirname(path)
    dir = os.path.basename(dir)
    newname = newname.replace('{dir}', dir)

    # Some date replacements
    newname = newname.replace('{date}', time.strftime("%d%b%Y", time.localtime()))
    newname = newname.replace('{year}', time.strftime("%Y", time.localtime()))
    newname = newname.replace('{month}', time.strftime("%m", time.localtime()))
    newname = newname.replace('{monthname}', time.strftime("%B", time.localtime()))
    newname = newname.replace('{monthsimp}', time.strftime("%b", time.localtime()))
    newname = newname.replace('{day}', time.strftime("%d", time.localtime()))
    newname = newname.replace('{dayname}', time.strftime("%A", time.localtime()))
    newname = newname.replace('{daysimp}', time.strftime("%a", time.localtime()))


    # Some pattern matches for creation and modification date
    createdate, modifydate = get_filestat_data(get_new_path(name, path))
    if createdate is not None:
        newname = newname.replace('{createdate}', time.strftime("%d%b%Y", createdate))
        newname = newname.replace('{createyear}', time.strftime("%Y", createdate))
        newname = newname.replace('{createmonth}', time.strftime("%m", createdate))
        newname = newname.replace('{createmonthname}', time.strftime("%B", createdate))
        newname = newname.replace('{createmonthsimp}', time.strftime("%b", createdate))
        newname = newname.replace('{createday}', time.strftime("%d", createdate))
        newname = newname.replace('{createdayname}', time.strftime("%A", createdate))
        newname = newname.replace('{createdaysimp}', time.strftime("%a", createdate))
    else:
        newname = newname.replace('{createdate}', '')
        newname = newname.replace('{createyear}', '')
        newname = newname.replace('{createmonth}', '')
        newname = newname.replace('{createmonthname}', '')
        newname = newname.replace('{createmonthsimp}', '')
        newname = newname.replace('{createday}', '')
        newname = newname.replace('{createdayname}', '')
        newname = newname.replace('{createdaysimp}', '')

    if modifydate is not None:
        newname = newname.replace('{modifydate}', time.strftime("%d%b%Y", modifydate))
        newname = newname.replace('{modifyyear}', time.strftime("%Y", modifydate))
        newname = newname.replace('{modifymonth}', time.strftime("%m", modifydate))
        newname = newname.replace('{modifymonthname}', time.strftime("%B", modifydate))
        newname = newname.replace('{modifymonthsimp}', time.strftime("%b", modifydate))
        newname = newname.replace('{modifyday}', time.strftime("%d", modifydate))
        newname = newname.replace('{modifydayname}', time.strftime("%A", modifydate))
        newname = newname.replace('{modifydaysimp}', time.strftime("%a", modifydate))
    else:
        newname = newname.replace('{modifydate}', '')
        newname = newname.replace('{modifyyear}', '')
        newname = newname.replace('{modifymonth}', '')
        newname = newname.replace('{modifymonthname}', '')
        newname = newname.replace('{modifymonthsimp}', '')
        newname = newname.replace('{modifyday}', '')
        newname = newname.replace('{modifydayname}', '')
        newname = newname.replace('{modifydaysimp}', '')

    # Replace {rand} with random number between 0 and 100.
    # If {rand500} the number will be between 0 and 500
    # If {rand10-20} the number will be between 10 and 20
    # If you add ,5 the number will be padded with 5 digits
    # ie. {rand20,5} will be a number between 0 and 20 of 5 digits (00012)
    rnd = ''
    cr = re.compile("{(rand)([0-9]*)}"
                    "|{(rand)([0-9]*)(\-)([0-9]*)}"
                    "|{(rand)([0-9]*)(\,)([0-9]*)}"
                    "|{(rand)([0-9]*)(\-)([0-9]*)(\,)([0-9]*)}")
    try:
        cg = cr.search(newname).groups()
        if len(cg) == 16:

            if cg[0] == 'rand':
                if cg[1] == '':
                    # {rand}
                    rnd = random.randint(0,100)
                else:
                    # {rand2}
                    rnd = random.randint(0,int(cg[1]))

            elif cg[2] == 'rand' and cg[4] == '-' and cg[3] != '' and cg[5] != '':
                # {rand10-100}
                rnd = random.randint(int(cg[3]),int(cg[5]))

            elif cg[6] == 'rand' and cg[8] == ',' and cg[9] != '':
                if cg[7] == '':
                    # {rand,2}
                    rnd = str(random.randint(0,100)).zfill(int(cg[9]))
                else:
                    # {rand10,2}
                    rnd = str(random.randint(0,int(cg[7]))).zfill(int(cg[9]))

            elif cg[10] == 'rand' and cg[12] == '-' and cg[14] == ',' and cg[11] != '' and cg[13] != '' and cg[15] != '':
                # {rand2-10,3}
                rnd = str(random.randint(int(cg[11]),int(cg[13]))).zfill(int(cg[15]))

        newname = cr.sub(str(rnd), newname)
    except:
        pass

    # Returns new name and path
    newpath = get_new_path(newname, path)
    return str(newname), str(newpath)


def get_filestat_data(path):
    """ Get file status attributes from a file. """
    createdate = None
    modifydate = None

    try:
        st = os.stat(path)
        if not st:
            print("ERROR: File attributes could not be read", path)
            return createdate, modifydate
    except:
        print("ERROR: processing file attributes on", path)
        return createdate, modifydate

    createdate = datetime.fromtimestamp(st.st_ctime).timetuple()
    modifydate = datetime.fromtimestamp(st.st_mtime).timetuple()

    return createdate, modifydate 


def rename_file(ori, new):
    """ Change filename with the new one """

    if ori == new:
        return True, None    # We don't need to rename the file, but don't show error message

    if os.path.exists(new):
        print(_("Error while renaming %s to %s! -> %s already exists!") % (ori, new, new))
        error = "[Errno 17] %s" % os.strerror(17)
        return False, error

    try:
        os.renames(ori, new)
        print("Renaming %s to %s" % (ori, new))
        return True, None
    except Exception as e:
        print(_("Error while renaming %s to %s!") % (ori, new))
        print(e)
        return False, e


def insert_at(name, path, text, pos):
    """ Append text at given position"""
    if pos >= 0:
        ini = name[0:pos]
        end = name[pos:len(name)]
        newname = ini + text + end
    else:
        newname = name + text

    newpath = get_new_path(newname, path)
    return str(newname), str(newpath)


def delete_from(name, path, ini, to):
    """ Delete chars from ini till to"""
    textini = name[0:ini]
    textend = name[to+1:len(name)]
    newname = textini + textend

    newpath = get_new_path(newname, path)
    return str(newname), str(newpath)

def cut_extension(name, path):
    """ Remove extension from file name """

    if '.' in name:
        ext = name.split('.')[-1]
        name = name[0:len(name)-len(ext)-1]
        path = path[0:len(path)-len(ext)-1]
        return name, path, ext
    else:
        return name, path, ''

def add_extension(name, path, ext):
    """ Add extension to file name """

    if ext != '' and ext != None and name != '' and name != None:
        name = name + '.' + ext
        path = path + '.' + ext
    return name, path
