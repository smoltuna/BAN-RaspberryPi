# Python image (debian-based)
FROM python:3.7.3

# Create working directory
WORKDIR /OPERA/

# Copy project files
COPY . /OPERA/

# Make entrypoint executable
RUN ["chmod", "+x", "entrypoint.sh"]

RUN ls -la /OPERA/

# RUN command to update packages & install dependencies for the project
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install bluez related packages for bluethoot communication
RUN apt-get update && apt-get install -y bluez dbus sudo

# Setup bluetooth permissions
COPY bluezuser.conf /etc/dbus-1/system.d/
RUN useradd -m bluezuser && adduser bluezuser sudo && passwd -d bluezuser

RUN ["chown", "-R", "bluezuser", "/OPERA/"]
RUN ["chown", "root", "/OPERA/entrypoint.sh"]

USER bluezuser

RUN ls -la /OPERA/

# Commands to run within the container
CMD ./entrypoint.sh