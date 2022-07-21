import getpass
import os
import random
import shutil
import string
import time

import requests
from bs4 import BeautifulSoup as Bs
from fake_useragent import UserAgent

import secret

# 最大檔案大小(byte)
max_file_size = 32 * 1024 * 1024

# 爬蟲延遲時間(秒)
min_sleep_time = 2
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
temp_file = 'temp.txt'


def check_login(login_html):
    while login_html.text.find('權限不足') != -1:
        print('登入失敗')
        print('請輸入帳密登入')
        user_data['account'] = input('學號：')
        user_data['password'] = getpass.getpass('密碼：')
        print()

        login.post(login_url, headers={'user-agent': UserAgent().random}, data=user_data)
        login_html = login.get(all_class_url, headers={'user-agent': UserAgent().random})
        login_html.encoding = 'utf-8'

    return login_html


def normalize_str(s):
    return "".join(filter(lambda x: x not in string.whitespace, "".join(filter(lambda x: x not in '\\/:*?"<>|', s)).replace(' ', '_')))


def check_create(path):
    if os.path.isdir(path) and not os.path.isfile(os.path.join(path, temp_file)):
        return True
    else:
        os.makedirs(path, exist_ok=True)
        open(os.path.join(path, temp_file), 'w').close()
        return False


def check_remove(path):
    os.remove(os.path.join(path, temp_file))
    if not os.listdir(path):
        os.rmdir(path)


def download_file(url, path, name):
    with login.get(url, headers={'user-agent': UserAgent().random}, stream=True) as r:
        if int(r.headers['Content-Length']) > max_file_size:
            print(name + ' 檔案太大，跳過')
        else:
            os.makedirs(path, exist_ok=True)

            print('下載 ' + name, end='')
            with open(os.path.join(path, name), 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            print(' 完成')


def wait():
    time.sleep(random.uniform(min_sleep_time, max_sleep_time))


login = requests.Session()
login.keep_alive = False
login.adapters.DEFAULT_RETRIES = 10
login.post(login_url, headers={'user-agent': UserAgent().random}, data=user_data)

ac_html = login.get(all_class_url, headers={'user-agent': UserAgent().random})
ac_html.encoding = 'utf-8'
ac_html = check_login(ac_html)
print('登入成功')

all_class = Bs(ac_html.text, 'html.parser')
semesters = all_class.find_all('div', {'style': 'padding-bottom:20px'})
semesters.reverse()

for semester in semesters:
    semester_num = semester.find('div', {'style': 'float:left'}).text
    semester_num = semester_num[0:3] + '-' + semester_num[-1]
    semester_path = os.path.join(download_dir, semester_num)

    time.sleep(min_sleep_time)
    print('\n開始搜尋%s學年度第%s學期的課程' % (semester_num[0:3], semester_num[-1]))
    classes = semester.find_all('a', {'class': 'link'})
    for class_ in classes:
        class_name = class_.text.split(' ')[0]
        class_name = normalize_str(class_name)
        class_path = os.path.join(semester_path, class_name)
        if check_create(class_path):
            print('已下載過 %s 的檔案' % class_name)
            continue

        class_id = class_['href'].split('/')[-1]
        print('\n找到未下載課程：' + class_name)

        wait()
        doc_list_html = login.get(doc_list_url % (class_id, 1), headers={'user-agent': UserAgent().random})
        doc_list_html.encoding = 'utf-8'
        doc_list = Bs(doc_list_html.text, 'html.parser')
        page_num = 1 if len(doc_list.find_all('span', {'class': 'item'})) == 0 else len(doc_list.find_all('span', {'class': 'item'}))

        for page in range(1, page_num + 1):
            wait()
            doc_list_html = login.get(doc_list_url % (class_id, page), headers={'user-agent': UserAgent().random})
            doc_list_html.encoding = 'utf-8'
            doc_list = Bs(doc_list_html.text, 'html.parser')

            docs = doc_list.find_all('div', {'class': 'Econtent'})

            if len(docs) == 0:
                print(class_name + ' 沒有任何上課教材')
                break

            for doc in docs:
                doc_name = doc.find('a').text
                doc_name = normalize_str(doc_name)
                doc_id = doc.find('a')['href'].split('=')[-1]

                wait()
                doc_html = login.get(doc_url % (class_id, doc_id), headers={'user-agent': UserAgent().random})
                doc_html.encoding = 'utf-8'
                DOC = Bs(doc_html.text, 'html.parser')

                download_path = os.path.join(class_path, "上課教材", doc_name)

                attachments = DOC.find_all('a', {'target': '_blank'})

                for attachment in attachments:
                    if not attachment['href'].startswith('/sys/') or attachment.text.strip(string.digits + '.') == "":
                        continue

                    attachment_name = attachment.text
                    attachment_name = normalize_str(attachment_name)
                    attachment_id = attachment['href'].split('=')[-1]

                    if os.path.isfile(os.path.join(download_path, attachment_name)):
                        print(attachment_name + ' 已下載')
                        continue

                    wait()
                    download_file(download_url % attachment_id, download_path, attachment_name)

        wait()
        hw_list_html = login.get(hw_list_url % class_id, headers={'user-agent': UserAgent().random})
        hw_list_html.encoding = 'utf-8'
        hw_list = Bs(hw_list_html.text, 'html.parser')

        hws = hw_list.find_all('tr', {'onmouseover': 'this.className="rowOver"'})

        if len(hws) == 0:
            print(class_name + ' 沒有任何作業')
        else:
            for hw in hws:
                hw_name = hw.find('td', {'align': 'left'}).find('a').text
                hw_name = normalize_str(hw_name)
                hw_id = hw.find('td', {'align': 'left'}).find('a')['href'].split('=')[-1]

                wait()
                hw_html = login.get(hw_url % (class_id, hw_id), headers={'user-agent': UserAgent().random})
                hw_html.encoding = 'utf-8'
                HW = Bs(hw_html.text, 'html.parser')

                attach = HW.find_all('td', {'class': 'cell col2 bg'})[-1]
                if len(attach.text) == 0:
                    print(hw_name + ' 沒有作業附件')
                    continue

                download_path = os.path.join(class_path, '作業檔案', hw_name, "作業附件")

                attachments = attach.find_all('a')
                for num in range(len(attachments)):
                    attachment_name = attachments[num].text
                    attachment_name = normalize_str(attachment_name)
                    attachment_id = attachments[num]['href'].split('=')[-1]

                    if os.path.isfile(os.path.join(download_path, attachment_name)):
                        print(attachment_name + ' 已下載')
                        continue

                    wait()
                    download_file(download_url % attachment_id, download_path, attachment_name)

                myself_id = HW.find('span', {'class': 'toolWrapper'}).find_all('a')[-1]['href'].split('=')[-1]

                wait()
                myself_html = login.get(doc_url % (class_id, myself_id), headers={'user-agent': UserAgent().random})
                myself_html.encoding = 'utf-8'
                me = Bs(myself_html.text, 'html.parser')

                attach = me.find('div', {'class': 'block'})
                if attach is None:
                    print(hw_name + ' 沒有繳交作業')
                    continue

                download_path = os.path.join(class_path, '作業檔案', hw_name, "我的作業")

                attachments = attach.find_all('div')
                for attachment in attachments:
                    attachment_name = attachment.find_all('a')[-1].text
                    attachment_name = normalize_str(attachment_name)
                    attachment_id = attachment.find_all('a')[-1]['href'].split('=')[-1]

                    if os.path.isfile(os.path.join(download_path, attachment_name)):
                        print(attachment_name + ' 已下載')
                        continue

                    wait()
                    download_file(download_url % attachment_id, download_path, attachment_name)

        check_remove(class_path)
        print('成功下載 ' + class_name + ' 的檔案\n')

print('所有檔案下載完成')
