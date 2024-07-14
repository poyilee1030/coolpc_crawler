<p float="left">
  <img src="/coolpc.jpg" width="480" />
</p>

這個爬蟲會抓取原價屋的所有商品和價錢
並且會建立數個 sqlite 資料庫 (每個類別一個)
預設是每小時抓取一次
並且發現價錢跟資料庫不一致時
會用 line 通知使用者價錢異動

安裝步驟
1. 建立環境 python 3.6 ~ 3.8 都是測試過可行的
2. selenium 4 不相容某個語法，建議安裝 selenium 3.141.0
3. 檢查你的 chrome 版本，並且去下載相容的 chromedriver.exe 放在這個目錄下

-------------------------------------------------------------------------------------------------

This web crawler will fetch all products and prices from Original House.
It will create several SQLite databases (one for each category).
By default, it fetches data every hour.
If it detects a price discrepancy with the database, it will notify the user via LINE.

Installation Steps:
Set up your environment; Python versions 3.6 to 3.8 have been tested and are compatible.
Use Selenium 3.141.0; Selenium 4 is incompatible with certain syntax.
Check your Chrome version and download the compatible chromedriver.exe, placing it in this directory.


