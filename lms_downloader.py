import getpass
import os
import random
import shutil
import string
import time

import requests
from bs4 import BeautifulSoup as Bs
from fake_useragent import UserAgent as Ua

import secret

# 最大檔案大小(byte)
max_file_size = 32 * 1024 * 1024

# 爬蟲延遲時間(秒)
min_sleep_time = 2.5
max_sleep_time = 4

# 建立登入資料
user_data = {
    'account': secret.user_name,
    'password': secret.user_password,
}

# 預設網址及路徑
login_url = 'https://lms.ntpu.edu.tw/sys/lib/ajax/login_submit.php'
all_class_url = 'https://lms.ntpu.edu.tw/home.php?f=allcourse'
doc_list_url = 'https://lms.ntpu.edu.tw/course.php?courseID=%s&f=doclist&order=&precedence=DESC&page=%d'
doc_url = 'https://lms.ntpu.edu.tw/course.php?courseID=%s&f=doc&cid=%s'
hw_list_url = 'https://lms.ntpu.edu.tw/course.php?courseID=%s&f=hwlist'
hw_url = 'https://lms.ntpu.edu.tw/course.php?courseID=%s&f=hw&hw=%s'
download_url = 'https://lms.ntpu.edu.tw/sys/read_attach.php?id=%s'
download_dir = 'download'
youtube_file = 'youtube.txt'
other_file = 'other.txt'
temp_file = 'temp.txt'


# 英文關鍵字
en_keyword = ['1', '英文', '英', 'English', 'english', 'En', 'en']


# 確認是否成功登入
def check_login(login_html):
    while '權限不足' in login_html.text:
        print('登入失敗')
        print('請輸入帳密登入')
        user_data['account'] = input('學號：')
        user_data['password'] = getpass.getpass('密碼：')
        print()

        login.post(login_url, headers={'user-agent': Ua().random}, data=user_data)
        login_html = login.get(all_class_url, headers={'user-agent': Ua().random})
        login_html.encoding = 'utf-8'

    return login_html


# 字串正規化，用來確保檔案路徑合法
def normalize_str(s):
    return "".join(filter(lambda x: x not in '\\/:*?"<>|' + string.whitespace, s))


# 檢查是否還需下載，順便建立檔案來表示下載中
def check_create(path):
    if os.path.isdir(path) and not os.path.isfile(os.path.join(path, temp_file)):
        return True
    else:
        os.makedirs(path, exist_ok=True)
        open(os.path.join(path, temp_file), 'w').close()
        return False


# 移除用來表示下載中的檔案，並整理空資料夾
def check_remove(path):
    os.remove(os.path.join(path, temp_file))
    if not os.listdir(path):
        os.rmdir(path)


# 下載檔案
def download_file(url, path, name):
    wait()
    with login.get(url, headers={'user-agent': Ua().random}, stream=True) as r:
        if int(r.headers['Content-Length']) > max_file_size:
            print(name + ' 檔案太大，跳過')
        else:
            os.makedirs(path, exist_ok=True)

            print('下載 ' + name, end='')
            with open(os.path.join(path, name), 'wb') as F:
                shutil.copyfileobj(r.raw, F)
            print(' 完成')


# 等待
def wait():
    time.sleep(random.uniform(min_sleep_time, max_sleep_time))


login = requests.Session()
login.keep_alive = False
login.adapters.DEFAULT_RETRIES = 10
login.post(login_url, headers={'user-agent': Ua().random}, data=user_data)

ac_html = login.get(all_class_url, headers={'user-agent': Ua().random})
ac_html.encoding = 'utf-8'
ac_html = check_login(ac_html)
print('登入成功')

all_class = Bs(ac_html.text, 'html.parser')
semesters = all_class.find_all('div', {'style': 'padding-bottom:20px'})
semesters.reverse()

language = 1 if input('\n設定課程資料夾語言\n中文(0) 英文(1)\n>> ') in en_keyword else 0

while True:
    # 輸入關鍵字
    target = input('\n請輸入要下載的課程名稱或教授姓名(關鍵字即可)\n>> ')
    print()

    # 搜尋每個學期的課程
    for semester in semesters:
        semester_num = semester.find('div', {'style': 'float:left'}).text
        semester_num = semester_num[0:3] + '-' + semester_num[-1]
        semester_path = os.path.join(download_dir, semester_num)

        if len(target) == 0:
            print('\n開始搜尋%s學年度第%s學期的課程' % (semester_num[0:3], semester_num[-1]))

        # 搜尋每個課程
        classes = semester.find_all('tr', {'onmouseover': 'this.className="postRowOver"'})
        for class_ in classes:
            # 若課程名稱或教授姓名中不包含關鍵字則跳過
            if target not in class_.find('a', {'class': 'link'}).text + ' ' + class_.find('div', {'title': '0'}).text:
                continue

            cur_class = class_.find('a', {'class': 'link'})

            class_name = ' '.join(cur_class.text.split()[language:]) if language else cur_class.text.split()[language]
            class_path = os.path.join(semester_path, class_name)
            if check_create(class_path):
                print('已下載過 %s 的檔案' % class_name)
                time.sleep(random.uniform(min_sleep_time, max_sleep_time) / 6)
                continue

            class_id = cur_class['href'].split('/')[-1]
            print('\n找到未下載課程：' + class_name)

            # 搜尋上課教材
            wait()
            with login.get(doc_list_url % (class_id, 1), headers={'user-agent': Ua().random}) as doc_list_html:
                doc_list_html.encoding = 'utf-8'
                doc_list = Bs(doc_list_html.text, 'html.parser')
                page_num = 1 if len(doc_list.find_all('span', {'class': 'item'})) == 0 else len(doc_list.find_all('span', {'class': 'item'}))

                # 遍歷每一頁
                for page in range(1, page_num + 1):
                    wait()
                    doc_list_html = login.get(doc_list_url % (class_id, page), headers={'user-agent': Ua().random})
                    doc_list_html.encoding = 'utf-8'
                    doc_list = Bs(doc_list_html.text, 'html.parser')

                    docs = doc_list.find_all('div', {'class': 'Econtent'})

                    if len(docs) == 0:
                        print(class_name + ' 沒有任何上課教材')
                        break

                    # 搜尋每個上課教材
                    for doc in docs:
                        doc_name = doc.find('a').text
                        doc_name = normalize_str(doc_name)
                        doc_id = doc.find('a')['href'].split('=')[-1]

                        wait()
                        doc_html = login.get(doc_url % (class_id, doc_id), headers={'user-agent': Ua().random})
                        doc_html.encoding = 'utf-8'
                        DOC = Bs(doc_html.text, 'html.parser')

                        download_path = os.path.join(class_path, '上課教材', doc_name)

                        attachments = DOC.find_all('a')

                        # 搜尋某上課教材的每個附件
                        for attachment in attachments:
                            if len(attachment.text.strip(string.digits + '.')) == 0 or attachment.get('href') is None:
                                continue

                            # 把網址分類，非檔案會進到裡面
                            if not attachment['href'].startswith('/sys/'):
                                # youtube 連結
                                if attachment['href'].startswith('https://www.youtube.com/'):
                                    youtube_path = os.path.join(download_path, youtube_file)
                                    if not os.path.isfile(youtube_path) or attachment['href'] + '\n' not in open(youtube_path, 'r').readlines():
                                        os.makedirs(download_path, exist_ok=True)
                                        with open(youtube_path, 'a') as f:
                                            f.write(attachment['href'] + '\n')
                                # 其他外部連結
                                elif attachment['href'].startswith('http') and '.ntpu.edu.tw' not in attachment['href'] and \
                                        attachment['href'] != 'http://www.powercam.com.tw/':
                                    other_path = os.path.join(download_path, other_file)
                                    if not os.path.isfile(other_path) or attachment['href'] + '\n' not in open(other_path, 'r').readlines():
                                        os.makedirs(download_path, exist_ok=True)
                                        with open(other_path, 'a') as f:
                                            f.write(attachment['href'] + '\n')
                                continue

                            attachment_name = attachment.text
                            attachment_name = normalize_str(attachment_name)
                            attachment_id = attachment['href'].split('=')[-1]

                            if os.path.isfile(os.path.join(download_path, attachment_name)):
                                print(attachment_name + ' 已下載')
                                continue

                            download_file(download_url % attachment_id, download_path, attachment_name)

            # 搜尋作業
            wait()
            with login.get(hw_list_url % class_id, headers={'user-agent': Ua().random}) as hw_list_html:
                hw_list_html.encoding = 'utf-8'
                hw_list = Bs(hw_list_html.text, 'html.parser')

                hws = hw_list.find_all('tr', {'onmouseover': 'this.className="rowOver"'})

                if len(hws) == 0:
                    print(class_name + ' 沒有任何作業')
                else:
                    # 搜尋每個作業
                    for hw in hws:
                        hw_name = hw.find('td', {'align': 'left'}).find('a').text
                        hw_name = normalize_str(hw_name)
                        hw_id = hw.find('td', {'align': 'left'}).find('a')['href'].split('=')[-1]

                        wait()
                        hw_html = login.get(hw_url % (class_id, hw_id), headers={'user-agent': Ua().random})
                        hw_html.encoding = 'utf-8'
                        HW = Bs(hw_html.text, 'html.parser')

                        attach = HW.find_all('td', {'class': 'cell col2 bg'})[-1]
                        if len(attach.text) == 0:
                            print(hw_name + ' 沒有作業附件')
                            continue

                        download_path = os.path.join(class_path, '作業檔案', hw_name, '作業附件')

                        # 搜尋某作業的每個附件
                        attachments = attach.find_all('a')
                        for num in range(len(attachments)):
                            attachment_name = attachments[num].text
                            attachment_name = normalize_str(attachment_name)
                            attachment_id = attachments[num]['href'].split('=')[-1]

                            if os.path.isfile(os.path.join(download_path, attachment_name)):
                                print(attachment_name + ' 已下載')
                                continue

                            download_file(download_url % attachment_id, download_path, attachment_name)

                        myself_id = HW.find('span', {'class': 'toolWrapper'}).find_all('a')[-1]['href'].split('=')[-1]

                        wait()
                        myself_html = login.get(doc_url % (class_id, myself_id), headers={'user-agent': Ua().random})
                        myself_html.encoding = 'utf-8'
                        me = Bs(myself_html.text, 'html.parser')

                        attach = me.find('div', {'class': 'block'})
                        if attach is None:
                            print(hw_name + ' 沒有繳交作業')
                            continue

                        download_path = os.path.join(class_path, '作業檔案', hw_name, '我的作業')

                        # 搜尋某作業中的繳交檔案
                        attachments = attach.find_all('div')
                        for attachment in attachments:
                            attachment_name = attachment.find_all('a')[-1].text
                            attachment_name = normalize_str(attachment_name)
                            attachment_id = attachment.find_all('a')[-1]['href'].split('=')[-1]

                            if os.path.isfile(os.path.join(download_path, attachment_name)):
                                print(attachment_name + ' 已下載')
                                continue

                            download_file(download_url % attachment_id, download_path, attachment_name)

            check_remove(class_path)
            print('成功下載 ' + class_name + ' 的資料\n')

    if input('\n下載結束，是否要繼續下載？(Y/n)：') in ['n', 'N']:
        break
