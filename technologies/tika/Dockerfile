FROM apache/tika:4.2.0-1-full

USER root

# Install curl for downloading dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create Tika extras directory and download JAI ImageIO libraries
RUN mkdir -p /tika-extras && \
    cd /tika-extras && \
    curl -L -O https://repo1.maven.org/maven2/com/github/jai-imageio/jai-imageio-core/1.4.0/jai-imageio-core-1.4.0.jar && \
    curl -L -O https://repo1.maven.org/maven2/com/github/jai-imageio/jai-imageio-jpeg2000/1.4.0/jai-imageio-jpeg2000-1.4.0.jar && \
    chown -R 1000:1000 /tika-extras

# Add Java module permissions
ENV JAVA_OPTS="--add-opens java.base/java.lang=ALL-UNNAMED --add-opens java.base/java.io=ALL-UNNAMED"

USER 1000 