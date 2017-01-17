import json
import os
from time import sleep

import psycopg2
import psycopg2.extras
from selenium import webdriver

from william import william


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
    number_of_redirects = 0

    try:
        conn = psycopg2.connect(os.getenv('WILLIAM_POSTGRES_URL'))
    except:
        print("I am unable to connect to the database")
        os.exit(1)

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    driver = webdriver.PhantomJS('./webdrivers/phantomjs-mac')
    for side in ('HB', 'SB'):
        for x in range(1, 10000):
            sleep(5)
            if number_of_redirects > 50:
                break

            bill = william.retrieve_bill_info(driver, '{}{}'.format(side, x))
            if not bill:
                number_of_redirects += 1
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

    driver.quit()
