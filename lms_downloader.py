import os

import requests
from bs4 import BeautifulSoup as BS4
from fake_useragent import UserAgent

import secret

max_file_size = 64

user_data = {
    'account': secret.user_name,
    'password': secret.user_password,
}

login_url = 'https://lms.ntpu.edu.tw/sys/lib/ajax/login_submit.php'
all_class_url = 'https://lms.ntpu.edu.tw/home.php?f=allcourse'
doclist_url = 'https://lms.ntpu.edu.tw/course.php?courseID=%s&f=doclist&order=&precedence=DESC&page=%d'
doc_url = 'http://lms.ntpu.edu.tw/course.php?courseID=%s&f=doc&cid=%s'
hwlist_url = 'https://lms.ntpu.edu.tw/course.php?courseID=%s&f=hwlist'
hw_url = 'https://lms.ntpu.edu.tw/course.php?courseID=%s&f=hw&hw=%s'
download_url = 'https://lms.ntpu.edu.tw/sys/read_attach.php?id=%s'
download_dir = 'download'


def check_login(login_html):
    while login_html.text.find('權限不足') != -1:
        print('登入失敗')
        print('請輸入帳密登入')
        user_data['account'] = input('學號：')
        user_data['password'] = input('密碼：')
        print()

        home.post(login_url, headers={'user-agent': UserAgent().random}, data=user_data)
        login_html = home.get(all_class_url, headers={'user-agent': UserAgent().random})

    return login_html


def normalize_str(s):
    return "".join(filter(lambda x: x not in '\\/:*?"<>|', s))


home = requests.Session()
home.post(login_url, headers={'user-agent': UserAgent().random}, data=user_data)

ac_html = home.get(all_class_url, headers={'user-agent': UserAgent().random})
ac_html.encoding = 'utf-8'
ac_html = check_login(ac_html)

all_class = BS4(ac_html.text, 'html.parser')
semesters = all_class.find_all('div', {'style': 'padding-bottom:20px'})
semesters.reverse()

for semester in semesters:
    semester_num = semester.find('div', {'style': 'float:left'}).text
    classes = semester.find_all('a', {'class': 'link'})
    print('正在搜尋%s學年度第%s學期的課程' % (semester_num[0:3], semester_num[-1]))
    semester_num = semester_num[0:3] + '-' + semester_num[-1]

    for class_ in classes:
        class_name = class_.text.split(' ')[0]
        class_name = normalize_str(class_name)
        class_id = class_.get('href').split('/')[-1]
        print('找到課程：%s' % class_name)

        doclist_html = home.get(doclist_url % (class_id, 1), headers={'user-agent': UserAgent().random})
        doclist_html.encoding = 'utf-8'
        doclist = BS4(doclist_html.text, 'html.parser')
        page_num = 1 if len(doclist.find_all('span', {'class': 'item'})) == 0 else len(doclist.find_all('span', {'class': 'item'}))

        for page in range(1, page_num + 1):
            doclist_html = home.get(doclist_url % (class_id, page), headers={'user-agent': UserAgent().random})
            doclist_html.encoding = 'utf-8'
            doclist = BS4(doclist_html.text, 'html.parser')

            docs = doclist.find_all('div', {'class': 'Econtent'})

            if len(docs) == 0:
                print(class_name + '沒有任何上課教材')
                break

            for doc in docs:
                doc_name = doc.find('a').text
                doc_name = normalize_str(doc_name)
                doc_id = doc.find('a').get('href').split('=')[-1]

                doc_html = home.get(doc_url % (class_id, doc_id), headers={'user-agent': UserAgent().random})
                doc_html.encoding = 'utf-8'
                DOC = BS4(doc_html.text, 'html.parser')

                attach = DOC.find('div', {'class': 'block'})
                if attach is None:
                    continue

                attachments = attach.find_all('div')

                for attachment in attachments:
                    attachment_name = attachment.find_all('a')[-1].text
                    attachment_name = normalize_str(attachment_name)
                    attachment_id = attachment.find_all('a')[-1].get('href').split('=')[-1]

                    space_num = "".join(filter(lambda x: x in '0123456789.', attachment.find('span').text))
                    space_unit = "".join(filter(str.isalpha, attachment.find('span').text))

                    if space_unit == 'GB' or (space_unit == 'MB' and float(space_num) > max_file_size):
                        print(attachment_name + ' 檔案太大，跳過')
                    else:
                        download_path = os.path.join(os.getcwd(), download_dir, semester_num, class_name, "上課教材", doc_name)

                        if not os.path.exists(download_path):
                            os.makedirs(download_path)

                        if os.path.isfile(os.path.join(download_path, attachment_name)):
                            print(attachment_name + ' 已存在')
                        else:
                            print('下載 ' + attachment_name, end='')
                            open(os.path.join(download_path, attachment_name), 'wb').write(
                                home.get(download_url % attachment_id, headers={'user-agent': UserAgent().random}).content)
                            print(' 完成')

        hwlist_html = home.get(hwlist_url % class_id, headers={'user-agent': UserAgent().random})
        hwlist_html.encoding = 'utf-8'
        hwlist = BS4(hwlist_html.text, 'html.parser')

        hws = hwlist.find_all('tr', {'onmouseover': 'this.className="rowOver"'})

        if len(hws) == 0:
            print(class_name + '沒有任何作業')
            continue

        for hw in hws:
            hw_name = hw.find('td', {'align': 'left'}).find('a').text
            hw_name = normalize_str(hw_name)
            hw_id = hw.find('td', {'align': 'left'}).find('a').get('href').split('=')[-1]

            hw_html = home.get(hw_url % (class_id, hw_id), headers={'user-agent': UserAgent().random})
            hw_html.encoding = 'utf-8'
            HW = BS4(hw_html.text, 'html.parser')

            attach = HW.find_all('td', {'class': 'cell col2 bg'})[-1]
            if len(attach.text) != 0:
                attachments = attach.find_all('a')

                for num in range(len(attachments)):
                    attachment_name = attachments[num].text
                    attachment_name = normalize_str(attachment_name)
                    attachment_id = attachments[num].get('href').split('=')[-1]

                    space_num = "".join(filter(lambda x: x in '0123456789.', attach.find_all('span')[num].text))
                    space_unit = "".join(filter(str.isalpha, attach.find_all('span')[num].text))

                    if space_unit == 'GB' or (space_unit == 'MB' and float(space_num) > max_file_size):
                        print(attachment_name + ' 檔案太大，跳過')
                    else:
                        download_path = os.path.join(os.getcwd(), download_dir, semester_num, class_name, '作業', hw_name, "作業附件")

                        if not os.path.exists(download_path):
                            os.makedirs(download_path)

                        if os.path.isfile(os.path.join(download_path, attachment_name)):
                            print(attachment_name + ' 已存在')
                        else:
                            print('下載 ' + attachment_name, end='')
                            open(os.path.join(download_path, attachment_name), 'wb').write(
                                home.get(download_url % attachment_id, headers={'user-agent': UserAgent().random}).content)
                            print(' 完成')

            myself_id = HW.find('span', {'class': 'toolWrapper'}).find_all('a')[-1].get('href').split('=')[-1]
            myself_html = home.get(doc_url % (class_id, myself_id), headers={'user-agent': UserAgent().random})
            myself_html.encoding = 'utf-8'
            me = BS4(myself_html.text, 'html.parser')

            attach = me.find('div', {'class': 'block'})
            if attach is None:
                continue

            attachments = attach.find_all('div')

            for attachment in attachments:
                attachment_name = attachment.find_all('a')[-1].text
                attachment_name = normalize_str(attachment_name)
                attachment_id = attachment.find_all('a')[-1].get('href').split('=')[-1]

                space_num = "".join(filter(lambda x: x in '0123456789.', attachment.find('span').text))
                space_unit = "".join(filter(str.isalpha, attachment.find('span').text))

                if space_unit == 'GB' or (space_unit == 'MB' and float(space_num) > max_file_size):
                    print(attachment_name + ' 檔案太大，跳過')
                else:
                    download_path = os.path.join(os.getcwd(), download_dir, semester_num, class_name, '作業', hw_name, "我的作業")

                    if not os.path.exists(download_path):
                        os.makedirs(download_path)

                    if os.path.isfile(os.path.join(download_path, attachment_name)):
                        print(attachment_name + ' 已存在')
                    else:
                        print('下載 ' + attachment_name, end='')
                        open(os.path.join(download_path, attachment_name), 'wb').write(
                            home.get(download_url % attachment_id, headers={'user-agent': UserAgent().random}).content)
                        print(' 完成')
