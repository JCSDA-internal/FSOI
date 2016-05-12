!##############################################################
! < next few lines under version control, D O  N O T  E D I T >
! $Date$
! $Revision$
! $Author$
! $Id$
!##############################################################

program read_jma

    use jma, only: get_header, get_data

    implicit none

    character(len=8) :: formulation
    integer(4) :: idate(1:5)
    integer(4) :: nobstot,nmetric
    real(4),allocatable,dimension(:) :: lat,lon,lev,omb,oberr
    integer(4),allocatable,dimension(:) :: channel
    character(len=20),allocatable,dimension(:) :: obtype,platform
    real(4),allocatable,dimension(:,:) :: impact

    character(len=255) :: ifile
    integer(4) :: i

    call getarg(1,ifile)

    write(6,'(A,A)') 'input file = ', trim(ifile)

    call get_header(ifile,formulation,idate,nobstot,nmetric)

    write(6,'(A,5(I4))') '# analysis date  : ', idate(1:5)
    write(6,'(A,A)')     '# formulation    : ', formulation
    write(6,'(A,I8)')    '# no. of tot obs : ', nobstot
    write(6,'(A,I8)')    '# no. of metrics : ', nmetric
   
    if ( nobstot <= 0 ) then
       write(6,'(A)') 'ERROR: no observations to dump'
       stop
    endif

    allocate(platform(nobstot))
    allocate(obtype(nobstot))
    allocate(channel(nobstot))
    allocate(lat(nobstot))
    allocate(lon(nobstot))
    allocate(lev(nobstot))
    allocate(omb(nobstot))
    allocate(oberr(nobstot))
    allocate(impact(nobstot,3))

    call get_data(ifile,nobstot,nmetric,obtype,platform,channel,lat,lon,lev,omb,oberr,impact)

    write(6,'(A,A)') &
    & 'OBNUM     PLATFORM        OBTYPE     CHAN   LAT    LON    LEV      OmF        Impact'
    do i=1,nobstot
        write(6,'(I8,1X,A15,1X,A10,1X,I5,1X,3(F7.2,1X),2(E10.3,1X))') &
    & i,trim(platform(i)),trim(obtype(i)),channel(i),lat(i),lon(i),lev(i),omb(i),impact(i,1)
    enddo

    stop
end program read_jma
