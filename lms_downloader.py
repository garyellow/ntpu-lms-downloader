import getpass
import os
import random
import string
import time

import requests
from bs4 import BeautifulSoup as Bs
from fake_useragent import UserAgent

import secret

max_file_size = 32 * 1024 * 1024
min_sleep_time = 2
max_sleep_time = 4

user_data = {
    'account': secret.user_name,
    'password': secret.user_password,
}

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

    print('開始搜尋%s學年度第%s學期的課程' % (semester_num[0:3], semester_num[-1]))
    classes = semester.find_all('a', {'class': 'link'})
    for class_ in classes:
        class_name = class_.text.split(' ')[0]
        class_name = normalize_str(class_name)
        class_path = os.path.join(semester_path, class_name)
        if check_create(class_path):
            print('已下載過 %s 的檔案' % class_name)
            continue

        time.sleep(random.uniform(min_sleep_time, max_sleep_time))

        class_id = class_.get('href').split('/')[-1]
        print('找到未下載課程：' + class_name)

        doc_list_html = login.get(doc_list_url % (class_id, 1), headers={'user-agent': UserAgent().random})
        doc_list_html.encoding = 'utf-8'
        doc_list = Bs(doc_list_html.text, 'html.parser')
        page_num = 1 if len(doc_list.find_all('span', {'class': 'item'})) == 0 else len(doc_list.find_all('span', {'class': 'item'}))

        for page in range(1, page_num + 1):
            doc_list_html = login.get(doc_list_url % (class_id, page), headers={'user-agent': UserAgent().random})
            doc_list_html.encoding = 'utf-8'
            doc_list = Bs(doc_list_html.text, 'html.parser')

            docs = doc_list.find_all('div', {'class': 'Econtent'})

            if len(docs) == 0:
                print(class_name + '沒有任何上課教材')
                break

            for doc in docs:
                time.sleep(random.uniform(min_sleep_time, max_sleep_time))

                doc_name = doc.find('a').text
                doc_name = normalize_str(doc_name)
                doc_id = doc.find('a').get('href').split('=')[-1]

                doc_html = login.get(doc_url % (class_id, doc_id), headers={'user-agent': UserAgent().random})
                doc_html.encoding = 'utf-8'
                DOC = Bs(doc_html.text, 'html.parser')

                download_path = os.path.join(class_path, "上課教材", doc_name)

                attachments = DOC.find_all('a', {'target': '_blank'})

                for attachment in attachments:
                    if "/sys/read_attach.php?id=" not in attachment.get('href') or \
                            "".join(filter(lambda x: x in string.ascii_letters, attachment.text)) == "":
                        continue

                    attachment_name = attachment.text
                    attachment_name = normalize_str(attachment_name)
                    attachment_id = attachment.get('href').split('=')[-1]

                    if os.path.isfile(os.path.join(download_path, attachment_name)):
                        print(attachment_name + ' 已下載')
                        continue

                    time.sleep(random.uniform(min_sleep_time, max_sleep_time))

                    file = login.get(download_url % attachment_id, headers={'user-agent': UserAgent().random}, stream=True)
                    if int(file.headers['Content-Length']) > max_file_size:
                        print(attachment_name + ' 檔案太大，跳過')
                    else:
                        if not os.path.exists(download_path):
                            os.makedirs(download_path)

                        print('下載 ' + attachment_name, end='')
                        with open(os.path.join(download_path, attachment_name), 'wb') as f:
                            for chunk in file.iter_content(chunk_size=512):
                                if chunk:
                                    f.write(chunk)
                                    f.flush()
                        print(' 完成')

        hw_list_html = login.get(hw_list_url % class_id, headers={'user-agent': UserAgent().random})
        hw_list_html.encoding = 'utf-8'
        hw_list = Bs(hw_list_html.text, 'html.parser')

        hws = hw_list.find_all('tr', {'onmouseover': 'this.className="rowOver"'})

        if len(hws) == 0:
            print(class_name + '沒有任何作業')
        else:
            for hw in hws:
                time.sleep(random.uniform(min_sleep_time, max_sleep_time))

                hw_name = hw.find('td', {'align': 'left'}).find('a').text
                hw_name = normalize_str(hw_name)
                hw_id = hw.find('td', {'align': 'left'}).find('a').get('href').split('=')[-1]

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
                    attachment_id = attachments[num].get('href').split('=')[-1]

                    if os.path.isfile(os.path.join(download_path, attachment_name)):
                        print(attachment_name + ' 已下載')
                        continue

                    time.sleep(random.uniform(min_sleep_time, max_sleep_time))

                    file = login.get(download_url % attachment_id, headers={'user-agent': UserAgent().random}, stream=True)
                    if int(file.headers['Content-Length']) > max_file_size:
                        print(attachment_name + ' 檔案太大，跳過')
                    else:
                        if not os.path.exists(download_path):
                            os.makedirs(download_path)

                        print('下載 ' + attachment_name, end='')
                        with open(os.path.join(download_path, attachment_name), 'wb') as f:
                            for chunk in file.iter_content(chunk_size=512):
                                if chunk:
                                    f.write(chunk)
                                    f.flush()
                        print(' 完成')

                myself_id = HW.find('span', {'class': 'toolWrapper'}).find_all('a')[-1].get('href').split('=')[-1]
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
                    attachment_id = attachment.find_all('a')[-1].get('href').split('=')[-1]

                    if os.path.isfile(os.path.join(download_path, attachment_name)):
                        print(attachment_name + ' 已下載')
                        continue

                    time.sleep(random.uniform(min_sleep_time, max_sleep_time))

                    file = login.get(download_url % attachment_id, headers={'user-agent': UserAgent().random}, stream=True)
                    if int(file.headers['Content-Length']) > max_file_size:
                        print(attachment_name + ' 檔案太大，跳過')
                    else:
                        if not os.path.exists(download_path):
                            os.makedirs(download_path)

                        print('下載 ' + attachment_name, end='')
                        with open(os.path.join(download_path, attachment_name), 'wb') as f:
                            for chunk in file.iter_content(chunk_size=512):
                                if chunk:
                                    f.write(chunk)
                                    f.flush()
                        print(' 完成')

        check_remove(class_path)
        print('成功下載 ' + class_name + ' 的檔案\n')

print('所有檔案下載完成')
