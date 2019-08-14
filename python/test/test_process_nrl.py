"""
Regression test for the process_NRL.py script
"""


def test_process_sample_nrl_file():

    from fsoi.ingest.nrl.process_nrl import main as process_nrl_main

    data = '2019060200'

    process_nrl_main(data)

