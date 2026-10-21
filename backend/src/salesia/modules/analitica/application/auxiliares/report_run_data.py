import json


def report_run_data(row):

    return json.loads(row.data_json)
