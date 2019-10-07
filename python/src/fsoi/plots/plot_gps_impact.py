#!/usr/bin/python

"""
Python code to plot global averages of GPS bending angle
innovation as a function of impact height

The innov_ar file is processed by module read_xiv.py

The routine computes averages over ndays (default 30)
with the date_time_group input being the last day

Usage:
python innovar_gps.py [data_time_group] [ndays]

"""

#import pdb

import glob
import os.path
import sys
import h5py

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import SymLogNorm
from matplotlib.ticker import FormatStrFormatter

import numpy as np

#import read_xiv
#from read_xiv import xiv_fld
import fsoi.plots.innovar_gps_io as innovar_gps_io
#from time_bar import add_time_bar

font_base = 16
thickness = 3.5

data_define = { 'zonal_fg_depar' : { 'range' : [-100.0, 100.0, None],
                                     'title' : ' Zonal Mean GPS-RO Bending Angle (O-B)/B % Innovation',
                          'filename_keyword' : 'mean',
                                      'cmap' : matplotlib.cm.bwr},
                'zonal_stdv_fg_depar' : { 'range' : [ 0.1, 100.0, None ],
                                     'title' : ' Zonal STDV GPS-RO Bending Angle (O-B)/B % Innovation',
                          'filename_keyword' : 'stdv',
                                      'cmap' : matplotlib.cm.nipy_spectral},
                'zonal_cnt'  : {     'range' : [   0, None, None ],
                                     'title' : ' Zonal Count GPS-RO Bending Angle Innovation',
                          'filename_keyword' : 'count',
                                      'cmap' : matplotlib.cm.nipy_spectral},}

colors = {'black'     :  '#000000', 
          'magenta'   :  '#ff00ff', 
          'cyan'      :  '#00ffff', 
          'yellow'    :  '#ffff00', 
          'green'     :  '#007f00', 
          'red'       :  '#ff0000', 
          'blue'      :  '#0000ff', 
          'navy'      :  '#000073', 
          'gold'      :  '#ffbb00', 
          'pink'      :  '#ff7f7f', 
          'aqua'      :  '#70db93', 
          'orchid'    :  '#db70db', 
          'gray'      :  '#7f7f7f', 
          'sky'       :  '#00a3ff', 
          'beige'     :  '#ffab7f'}
color_keys = list(colors.keys())

# Get constants from innovar_gps_io
REAL_SIZE = innovar_gps_io.REAL_SIZE
REAL_TYPE = innovar_gps_io.REAL_TYPE
MISSING = innovar_gps_io.MISSING
ly = innovar_gps_io.LY
lx = innovar_gps_io.LX
known_gps = innovar_gps_io.KNOWN_GPS
known_gps_id = innovar_gps_io.KNOWN_GPS_ID
known_gps_name = innovar_gps_io.KNOWN_GPS_NAME
gps_types = innovar_gps_io.NUMBER_OF_GPS_TYPES

#############################################################################
def main(filepath, cdtg, ndays, image_dir, exp_name):

    dtg_indx, mon_indx = innovar_gps_io.time_window(ndays, cdtg)
    d = get_data(dtg_indx, filepath)

    # finished computing stats - begin plotting
    print('  ')
    print('  ')
    print('Plotting...')

    ######################################################
    ###        now plot observation sensitivities      ###
    ######################################################
    if np.sum(d['cnt']) == 0: sys.exit(0)

    generate_gps_sensor_impact_plots(d, exp_name, dtg_indx, mon_indx, image_dir['obsens'])
    generate_gps_vertical_impact_plots(d, exp_name, dtg_indx, mon_indx, image_dir['obsens'])

    ######################################################
    ###    plot the mean & stdv for all GPS sensors    ###
    ######################################################
    #WINDOWS TESTS
    #image_name = os.path.join(image_dir['gps'],'gps_innov_'+cdtg)
    image_name = 'gps_innov_'+cdtg
    image_title = 'Global BA Innovation Statistics'
    plot_gps_global(d, d['sat_ids'], image_name, image_title, exp_name)

    ######################################################
    ### plot the zonal mean & stdv for each GPS sensor ###
    ######################################################
    d['zonal_cnt'] = np.ma.masked_less_equal(d['zonal_cnt'],2)
    d['zonal_fg_depar'] = np.ma.array(d['zonal_fg_depar'], mask = d['zonal_cnt'].mask)
    d['zonal_stdv_fg_depar'] = np.ma.array(d['zonal_stdv_fg_depar'], mask = d['zonal_cnt'].mask)

    for i,sat_id in enumerate(d['sat_ids']):
        (sensor_match, sensor) = get_matching_sensor(sat_id)

        # if we don't check this, it will match a non-matching sensor to the last index
        if not sensor_match:
            print(' ... could not recognize sat id: ' + sat_id)
            continue

        # skip times with no observations
        if np.sum(d['cnt'][:,i]) == 0: continue

        (image_title, image_name, sub_d) = get_single_sensor_global_plot_info_and_data(i, sensor, cdtg, image_dir, d)
        #WINDOWS_TESTS
        image_name = sensor + '_gps_innov_' +cdtg
        plot_gps_global(sub_d, [sat_id], image_name, image_title, exp_name)

        print('ok')

        # skip times with no observations
        if np.sum(d['zonal_cnt'][:,:,i]) == 0: continue

        print('ok')

        # plot the zonal mean for each GPS sensor
        for k in ['zonal_fg_depar', 'zonal_stdv_fg_depar', 'zonal_cnt']:
            data = d[k][:,:,i]

            (ttl, image_name, prange, color_map) = get_single_sensor_zonal_plot_info(sensor, k, cdtg, dtg_indx, image_dir, data)
            image_name = sensor + '_' + k + '_gps_innov_mean_' + cdtg
            plot_gps_zonal(data, image_name, ttl, prange=prange, color_map=color_map)

    # compress zonal mean & stdv for each GPS sensor into a single zonal field for plotting
    data = compress_zonal_stats(d)

    # plot the zonal stats for all assimilated GPS sensors
    for k, v in data.items():
        (ttl, image_name, prange, color_map) = get_all_sensors_zonal_plot_info(k, cdtg, dtg_indx, image_dir, v)
        #WINDOWS TESTS
        image_name = '_'.join(['gps', 'zonal', 'innov', data_define[k]['filename_keyword'], cdtg])
        plot_gps_zonal(data[k], image_name, ttl, prange=prange, color_map=color_map)

def get_matching_sensor(sat_id):
    sensor = False
    sensor_match = False
    for known_sat, known_sat_id in zip(known_gps_name, known_gps_id):
        if sat_id == known_sat_id:
            sensor_match = True
            sensor = known_sat
            break
    return (sensor_match, sensor)

#############################################################################
def get_data(dtg_indx, filepath):
    d = innovar_gps_io.initialize_data(dtg_index=dtg_indx, fsoi=True)

    for cloop in ['fg_depar', 'stdv_fg_depar']:
        for dx, dtg in enumerate(dtg_indx):

            # get path for h5 input file
            # input_path = os.path.join(filepath, 'g'+dtg)
            # input_file = os.path.join(filepath, 'g'+dtg, 'global_gps_stats_'+dtg+'.h5')


            # read h5 input file or skip dtg
            """
            if os.path.exists(input_file):
                glb, sens_on = innovar_gps_io.read_statistics(input_file)
            else:
                print(" at " + dtg + " no input .h5 file ")
                continue
            """
            glb, sens_on = innovar_gps_io.read_statistics(filepath)
            d = calculate_dtg_stats(d, dx, glb, dtg, cloop, sens_on)

        d = calculate_final_stats(d, cloop, sens_on)
    return d

#############################################################################
def get_single_sensor_global_plot_info_and_data(i, sensor, cdtg, image_dir, d):
    image_title = sensor + ' Global BA Innovation Statistics'
    ttlj='_'.join([sensor,'gps','innov',cdtg])
    image_name = os.path.join(image_dir['gps'], ttlj)
    sub_d = {}
    sub_d['times'] = d['times']
    for akey in ['fg_depar', 'stdv_fg_depar', 'cnt', 'nob']:
        sub_d[akey] = np.atleast_2d( d[akey][:,i] ).T

    return (image_title, image_name, sub_d)

#############################################################################
def get_single_sensor_zonal_plot_info(sensor, k, cdtg, dtg_indx, image_dir, data):
    # create Image title
    ttl = sensor + data_define[k]['title'] + '\n' + 'Data Period = ' + dtg_indx[0] + ' - ' + dtg_indx[-1]

    # create image file name
    ttlj='_'.join([sensor, 'gps', 'zonal', 'innov', data_define[k]['filename_keyword'], cdtg])
    image_name = os.path.join(image_dir['gps'], ttlj)

    # set range for plot
    prange = [ data_define[k]['range'][0], data_define[k]['range'][1], data_define[k]['range'][2] ]
    if not prange[1]: prange[1] = np.max( data )
    if not prange[2]: prange[2] = np.max([np.round(prange[1] / 5, decimals = -2), 100])

    # load color table
    color_map = data_define[k]['cmap']

    return (ttl, image_name, prange, color_map)


#############################################################################
def get_all_sensors_zonal_plot_info(k, cdtg, dtg_indx, image_dir, v):
    # create Image title
    ttl = data_define[k]['title'] + '\n' + 'Data Period = ' + dtg_indx[0] + ' - ' + dtg_indx[-1]

    # create image file name
    ttlj='_'.join(['gps', 'zonal', 'innov', data_define[k]['filename_keyword'], cdtg])
    image_name = os.path.join(image_dir['gps'], ttlj)

    # set range for plot
    prange = [ data_define[k]['range'][0], data_define[k]['range'][1], data_define[k]['range'][2] ]
    if not prange[1]: prange[1] = np.max( v )
    if not prange[2]: prange[2] = np.max([np.round(prange[1] / 5, decimals = -2), 100])

    # load color table
    color_map = data_define[k]['cmap']

    return (ttl, image_name, prange, color_map)

#############################################################################
def compress_zonal_stats(d):
    # first get count
    count = np.ma.masked_less_equal( np.sum( d['zonal_cnt'], axis = 2 ), 1 )

    # second get the mean
    mean = np.ma.array( np.sum( d['zonal_cnt'] * d['zonal_fg_depar'], axis = 2 ), mask = count.mask, fill_value = MISSING )
    mean = mean / count 

    # third use mean to get the stdv
    stdv = mean[:,:,np.newaxis] - d['zonal_fg_depar' ]
    stdv = d['zonal_cnt'] * ( stdv**2 + d['zonal_stdv_fg_depar']**2 )
    stdv = np.ma.array( np.sum( stdv, axis=2 ), mask = count.mask, fill_value = MISSING )
    stdv = np.sqrt( stdv / count )

    data = {'zonal_fg_depar' : mean,
            'zonal_stdv_fg_depar' : stdv,
            'zonal_cnt'  : count}
    return data

#############################################################################
def calculate_final_stats(d, cloop, sens_on):

    good = np.where(d['cnt'] > 1)
    good_zonal = np.where(d['zonal_cnt'] > 1)

    not_good = np.where(d['cnt'] <= 1)
    not_good_sens = np.where(d['sens_cnt'] <= 1)
    not_good_zonal = np.where(d['zonal_cnt'] <= 1)
    not_good_zonal_sens = np.where(d['zonal_sens_cnt'] <= 1)

    if cloop == 'fg_depar':
        # compute the average
        d['fg_depar'][good] = d['fg_depar'][good] / d['cnt'][good]
        d['zonal_fg_depar'][good_zonal] = d['zonal_fg_depar'][good_zonal] / d['zonal_cnt'][good_zonal]
        d['fg_depar'][not_good] = MISSING
        d['zonal_fg_depar'][not_good_zonal] = MISSING
        if sens_on:
            d['ob_sens'][not_good_sens] = MISSING
            d['zonal_ob_sens'][not_good_zonal_sens] = MISSING
    else:
        d['stdv_fg_depar'][good] = np.sqrt( d['stdv_fg_depar'][good] / d['cnt'][good] )
        d['zonal_stdv_fg_depar'][good_zonal] = np.sqrt( d['zonal_stdv_fg_depar'][good_zonal] / d['zonal_cnt'][good_zonal] )
        d['stdv_fg_depar'][not_good] = MISSING
        d['zonal_stdv_fg_depar'][not_good_zonal] = MISSING

    return d

#############################################################################
def calculate_dtg_stats(d, dx, glb, dtg, cloop, sens_on):

    # count overall for this date time group
    d['dtg_cnt'][dx] = glb['cnt'].sum()
    for d_sat_index, d_sat_id in enumerate(d['sat_ids']):
        sensor_match = False
        for glb_sat_index, glb_sat_id in enumerate(glb['sat_ids']):
            if d_sat_id == glb_sat_id:
                sensor_match = True
                break
        if sensor_match:
            d['sensor_dtg_cnt'][dx, d_sat_index] = glb['cnt'][:,glb_sat_index].sum()
    d['times'].append(dtg)

    if cloop == 'fg_depar':
        # weight mean from date time group by its count
        d['fg_depar'] += glb['cnt'] * glb['fg_depar']
        d['cnt'] += glb['cnt']
        d['nob'] += glb['nob']
        d['zonal_fg_depar'] += glb['zonal_cnt'] * glb['zonal_fg_depar']
        d['zonal_cnt'] += glb['zonal_cnt']
        ### ob sensitivity
        if sens_on:
            d['ob_sens'] += glb['ob_sens']
            d['sens_cnt'] += glb['sens_cnt']
            d['zonal_ob_sens'] += glb['zonal_ob_sens']
            d['zonal_sens_cnt'] += glb['zonal_sens_cnt']
    else:
        # weight stdv from date time group by its count
        d['stdv_fg_depar'] += glb['cnt'] * (glb['stdv_fg_depar']**2 + (d['fg_depar']-glb['fg_depar'])**2)
        d['zonal_stdv_fg_depar'] += glb['zonal_cnt'] * \
                        (glb['zonal_stdv_fg_depar']**2 + (d['zonal_fg_depar'] - glb['zonal_fg_depar'])**2)

    return d

#############################################################################
def plot_gps_global(d, csat_ids, image_name, image_title, exp_name):
    # ============================================
    # == now plot the vertical means averaged over time
    # ============================================

    fig = plt.figure(figsize=(6.5,6.5))

    pion=(0.1, 0.075, 0.85, 0.8)
    ax = fig.add_axes(pion)

    font_base = 16
    thickness = 3.5

    # set min/max of x&y axes[xmin,xmax,ymin,ymax]
    xrange=np.array([-10.0, 10.0])
    yrange=np.array([0.0, 60.0])

    # make a vertical dotted line along x=0
    plt.plot([0.0,0.0],yrange,'-',linewidth=3.5,color='#b1b1b1')

    iclr = -1
    for l, sat_id in enumerate(csat_ids):
        (sensor_match, sensor) = get_matching_sensor(sat_id)
        if not sensor_match:
            continue
        good = d['nob'][:,l]
        xses = d['fg_depar'][:,l]
        xses = xses.compress((good>1).flat) 
        yses = ly['bins'].compress((good>1).flat)/1000.
        if np.sum(good) > 0:
            print(sensor, np.sum(good))
            iclr += 1
            if len(csat_ids) == 1:
                iclr = color_keys.index('blue')
            plt.plot(xses,yses,'-', linewidth=thickness,
                     color=colors[color_keys[iclr]], label=sensor)

    plt.axis((xrange[0], xrange[1], yrange[0], yrange[1]))
    leg = ax.legend(loc='center left',labelspacing=0.025)

    # legend handles have changed? bypass if not compatible
    try:
        leg.draw_frame(False)
        frame  = leg.get_frame()  
        # matplotlib.text.Text instances
        for t in leg.get_texts():
            t.set_fontsize(font_base*0.75)    # the legend text fontsize
            t.set_fontweight('demibold') 
        # matplotlib.lines.Line2D instances
        for l in leg.get_lines():
            l.set_linewidth(thickness)  # the legend line width
    except:
        pass


    # frame has the legend coordinates would like to use
    # add the beginning and ending dtg
    cstr = 'first cycle:\n' + d['times'][0]+'\n' + \
          '\nlast cycle:\n' + d['times'][-1]
    xoff = (xrange[1]-xrange[0])/5.5
    yoff = (yrange[1]-yrange[0])/17
    ax.text(xrange[0]+xoff, yrange[0]+yoff,cstr, fontsize=font_base*0.75, \
            horizontalalignment='center', weight='demibold', color='k')

    # frame has the legend coordinates would like to use
    # add label for what the different line styles designate
    cstr = 'Mean -- Solid\n' + \
           'STDV -- Dashed\n' + \
           'Count -- Dotted'
    xoff = (xrange[1]-xrange[0])/4.5
    yoff = (yrange[1]-yrange[0])/3.5
    ax.text(xrange[0]+xoff, yrange[1]-yoff,cstr, fontsize=font_base*0.75, \
            horizontalalignment='center', weight='demibold', color='k')

    plt.xlabel('(O-B)/B %',weight='demibold')
    plt.ylabel('Impact Height (km)',weight='demibold')

    # plot the STDV as a dashed line
    iclr = -1
    for l, sensor in enumerate(csat_ids):
        (sensor_match, sensor) = get_matching_sensor(sat_id)
        if not sensor_match:
            continue
        good = d['nob'][:,l]
        xses = d['stdv_fg_depar'][:,l]
        xses = xses.compress((good>1).flat)
        yses = ly['bins'].compress((good>1).flat)/1000.
        if np.sum(good) > 0:
            iclr += 1
            if len(csat_ids) == 1:
                iclr = color_keys.index('blue')
            plt.plot(xses,yses,'--', linewidth=thickness,
                     color=colors[color_keys[iclr]])
    plt.axis((xrange[0], xrange[1], yrange[0], yrange[1]))
    majorLocator  = matplotlib.ticker.MultipleLocator(2)  # set Major x-tick interval to 2
    minorLocator  = matplotlib.ticker.MultipleLocator(1)  # set minor x-tick interval to 1
    ax.xaxis.set_major_locator( majorLocator )
    ax.xaxis.set_minor_locator( minorLocator )

    for t in ax.get_xticklabels() + ax.get_yticklabels():
        t.set_fontsize(font_base*0.75)
        t.set_fontweight('demibold')


    # plot the number of assimilated observations as a dotted line
    ax2 = ax.twiny()
    iclr = -1
    for l, sensor in enumerate(csat_ids):
        (sensor_match, sensor) = get_matching_sensor(sat_id)
        if not sensor_match:
            continue
        good = d['nob'][:,l]
        xses = d['cnt'][:,l]
        xses = xses.compress((good>1).flat) / 1000.
        xses2 = d['nob'][:,l]
        xses2 = xses2.compress((good>1).flat) / 1000.
        yses = ly['bins'].compress((good>1).flat) / 1000.
        for k, val in enumerate(xses):
            print ( "%s  height %9.2f  count %11.3f   nob %11.3f" % (sensor, yses[k], val, xses2[k]) )
        if np.sum(good) > 0:
            iclr += 1
            if len(csat_ids) == 1:
                iclr = color_keys.index('blue')
            plt.plot(xses,yses,':', linewidth=thickness,
                     color=colors[color_keys[iclr]])

    for t in ax2.get_xticklabels(): 
        t.set_fontsize(font_base*0.75)
        t.set_fontweight('demibold')


    plt.xlabel('Observation Count (thousands)   Run: '+exp_name,weight='demibold')
    plt.suptitle(image_title,fontweight='demibold',fontsize=font_base)

    #plt.show()
    #plt.ion()

    fig.savefig('%s.png' % image_name, format='png') 
    plt.close(fig)

#############################################################################
def plot_gps_zonal(data, image_name, ttl, prange=None, color_map=None):

    font_base = 12

    # plot the data
    fig = plt.figure(figsize=(14,11.5))

    pion = (0.10, 0.15, 0.85, 0.80)
    cb_pion = (0.10, 0.05, 0.825, 0.05)

    # define plotting axis 
    ax = fig.add_axes(pion)

    if not color_map: color_map = matplotlib.cm.nipy_spectral

    # set the labels for the x-axis (latitude) 
    xticks=[] 
    xlabs=[]
    xstep = int(30)/int(lx['bin'])  # 10-degree labels x-axis
    for atick in range(0,int(lx['num']),int(xstep)):
        xticks.append(float(atick) + 0.5)
        xlabs.append(np.round(lx['bins'][atick]))
    ax.xaxis.set_ticks(xticks)
    ax.xaxis.set_ticklabels(np.array(xlabs,dtype='int32'),fontsize=font_base,
                            fontweight='demibold',color='k')

    # set the labels for the y-axis (impact height)
    yticks=[]
    ylabs=[]
    ystep = int(5000)/int(ly['bin'])  # 5-km labels y-axis
    for atick in range(0,int(ly['num']),int(ystep)):
        yticks.append(float(atick) + 0.5)
        ylabs.append(np.round(ly['bins'][atick]/1000.))
    ax.yaxis.set_ticks(yticks)
    ax.yaxis.set_ticklabels(np.array(ylabs,dtype='int32'),fontsize=font_base,
                            fontweight='demibold',color='k')

    #  define colorbar ticks and normalization of colors for data 
    if 'mean' in image_name:
        norm = SymLogNorm(0.2718, vmin=prange[0], vmax=prange[1])
        #norm = matplotlib.colors.Normalize(vmin=prange[0], vmax=prange[1])
        cb_format = '%0.1f'
    elif 'stdv' in image_name:
        norm = matplotlib.colors.LogNorm(vmin=prange[0], vmax=prange[1])
        cb_format = '%0.1f'
    elif 'count' in image_name:
        norm = matplotlib.colors.Normalize(vmin=prange[0], vmax=prange[1])
        cb_format = '%d'
    else:
        norm = matplotlib.colors.Normalize(vmin=prange[0], vmax=prange[1])
        cb_format = None

    ####  main plot using 'pcolor'  ####
    c = plt.pcolor(data, edgecolors='none', norm=norm, cmap=color_map )

    # set min/max of x&y axes[xmin,xmax,ymin,ymax]
    ymax = np.min( np.where(ly['bins'] > 60000) )
    plt.axis([ 0, lx['num'], 1, ymax ])

    plt.ylabel('Impact Height (km)',fontsize=font_base,fontweight='demibold')
    plt.title(ttl,fontweight='demibold',fontsize=1.5*font_base)

    #   add a colorbar 
    cax = fig.add_axes(cb_pion)
    if 'mean' in image_name:
        cb = matplotlib.colorbar.ColorbarBase(ax=cax,orientation='horizontal', 
                                      ticks=[-100, -10, -1., 0.0, 1., 10., 100.],
                                      cmap=color_map, norm=norm, format=cb_format )
    else:
        cb = matplotlib.colorbar.ColorbarBase(ax=cax,orientation='horizontal', 
                                      cmap=color_map, norm=norm, format=cb_format )

    for line in cax.get_xticklabels():
        line.set_color('k')
        line.set_fontsize(font_base)
        line.set_fontweight('demibold')

    print('writing image %s.png' % image_name)
    fig.savefig('%s.png' % image_name, format='png') 
    plt.close(fig)

#############################################################################
def generate_gps_vertical_impact_plots(d, exp_name, dtg_indx, mon_indx, image_dir):
    # _+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_
    #|                                                   | 
    #|  plot channel sensitivities for each vertical bin |
    #|_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _|
    #  + + + + + + + + + + + + + + + + + + + + + + + + +
    for i,sat_id in enumerate(d['sat_ids']):

        #skip this sensor if it doesn't match any of the known ids
        (sensor_match, sensor) = get_matching_sensor(sat_id)
        if not sensor_match:
            continue

        if np.sum(d['sens_cnt'][:,i]) == 0:  # no observation check
            print('skipping: ', sensor)
            continue

        nobs = np.array( d['sensor_dtg_cnt'][:,i] )

        # plot total impact
        sens = -1.0 * np.ma.masked_less_equal( d['ob_sens'][:,i], -990 )
        title = "NAVDAS-AR Observation Sensitivity"
        imgname = '_'.join( [exp_name, 'navadj', 'ar', 'gps', sensor ] )
        #WINDOWS TEST
        #imgname = os.path.join(image_dir , imgname)
        plot_gps_vertical_impact(sens, title, imgname, sensor, nobs, dtg_indx, mon_indx)
        print("ca passe")
        # plot per ob impact
        sens_cnt = d['sens_cnt'][:,i]
        sens_per_ob = []
        for data,cnt in zip(sens,sens_cnt):
            if cnt == 0.0:
                sens_per_ob.append(0.0)
            else:
                sens_per_ob.append(float(data/cnt)*1.e6)
        title = "NAVDAS-AR Per Observation Sensitivity (1e-6)"
        imgname = '_'.join( [exp_name, 'navadj', 'ar', 'gps', sensor , 'per_ob'] )
        #WINDOWS TESTS
        #imgname = os.path.join(image_dir , imgname)
        plot_gps_vertical_impact(sens_per_ob, title, imgname, sensor, nobs, dtg_indx, mon_indx)

def plot_gps_vertical_impact(sens, title, imgname, sensor, nobs, dtg_indx, mon_indx):
    rnd = np.ceil(np.max(np.absolute(sens))/0.05)*0.05   #  Fixed Min/Max
    if rnd > 0.5 : 
        rnd = np.ceil(rnd/0.1)*0.1
    if rnd > 1.1 :
        rnd = np.ceil(rnd/0.5)*0.5
    xival = rnd/2.5

    # make the colorbar xrange symetric
    xrange = np.array([-1.*rnd,rnd])

    yrange = np.array([0.,60000.])

    fig = plt.figure(figsize=(6.5,6.5))

    # the gridspec nrows and ncols, then ratios for each row 
    gs = matplotlib.gridspec.GridSpec(3,1,height_ratios=[12,2,1],hspace=0)

    ax = plt.subplot(gs[0])

    #make a vertical dotted line along x=0
    ax.plot([0.0,0.0],yrange,'-',linewidth=0.75*thickness,color='k')
    ax.set_axisbelow(True)
    ax.grid(which='major', axis='both')

    ypos = ly['bins'] + ly['bin']/2.
    norm = matplotlib.colors.Normalize(vmin=xrange.min(),vmax=xrange.max()) # normalize colors
    cmap = matplotlib.cm.get_cmap('RdBu')

    #plot the bars indicating the observation sensitivity
    patches = ax.barh(ypos, sens, align='center', height=ly['bin']/1.5)
    for (obsens, patch) in zip(sens, patches):
        patch.set_facecolor(cmap(norm(obsens)))

    #define x and y axis limits
    ax.axis((xrange[0], xrange[1], yrange[0], yrange[1]))

    ax.get_xaxis().tick_bottom()
    xmin, xmax = ax.get_xaxis().get_view_interval()
    ymin, ymax = ax.get_yaxis().get_view_interval()
    ax.add_artist(Line2D((xmin, xmax), (ymin, ymin), color='black', linewidth=2))
    ax.add_artist(Line2D((xmin, xmin), (ymin, ymax), color='black', linewidth=2))
    for t in ax.get_xticklabels()+ax.get_yticklabels():
        t.set_fontsize(0.75*font_base)
        t.set_fontweight('demibold')
    ax.tick_params(axis='x',which='minor',bottom=False)
    ax.tick_params(axis='y',which='minor',bottom=False)
    ax.xaxis.set_label_text('24 Hr Fcst Error Norm Reduction', size=0.75*font_base, weight='demibold')
    ax.yaxis.set_label_text('Impact Height (m)', size=0.75*font_base, weight='demibold')

    #print the instrument name on plot
    plt.title(sensor,fontsize=0.75*font_base,fontweight='demibold')

    nobs = nobs / 1.e3
    time_bar_ax = plt.subplot(gs[2])
    # add_time_bar(time_bar_ax, nobs, dtg_indx, mon_indx, gs, exp=3)   # need sensor total of gps counts

    plt.suptitle(title ,weight='demibold')

    fig.subplots_adjust(left=0.15, right=0.9)

    print('saving gps figure %s.png'%imgname)
    fig.savefig('%s.png' % imgname, format='png') 
    plt.close(fig)

def generate_gps_sensor_impact_plots(d, exp_name, dtg_indx, mon_indx, image_dir):
    # _+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_+_
    #|                                               | 
    #|  plot sensitivities for each sensor           |
    #|_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _|
    #  + + + + + + + + + + + + + + + + + + + + + + + 
    instr_sens = { 'name' : [],
                    'cnt' : [],
                   'sens' : [],
            'sens_per_ob' : [] }

    if np.sum(d['sens_cnt']) == 0: return    # absolutely no observations

    for i, sensor_id in enumerate(d['sat_ids']):
        (sensor_match, sensor) = get_matching_sensor(sensor_id)
        if not sensor_match:
            continue
 
        if np.sum(d['sens_cnt'][:,i]) == 0:  # no observation check
            continue
        # == store the sensor values for the summary plot ==
        instr_sens['name'].append( sensor )
        instr_sens['cnt'].append(np.sum( d['sens_cnt'][:,i] ))
        sens = np.ma.masked_less_equal( d['ob_sens'][:,i], -990 )
        instr_sens['sens'].append(np.sum(sens) )
        instr_sens['sens_per_ob'].append(np.sum(sens) / np.sum( d['sens_cnt'][:,i] ))

    # plot total impact
    csens = -1.0 * np.array(instr_sens['sens'])
    title = 'NAVDAS-AR GPS Ob Sensitivity'
    imgname = '_'.join( [exp_name, 'navadj', 'ar', 'gsnn', 'summary'] )
    #WINDOWS TESTS
    #imgname = os.path.join(image_dir, imgname)
    plot_gps_sensor_impact(csens, d, dtg_indx, mon_indx, instr_sens, title, imgname)
    # plot per ob impact
    sens_per_ob = -1.0 * np.array(instr_sens['sens_per_ob']) * 1.e6
    title = 'NAVDAS-AR GPS Per Ob Sensitivity (1e-6)'
    imgname = '_'.join( [exp_name, 'navadj', 'ar', 'gsnn', 'per', 'ob'] )
    #WINDOWS TESTS
    #imgname = os.path.join(image_dir, imgname)
    plot_gps_sensor_impact(sens_per_ob, d, dtg_indx, mon_indx, instr_sens, title, imgname)

#############################################################################
def plot_gps_sensor_impact(csens, d, dtg_indx, mon_indx, instr_sens, title, imgname):
    rnd = np.ceil(np.absolute(np.max(csens))/0.05)*0.05
    if rnd > 0.5: 
        rnd = np.ceil(rnd/0.25)*0.25
    if rnd > 1.1:
        rnd = np.ceil(rnd/2.5)*2.5

    xrange = np.array([ 0.0, rnd ])
    yrange = np.array([ 0.0, len(csens) ])

    fig = plt.figure(figsize=(8.0,7.0))

    # the gridspec nrows and ncols, then ratios for each row 
    gs = matplotlib.gridspec.GridSpec(3,1,height_ratios=[12,2,1],hspace=0)

    ax = plt.subplot(gs[0])

    ypos = np.arange(yrange[1])+0.5
    norm = matplotlib.colors.Normalize(vmin=xrange.min(), vmax=xrange.max()) # normalize colors
    cmap = matplotlib.cm.get_cmap('RdBu')

    patches = ax.barh(ypos, csens, align='center')
    # Lastly, write in the ranking inside each bar to aid in interpretation
    for patch in patches:
        width = patch.get_width()
        if (width < .05*float(xrange[1])): # The bars aren't wide enough to print the ranking inside
            xloc = width + .02*float(xrange[1]) # Shift the text to the right side of the right edge
            clr = 'black' # Black against white background
            align = 'left'
        else:
            xloc = 0.98*width # Shift the text to the left side of the right edge
            clr = 'white' # White on magenta
            align = 'right'

        bar_label = str( np.round(width, decimals=2) )
        yloc = patch.get_y()+patch.get_height()/2.0 #Center the text vertically in the bar
        ax.text(xloc, yloc, bar_label, horizontalalignment=align,
                 verticalalignment='center', color=clr, weight='demibold', size=0.75*font_base)

    ax.axis((xrange[0], xrange[1], yrange[0], yrange[1]))
    ax.yaxis.set_ticks(ypos)
    ax.yaxis.set_ticklabels(instr_sens['name'])
    for t in ax.get_xticklabels():
        t.set_fontsize(0.75*font_base)
        t.set_fontweight('demibold')
    ax.xaxis.set_label_text('24 Hr Fcst Error Norm Reduction', size=0.75*font_base, weight='demibold')

    # put total number of assimilated observations as 2nd y-axis label
    ax2 = ax.twinx()
    ob_cnt = np.round( np.array(instr_sens['cnt'],dtype='float64')/1.e6, decimals=2)
    ax2.xaxis.set_visible(False)
    ax2.yaxis.set_ticks(np.arange(len(csens))+0.5)
    ax2.yaxis.set_ticklabels(ob_cnt)
    ax2.yaxis.set_label_text('Observation Count (1e6)')
    ax2.yaxis.label.set_fontweight('demibold')
    for t in ax2.get_yticklabels():
        t.set_fontsize(0.75*font_base)
        t.set_fontweight('demibold')
    ax2.axis((xrange[0], xrange[1], yrange[0], yrange[1]))

    # add bar at bottom showing time history of observations
    nobs = np.array( d['dtg_cnt'] ) / 1.e3
    # time_bar_ax = plt.subplot(gs[2])
    # add_time_bar(time_bar_ax, nobs, dtg_indx, mon_indx, gs, exp=3)  # need total from all sensors

    plt.suptitle(title, weight='demibold', fontsize=font_base)

    fig.subplots_adjust(left=0.15, right=0.875)

    print('saving figure %s.png' % imgname)

    fig.savefig('%s.png' % imgname, format='png')
    plt.close(fig)


if __name__ == "__main__":

    from optparse import OptionParser

    usage = 'usage: %prog -d date-time -i input-loc -o image-dir -r ar_run [-n ndays]'

    parser = OptionParser(usage)
    parser.add_option('-o', '--image-dir', dest='image_dir',
                      action='store', default=None,
                      help='Output location for image')
    parser.add_option('-i', '--input-loc', dest='filepath',
                      action='store', default=None,
                      help='Location of input files')
    parser.add_option('-d', '--date-time', dest='cdtg',
                      action='store', default=None,
                      help='10-digit date time group')
    parser.add_option('-n', '--ndays', dest='ndays',
                      action='store', default=30,
                      help='size of time window days backwards')
    parser.add_option('-r', '--run-name', dest='ar_run',
                      action='store', default=None,
                      help='name of experiment run')

    (options, args) = parser.parse_args()

    # chk date
    if (options.cdtg):
        if len(options.cdtg) != 10:
            parser.error("expecting date in 10 character (yyyymmddhh) format \n \
                        received date: %s" % options.cdtg)
    else:
        parser.error("provide date in 10 character (yyyymmddhh) format, specify with -d option")

    if not options.filepath:
        parser.error("no path to monitoring directories given, specify with -i option")
    if not os.path.isdir(options.filepath):    
        parser.error("Missing monitoring directory: %s"% options.filepath)

    if not options.image_dir:
        parser.error("no path for outputting images given, specify with -o option")
    image_dir = { 'gps' :  os.path.join( options.image_dir, 'gps' ), 
                  'obsens' : os.path.join( options.image_dir, 'obsens' ) }
    for adir in image_dir:
        if not os.path.exists(image_dir[adir]):
            os.makedirs(image_dir[adir])

    if not options.ar_run:
        parser.error("no name for experiment run given, specify with -r option")

    main(options.filepath, options.cdtg, options.ndays, image_dir, options.ar_run)
