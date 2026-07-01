# Use the lightweight Alpine image as a base
FROM alpine:latest

# Create a non-root user and group for security
RUN addgroup -S labgroup && adduser -S labuser -G labgroup

# Update packages and install basic utilities
RUN apk update && apk add --no-cache \
    curl \
    wget \
    nano \
    bash

# Set the default working directory to the new user's home folder
WORKDIR /home/labuser

# Expose a default port for the backend to route traffic to
EXPOSE 8080

# Switch from the root system user to the restricted labuser
USER labuser

# Keep the container running interactively
CMD ["/bin/bash"]