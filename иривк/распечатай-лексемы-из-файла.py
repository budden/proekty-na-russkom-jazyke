#!/usr/bin/python3.7

import os
import sys
import pathlib
import re
import requests
from subprocess import call
import threading
import pygments
from pygments.lexers import get_lexer_for_filename
import pygments.token 
from concurrent.futures import ThreadPoolExecutor

## Появились ложноположительные срабатывания. Пытаемся распечатать русские лексемы, которые являются 
## такими срабатываниями
## Принимает в качестве параметра имя файла. Кодировку можно поменять в исходном тексте

кодировка = 'utf-8'

def main():
    file_path = sys.argv[1]
    file_ext = os.path.splitext(file_path)[1]
    lexer = get_lexer_for_filename(file_ext)
    if lexer is None:
        print("Не удалось определить лексер")
        exit(1)

    print("лексер = %s" % lexer.name)

    with open(file_path, 'r', encoding=кодировка, errors = 'ignore') as f:
        лексемы = pygments.lex(f.read(), lexer)
        for token, value in лексемы:
            if pygments.token.is_token_subtype(token, pygments.token.Name):
                if re.search('[а-яА-ЯёЁ]', value):
                    print("класс = %s, текст = %s" % (token, value))
                

main()

