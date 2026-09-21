FROM quay.io/jupyter/datascience-notebook:latest

USER root

RUN groupadd jovyan \
    && usermod -g jovyan -a -G users jovyan

USER jovyan