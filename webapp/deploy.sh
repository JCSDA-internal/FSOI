#! /bin/sh

bucket=ios.jcsda.org
profile=jcsda

ng build --prod

for file in `find dist/webapp -type f`; do
  skim=`echo $file | sed "s/dist\/webapp\///g"`
  aws --profile ${profile} s3 cp dist/webapp/$skim s3://$bucket/$skim
done

for file in `find src -type f -name *.png`; do
  skim=`echo $file | sed "s/src\///g"`
  aws --profile ${profile} s3 cp src/$skim s3://$bucket/$skim
done

echo "If you want to create an invalidation:"
aws --profile ${profile} cloudfront list-distributions | jq '.DistributionList.Items[] | "\(.Id) \(.Comment)"'
dist_id_beta=$(aws --profile jcsda cloudfront list-distributions | jq -r '.DistributionList.Items[] | "\(.Id) \(.Comment)"' | grep FSOIbeta | awk \{print\$1\})
dist_id_prod=$(aws --profile jcsda cloudfront list-distributions | jq -r '.DistributionList.Items[] | "\(.Id) \(.Comment)"' | grep FSOI | grep -v FSOIbeta | awk \{print\$1\})
echo '  FSOIbeta'
echo '    'aws --profile ${profile} cloudfront create-invalidation --distribution-id ${dist_id_beta} --paths \'/*\'
echo '  FSOIproduction'
echo '    'aws --profile ${profile} cloudfront create-invalidation --distribution-id ${dist_id_prod} --paths \'/*\'
