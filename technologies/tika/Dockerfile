FROM apache/tika:4.2.0-1-full

USER root

# Install curl for downloading dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl tesseract-ocr-nld \
    && rm -rf /var/lib/apt/lists/*

# Create Tika extras directory and download JAI ImageIO libraries
RUN mkdir -p /tika-extras && \
    cd /tika-extras && \
    curl -L -O https://repo1.maven.org/maven2/com/github/jai-imageio/jai-imageio-core/1.4.0/jai-imageio-core-1.4.0.jar && \
    curl -L -O https://repo1.maven.org/maven2/com/github/jai-imageio/jai-imageio-jpeg2000/1.4.0/jai-imageio-jpeg2000-1.4.0.jar && \
    chown -R 35002:35002 /tika-extras

# Match the unprivileged user in the official Tika 4 image.
USER 35002:35002
