
import time
import sqlite3
import datetime
import random


#  Checking if the database exists#
con = sqlite3.connect('weather_fake.db')
cur = con.cursor()

cur.close()
con.commit()
con.close()
###############################

command = (''' CREATE TABLE IF NOT EXISTS data (
                                 abs_pressure REAL,
                                 delay REAL,
                                 hum_in REAL,
                                 hum_out REAL,
                                 idx TEXT,
                                 rain REAL,
                                 temp_in REAL,
                                 temp_out REAL,
                                 wind_ave REAL,
                                 wind_dir REAL,
                                 wind_gust REAL)''')


con = sqlite3.connect('weather_fake.db')
cur = con.cursor()
cur.execute(command)
cur.close()
con.commit()
if con is not None:
    con.close()


class Forecast():

    def addData(self, tagged_data):
        con = sqlite3.connect('weather_fake.db')
        cur = con.cursor()
        command = ('''INSERT INTO data(abs_pressure,
                                        delay,
                                        hum_in,
                                        hum_out,
                                        idx,
                                        rain,
                                        temp_in,
                                        temp_out,
                                        wind_ave,
                                        wind_dir,
                                        wind_gust) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (tagged_data['abs_pressure'],
                                                                                                          tagged_data['delay'],
                                                                                                          tagged_data['hum_in'],
                                                                                                          tagged_data['hum_out'],
                                                                                                          datetime.datetime.now().strftime('%s'),
                                                                                                          tagged_data['rain'],
                                                                                                          tagged_data['temp_in'],
                                                                                                          tagged_data['temp_out'],
                                                                                                          tagged_data['wind_ave'],
                                                                                                          tagged_data['wind_dir'],
                                                                                                          tagged_data['wind_gust']))
        con.commit()
        cur.close()
        con.close()

        m_time = datetime.datetime.now().strftime('%s')
        print(m_time)
        print(time.ctime(int(m_time)))
        print(tagged_data['idx'])

    def main(self):

        while True:
            dict_of_data = {}
            dict_of_data['abs_pressure'] = random.randrange(1022.0, 1025, 1)
            dict_of_data['delay'] = random.randint(2, 7)
            dict_of_data['hum_in'] = random.randrange(33.0, 40.0, 1)
            dict_of_data['hum_out'] = random.randrange(33.0, 80.0, 1)
            dict_of_data['idx'] = datetime.datetime.now()
            dict_of_data['rain'] = random.randrange(70.0, 74.0, 1)
            dict_of_data['temp_in'] = random.randrange(18, 28, 1)
            dict_of_data['temp_out'] = random.randrange(2, 20, 1)
            dict_of_data['wind_ave'] = random.randrange(0, 10, 1)
            dict_of_data['wind_dir'] = random.randrange(0, 14, 1)
            dict_of_data['wind_gust'] = random.randrange(1, 7, 1)
            print(dict_of_data)
            self.addData(dict_of_data)
            time.sleep(5)


if __name__ == '__main__':
    a = Forecast()
    a.main()
