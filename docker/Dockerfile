# Phusion base image (minimal Docker-friendly Ubuntu)
FROM phusion/baseimage:master as base

# Install packages
COPY install_scripts/ /
RUN ./install_packages.sh
RUN ldconfig /usr/local/lib
RUN ./install_assimp.sh
RUN ./install_libLAS.sh
RUN ./install_VTK.sh
RUN ./install_libgeos.sh
#RUN ./install_debugging.sh

# Add /usr/local/lib into LD
RUN ldconfig /usr/local/lib

# Add user
ENV USER dtcc
ENV HOME /home/$USER
ENV DIR dtcc-platform
RUN useradd -m $USER -G sudo && \
    echo "$USER:$USER" | chpasswd && \
    echo "$USER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER $USER

# Create shared volume
VOLUME $HOME/$DIR
WORKDIR $HOME/$DIR

# Start login shell
CMD ["/bin/bash", "-i"]
