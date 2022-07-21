# ntpu lms downloader

## 主要功能
爬取並下載國立臺北大學數位學苑2.0上的資料

## 使用方法
1. 直接[下載](https://github.com/garyellow/ntpu_lms_downloader/archive/refs/heads/master.zip)這個 repo
2. 解壓縮後用**命令提示字元**(windows)或**終端機**(mac, linux)進入該資料夾
3. 輸入 `pip install -r requirements.txt` or `pip3 install -r requirements.txt` 檢查 python 套件版本
4. 將學號和密碼填入 **secret.py** 中 (非必要，但有填就能不用每次都打帳密)
5. 輸入 `python lms_downloader.py` or `python3 lms_downloader.py` 開始下載
6. 耐心等候，~可以先吃飯睡覺打東東~，如果程式停掉了，[下面](#%E5%85%B6%E4%BB%96)有說要怎麼處理

## 簡單說明
1. 程式會在同一個資料夾下建造一個 **download** 資料夾  
2. 資料夾內會有各個學期的子資料夾，如 **110-1**  
3. 這些資料夾裡面又會有那學期每堂課的子資料夾
4. 程式會下載每堂課的資料到那堂課的資料夾中

## 下載資料
1. **上課教材**和**作業**中的所有附件檔案
2. **上課教材**中的youtube影片連結，會存到 **youtube.txt** 中
3. **上課教材**中的其他連結，會存到 **other.txt** 中
    > 內文的部分因為每個老師的習慣不同，不太好爬取  
    有需要的人再自己額外去找來存

## 錯誤資訊
* 如果未輸入或輸入錯誤導致登入失敗，程式會再提供輸入區重新輸入
* 預設爬蟲的間隔時間是 2 ~ 4 秒，若常常碰到 Max retries exceeded 的 exception，可以將秒數調高，比較不會被系統擋
* 如果程式因為網路不穩等連線問題停掉，直接關掉重開就好  
* 如果來不及下載完也可以直接關掉，下次會繼續下載
    > 但如果在儲存檔案時發生錯誤，該檔案有可能會損壞，建議把最後下載的檔案或課程刪掉，下次執行會重新下載
* 注意不要讓電腦進入睡眠或休眠，程式有大機率會停掉

## 其他
* 內文的部分因為每個老師的習慣不同，不太好爬取，就不存了
* 預設大於 **32MB** 的檔案會跳過，有下載大檔案需求的可以再自行修改程式碼
* 下載前程式會先檢查有沒有下載過，沒下載過的才會繼續下載
* 如果要重新下載某課程的檔案，可以刪掉該課程的資料夾
    > 刪掉其他裡面的資料夾或資料都是**不會**觸發重新下載的
* 程式有什麼 bug 或想要多什麼功能都可以到 [**issue**](https://github.com/garyellow/ntpu_lms_downloader/issues) 頁面提出  
  也可以 [**fork**](https://github.com/garyellow/ntpu_lms_downloader/fork) 這個 repo 自己修好或新增功能
