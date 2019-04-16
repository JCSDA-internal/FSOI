#!/bin/csh
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set center = "GMAO"
set norm = "txe"
set bdate = "2014120100"
set edate = "2015030100"
set remote_datadir = "/pub/data/obs_impact/DJF_${norm}_2014_2015"
set datadir = "$data/FSOI/data/$center"

# Get FTP information from GMAO.netrc
source GMAO.netrc

set adate = $bdate
while ( $adate < $edate )

    set yyyy = `echo $adate | cut -c1-4`
    set mm   = `echo $adate | cut -c5-6`
    set dd   = `echo $adate | cut -c7-8`
    set hh   = `echo $adate | cut -c9-10`

    mkdir -p $datadir/Y$yyyy/M$mm/D$dd
    cd $datadir/Y$yyyy/M$mm/D$dd

    echo "Fetching files for ... $norm, $adate"

    ftp -in $ftphost << EOT
user $ftpuser $ftppasswd
binary
cd $remote_datadir/M$mm/D$dd
mget *.ods
bye
EOT

    @ nfiles = `ls -1 *.ods | grep $norm | wc -l`

    echo "Fetched  files for ... $norm, $adate = $nfiles"

    set adate = `advance_time $adate +24h`

end

exit 0
