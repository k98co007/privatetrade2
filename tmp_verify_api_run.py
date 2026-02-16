import time
from collections import Counter
from fastapi.testclient import TestClient

from webapi import app


def main() -> None:
    client = TestClient(app)

    start_resp = client.post(
        '/api/simulations',
        json={'symbol': '005930.KS', 'strategy': 'sell_trailing_stop'},
    )
    start_json = start_resp.json()
    sim_id = start_json.get('data', {}).get('simulation_id')

    print('START_STATUS', start_resp.status_code)
    print('START_BODY', start_json)
    print('SIM_ID', sim_id)

    final_status = None
    for _ in range(120):
        status_resp = client.get(f'/api/simulations/{sim_id}')
        status_json = status_resp.json()
        final_status = status_json.get('data', {}).get('status')
        if final_status in ('completed', 'error'):
            print('STATUS_BODY', status_json)
            break
        time.sleep(0.25)

    print('FINAL_STATUS', final_status)

    report_resp = client.get(
        f'/api/simulations/{sim_id}/report?schema_version=1.0&include_no_trade=true&sort_order=asc'
    )
    report_json = report_resp.json()

    print('REPORT_STATUS', report_resp.status_code)
    print('REPORT_SUCCESS', report_json.get('success'))

    if report_json.get('success'):
        trades = report_json.get('data', {}).get('trades', [])
        print('TRADE_COUNT', len(trades))
        print('REASONS', dict(Counter(item.get('sell_reason') for item in trades)))
    else:
        print('REPORT_ERROR', report_json.get('error'))


if __name__ == '__main__':
    main()
