#! /bin/bash

files="Y1980.tar.gz Y1981.tar.gz Y1982.tar.gz Y1983.tar.gz Y1984.tar.gz Y1985.tar.gz Y1986.tar.gz Y1987.tar.gz \
Y1988.tar.gz Y1989.tar.gz Y1990.tar.gz Y1991.tar.gz Y1992.tar.gz Y1993.tar.gz Y1994.tar.gz Y1995.tar.gz Y1996.tar.gz \
Y1997.tar.gz Y1998.tar.gz Y1999.tar.gz Y2000.tar.gz Y2001.tar.gz Y2002.tar.gz Y2003.tar.gz Y2004.tar.gz Y2005.tar.gz \
Y2006.tar.gz Y2007.tar.gz Y2008.tar.gz Y2009.tar.gz Y2010.tar.gz Y2011.tar.gz Y2012.tar.gz Y2013.tar.gz Y2014.tar.gz \
Y2015.tar.gz Y2015_20190723.tar.gz Y2015_20190905.tar.gz Y2016.tar.gz Y2017.tar.gz Y2018.tar.gz Y2019.tar.gz"

for file in ${files}; do
  aws s3 cp s3://fv3gfs/MERRA/${file} ${file}
  tar -xvzf ${file}
  rm -f ${file}
done
