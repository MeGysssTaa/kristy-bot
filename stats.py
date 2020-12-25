import json
import traceback


global records


stats = {}


def new_report():
    if len(stats) == 0:
        raise RuntimeError('not loaded')

    # TODO
    pass


def save_and_reset():
    global stats

    if len(stats) == 0:
        raise RuntimeError('not loaded')

    with open('../last_stats_record.json', 'w', encoding='utf8') as fstream:
        json.dump(stats, fstream, ensure_ascii=False)
        stats = {}


def load():
    global stats

    with open('../last_stats_record.json', 'r', encoding='utf8') as fstream:
        try:
            stats_json = fstream.read()
            stats = json.loads(stats_json)
        except json.decoder.JSONDecodeError:
            print('Failed to read stats file:')
            traceback.print_exc()
