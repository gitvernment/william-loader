from csv import DictWriter

from selenium import webdriver

from william import william


if __name__ == "__main__":
    output_filename = 'out.csv'

    driver_path = './webdrivers/phantomjs-win'
    driver = webdriver.PhantomJS(driver_path)

    with open(output_filename, 'w') as output:
        headers = ['identifier', 'session', 'last_action', 'version', 'summary', 'action_info', 'authors', 'coauthors', 'sponsors', 'house_committee_data', 'senate_committee_data', 'house_conferees', 'senate_conferees']
        writer = DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for x in range(41, 200):
            bill_data = william.retrieve_bill_info(driver, 'HB{}'.format(x))
            if bill_data:
                writer.writerow(bill_data.__dict__)

        driver.quit()
