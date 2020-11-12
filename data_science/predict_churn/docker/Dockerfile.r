FROM python:3.8

# Install R.
RUN apt-get update && apt-get install -y r-base
RUN Rscript -e 'install.packages(c("jsonlite", "argparser"))'

# Install python packages.
RUN pip3 install conducto
