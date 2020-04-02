FROM python:3

ADD python /fsoi
ADD docker/hdf5.tar.gz /

ENV HDF5_DIR /usr
ENV LD_LIBRARY_PATH /opt/hdf5/lib
ENV CACHE_BUCKET "fsoi-image-cache"
ENV DATA_BUCKET "fsoi"
ENV FSOI_ROOT_DIR "/tmp/fsoi"
ENV OBJECT_PREFIX "intercomp/hdf5"
ENV REGION "us-east-1"
ENV AWS_DEFAULT_REGION "us-east-1"

RUN pip3 install matplotlib
RUN pip3 install boto3
RUN pip3 install numpy
RUN pip3 install pandas
RUN pip3 install tables
RUN pip3 install requests
RUN pip3 install netCDF4
RUN pip3 install fortranformat
RUN pip3 install pyyaml
RUN pip3 install certifi
RUN pip3 install urllib3
RUN pip3 install bokeh
RUN pip3 install selenium
RUN pip3 install phantomjs
RUN pip3 install /fsoi
RUN rm -Rf /fsoi
