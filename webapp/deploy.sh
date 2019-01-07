#! /bin/sh

bucket=ios.jcsda.org

ng build --prod

for file in `find dist/webapp -type f`; do
  skim=`echo $file | sed "s/dist\/webapp\///g"`
  aws s3 cp dist/webapp/$skim s3://$bucket/$skim
done

for file in `find src -type f -name *.png`; do
  skim=`echo $file | sed "s/src\///g"`
  aws s3 cp src/$skim s3://$bucket/$skim
done

