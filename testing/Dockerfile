
FROM fedora:31 

USER root

# copr repo
RUN dnf install -y 'dnf-command(copr)'
RUN dnf -y copr enable karmab/kcli

# pkgs 
RUN dnf install -y \
        tree \
        kcli \
        libvirt \
        libvirt-daemon-driver-qemu \
        qemu-img \
        qemu-system-x86 \
        qemu-system-x86-core \
        rust \
        cargo

# make alternative
RUN cargo install mask
ENV PATH="/root/.cargo/bin:${PATH}"

ENTRYPOINT "${SOFT_RESIDE}/run.sh"
