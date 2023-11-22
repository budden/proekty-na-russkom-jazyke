#!/usr/bin/python3.7

import os
import pathlib
import re
import requests
from subprocess import call
import threading
import pygments
from pygments.lexers import get_lexer_for_filename
import pygments.token 
from concurrent.futures import ThreadPoolExecutor

### Проверен на python 3.7.5
### Для установки:
### python3.7 -m pip install requests re 
### Перед запуском надо стереть поддиректорию cloned_repos, если она есть, иначе повторная обработка ранее обработанных URL-ов
### будет неверной. Запуск без параметров. Список репозиториев - простой текст, repos.txt. 
### Вы должны настроить клонирование репозиториев с гитхаба по URL вида git@github.com:user/repo, т.е. добавить свой
### ssh-ключ на гитхаб. 

возможныеПутиК_README_mdВнутриРепозитория = ["/blob/main/README.md", "/blob/master/README.md", "/README.md", "/", ""]    
найденныеЯзыкиКоторыеМыНеЗаказывали = []
интересныеЯзыки = ['Ruby', 'VB.net', 'GLSL', 'Perl', 'PHP', 'Python', 'Common Lisp', 'OCaml', 'Java', 
    'C#', 'JavaScript', 'C', 'C++', 'Prolog', 'Go', 'Rust', 'Scheme', 'Transact-SQL', 'PL-SQL', 'tsql', 'PL/1', 'plsql', 'pli', 'Pascal', 'Delphi', 'Modula-2',
    'Modelica', 'Lua', 'TypeScript', 'Haskell']

неинтересныеРасширенияФайлов = ['.md','.txt','.html','.xml','.XML','.json','.jpg','.png','.svg','.ttf','.sample']


def НайденЯзыкКоторыйМыНеЗаказывали(lexer_name, url, log, файлДляНезаказанныхЯзыков):
    if lexer_name not in найденныеЯзыкиКоторыеМыНеЗаказывали:
        найденныеЯзыкиКоторыеМыНеЗаказывали.append(lexer_name)
        log.write(f"{url} - Лексер определил язык, который не включён в список разрешённых. {lexer_name}  \n")
        print(f"{url} - Лексер определил язык, который не включён в список разрешённых. {lexer_name} ")
        файлДляНезаказанныхЯзыков.write("%s\n" % lexer_name)

def download_repo(url, log):
    httpsPrefix = "https://github.com/"
    assert(url.startswith(httpsPrefix))
    repo_dir = os.path.join("cloned_repos",*url.split('/')[3:])
    gitUrl = url.replace(httpsPrefix, "git@github.com:")
    try:
        call(['git', 'clone', '--depth', '1', gitUrl, repo_dir])
        #git.Repo.clone_from(url, repo_dir)
        return repo_dir
    except Exception as e:
        log.write(f"{gitUrl} - Произошла ошибка при клонирровании репозитория:: {str(e)}  \n")
        print(f"{gitUrl} - Произошла ошибка при клонирровании репозитория: {str(e)}")
    return 0

def analyze_readme(url, log):
    for suburl in возможныеПутиК_README_mdВнутриРепозитория:
        try:
            readme_url = url + suburl
            response = requests.get(readme_url)
            if response.status_code == 200:
                content = response.text
                if not(re.search('[а-яА-Я]', content)):
                    log.write(f"{readme_url} - Нет русских символов в README.  \n")
                    print(f"{readme_url} - Нет русских символов в README.")
                    return 0
                else:
                    return 1
        except Exception as e:
            print(f"{readme_url} - Не найден README.")
    return 0


def analyze_repo(url, log, файлДляНезаказанныхЯзыков):
    try:
            print(f"{url} STP загрузуа и анализ README")
            res = analyze_readme(url, log)
            if not (res == 1):
                return
            print(f"{url} STP Загрузка репозитория")
            res = download_repo(url, log)
            if res == 0:
                return
            print(f"{url} Анализ репозитория")
            files_with_russian = []
            for root, dirs, files in os.walk(res):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_ext = os.path.splitext(file_path)[1]
                        неинтересноеРасширение = False
                        for расш in неинтересныеРасширенияФайлов:
                            if file_ext.endswith(расш):
                                неинтересноеРасширение = True
                                break
                        
                        if неинтересноеРасширение:
                            continue

                        lexer = None
                        if file_ext:
                            try:
                                lexer = get_lexer_for_filename(file_ext)
                            except:
                                print(f"{url}...{file_ext} - Лексер не определил язык. ")
                                lexer = None
                        if lexer is None:
                            continue
                        if not(lexer.name in интересныеЯзыки):
                            НайденЯзыкКоторыйМыНеЗаказывали(lexer.name, url, log, файлДляНезаказанныхЯзыков)
                        if (lexer.name in интересныеЯзыки):
                                def ИщиРусскиеИменаВТакойКодировке(encoding):
                                    try:
                                        with open(file_path, 'r', encoding=encoding) as f:
                                            content = f.read()
                                        if not re.search('[а-яА-ЯёЁ]',content):
                                            return False
                                        with open(file_path, 'r', encoding=encoding) as f:
                                            лексемы = pygments.lex(f.read(), lexer)
                                            for token, value in лексемы:
                                                # print(token)
                                                if pygments.token.is_token_subtype(token, pygments.token.Name):
                                                    if re.search('[а-яА-ЯёЁ]', value):
                                                        # аномалия с cp1251, во всяком случае, в минифицированных файлах
                                                        if not (encoding=='cp1251' and value == 'п'):
                                                            return True
                                        return False
                                    except:
                                        print(f"{url} - Ошибка при разборе файла.")
                                        return None
                                    
                                успех = ИщиРусскиеИменаВТакойКодировке('utf-8') 
                                if успех is None:
                                    успех = ИщиРусскиеИменаВТакойКодировке('cp1251')
                                if успех == True:
                                    files_with_russian.append(file_path)
                                
            if len(files_with_russian) == 0:
                log.write(f"{url} - Не обнаруженно файлов содержащих русские символы. \n")
                print(f"{url} - Не обнаруженно файлов содержащих русские символы.")
            else:
                log.write(f"{url} - Русский язык был найден в этом репозитории: {files_with_russian}  \n")
                log.flush()
                print(f"{url} - Русский язык был найден в этом репозитории: {files_with_russian}")
                return
                    
    except Exception as e:
        log.write(f"{url} - Произошла ошибка: {str(e)}  \n")
        print(f"{url} - Произошла ошибка: {str(e)}")
    log.flush()


def main():
    # Чтение ссылок из файла
    with open("ЯзыкиКоторыеМыНеЗаказывали.txt", "w") as файлДляНезаказанныхЯзыков:
        with open("repos.txt", "r") as file:
            urls = file.readlines()
            urls = [url.strip() for url in urls]
        with open("log.txt", "w") as log:
            for url in urls:
                analyze_repo(url,log,файлДляНезаказанныхЯзыков)
                
main()

