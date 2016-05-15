#!/bin/csh
###############################################################
# < next few lines under version control, D O  N O T  E D I T >
# $Date$
# $Revision$
# $Author$
# $Id$
###############################################################

set formulation = $1
set center = "JMA"
set dir_scripts="$data/FSOI/process/$center"
set indir = "/data/users/jxu/FSOI/FSO_data/$center"
if ( $formulation == "ens" ) then
    set indir = "$indir/original"
else if ( $formulation == "adj" ) then
    set indir = "$indir/DJF_JMA_DRY_Original_Adjoint"
endif
set outdir = "/data/users/rmahajan/FSOI/ascii/$center/$formulation"
set bdate = "2014120100"
set edate = "2015030100"

cd $dir_scripts

set adate = $bdate
while ( $adate < $edate )

    echo "Creating job script for $adate"

    rm -f job_script.csh
cat > job_script.csh << EOF
#!/bin/csh
#SBATCH --job-name=$center$adate
#SBATCH --account=star
#SBATCH --partition=serial
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=/scratch/%u/output/$center/log.$formulation.$adate.%j

source /etc/csh.cshrc

echo "Job started at \`date\`"

set input = $indir/${formulation}_fso_jma_${adate}00.dat
set output = $outdir/${center}_$adate.txt

cd $dir_scripts
./process_$center.py -i \$input -o \$output

echo "Job ended at \`date\`"
exit 0
EOF
    chmod +x job_script.csh

    sbatch job_script.csh

    set adate = `advance_time $adate +6h`
end

rm -f job_script.csh

exit 0
