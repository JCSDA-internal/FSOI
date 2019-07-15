def test_unknwown_platforms_nrl():

    from fsoi.ingest.nrl.process_nrl import main as process_nrl_main

    # bypassing parser for date input
    process_nrl_main('2019020800')



