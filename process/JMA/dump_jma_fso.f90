!----------------------------------------------------------------------!
! Sample program that dumps JMA's (E)FSO output file                   !
!                                                                      !
! * Compilation:                                                       !
!  $ ifort -save -convert big_endian -assume byterecl dump_jma_fso.f90 !
!                                                                      !
!                                            2016/02/16 Daisuke Hotta  !
!----------------------------------------------------------------------!
program dump_jma_fso
  implicit none
  character(len=256) :: ifile
  integer(4) :: iobs, obsnum=0
  
  ! Type definition for the header 
  type obsense_header
     sequence
     character(len=8) :: formulation ! "ADJOINT " or "ENSEMBLE"
     integer(4)       :: idate(1:5)  ! base (initial) time
                                     ! indices 1 to 5 correspond, respectively, to:
                                     !   year, month, day, hour, minutes (=0)
     integer(4) :: obsnum            ! number of observations
  end type obsense_header
  ! Type definition for the body 
  type obsense_info
     sequence
     character(len=8):: elem     ! observed element *1
     integer(4):: channel        ! channel for radiance observations; 0 for non-radiances
     real(4)   :: rlon           ! latitude  [deg]
     real(4)   :: rlat           ! longitude [deg]
     real(4)   :: rlev           ! level (height) *2
     character(len=12):: otype   ! obs type (sensor name for radiance) *3
     character(len=12):: satname ! satellite name (N/A if conventional) *4
     real(4)   :: omb            ! O-B departure
     real(4)   :: oma            ! O-A departure
     real(4)   :: oberr          ! standard deviation of the prescribed observation error
     real(4)   :: fso_kin        ! FSO impact   [J/kg] (kinetic     energy norm) *5
     real(4)   :: fso_dry        ! FSO impact   [J/kg] (dry   total energy norm)
     real(4)   :: fso_moist      ! FSO impact   [J/kg] (moist total energy norm) *5
     real(4)   :: fsr_kin        ! R-sensitivity[J/kg] (kinetic     energy norm) *5
     real(4)   :: fsr_dry        ! R-sensitivity[J/kg] (dry   total energy norm)
     real(4)   :: fsr_moist      ! R-sensitivity[J/kg] (moist total energy norm) *5
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
  end type obsense_info

  type(obsense_header):: header
  type(obsense_info)  :: body

  !read(5,'(a256)') ifile
  call getarg(1,ifile)
  open(10,file=ifile,action='read',form='unformatted',access='sequential',convert='big_endian')
  read(10) header
  obsnum=header%obsnum
  write(6,'(A10,I8)') '# obsnum: ', obsnum
  if (obsnum .le. 0) then
     print *, 'error: no observations to dump'
     stop 999
  end if

  write(6,'(A,A)')      '# formulation: ', header%formulation
  write(6,'(A,5(I4,1X))') '# date: ', header%idate(1:5)

  write(6,'(A,A)') &
       & '#elem/chan   lon     lat          lev        type      satname        O-B        O-A      oberr', &
       & '    fso_kin    fso_dry  fso_moist    fsr_kin    fsr_dry  fsr_moist'
  do iobs=1,obsnum
     read(10) body
     if (body%elem.eq.'N/A     ') then ! radiances
        write(6,'(I8,1X,2(F7.2,1X),F12.2,2(A12,1X),9(E10.3,1X))') &
             & body%channel, body%rlon, body%rlat, body%rlev, & 
             & adjustr(body%otype), adjustr(body%satname), &
             & body%omb, body%oma, body%oberr, &
             & body%fso_kin, body%fso_dry, body%fso_moist, &
             & body%fsr_kin, body%fsr_dry, body%fsr_moist
     else ! non-radiance
        write(6,'(A8,1X,2(F7.2,1X),F12.2,2(A12,1X),9(E10.3,1X))') &
             & body%elem, body%rlon, body%rlat, body%rlev, & 
             & adjustr(body%otype), adjustr(body%satname), &
             & body%omb, body%oma, body%oberr, &
             & body%fso_kin, body%fso_dry, body%fso_moist, &
             & body%fsr_kin, body%fsr_dry, body%fsr_moist
     end if
  end do
  close(10)
  stop
end program dump_jma_fso
