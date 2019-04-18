FROM python:3

ADD python/dist/fsoi-0.1-py3.7.egg /
ADD docker/hdf5.tar.gz /

ENV HDF5_DIR /usr
ENV LD_LIBRARY_PATH /opt/hdf5/lib
ENV CACHE_BUCKET "fsoi-image-cache"
ENV DATA_BUCKET "fsoi"
ENV FSOI_ROOT_DIR "/tmp/fsoi"
ENV OBJECT_PREFIX "intercomp/hdf5"
ENV REGION "us-east-1"
ENV AWS_DEFAULT_REGION "us-east-1"

RUN pip install matplotlib
RUN pip install boto3
RUN pip install numpy
RUN pip install pandas
RUN pip install tables
RUN pip install requests
RUN pip install netCDF4
RUN pip install fortranformat
RUN easy_install-3.7 fsoi-0.1-py3.7.egg

CMD ["batch_wrapper"]
