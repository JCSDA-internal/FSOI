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

    public :: strtoarr
    public :: arrtostr
    public :: open_file

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

    integer(4) :: iflag

    call open_file(ifile,endian)

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
    integer(4),dimension(nobstot,21),intent(out) :: x_obtype
    integer(4),dimension(nobstot,21),intent(out) :: x_platform
    integer(4),dimension(nobstot),intent(out) :: x_channel
    real(4),dimension(nobstot),intent(out) :: x_lat
    real(4),dimension(nobstot),intent(out) :: x_lon
    real(4),dimension(nobstot),intent(out) :: x_lev
    real(4),dimension(nobstot),intent(out) :: x_omb
    real(4),dimension(nobstot),intent(out) :: x_oberr
    real(4),dimension(nobstot,3),intent(out) :: x_impact

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

    call open_file(ifile,endian)

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

        call strtoarr(obtype,x_obtype(iobs,:),20)
        call strtoarr(platform,x_platform(iobs,:),20)
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

end module emc
