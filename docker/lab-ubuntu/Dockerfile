# Use the official Ubuntu image as a base
FROM ubuntu:latest

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update packages and install basic utilities for the lab terminal
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Set the default working directory inside the container
WORKDIR /root

# Keep the container running interactively
CMD ["/bin/bash"]