import requests
from multiprocessing import Pool

from regparser.notice.build import build_notice

FR_BASE = "https://www.federalregister.gov"
API_BASE = FR_BASE + "/api/v1/"


def fetch_notice_json(cfr_title, cfr_part, only_final=False):
    """Search through all articles associated with this part. Right now,
    limited to 1000; could use paging to fix this in the future."""
    params = {
        "conditions[cfr][title]": cfr_title,
        "conditions[cfr][part]": cfr_part,
        "per_page": 1000,
        "order": "oldest",
        "fields[]": [
            "abstract", "action", "agency_names", "cfr_references", "citation",
            "comments_close_on", "dates", "document_number", "effective_on",
            "end_page", "full_text_xml_url", "html_url", "publication_date",
            "regulation_id_numbers", "start_page", "type", "volume"]}
    if only_final:
        params["conditions[type][]"] = 'RULE'
    response = requests.get(API_BASE + "articles", params=params).json()
    if 'results' in response:
        return response['results']
    else:
        return []


class AsyncBuildFn(object):
    def __init__(self, title, part):
        self.title = title
        self.part = part
    def __call__(self, json_notice):
        print "Processing:", json_notice['document_number']
        return build_notice(self.title, self.part, json_notice)

def fetch_notices(cfr_title, cfr_part, only_final=False):
    """Search and then convert to notice objects (including parsing)"""
    notices = []
    print "Fetching notices..."
    json_notices = fetch_notice_json(cfr_title, cfr_part, only_final)

    p = Pool(10)
    print "Building notice objects..."
    built_notices_lists = p.map(AsyncBuildFn(cfr_title, cfr_title), json_notices)

    for built_notices_list in built_notices_lists:
        notices.extend(built_notices_list)

    print "Done."
    return notices
