#!/bin/csh
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set center = "GMAO"
set norm = "twe"
set bdate = "2014120100"
set edate = "2015030100"
set remote_rootdir = "/pub/data/obs_impact"
set remote_datadir = "DJF_${norm}_2014_2015"
set datadir = "$data/FSOI/data/$center"

set adate = $bdate
while ( $adate < $edate )

    set yyyy = `echo $adate | cut -c1-4`
    set mm = `echo $adate | cut -c5-6`
    set dd = `echo $adate | cut -c7-8`
    set hh = `echo $adate | cut -c9-10`

    # We already have 00Z and 06Z sensitivities
    if ( $hh == "00" | $hh == "06" ) then
        set adate = `advance_time $adate +6h`
        continue
    endif

    rm -f job_script.csh
    cat > job_script.csh << EOF
#!/bin/csh -x
#SBATCH --job-name=$center$adate
#SBATCH --account=star
#SBATCH --partition=serial
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --output=/scratch/%u/output/$center/get.$adate.%j

source /etc/csh.cshrc

echo "Job started at \`date\`"

cd $data/FSOI/data/$center/Y${yyyy}/M${mm}/D${dd}

ftp -n gmaoftp.gsfc.nasa.gov << EOT
user anonymous anonymous
prompt
binary
cd $remote_rootdir/$remote_datadir/M${mm}/D${dd}
mget *_${hh}z.ods
bye
EOT

echo "Job ended at \`date\`"
exit 0
EOF
    chmod +x job_script.csh

    sbatch job_script.csh

    set adate = `advance_time $adate +6h`

end

rm -f job_script.csh

exit 0
