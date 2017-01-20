import os
import re

import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .sentry import sentry_client
from .models import Bill

LAST_ACTION_XPATH = '//*[@id="cellLastAction"]'
VERSION_XPATH = '//*[@id="cellCaptionVersion"]'
SUMMARY_XPATH = '//*[@id="cellCaptionText"]'
SUBJECT_XPATH = '//*[@id="cellSubjects"]'

ACTION_TABLE_XPATH = '//*[@id="usrBillInfoActions_tblActions"]/following::table'
HOUSE_COMMITTEE_TABLE_XPATH = '//*[@id="tblComm1Committee"]/tbody/tr'
SENATE_COMMITTEE_TABLE_XPATH = '//*[@id="tblComm2Committee"]/tbody/tr'

AUTHORS_XPATH = '//*[@id="cellAuthors"]'
COAUTHORS_XPATH = '//*[@id="cellCoauthors"]'
SPONSORS_XPATH = '//*[@id="cellSponsors"]'

HOUSE_CONFEREES_XPATH = '//*[@id="cellComm1Conferees"]'
SENATE_CONFEREES_XPATH = '//*[@id="cellComm2Conferees"]'


def clean_string(string):
    return string.strip().lower().replace(' ', '_')

def retrieve_element_or_not(driver, xpath, altering_func=None):
    try:
        result = driver.find_element_by_xpath(xpath).text
        if altering_func is not None:
            result = altering_func(result)
        return result

    except NoSuchElementException:
        return None


def parse_action_table(action_table):
    # roughly lifted from http://stackoverflow.com/a/8143352
    action_info = []
    data = []
    for tr in action_table:
        tds = tr.find_elements_by_tag_name('td')
        if tds:
            data.append([td.text.strip() for td in tds])
    for row in data[1:]:
        row_data = {}
        row[0] = '{} {}'.format(row[0], row[1])
        row.pop(1)
        for index, val in enumerate(row):
            row_data[clean_string(data[0][index])] = val
        action_info.append(row_data)

    return action_info


def parse_committee_table(committee_table):
    committee_info = {}
    vote_data = {}
    data = []
    for tr in committee_table:
        tds = tr.find_elements_by_tag_name('td')
        if tds:
            data.append([td.text.strip() for td in tds])
    for row in [d for d in data if len(d) > 1]:
        if row[0] != 'Vote:':
            committee_info[clean_string(row[0]).replace(':', '')] = row[1]
        else:
            vote_info = row[1].split('  ')
            for vote_type in vote_info:
                t, val = vote_type.split('=')
                vote_data[clean_string(t)] = val
    committee_name = committee_info.get('House Committee') or committee_info.get('Senate Committee') or ''
    committee_status = committee_info.get('Status')

    committee = {
        'name': committee_name,
        'status': committee_status,
        'votes': vote_data,
    }
    return committee


def modify_conferees(conferee_data):
    return [x.strip() for x in re.sub(r'Appointed \(\d{2}/\d{2}/\d{4}\)', '', conferee_data).strip().split('|')]


def retrieve_bill_info(driver, bill_number, session='85R'):
    url = 'http://www.legis.state.tx.us/BillLookup/History.aspx?LegSess={}&Bill={}'.format(session, bill_number)
    try:
        res = requests.get(url)
    except TimeoutException:
        sentry_client.captureMessage('Request for bill {} timed out'.format(bill_number))
        sentry_client.captureException()
        return None

    if len(res.history):
        # the state redirects to the search page when you enter a bill that doesn't exist.
        return None

    try:
        driver.get(url)
    except:
        sentry_client.captureException()
        return None


    last_action = driver.find_element_by_xpath(LAST_ACTION_XPATH).text
    version = driver.find_element_by_xpath(VERSION_XPATH).text
    summary = driver.find_element_by_xpath(SUMMARY_XPATH).text

    authors = [x.strip() for x in driver.find_element_by_xpath(AUTHORS_XPATH).text.split('|')]

    # action_table = driver.find_element_by_xpath(ACTION_TABLE_XPATH).find_elements_by_tag_name('tr')
    # action_info = parse_action_table(action_table)

    subjects = [x.strip() for x in driver.find_element_by_xpath(SUBJECT_XPATH).text.split('\n')]

    # unreliable elements
    coauthors = retrieve_element_or_not(driver, COAUTHORS_XPATH, altering_func=modify_conferees)
    sponsors = retrieve_element_or_not(driver, SPONSORS_XPATH, altering_func=modify_conferees)

    house_committee_table = driver.find_elements_by_xpath(HOUSE_COMMITTEE_TABLE_XPATH)
    senate_committee_table = driver.find_elements_by_xpath(SENATE_COMMITTEE_TABLE_XPATH)

    house_committee_data = parse_committee_table(house_committee_table)
    senate_committee_data = parse_committee_table(senate_committee_table)

    house_conferees = retrieve_element_or_not(driver, HOUSE_CONFEREES_XPATH, altering_func=modify_conferees)
    senate_conferees = retrieve_element_or_not(driver, SENATE_CONFEREES_XPATH, altering_func=modify_conferees)

    bill = Bill(
        identifier=bill_number,
        url=url,
        session=session,
        last_action=last_action,
        version=version,
        summary=summary,
        subjects=subjects,
        authors=authors,
        coauthors=coauthors,
        sponsors=sponsors,
        house_committee_data=house_committee_data,
        senate_committee_data=senate_committee_data,
        house_conferees=house_conferees,
        senate_conferees=senate_conferees,
    )
    return bill
