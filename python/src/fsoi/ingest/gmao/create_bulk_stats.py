import sys

sys.path.append('../lib')
import lib_utils as lutils
import lib_obimpact as loi


def main():

    full_file_list = sys.argv[1:]

    for full_file in full_file_list:
        file = full_file.split('/')[-1]
        path = full_file.split(file)[0]

        df = lutils.readHDF(full_file, 'df')

        df = loi.BulkStats(df)
        bulk_full_file = '%s/bulk.%s' % (path, file)
        lutils.writeHDF(bulk_full_file, 'df', df, complevel=1, complib='zlib', fletcher32=True)

        df = loi.accumBulkStats(df)
        accum_full_file = '%s/accumbulk.%s' % (path, file)
        lutils.writeHDF(accum_full_file, 'df', df, complevel=1, complib='zlib', fletcher32=True)

        center = file.split('.')[0]
        platforms = loi.Platforms(center)
        df = loi.groupBulkStats(df, platforms)
        group_full_file = '%s/grpbulk.%s' % (path, file)
        lutils.writeHDF(group_full_file, 'df', df, complevel=1, complib='zlib', fletcher32=True)

    # accum = loi.accumBulkStats(all_df)
    # accum = loi.accumBulkStats(all_df)
    # accum = loi.accumBulkStats(ddf[0])
    # accums = []
    # accums.append(loi.accumBulkStats(ddf[0]))
    # accums.append(loi.accumBulkStats(ddf[1]))
    # accum = pd.concat(accums, axis=0)
    # av, std = loi.tavg(accum, level='PLATFORM')
    # summary = loi.summarymetrics(av)
    # df = av
    # df_std = std
    # for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
    #     try:
    #         plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                                  platform=platform, domain='Global')
    #         plotOpt['figname'] = '/tmp/sample.png'
    #         loi.summaryplot(df, qty=qty, plotOpt=plotOpt, std=df_std)
    #     except Exception as e:
    #         print(e)
    # cycle = 0
    # for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
    #     try:
    #         plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                                  platform=platform, domain='Global')
    #         plotOpt['figname'] = '/tmp/sample.png'
    #         loi.summaryplot(df, qty=qty, plotOpt=plotOpt, std=df_std)
    #     except Exception as e:
    #         print(e)
    # center = 'EMC'
    # savefig = True
    # for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
    #     try:
    #         plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                                  platform=platform, domain='Global')
    #         plotOpt['figname'] = '/tmp/sample.png'
    #         loi.summaryplot(df, qty=qty, plotOpt=plotOpt, std=df_std)
    #     except Exception as e:
    #         print(e)
    # platform = 'AMSUA'
    # for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
    #     try:
    #         plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                                  platform=platform, domain='Global')
    #         plotOpt['figname'] = '/tmp/sample.png'
    #         loi.summaryplot(df, qty=qty, plotOpt=plotOpt, std=df_std)
    #     except Exception as e:
    #         print(e)
    # qty = 'FracBenObs'
    # plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                          platform=platform, domain='Global')
    # cycle = [0]
    # plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                          platform=platform, domain='Global')
    # plotOpt['figname'] = '/tmp/sample.png'
    # loi.summaryplot(df, qty=qty, plotOpt=plotOpt, std=df_std)
    # platforms = loi.Platforms(center)
    # plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                          platform=platform, domain='Global')
    # loi.groupBulkStats(accum, platforms)
    # plotOpt = loi.getPlotOpt(qty, cycle=cycle, center=center, savefigure=savefig,
    #                          platform=platform, domain='Global')


if __name__ == '__main__':
    main()
