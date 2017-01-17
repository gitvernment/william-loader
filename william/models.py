class Bill:
    def __init__(self,
                 identifier,
                 url,
                 session,
                 last_action,
                 version,
                 summary,
                 subjects,
                 authors,
                 coauthors=None,
                 sponsors=None,
                 house_committee_data=None,
                 senate_committee_data=None,
                 house_conferees=None,
                 senate_conferees=None):
        self.identifier = identifier
        self.url = url
        self.session = session
        self.last_action = last_action
        self.version = version
        self.summary = summary
        self.subjects = subjects
        self.authors = authors
        self.coauthors = coauthors
        self.sponsors = sponsors
        self.house_committee_data = house_committee_data
        self.senate_committee_data = senate_committee_data
        self.house_conferees = house_conferees
        self.senate_conferees = senate_conferees

    def is_equal_to(self, alt_bill):
        try:
            assert self.identifier == alt_bill.identifier
            assert self.url == alt_bill.url
            assert self.session == alt_bill.session
            assert self.last_action == alt_bill.last_action
            assert self.version == alt_bill.version
            assert self.summary == alt_bill.summary
            assert self.subjects == alt_bill.subjects
            assert self.authors == alt_bill.authors
            assert self.coauthors == alt_bill.coauthors
            assert self.sponsors == alt_bill.sponsors
            assert self.house_committee_data == alt_bill.house_committee_data
            assert self.senate_committee_data == alt_bill.senate_committee_data
            assert self.house_conferees == alt_bill.house_conferees
            assert self.senate_conferees == alt_bill.senate_conferees
        except AssertionError:
            return False
        return True
