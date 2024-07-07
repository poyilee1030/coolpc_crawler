import sqlite3
import datetime
import os
import glob


sql_extension = ".sqlite3"


# coolpc_dict = {"04": "cpu", "05": "mb", "06": "ram", "07": "ssd", "08": "hdd",
#                "10": "air_cooler", "11": "water_cooler", "12": "vga", "14": "case", "15": "power",
#                "16": "case_cooler", "17": "keyboard", "18": "mouse", "19": "network", "20": "nas",
#                "21": "tv_box", "22": "speaker", "23": "cd_dvd", "24": "usb", "30": "welfare"}
sql_path_dict = {"cpu": "cpu", "mb": "mb", "ram": "ram", "ssd": "ssd", "hdd": "hdd", "air_cooler": "air_cooler",
                 "water_cooler": "water_cooler", "vga": "vga", "monitor": "monitor", "case": "case", "power": "power",
                 "case_cooler": "case_cooler", "keyboard": "keyboard", "mouse": "mouse", "network": "network",
                 "nas": "nas", "tv_box": "tv_box", "speaker": "speaker", "cd_dvd": "cd_dvd", "usb": "usb",
                 "welfare": "welfare"}

sql_table_dict = {"cpu": "cpu_table", "mb": "mb_table", "ram": "ram_table", "ssd": "ssd_table", "hdd": "hdd_table",
                  "air_cooler": "air_cooler_table", "water_cooler": "water_cooler_table", "vga": "vga_table",
                  "monitor": "monitor_table",
                  "case": "case_table", "power": "power_table", "case_cooler": "case_cooler_table",
                  "keyboard": "keyboard_table", "mouse": "mouse_table", "network": "network_table", "nas": "nas_table",
                  "tv_box": "tv_box_table", "speaker": "speaker_table", "cd_dvd": "cd_dvd_table", "usb": "usb_table",
                  "welfare": "welfare_table"}

sql_label_dict = {"cpu": ["時間", "名稱", "舊價格", "新價格"], "mb": ["時間", "名稱", "舊價格", "新價格"],
                  "ram": ["時間", "名稱", "舊價格", "新價格"], "ssd": ["時間", "名稱", "舊價格", "新價格"],
                  "hdd": ["時間", "名稱", "舊價格", "新價格"], "air_cooler": ["時間", "名稱", "舊價格", "新價格"],
                  "water_cooler": ["時間", "名稱", "舊價格", "新價格"], "vga": ["時間", "名稱", "舊價格", "新價格"],
                  "monitor": ["時間", "名稱", "舊價格", "新價格"],
                  "case": ["時間", "名稱", "舊價格", "新價格"], "power": ["時間", "名稱", "舊價格", "新價格"],
                  "case_cooler": ["時間", "名稱", "舊價格", "新價格"], "keyboard": ["時間", "名稱", "舊價格", "新價格"],
                  "mouse": ["時間", "名稱", "舊價格", "新價格"], "network": ["時間", "名稱", "舊價格", "新價格"],
                  "nas": ["時間", "名稱", "舊價格", "新價格"], "tv_box": ["時間", "名稱", "舊價格", "新價格"],
                  "speaker": ["時間", "名稱", "舊價格", "新價格"], "cd_dvd": ["時間", "名稱", "舊價格", "新價格"],
                  "usb": ["時間", "名稱", "舊價格", "新價格"], "welfare": ["時間", "名稱", "舊價格", "新價格"]
                  }


symbol_list = ["(", ")", "%", "+", "-", "/"]


def filter_symbol(text):
    new_text = ""
    for c in text:
        if c not in symbol_list:
            new_text += c
    return new_text


class CoolPCSqliteManager:
    def __init__(self, working_folder):
        self.working_folder = working_folder
        self.cur_category_name = ""
        self.cur_stock_id = ""
        self.conn = None
        self.cursor = None
        self.print_log = False

    def set_print_log(self, enable):
        self.print_log = enable

    def use_db(self, category_name):
        if self.cur_category_name != category_name:
            if self.conn is not None:
                self.conn.close()

            self.cur_category_name = category_name
            sub_path = sql_path_dict[category_name]
            db_path = os.path.expanduser(self.working_folder + "/" + sub_path + sql_extension)
            print("db_path = ", db_path)
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

    def create_table_if_not_exist(self, category_name):
        table_name = sql_table_dict[category_name]
        sql_table_name = table_name + " ("
        cmd_line1 = "CREATE TABLE IF NOT EXISTS " + sql_table_name
        cmd_line1 += "id INTEGER PRIMARY KEY,"
        label_list = sql_label_dict[category_name]

        cmd_line2 = " TEXT,".join(label_list)
        cmd_line2 = filter_symbol(cmd_line2)
        cmd_line = cmd_line1 + cmd_line2 + " TEXT); "
        if self.print_log:
            print(cmd_line)
        self.cursor.execute(cmd_line)

    def insert_to_table(self, category_name, val_list):
        table_name = sql_table_dict[category_name]
        sql_table_name = table_name + " ("
        cmd_line1 = "INSERT INTO " + sql_table_name

        label_list = sql_label_dict[category_name]

        cmd_line2 = ",".join(label_list)
        cmd_line2 = filter_symbol(cmd_line2)
        cmd_line3 = ""
        label_count = len(label_list)
        for i in range(label_count):
            cmd_line3 += "?,"
        cmd_line3 = cmd_line3[:-1]
        cmd_line = cmd_line1 + cmd_line2 + ") VALUES(" + cmd_line3 + "); "
        if self.print_log:
            print("insert_to_table cmd_line = {}".format(cmd_line))
        for i in range(len(val_list)):
            val = val_list[i]
            val = val.replace(",", "")
            val_list[i] = val

        tup = tuple(val_list)
        if self.print_log:
            print("tup = {}".format(tup))
        self.cursor.execute(cmd_line, tup)
        self.conn.commit()

    def update_to_table(self, category_name, val_list):
        val2_list = val_list.copy()
        table_name = sql_table_dict[category_name]
        label_list = sql_label_dict[category_name]
        sql_table_name = table_name
        cmd_line1 = "UPDATE " + sql_table_name
        cmd_line1 += " SET "

        cmd_line2 = " = ?,".join(label_list)
        cmd_line2 += " = ?"
        cmd_line3 = " WHERE 名稱 = ?"

        cmd_line = cmd_line1 + cmd_line2 + cmd_line3
        if self.print_log:
            print("update_to_table cmd_line = {}".format(cmd_line))

        item_name = val2_list[1]
        val2_list.append(item_name)

        tup = tuple(val2_list)
        if self.print_log:
            print("tup = {}".format(tup))
        self.cursor.execute(cmd_line, tup)
        self.conn.commit()

    def do_select_all(self, category_name, item_name):
        table_name = sql_table_dict[category_name]
        sql_table_name = table_name
        cmd_line1 = "SELECT * FROM " + sql_table_name + " WHERE 名稱=?"
        if self.print_log:
            print("do_select_all cmd = {}", cmd_line1)
        self.cursor.execute(cmd_line1, (item_name,))
        rows = self.cursor.fetchall()
        return rows
