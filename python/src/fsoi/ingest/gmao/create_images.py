import sys

sys.path.append('../lib')
import lib_utils as lutils
import lib_obimpact as loi
import pandas as pd


def main():

    ddf = {}
    for (i, file) in enumerate(sys.argv[1:]):
        ddf[i] = lutils.readHDF(file, 'df')

    df, df_std = loi.tavg(pd.concat(ddf, axis=0), 'PLATFORM')

    center = 'EMC'

    platform = loi.Platforms(center)

    for qty in ['TotImp', 'ImpPerOb', 'FracBenObs', 'FracNeuObs', 'FracImp', 'ObCnt']:
        try:
            plot_options = loi.getPlotOpt(qty, cycle=[0], center=center, savefigure=True,
                                     platform=platform, domain='Global')
            plot_options['figname'] = '/tmp/%s' % qty
            loi.summaryplot(df, qty=qty, plotOpt=plot_options, std=df_std)
        except Exception as e:
            print(e)

    break_here = 0

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
