class Bill:
    def __init__(self,
                 identifier,
                 session,
                 last_action,
                 version,
                 summary,
                 action_info,
                 authors,
                 coauthors=None,
                 sponsors=None,
                 house_committee_data=None,
                 senate_committee_data=None,
                 house_conferees=None,
                 senate_conferees=None):
        self.identifier = identifier
        self.session = session
        self.last_action = last_action
        self.version = version
        self.summary = summary
        self.authors = authors
        self.action_info = action_info
        self.coauthors = coauthors
        self.sponsors = sponsors
        self.house_committee_data = house_committee_data
        self.senate_committee_data = senate_committee_data
        self.house_conferees = house_conferees
        self.senate_conferees = senate_conferees
