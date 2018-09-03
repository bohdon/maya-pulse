ARG maya_version=2018
FROM mottosso/maya:${maya_version}

RUN mkdir /root/maya/modules -p
ENV MAYA_MODULES_INSTALL_PATH=/root/maya/modules
ENV PYMEL_SKIP_MEL_INIT=1

RUN git clone https://github.com/bohdon/maya-pymetanode
RUN maya-pymetanode/setup.sh install

WORKDIR /app

ADD setup.sh /app
ADD src /app/src
RUN ./setup.sh install

ADD tests /app/tests
