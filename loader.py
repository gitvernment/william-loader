import json
import os
from time import sleep
import sys
from sys import platform

import psycopg2
import psycopg2.extras
from selenium import webdriver

from william import william
from william.sentry import sentry_client


def insert_bill(cursor, connection, bill):
    insertion_query = """
        INSERT INTO bills
            ("identifier", "url", "session", "last_action", "version", "summary",
             "subjects", "authors", "coauthors", "sponsors", "house_committee_data",
             "senate_committee_data", "house_conferees", "senate_conferees", "created")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW());
    """
    values = [bill.identifier, bill.url, bill.session, bill.last_action, bill.version, bill.summary,
              bill.subjects, bill.authors, bill.coauthors, bill.sponsors, json.dumps(bill.house_committee_data),
              json.dumps(bill.senate_committee_data), bill.house_conferees, bill.senate_conferees]
    cursor.execute(insertion_query, values)
    connection.commit()


def archive_bill(cursor, connection, bill):
    archiving_query = 'UPDATE bills set archived = NOW() where id = %s;'
    values = [bill['id']]
    cursor.execute(archiving_query, values)
    connection.commit()

def populate_bill_from_db_dict(bill_from_db):
    db_bill = william.Bill(
        identifier=bill_from_db['identifier'],
        url=bill_from_db['url'],
        session=bill_from_db['session'],
        last_action=bill_from_db['last_action'],
        version=bill_from_db['version'],
        summary=bill_from_db['summary'],
        subjects=bill_from_db['subjects'],
        authors=bill_from_db['authors'],
        coauthors=bill_from_db['coauthors'],
        sponsors=bill_from_db['sponsors'],
        house_committee_data=bill_from_db['house_committee_data'],
        senate_committee_data=bill_from_db['senate_committee_data'],
        house_conferees=bill_from_db['house_conferees'],
        senate_conferees=bill_from_db['senate_conferees'],
    )
    return db_bill

if __name__ == "__main__":
    try:
        conn = psycopg2.connect(os.getenv('WILLIAM_POSTGRES_URL'))
    except:
        sentry_client.captureException()
        sys.exit(1)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    webdriver_map = {
        'darwin': './webdrivers/phantomjs-mac',
        'linux': './webdrivers/phantomjs-linux',
    }
    if not webdriver_map.get(platform):
        sentry_client.captureMessage('Somehow the provided platform had no webdriver.')
        sys.exit(1)

    driver = webdriver.PhantomJS(webdriver_map[platform])
    driver.set_page_load_timeout(30)
    while True:
        try:
            for side in ['HB', 'HCR', 'SB', 'SCR']:
                number_of_redirects = 0
                print('starting with the {}s'.format(side))
                for x in range(1, 10000):
                    if number_of_redirects > 50:
                        break

                    bill_identifier = '{}{}'.format(side, x)
                    print('retrieving info for {}'.format(bill_identifier))
                    bill = william.retrieve_bill_info(driver, bill_identifier)
                    if not bill:
                        print('Nothing found for bill {}'.format(bill_identifier))
                        number_of_redirects += 1
                        continue
                    else:
                        number_of_redirects = 0
                        cur.execute("select * from bills where identifier = %s and archived is null", [bill.identifier])

                        bill_from_db = cur.fetchone()

                        if bill_from_db:
                            bill_from_db = dict(bill_from_db)
                            parsed_bill = populate_bill_from_db_dict(bill_from_db)

                            if not bill.is_equal_to(parsed_bill):
                                archive_bill(cur, conn, bill_from_db)
                                insert_bill(cur, conn, bill)
                        else:
                            insert_bill(cur, conn, bill)
                        print('successfully processed bill {}'.format(bill_identifier))
                        sleep(2.5)
        except Exception as e:
            sentry_client.captureException()
            driver.quit()
            raise e
            break
