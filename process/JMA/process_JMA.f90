!##############################################################
! < next few lines under version control, D O  N O T  E D I T >
! $Date$
! $Revision$
! $Author$
! $Id$
!##############################################################

program process_JMA

    implicit none

    integer, parameter :: i_kind = 4
    integer, parameter :: r_kind = 4

    ! Header
    type diag_header
        sequence
        character(len=8) :: formulation    ! "ADJOINT" or "ENSEMBLE"
        integer(i_kind)  :: idate(1:5)     ! Base date (initial date)
        integer(i_kind)  :: nobstot        ! No. of observations (total)
    end type diag_header

    ! Body
    type diag_data
        sequence
        character(len=8):: elem      ! observed element *1
        integer(i_kind) :: channel   ! channel for radiance observations; 0 for non-radiances
        real(r_kind)    :: rlon      ! latitude  [deg]
        real(r_kind)    :: rlat      ! longitude [deg]
        real(r_kind)    :: rlev      ! level (height) *2
        character(len=12):: otype    ! obs type (sensor name for radiance) *3
        character(len=12):: satname  ! satellite name (N/A if conventional) *4
        real(r_kind)    :: omb       ! O-B departure
        real(r_kind)    :: oma       ! O-A departure
        real(r_kind)    :: oberr     ! standard deviation of the prescribed observation error
        real(r_kind)    :: fso_kin   ! FSO impact   [J/kg] (kinetic     energy norm) *5
        real(r_kind)    :: fso_dry   ! FSO impact   [J/kg] (dry   total energy norm)
        real(r_kind)    :: fso_moist ! FSO impact   [J/kg] (moist total energy norm) *5
        real(r_kind)    :: fsr_kin   ! R-sensitivity[J/kg] (kinetic     energy norm) *5
        real(r_kind)    :: fsr_dry   ! R-sensitivity[J/kg] (dry   total energy norm)
        real(r_kind)    :: fsr_moist ! R-sensitivity[J/kg] (moist total energy norm) *5
        ! Notes:
        !  *1: one of the following: U, V, T, RH, PS, ZTD, BendAng and N/A (N/A is for radiances).
        !  *2: On ENSEMBLE, the height is represented as pressure in [Pa]; the height
        !      for radiance observations is the pressure at which the corresponding
        !      weighting function takes its maximum.
        !      On ADJOINT, the height for conventional observations (except GNSS-RO) is
        !      represented as pressure in [Pa]; the height for GNSS-RO observations is
        !      represented as geometrical height in [km]; for radiance observations, height is not available. 
        !  *3: one of the following:
        !   SYNOP       GNSSTPW     HIRS        SSMI        
        !   SHIP        GNSSDELAY   AIRS        TMI         
        !   BUOY        GNSSRO      MHS         GMI         
        !   RADIOSONDE  AMV-GEOSTAT IASI        AMSRE       
        !   PILOT       AMV-MODIS   ATMS        AMSR2       
        !   AIRCRAFT    AMV-AVHRR   CrIS        SSMIS       
        !   PAOB        AMV-LEOGEO  FY3MWHS     Coriolis    
        !   TYBOGUS     AMV-MODIS   FY3MWTS     FY3MWRI     
        !   PROFILER    AMSUB       SAPHIR      CSR         
        !   RADAR       AMSUA       SCATWIND    OTHERS      
        !  *4: one of the following (subject to the exception for GNSS-RO on ADJOINT):
        !   Aqua     DMSP-F13 FY-3B   GOES14       METEOSAT4  Metop-C   NOAA19    
        !   C/NOFS   DMSP-F14 GCOM-W1 GOES15       METEOSAT5  MTSAT-1R  NPP       
        !   CHAMP    DMSP-F15 GMS4    GRACE-A      METEOSAT6  MTSAT-2   QuikSCAT   
        !   Coriolis DMSP-F16 GMS5    GRACE-B      METEOSAT7  NOAA11    SAC-C      
        !   COSMIC1  DMSP-F17 GOES8   Himawari-8   METEOSAT8  NOAA12    Terra      
        !   COSMIC2  DMSP-F18 GOES9   Himawari-9   METEOSAT9  NOAA14    TerraSAR-X 
        !   COSMIC3  FY-2C    GOES10  INSAT        METEOSAT10 NOAA15    TRMM       
        !   COSMIC4  FY-2D    GOES11  KALPANA      METEOSAT11 NOAA16    N/A
        !   COSMIC5  FY-2E    GOES12  LEO/GEO      Metop-A    NOAA17   
        !   COSMIC6  FY-3A    GOES13  Megha-Tropiq Metop-B    NOAA18   
        !   * exception: On ADJOINT, the exact satellite name for GNSS-RO observations
        !                are not available. Instead, the sensor name (one of the
        !                following) is given: GRACE-A, IGOR or GRAS.
        !  *5: Available only on ENSEMBLE; on ADJOINT, these fields are filled with
        !      HUGE(real*4)
    end type diag_data

    integer, parameter :: iunit=10
    integer, parameter :: ounit=20
    type(diag_header) :: oheader
    type(diag_data) :: odata
    character(len=255) :: ifile,ofile
    integer(i_kind) :: iflag,iobs,nmetric
    logical :: fexist

    character(len=8) :: obtype
    character(len=25) :: platform
    integer(i_kind) :: channel
    real(r_kind) :: lat,lon,lev,oma,omb,oberr
    real(r_kind),allocatable,dimension(:) :: impact

    call getarg(1,ifile)
    call getarg(2,ofile)

    inquire(file=ifile,exist=fexist)
    if ( .not. fexist ) then
        write(6,'(a,a)') '***ERROR*** file does not exist, file = ', trim(ifile)
        go to 900
    endif

    open(iunit,file=trim(ifile),action='read',form="unformatted",access='sequential',convert='big_endian',iostat=iflag)
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') '***ERROR*** cannot open file for reading, iostat = ', iflag
        goto 900
    endif

    open(ounit,file=trim(ofile),action='write',form='formatted',iostat=iflag)
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') '***ERROR*** cannot open file for writing, iostat = ', iflag
        goto 900
    endif

    read(iunit,iostat=iflag) oheader
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') '***ERROR***. cannot read header, iostat = ', iflag
        goto 800
    endif

    if ( oheader%formulation == 'ENSEMBLE' ) then
        nmetric = 3
    elseif ( oheader%formulation == 'ADJOINT' ) then
        nmetric = 1
    endif

    allocate(impact(nmetric))

    do iobs = 1,oheader%nobstot

        read(iunit,iostat=iflag) odata
        if ( iflag /= 0 ) then
            write(6,'(a,a,i5)') '***ERROR***. cannot read data, iostat = ', iflag
            goto 800
        endif

        if ( odata%elem == 'N/A     ' ) then ! radiances
            obtype        = 'Tb      '
            channel       = odata%channel
            platform = trim(adjustl(odata%otype)) // '_' // trim(adjustl(odata%satname))
        else ! non-radiance
            obtype        = odata%elem
            channel       = -999
            platform = adjustr(odata%otype)
        endif

        lat            = odata%rlat
        lon            = odata%rlon
        lev            = odata%rlev
        omb            = odata%omb
        oma            = odata%oma
        oberr          = odata%oberr
        impact(1)      = odata%fso_dry
        if ( nmetric > 1 ) then
            impact(2) = odata%fso_moist
            impact(3) = odata%fso_kin
        endif

        if ( lev == HUGE(0.0_r_kind) ) then
            lev = -999.0_r_kind
        else
            if ( oheader%formulation == 'ENSEMBLE' ) then
                lev = lev / 100.0_r_kind
            elseif ( oheader%formulation == 'ADJOINT' ) then
                if ( odata%elem == 'N/A     ' ) then ! radiances
                    lev = -999.0_r_kind
                else
                    if ( trim(adjustl(platform)) == 'GNSSRO' ) then ! GPSRO Obs seem to be in m 
                        lev = lev / 1000.0_r_kind
                    else
                        lev = lev / 100.0_r_kind
                    endif
                endif
            endif
        endif

        write(ounit,'(A15,1X,A10,1X,I5,3(1X,F10.4),2(1X,E15.8))',iostat=iflag) &
            adjustl(platform),adjustl(obtype),channel,lon,lat,lev,impact(1),omb
        if ( iflag /= 0 ) then
            write(6,'(a,a,i5)') '***ERROR***. cannot write data, iostat = ', iflag
            goto 800
        endif

    enddo

800 continue

    if ( allocated(impact) ) deallocate(impact)

    close(iunit)
    close(ounit)

900 continue

    stop

end program process_JMA
