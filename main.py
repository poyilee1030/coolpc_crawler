import os
import datetime
from selenium import webdriver
from coolpc_sqlite_manager import CoolPCSqliteManager
from line_notify import LineNotify


url = "https://www.coolpc.com.tw/m/"


# number_list = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
coolpc_dict = {"04": "cpu", "05": "mb", "06": "ram", "07": "ssd", "08": "hdd",
               "10": "air_cooler", "11": "water_cooler", "12": "vga", "13": "monitor", "14": "case", "15": "power",
               "16": "case_cooler", "17": "keyboard", "18": "mouse", "19": "network", "20": "nas",
               "21": "tv_box", "22": "speaker", "23": "cd_dvd", "24": "usb", "30": "welfare"}
# 01 品牌、AIO、VR # 02 筆電平板、行動電源 # 03 酷PC套裝
# 04 cpu # 05 mb # 06 ram # 07 ssd # 08 hdd # 09 外接碟、記憶卡
# 10 CPU VGA散熱 # 11 水冷套件 # 12 顯示卡 # 13 螢幕 # 14 機殼 # 15 Power
# 16 機殼散熱、配件 # 17 鍵盤組、搖桿 # 18 滑鼠、數位板 # 19 網卡、AP、hun
# 20 NAS IP Cam # 21 電視卡、棒、盒 # 22 喇叭、耳麥、音效 # 23 CD、DVD燒錄
# 24 USB、HD周邊 # 25 視訊行車紀錄 # 26 UPS、掃描印表機 # 27 介面卡、陣列卡
# 28 傳輸線材、KVM # 29 OS系統、軟體 # 30 福利品出清


def handle_page(main_idx):
    driver.get(url)

    # countdown = 3
    # for i in range(countdown):
    #     print(countdown - i)
    #     time.sleep(1)

    str_main_idx = str(main_idx).zfill(2)
    category = coolpc_dict[str_main_idx]
    sql_manager.use_db(category)
    sql_manager.create_table_if_not_exist(category)

    # not work on selenium 4.0
    span_list = driver.find_elements_by_xpath('//span[contains(text(), "")]')

    idx = 0
    for span in span_list:
        if idx == main_idx:
            span.click()
            break
        idx += 1

    # not work on selenium 4.0
    table_list = driver.find_elements_by_xpath('//table[contains(text(), "")]')

    start = 3
    end = len(table_list) - 2
    for idx in range(start, end):
        table = table_list[idx]
        table_text = table.text + "\n"
        line_notify.append_msg([table_text])
        table.click()
        tbody_list = table.find_elements_by_css_selector('tbody')
        for tbody in tbody_list:
            rows = tbody.find_elements_by_css_selector('tr')
            for row in rows:
                handle_row(category, row)

        line_notify.send_msg()


def handle_row(category, row):
    tds = row.find_elements_by_tag_name('td')
    for td in tds:
        # print(td.text)
        text = td.text
        pos = text.find(",")
        if pos > 0:
            cur_obj_name, cur_obj_old_price, cur_obj_new_price = parse_text(text)
            results = sql_manager.do_select_all(category, cur_obj_name)
            if len(results) > 0:
                for result in results:
                    db_obj_datetime = result[1]
                    db_obj_name = result[2]
                    db_obj_old_price = result[3]
                    db_obj_new_price = result[4]
                    if db_obj_new_price and cur_obj_new_price:
                        diff = abs(int(db_obj_new_price) - int(cur_obj_new_price))
                        if diff > 10:
                            print("price changed, text = ", text)
                            if "銀欣 SX650-G(650W) 雙8/金牌/全模組/全日系/5年保【SFX規格】" in text:
                                pass
                            else:
                                cur_val_list = [today_string, cur_obj_name, db_obj_new_price, cur_obj_new_price]
                                sql_manager.update_to_table(category, cur_val_list)
                                if db_obj_new_price > cur_obj_new_price:
                                    cur_val_list.append(f"↘ 降價{diff}")
                                else:
                                    cur_val_list.append(f"↗ 漲價{diff}")
                                line_notify.append_msg(cur_val_list)
                        else:
                            # 價差在10元內
                            pass
                    else:
                        # 通常是category標題
                        pass
            else:
                # 新商品
                print("new item, text = ", text)
                cur_val_list = [today_string, cur_obj_name, cur_obj_old_price, cur_obj_new_price]
                sql_manager.insert_to_table(category, cur_val_list)
                cur_val_list.append("新商品!")
                line_notify.append_msg(cur_val_list)


def parse_text(text):
    pos = text.find(",")
    item_name = text[:pos]
    rest_text = text[pos+1:]
    money1, money1_end_pos = find_money(rest_text)

    remain_text = rest_text[money1_end_pos:]
    money2, money2_end_pos = find_money(remain_text)

    if not money2:
        money2 = money1

    return [item_name, money1, money2]


def find_money(text):
    pos = text.find("$")
    if pos < 0:
        return "", -1

    start = pos+1
    end = start
    money = ""
    for i in range(start, len(text)):
        c = text[i]
        if c.isnumeric():
            money += c
        else:
            end = i
            break
    return money, end


if __name__ == '__main__':
    driver = webdriver.Chrome()
    line_notify = LineNotify()
    working_folder = os.getcwd()

    pos = working_folder.find("coolpc_crawler")
    if pos < 0:
        working_folder += "/coolpc_crawler"
    sql_manager = CoolPCSqliteManager(working_folder)

    datetime_today_obj = datetime.datetime.today()
    today_string = datetime_today_obj.strftime('%Y%m%d_%H%M%S')
    print(today_string)

    # update_db_test(4)
    handle_page(4)  # cpu
    handle_page(5)  # mb
    handle_page(6)  # ram
    handle_page(7)  # ssd
    handle_page(8)  # hdd
    handle_page(10)  # air_cooler
    handle_page(11)  # water_cooler
    handle_page(12)  # vga
    handle_page(13)  # monitor
    handle_page(14)  # case
    handle_page(15)  # power
    handle_page(16)  # case_cooler
    handle_page(17)  # keyboard
    handle_page(18)  # mouse
    handle_page(30)  # welfare

    driver.close()

# 01 品牌、AIO、VR # 02 筆電平板、行動電源 # 03 酷PC套裝
# 04 cpu # 05 mb # 06 ram # 07 ssd # 08 hdd # 09 外接碟、記憶卡
# 10 CPU VGA散熱 # 11 水冷套件 # 12 顯示卡 # 13 螢幕 # 14 機殼 # 15 Power
# 16 機殼散熱、配件 # 17 鍵盤組、搖桿 # 18 滑鼠、數位板 # 19 網卡、AP、hun
# 20 NAS IP Cam # 21 電視卡、棒、盒 # 22 喇叭、耳麥、音效 # 23 CD、DVD燒錄
# 24 USB、HD周邊 # 25 視訊行車紀錄 # 26 UPS、掃描印表機 # 27 介面卡、陣列卡
# 28 傳輸線材、KVM # 29 OS系統、軟體 # 30 福利品出清


