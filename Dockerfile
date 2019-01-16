FROM python:3

ADD scripts/*.py /
ADD lib/*.py /
ADD docker/usr/bin/* /usr/bin/
ADD docker/usr/include/* /usr/include/
ADD docker/usr/lib/* /usr/lib/
ADD docker/usr/share/* /usr/share/

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

CMD [ "python", "./batch_wrapper.py" ]
