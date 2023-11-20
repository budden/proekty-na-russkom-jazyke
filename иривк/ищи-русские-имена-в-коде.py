import os
import re
import requests
from subprocess import call
import threading
import pygments
from pygments.token import Text
from pygments import lex
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
интересныеЯзыки = ['Ruby', 'VB.net', 'GLSL', 'Perl', 'PHP', 'Python', 'Common Lisp', 'OCaml', 'Java', 'C#', 'JavaScript', 'C', 'C++', 'Prolog', 'Go', 'Rust', 'Scheme', 'Transact-SQL', 'PL-SQL', 'tsql', 'PL/1', 'plsql', 'pli', 'Pascal', 'Delphi', 'Modula-2']


def НайденЯзыкКоторыйМыНеЗаказывали(lexer_name, url, log):
    if lexer_name not in найденныеЯзыкиКоторыеМыНеЗаказывали:
        найденныеЯзыкиКоторыеМыНеЗаказывали.append(lexer_name)
        log.write(f"{url} - Лексер определил язык, который не включеён в список разрешённых. {lexer.name}  \n")
        print(f"{url} - Лексер определил язык, который не включеён в список разрешённых. {lexer.name} ")

def download_repo(url, log):
    httpsPrefix = "https://github.com/"
    assert(url.startswith(httpsPrefix))
    repo_dir = "cloned_repos/" + url.split('/')[3:]
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
            log.write(f"{readme_url} - Не найден README.  \n")
            print(f"{readme_url} - Не найден README.")
    return 0


def analyze_repo(url, log):
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
                        lexer = None
                        try:
                            lexer = pygments.lexers.get_lexer_for_filename(file_ext)
                        except:
                            log.write(f"{url}...{file_ext} - Лексер не определил язык. \n")
                            print(f"{url}...{file_ext} - Лексер не определил язык. ")
                            pass
                        if lexer and not(lexer.name in интересныеЯзыки):
                            НайденЯзыкКоторыйМыНеЗаказывали(lexer.name, url, log)
                        if file_ext and lexer and (lexer.name in интересныеЯзыки) and not file_ext.endswith(".md"):
                                #with open(file_path, 'r', encoding='utf-8') as f:
                                def ИщиРусскиеИменаВТакойКодировке(encoding):
                                    try:
                                        with open(file_path, 'r', encoding=encoding, errors = 'ignore') as f:
                                            content = f.read()
                                        if not re.search('[а-яА-ЯёЁ]',content):
                                            return False
                                        with open(file_path, 'r') as f:
                                            for token, value in lex(f.read(), lexer):
                                                if token is pygments.token.Name:
                                                    if re.search('[а-яА-ЯёЁ]', value):
                                                        return True
                                        return False
                                    except:
                                        log.write(f"{url} - Ошибка при разборе файла. \n")
                                        print(f"{url} - Ошибка при разборе файла.")
                                        return False
                                    
                                успех = ИщиРусскиеИменаВТакойКодировке('utf-8') or ИщиРусскиеИменаВТакойКодировке('cp1251')
                                if успех:
                                    files_with_russian.append(file_path)
            if len(files_with_russian) == 0:
                log.write(f"{url} - Не обнаруженно файлов содержащих русские символы. \n")
                print(f"{url} - Не обнаруженно файлов содержащих русские символы.")
            else:
                log.write(f"{url} - Русский язык был найден в этом репозитории: {files_with_russian}  \n")
                print(f"{url} - Русский язык был найден в этом репозитории: {files_with_russian}")
                return
                    
    except Exception as e:
        log.write(f"{url} - Произошла ошибка: {str(e)}  \n")
        print(f"{url} - Произошла ошибка: {str(e)}")
    log.flush()


def main():
    # Чтение ссылок из файла
        with open("repos.txt", "r") as file:
            urls = file.readlines()
            urls = [url.strip() for url in urls]
        with open("log.txt", "w") as log:
            for url in urls:
                analyze_repo(url,log)
                
main()

print(f"Другие незамеченные языки: {найденныеЯзыкиКоторыеМыНеЗаказывали}")
with open("NotFound.txt", "w") as log:
	log.write(f'Другие незамеченные языки: {найденныеЯзыкиКоторыеМыНеЗаказывали} \n')
