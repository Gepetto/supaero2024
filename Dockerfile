FROM python:3.11

RUN useradd -m user
USER user
WORKDIR /home/user/tp
ENV PATH /home/user/.local/bin:$PATH
CMD jupyter lab --no-browser --ip='*'

ADD --chown=user . .
RUN --mount=type=cache,sharing=locked,uid=1000,gid=1000,target=/home/user/.cache \
    python -m pip install --user -U pip \
 && python -m pip install --user .
