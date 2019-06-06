from netCDF4 import Dataset

# open the data file
file = '/tmp/sample.nc'
data = Dataset(file)
# data.set_auto_mask(False)

# print the data
for row in data['kx']:
    for val in row:
        print('%0.2f, ' % float(val), end='')
    break  # print only the first row
