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

RUN pip3 install /fsoi
RUN rm -Rf /fsoi
