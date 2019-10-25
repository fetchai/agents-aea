
import sqlite3
import os
import shutil
import skimage
import time


class DetectionDatabase:
    def __init__(self, run_dir):
        self.this_dir =os.path.dirname(__file__)
        self.run_dir = run_dir
        self.temp_dir = str(os.path.join(self.run_dir, '', "temp_files"))

        self.mask_image_path = self.temp_dir + "/mask.tiff"
        self.mask_ref_image_path =self. temp_dir + "/mask_ref.tiff"
        self.raw_image_dir = self.temp_dir + "/db_raw_images/"
        self.processed_image_dir = self.temp_dir + "/db_processed_images/"
        # Note that this path should be under source control
        self.default_mask_ref_path = self.this_dir + "/default_mask_ref.png"
        self.num_digits_time = 12  # need to match this up with the generate functions below
        self.image_file_ext = ".png"

        self.database_path = self.temp_dir + "/" + "detection_results.db"
        self.initialise_backend()

    def reset_database(self):
        # If we need to reset the database, then remove the table and any stored images
        print("Database being reset")

        # Remove the actual database file
        if os.path.isfile(self.database_path):
            os.remove(self.database_path)

        # Clear stored images
        shutil.rmtree(self.raw_image_dir)
        shutil.rmtree(self.processed_image_dir)

        # Recreate them
        self.initialise_backend()


    def reset_mask(self):
        # If we need to reset the database, then remove the table and any stored images
        print("Database being reset")

        # Remove the actual database file
        if os.path.isfile(self.mask_image_path):
            os.remove(self.mask_image_path)
        if os.path.isfile(self.mask_ref_image_path):
            os.remove(self.mask_ref_image_path)
        self.ensure_dirs_exist()

    def initialise_backend(self):
        self.ensure_dirs_exist()
        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS images (epoch INTEGER, raw_image_path TEXT, "
            "processed_image_path TEXT, total_count INTEGER, "
            "moving_count INTEGER, free_spaces INTEGER, lat TEXT, lon TEXT)")

       # self.execute_single_sql("DROP TABLE fet_table")
        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS fet_table (id INTEGER PRIMARY KEY, amount BIGINT, last_updated TEXT)")

        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS status_table (system_name TEXT PRIMARY KEY, status TEXT)")


        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS name_lookup2 (oef_key TEXT PRIMARY KEY, friendly_name TEXT, epoch INT, is_self BIT)")

        # self.execute_single_sql("DROP TABLE transaction_history")
        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS transaction_history (tx TEXT PRIMARY KEY, epoch INT, oef_key_payer TEXT, oef_key_payee TEXT, amount BIGINT, status TEXT)")

        #self.execute_single_sql("DROP TABLE dialogue_statuses")
        self.execute_single_sql(
            "CREATE TABLE IF NOT EXISTS dialogue_statuses (dialogue_id TEXT, epoch DECIMAL, other_agent_key TEXT, received_msg TEXT, sent_msg TEXT)")



    def set_fet(self, amount, t):
        self.execute_single_sql(
            "INSERT OR REPLACE INTO fet_table(id, amount, last_updated) values(0, '{0}', '{1}')".format(amount, t))

    def get_fet(self):
        result = self.execute_single_sql("SELECT amount FROM fet_table WHERE id=0")
        if len(result) != 0:
            return result[0][0]
        else:
            return -99

    def save_max_capacity(self, max_capacity):
        self.set_system_status("max_capacity", str(max_capacity))

    def get_max_capacity(self):
        max_capacity = self.get_system_status("max_capacity")

        if max_capacity == "UNKNOWN":
            return None
        else:
            return int(max_capacity)

    def save_lat_lon(self, lat, lon):
       self.set_system_status("lat", str(lat))
       self.set_system_status("lon", str(lon))

    def get_lat_lon(self):
        lat = self.get_system_status("lat")
        lon = self.get_system_status("lon")
        if lat == "UNKNOWN" or lon == "UNKNOWN":
            return None, None
        else:
            return float(lat), float(lon)

    def set_system_status(self, system_name, status):
        self.execute_single_sql(
            "INSERT OR REPLACE INTO status_table(system_name, status) values('{}', '{}')".format(system_name, status))

    def get_system_status(self, system_name):
        result = self.execute_single_sql("SELECT status FROM status_table WHERE system_name='{}'".format(system_name))
        if len(result) != 0:
            return result[0][0]
        else:
            return "UNKNOWN"

    def set_dialogue_status(self, dialogue_id, other_agent_key, received_msg, sent_msg):
        t = time.time()
        self.execute_single_sql(
            "INSERT INTO dialogue_statuses(dialogue_id, epoch, other_agent_key, received_msg, sent_msg) "
            "values('{}', {}, '{}', '{}', '{}')".format(dialogue_id, t, other_agent_key, received_msg, sent_msg))

    def get_dialogue_statuses(self):
        data = self.execute_single_sql("SELECT * FROM dialogue_statuses ORDER BY epoch DESC LIMIT 100")
        results = []
        for datum in data:
            result = {}
            result['dialog_id'] = datum[0]
            result['epoch'] = datum[1]
            result['other_agent_key'] = datum[2]
            result['received_msg'] = datum[3]
            result['sent_msg'] = datum[4]
            results.append(result)

        return results

    def calc_uncleared_fet(self):
        cleared_fet_result = self.execute_single_sql("SELECT amount FROM fet_table WHERE id=0")
        if len(cleared_fet_result) != 0:
            uncleared_fet_result = self.execute_single_sql("SELECT SUM(amount) FROM transaction_history WHERE status = 'in_progress'")
            if len(uncleared_fet_result) == 0 or uncleared_fet_result[0][0] is None:
                return cleared_fet_result[0][0]
            else:
                return cleared_fet_result[0][0] + uncleared_fet_result[0][0]
        else:
            return -99

    def add_friendly_name(self, oef_key, friendly_name, is_self=False):
        t = int(time.time())
        self.execute_single_sql(
            "INSERT OR REPLACE INTO name_lookup2(oef_key, friendly_name, epoch, is_self) "
            "values('{}', '{}', {}, {})".format(oef_key, friendly_name, t, 1 if is_self else 0))

    def add_in_progress_transaction(self, tx, oef_key_payer, oef_key_payee, amount):
        t = int(time.time())
        self.execute_single_sql(
            "INSERT OR REPLACE INTO transaction_history(tx, epoch, oef_key_payer, oef_key_payee, amount, status) "
            "values('{}', {}, '{}', '{}', {}, 'in_progress')".format(
                tx,
                t,
                oef_key_payer,
                oef_key_payee,
                amount))

    def get_in_progress_transactions(self):
        return self.get_transactions_with_status("in_progress")

    def get_complete_transactions(self):
        return self.get_transactions_with_status("complete")


    def get_transactions_with_status(self, status):
        data = self.execute_single_sql("SELECT * from transaction_history WHERE status = '{}' ORDER BY epoch DESC".format(status))
        results = []
        for datum in data:
            result = {}
            result['tx_hash'] = datum[0]
            result['epoch'] = datum[1]
            result['oef_key_payer'] = datum[2]
            result['oef_key_payee'] = datum[3]
            result['amount'] = datum[4]
            result['status'] = datum[5]
            results.append(result)

        return results


    def get_n_transactions(self, count):
        data = self.execute_single_sql("SELECT * from transaction_history ORDER BY epoch DESC LIMIT {}".format(count))
        results = []
        for datum in data:
            result = {}
            result['tx_hash'] = datum[0]
            result['epoch'] = datum[1]
            result['oef_key_payer'] = datum[2]
            result['oef_key_payee'] = datum[3]
            result['amount'] = datum[4]
            result['status'] = datum[5]
            results.append(result)

        return results



    def set_transaction_complete(self, tx):
        self.execute_single_sql(
            "UPDATE transaction_history SET status ='complete' WHERE tx = '{}'".format(tx))

    def lookup_friendly_name(self, oef_key):
        results = self.execute_single_sql(
            "SELECT * FROM name_lookup2 WHERE oef_key = '{}' ORDER BY epoch DESC".format(oef_key))
        if len(results) == 0:
            return None
        else:
            return results[0][1]

    # return public_key, friendly_name
    def lookup_self_names(self):
        results = self.execute_single_sql(
            "SELECT oef_key, friendly_name FROM name_lookup2 WHERE is_self = 1 ORDER BY epoch DESC")
        if len(results) == 0:
            return None, None
        else:
            return results[0][0], results[0][1]

    def add_entry_no_save(self, raw_path, processed_path, total_count, moving_count, free_spaces, lat, lon):
        # need to extract the time!
        t = self.extract_time_from_raw_path(raw_path)
        self.execute_single_sql("INSERT INTO images VALUES ({}, '{}', '{}', {}, {}, {}, '{}', '{}')".format(
            t, raw_path, processed_path, total_count, moving_count, free_spaces, lat, lon))


    def add_entry(self, raw_image, processed_image, total_count, moving_count, free_spaces, lat, lon):
        t = int(time.time())
        raw_path = self.generate_raw_image_path(t)
        processed_path = self.generate_processed_path(t)

        skimage.io.imsave(raw_path, raw_image)
        skimage.io.imsave(processed_path, processed_image)

        self.execute_single_sql("INSERT INTO images VALUES ({}, '{}', '{}', {}, {}, {}, '{}', '{}')".format(
            t, raw_path, processed_path, total_count, moving_count, free_spaces, lat, lon))

    def execute_single_sql(self, command):
        conn = None
        ret = []
        try:
            conn = sqlite3.connect(self.database_path, timeout=300) # 5 mins
            c = conn.cursor()
            c.execute(command)
            ret = c.fetchall()
            conn.commit()
        except Exception as e:
            print("Exception in database: {}".format(e))
        finally:
            if conn is not None:
                conn.close()

        return ret

    def get_latest_detection_data(self, max_num_rows):
        results = self.execute_single_sql(
            "SELECT * FROM images ORDER BY epoch DESC LIMIT {}".format(max_num_rows))

        if results is None:
            return None
        ret_data = []
        for r in results:
            this_data = {}
            this_data["epoch"] = r[0]
            this_data["raw_image_path"] = r[1]
            this_data["processed_image_path"] = r[2]
            this_data["total_count"] = r[3]
            this_data["moving_count"] = r[4]
            this_data["free_spaces"] = r[5]
            this_data["lat"] = r[6]
            this_data["lon"] = r[7]
            ret_data.append(this_data)

        return ret_data

    def prune_image_table(self, max_entries):
        self.prune_table("images", max_entries)

    def prune_transaction_table(self, max_entries):
        self.prune_table("transaction_history", max_entries)


    def prune_table(self, table_name, max_entries):
        results = self.execute_single_sql(
            "SELECT epoch FROM {} ORDER BY epoch DESC LIMIT 1 OFFSET {}".format(table_name, max_entries - 1))

        if len(results) != 0:
            last_epoch = results[0][0]
            self.execute_single_sql("DELETE FROM {} WHERE epoch<{}".format(table_name, last_epoch))

    def ensure_dirs_exist(self):
        if not os.path.isdir(self.temp_dir):
            os.mkdir(self.temp_dir)
        if not os.path.isdir(self.raw_image_dir):
            os.mkdir(self.raw_image_dir)
        if not os.path.isdir(self.processed_image_dir):
            os.mkdir(self.processed_image_dir)

    def generate_raw_image_path(self, t):
        return self.raw_image_dir + "{0:012d}".format(t) + "_raw_image" + self.image_file_ext

    def generate_processed_path(self, t):
        return self.processed_image_dir + "{0:012d}".format(t)+ "_processed_image" + self.image_file_ext

    def generate_processed_from_raw_path(self, raw_name):
        return raw_name.replace("_raw_image.", "_processed_image.").replace(self.raw_image_dir, self.processed_image_dir)

    def extract_time_from_raw_path(self, raw_name):
        start_index = len(self.raw_image_dir)
        extracted_num = raw_name[start_index:start_index + self.num_digits_time]
        return int(extracted_num)
