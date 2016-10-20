!##############################################################
! < next few lines under version control, D O  N O T  E D I T >
! $Date$
! $Revision$
! $Author$
! $Id$
!##############################################################

module jma

    implicit none

    private

    public :: diag_header
    public :: diag_data
    public :: get_header
    public :: get_data

    public :: strtoarr
    public :: arrtostr
    public :: open_file

    integer(4),parameter :: iunit = 10
    logical,parameter :: lverbose = .false.

    ! Header
    type diag_header
        sequence
        character(len=8) :: formulation    ! "ADJOINT" or "ENSEMBLE"
        integer(4)       :: idate(1:5)     ! Base date (initial date)
        integer(4)       :: nobstot        ! No. of observations (total)
    end type diag_header

    ! Body
    type diag_data
        sequence
        character(len=8)  :: elem      ! observed element *1
        integer(4)        :: channel   ! channel for radiance observations; 0 for non-radiances
        real(4)           :: rlon      ! latitude  [deg]
        real(4)           :: rlat      ! longitude [deg]
        real(4)           :: rlev      ! level (height) *2
        character(len=12) :: otype     ! obs type (sensor name for radiance) *3
        character(len=12) :: satname   ! satellite name (N/A if conventional) *4
        real(4)           :: omb       ! O-B departure
        real(4)           :: oma       ! O-A departure
        real(4)           :: oberr     ! standard deviation of the prescribed observation error
        real(4)           :: fso_kin   ! FSO impact   [J/kg] (kinetic     energy norm) *5
        real(4)           :: fso_dry   ! FSO impact   [J/kg] (dry   total energy norm)
        real(4)           :: fso_moist ! FSO impact   [J/kg] (moist total energy norm) *5
        real(4)           :: fsr_kin   ! R-sensitivity[J/kg] (kinetic     energy norm) *5
        real(4)           :: fsr_dry   ! R-sensitivity[J/kg] (dry   total energy norm)
        real(4)           :: fsr_moist ! R-sensitivity[J/kg] (moist total energy norm) *5
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

contains

subroutine get_header(ifile,x_formulation,x_idate,x_nobstot,x_nmetric,endian)
    
    implicit none

    character(len=255),intent(in) :: ifile
    character(len=6),intent(in),optional :: endian
    character(len=8),intent(out) :: x_formulation
    integer(4),intent(out) :: x_idate(1:5)
    integer(4),intent(out) :: x_nobstot
    integer(4),intent(out) :: x_nmetric

    character(len=50),parameter :: myname = 'GET_HEADER'
    type(diag_header) :: oheader
    character(len=6) :: convert_endian
    integer(4) :: iflag

    call open_file(ifile,endian)
    
    read(iunit,iostat=iflag) oheader
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') trim(myname),': ***ERROR***. cannot read, iostat = ', iflag
        close(iunit)
        stop
    endif

    x_formulation = oheader%formulation
    x_idate       = oheader%idate
    x_nobstot     = oheader%nobstot
    if ( oheader%formulation == 'ENSEMBLE' ) then
        x_nmetric = 3
    elseif ( oheader%formulation == 'ADJOINT' ) then
        x_nmetric = 1
    endif

    close(iunit)

    return

end subroutine get_header

subroutine get_data(ifile,nobstot,nmetric,x_obtype,x_platform,x_channel,x_lat,x_lon,x_lev,x_omb,x_oberr,x_impact,endian)

    implicit none

    character(len=255),intent(in) :: ifile
    integer(4),intent(in) :: nobstot
    integer(4),intent(in) :: nmetric
    character(len=6),intent(in),optional :: endian
    integer(4),dimension(nobstot,21),intent(out) :: x_obtype
    integer(4),dimension(nobstot,21),intent(out) :: x_platform
    integer(4),dimension(nobstot),intent(out) :: x_channel
    real(4),dimension(nobstot),intent(out) :: x_lat
    real(4),dimension(nobstot),intent(out) :: x_lon
    real(4),dimension(nobstot),intent(out) :: x_lev
    real(4),dimension(nobstot),intent(out) :: x_omb
    real(4),dimension(nobstot),intent(out) :: x_oberr
    real(4),dimension(nobstot,nmetric),intent(out) :: x_impact

    character(len=50),parameter :: myname = 'GET_DATA'
    type(diag_header) :: oheader
    type(diag_data) :: odata
    character(len=20) :: obtype
    character(len=20) :: platform
    integer(4) :: channel
    integer(4) :: iobs,iflag
    real(4) :: lev

    call open_file(ifile,endian)

    read(iunit,iostat=iflag) oheader
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') trim(myname),': ***ERROR***. cannot read, iostat = ', iflag
        close(iunit)
        stop
    endif

    do iobs = 1,nobstot

        read(iunit,iostat=iflag) odata
        if ( iflag /= 0 ) then
            write(6,'(a,a,i5)') '***ERROR***. cannot read data, iostat = ', iflag
            exit
        endif

        if ( odata%elem == 'N/A     ' ) then ! radiances
            obtype        = 'Tb'
            channel       = odata%channel
            platform = trim(adjustl(odata%otype)) // '_' // trim(adjustl(odata%satname))
        else ! non-radiance
            obtype        = trim(adjustl(odata%elem))
            channel       = -999
            platform = trim(adjustl(odata%otype))
        endif

        lev = odata%rlev
        if ( lev == HUGE(0.0) ) then
            lev = -999.0
        else
            if ( oheader%formulation == 'ENSEMBLE' ) then
                lev = lev / 100.0
            elseif ( oheader%formulation == 'ADJOINT' ) then
                if ( odata%elem == 'N/A     ' ) then ! radiances
                    lev = -999.0
                else
                    if ( trim(adjustl(platform)) == 'GNSSRO' ) then ! GPSRO Obs seem to be in m 
                        lev = lev / 1000.0
                    else
                        lev = lev / 100.0
                    endif
                endif
            endif
        endif

        call strtoarr(obtype,x_obtype(iobs,:),20)
        call strtoarr(platform,x_platform(iobs,:),20)
        x_channel(iobs)  = channel
        x_lat(iobs)      = odata%rlat
        x_lon(iobs)      = odata%rlon
        x_lev(iobs)      = lev
        x_omb(iobs)      = odata%omb
        x_oberr(iobs)    = odata%oberr
        x_impact(iobs,1) = odata%fso_dry
        if ( nmetric > 1 ) x_impact(iobs,2) = odata%fso_moist
        if ( nmetric > 2 ) x_impact(iobs,3) = odata%fso_kin

    enddo ! do

    close(iunit)

    return

end subroutine get_data

subroutine strtoarr(strin, chararr, n_str)

    implicit none

    integer(4),intent(in) :: n_str
    character(len=n_str),intent(in) :: strin
    integer(4),intent(out) :: chararr(n_str+1)

    integer(4) :: j

    chararr = 32 ! space
    do j=1,n_str
        chararr(j) = ichar(strin(j:j))
    enddo
    chararr(n_str+1) = 124 ! '|'
   
    return

end subroutine strtoarr

subroutine arrtostr(chararr, strout, n_str)

    implicit none


    integer(4),intent(in) :: n_str
    integer(4),intent(in) :: chararr(n_str+1)
    character(len=n_str),intent(out) :: strout

    integer(4) :: j

    do j=1,n_str
        strout(j:j) = char(chararr(j))
    enddo
   
    return

end subroutine arrtostr

subroutine open_file(filename,endian)

    implicit none

    character(len=*), intent(in) :: filename
    character(len=*), intent(in), optional :: endian

    character(len=6) :: convert_endian
    character(len=50), parameter :: myname = 'OPEN_FILE'

    logical :: fexist
    integer(4) :: iflag

    if ( present(endian) ) then
        convert_endian = endian
    else
        convert_endian = 'big'
    endif

    inquire(file=trim(adjustl(filename)),exist=fexist)
    if ( .not. fexist ) then
        write(6,'(a,a,a)') trim(myname),': ***ERROR*** file does not exist', trim(adjustl(filename))
        stop
    endif

    if ( trim(convert_endian) == 'big' ) then
        open(iunit,file=trim(filename),action='read',form='unformatted',convert='big_endian',iostat=iflag)
    elseif ( trim(convert_endian) == 'little' ) then
        open(iunit,file=trim(filename),action='read',form='unformatted',convert='little_endian',iostat=iflag)
    elseif ( trim(convert_endian) == 'native' ) then
        open(iunit,file=trim(filename),action='read',form='unformatted',iostat=iflag)
    endif
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') trim(myname),': ***ERROR*** cannot open, iostat = ', iflag
        stop
    endif

end subroutine open_file

end module jma
