# ntpu_lms_downloader

## 主要功能
爬取並下載國立臺北大學數位學苑2.0上的資料

## 使用方法
1. 直接[下載](https://github.com/garyellow/ntpu_lms_downloader/archive/refs/heads/master.zip)這個 repo  
2. 檢查 python 套件版本 `pip install -r requirements.txt` or `pip3 install -r requirements.txt`
3. 將學號和密碼填入 **secret.py** 中  
    > 注意 secret.py 和 python lms_downloader.py 要放在同一個資料夾
4. 執行 python 檔 `python lms_downloader.py` or `python3 lms_downloader.py`  
5. ~吃飯睡覺打東東~

## 簡單說明
1. 程式會在同一個資料夾下建造一個 **download** 資料夾  
2. 資料夾內會有各個學期的子資料夾，如 **110-1**  
3. 這些資料夾又會再分成那學期的每堂課
4. 程式會下載每堂課中**上課教材**和**作業**的所有檔案到那堂課的資料夾
    > 只有檔案的部分會下載，連結或內文的部分因為每個老師的習慣不同，有點難整合
    
## 其他
* 如果未輸入或輸入錯誤導致登入失敗，程式會再提供輸入區重新輸入    
* 預設大於 **64MB** 的檔案會跳過，有這個需求的可以自行修改程式碼  
* 下載時程式會先檢查該檔案有沒有下載過，檢查到有沒下載過的地方會繼續下載  
    > 所以如果程式因為網路不穩等連線問題停掉，直接關掉重開就好  
    > 如果來不及下載完也可以直接關掉
* 程式有什麼 bug 或想要多什麼功能都可以到 [**issue**](https://github.com/garyellow/ntpu_lms_downloader/issues) 頁面提出  
  也可以 [**fork**](https://github.com/garyellow/ntpu_lms_downloader/fork) 這個 repo 自己修好或新增功能
