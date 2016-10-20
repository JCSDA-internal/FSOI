!##############################################################
! < next few lines under version control, D O  N O T  E D I T >
! $Date$
! $Revision$
! $Author$
! $Id$
!##############################################################

program read_emc

    use emc, only: get_header, get_data, arrtostr

    implicit none

    integer    :: idate
    integer(4) :: nobscon,nobsoz,nobssat,npred,nens
    real(4),allocatable,dimension(:) :: lat,lon,lev,omb,oberr
    integer(4),allocatable,dimension(:) :: channel
    integer(4),allocatable,dimension(:,:) :: iobtype,iplatform
    character(len=20),allocatable,dimension(:) :: obtype,platform
    real(4),allocatable,dimension(:,:) :: impact

    character(len=255) :: ifile
    integer(4) :: i,nobstot

    call getarg(1,ifile)

    write(6,'(A,A)') 'input file = ', trim(ifile)

    call get_header(ifile,idate,nobscon,nobsoz,nobssat,npred,nens)

    write(6,'(A,I10)') '# analysis date  : ', idate
    write(6,'(A,I8)')  '# no. of con obs : ', nobscon
    write(6,'(A,I8)')  '# no. of ozo obs : ', nobsoz
    write(6,'(A,I8)')  '# no. of rad obs : ', nobssat
    write(6,'(A,I8)')  '# no. of preds   : ', npred
    write(6,'(A,I8)')  '# no. of enss    : ', nens
   
    nobstot = nobscon + nobsoz + nobssat
    if ( nobstot <= 0 ) then
       write(6,'(A)') 'ERROR: no observations to dump'
       stop
    endif

    allocate(iplatform(nobstot,21))
    allocate(iobtype(nobstot,21))
    allocate(platform(nobstot))
    allocate(obtype(nobstot))
    allocate(channel(nobstot))
    allocate(lat(nobstot))
    allocate(lon(nobstot))
    allocate(lev(nobstot))
    allocate(omb(nobstot))
    allocate(oberr(nobstot))
    allocate(impact(nobstot,3))

    call get_data(ifile,nobstot,npred,nens,iobtype,iplatform,channel,lat,lon,lev,omb,oberr,impact)

    write(6,'(A,A)') &
    & 'OBNUM    PLATFORM        OBTYPE     CHAN  LAT     LON     LEV     OmF        ObErr      DRY        MOIST      KINETIC'
    do i=1,nobstot
        call arrtostr(iobtype(i,:),obtype(i),20)
        call arrtostr(iplatform(i,:),platform(i),20)
        write(6,'(I8,1X,A15,1X,A10,1X,I5,1X,3(F7.2,1X),5(E10.3,1X))') &
    & i,trim(platform(i)),trim(obtype(i)),channel(i),lat(i),lon(i),lev(i),omb(i),oberr(i),impact(i,1),impact(i,2),impact(i,3)
    enddo

    stop
end program read_emc
