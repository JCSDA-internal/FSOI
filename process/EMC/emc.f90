!##############################################################
! < next few lines under version control, D O  N O T  E D I T >
! $Date$
! $Revision$
! $Author$
! $Id$
!##############################################################

module emc

    implicit none

    private

    public :: diag_header
    public :: diag_data
    public :: get_header
    public :: get_data

    integer(4),parameter :: iunit = 10
    logical,parameter :: lverbose = .false.

    ! Header
    type diag_header
        sequence
        integer(4) :: idate     ! Base date (initial date)
        integer(4) :: obsnum    ! Observation number (total)
        integer(4) :: convnum   ! Observation number (conventional)
        integer(4) :: oznum     ! Observation number (ozone)
        integer(4) :: satnum    ! Observation number (satellite)
        integer(4) :: npred     ! Number of predictors for bias correction
        integer(4) :: nanals    ! Number of members
    end type diag_header

    ! Data
    type diag_data
        sequence
        real(4)  :: obfit_prior        ! Observation fit to the first guess
        real(4)  :: obsprd_prior       ! Spread of observation prior
        real(4)  :: ensmean_obnobc     ! Ensemble mean first guess (no bias correction)
        real(4)  :: ensmean_ob         ! Ensemble mean first guess (bias corrected)
        real(4)  :: ob                 ! Observation value
        real(4)  :: oberrvar           ! Observation error variance
        real(4)  :: lon                ! Longitude
        real(4)  :: lat                ! Latitude
        real(4)  :: pres               ! Pressure
        real(4)  :: time               ! Observation time
        real(4)  :: oberrvar_orig      ! Original error variance
        integer(4) :: stattype         ! Observation type
        character(len=20) :: obtype    ! Observation element / Satellite name
        integer(4) :: indxsat          ! Satellite index (channel)
        real(4)  :: osense_kin         ! Observation sensitivity (kinetic energy) [J/kg]
        real(4)  :: osense_dry         ! Observation sensitivity (Dry total energy) [J/kg]
        real(4)  :: osense_moist       ! Observation sensitivity (Moist total energy) [J/kg]
    end type diag_data

contains

subroutine get_header(ifile,x_idate,x_nobscon,x_nobsoz,x_nobssat,x_npred,x_nens,endian)

    implicit none

    character(len=255),intent(in) :: ifile
    character(len=6),intent(in),optional :: endian
    integer(4),intent(out) :: x_idate
    integer(4),intent(out) :: x_nobscon,x_nobsoz,x_nobssat
    integer(4),intent(out) :: x_npred
    integer(4),intent(out) :: x_nens

    character(len=50),parameter :: myname = 'GET_HEADER'
    type(diag_header) :: oheader
    character(len=6) :: convert_endian
    logical :: fexist
    integer(4) :: iflag

    if ( present(endian) ) then
        convert_endian = endian
    else
        convert_endian = 'big'
    endif

    inquire(file=ifile,exist=fexist)
    if ( .not. fexist ) stop

    if ( trim(convert_endian) == 'big' ) then
        open(iunit,file=trim(ifile),action='read',form='unformatted',convert='big_endian',iostat=iflag)
    elseif ( trim(convert_endian) == 'little' ) then
        open(iunit,file=trim(ifile),action='read',form='unformatted',convert='little_endian',iostat=iflag)
        open(iunit,file=trim(ifile),action='read',form='unformatted',convert='little_endian',iostat=iflag)
    elseif ( trim(convert_endian) == 'native' ) then
        open(iunit,file=trim(ifile),action='read',form='unformatted',iostat=iflag)
    endif
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') trim(myname),': ***ERROR*** cannot open, iostat = ', iflag
        stop
    endif

    read(iunit,iostat=iflag) oheader
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') trim(myname),': ***ERROR***. cannot read, iostat = ', iflag
        close(iunit)
        stop
    endif

    x_idate   = oheader%idate
    x_nobscon = oheader%convnum
    x_nobsoz  = oheader%oznum
    x_nobssat = oheader%satnum
    x_npred   = oheader%npred
    x_nens    = oheader%nanals

    close(iunit)

    return

end subroutine get_header

subroutine get_data(ifile,nobstot,npred,nens,x_obtype,x_platform,x_channel,x_lat,x_lon,x_lev,x_omb,x_oberr,x_impact,endian)

    implicit none

    character(len=255),intent(in) :: ifile
    integer(4),intent(in) :: nobstot
    integer(4),intent(in) :: npred
    integer(4),intent(in) :: nens
    character(len=6),intent(in),optional :: endian
    character(len=20),intent(out) :: x_obtype(nobstot)
    character(len=20),intent(out) :: x_platform(nobstot)
    integer(4),intent(out) :: x_channel(nobstot)
    real(4),intent(out) :: x_lat(nobstot)
    real(4),intent(out) :: x_lon(nobstot)
    real(4),intent(out) :: x_lev(nobstot)
    real(4),intent(out) :: x_omb(nobstot)
    real(4),intent(out) :: x_oberr(nobstot)
    real(4),intent(out) :: x_impact(nobstot,3)

    character(len=50),parameter :: myname = 'GET_DATA'
    type(diag_header) :: oheader
    type(diag_data) :: odata
    character(len=20) :: obtype
    character(len=20) :: platform
    integer(4) :: nobscon,nobsoz,nobssat
    integer(4) :: channel
    integer(4) :: iobs,iflag
    real(4) :: tmpanal(nens)
    real(4) :: tmppred(npred+1)
    character(len=6) :: convert_endian
    logical :: fexist

    if ( present(endian) ) then
        convert_endian = endian
    else
        convert_endian = 'big'
    endif

    inquire(file=ifile,exist=fexist)
    if ( .not. fexist ) stop

    if ( trim(convert_endian) == 'big' ) then
        open(iunit,file=trim(ifile),action='read',form='unformatted',convert='big_endian',iostat=iflag)
    elseif ( trim(convert_endian) == 'little' ) then
        open(iunit,file=trim(ifile),action='read',form='unformatted',convert='little_endian',iostat=iflag)
        open(iunit,file=trim(ifile),action='read',form='unformatted',convert='little_endian',iostat=iflag)
    elseif ( trim(convert_endian) == 'native' ) then
        open(iunit,file=trim(ifile),action='read',form='unformatted',iostat=iflag)
    endif
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') trim(myname),': ***ERROR*** cannot open, iostat = ', iflag
        stop
    endif

    read(iunit,iostat=iflag) oheader
    if ( iflag /= 0 ) then
        write(6,'(a,a,i5)') trim(myname),': ***ERROR***. cannot read, iostat = ', iflag
        close(iunit)
        stop
    endif

    nobscon = oheader%convnum
    nobsoz  = oheader%oznum
    nobssat = oheader%satnum
    
    do iobs = 1,nobstot

        if ( iobs <= (nobscon+nobsoz) ) then ! non-radiance
            read(iunit,iostat=iflag) odata,tmpanal
        else
            read(iunit,iostat=iflag) odata,tmpanal,tmppred
        endif ! radiance
        if ( iflag /= 0 ) then
            if ( iobs /= nobstot ) &
            write(6,'(a,a,i5)') trim(myname),': ***ERROR***. cannot read, iostat = ', iflag
            exit
        endif

        if ( iobs <= (nobscon+nobsoz) ) then ! non-radiance
            channel  = -999
            obtype   = trim(adjustl(odata%obtype))
            write(platform,'(I5)') odata%stattype
        else ! radiance
            channel  = odata%indxsat
            obtype   = 'Tb'
            platform = trim(adjustl(odata%obtype))
        endif

        x_obtype(iobs)   = obtype
        x_platform(iobs) = platform
        x_channel(iobs)  = channel
        x_lat(iobs)      = odata%lat
        x_lon(iobs)      = odata%lon
        x_lev(iobs)      = odata%pres
        x_omb(iobs)      = odata%obfit_prior
        x_oberr(iobs)    = odata%oberrvar
        x_impact(iobs,1) = odata%osense_dry
        x_impact(iobs,2) = odata%osense_moist
        x_impact(iobs,3) = odata%osense_kin

    enddo ! do

    close(iunit)

    return

end subroutine get_data

end module emc
