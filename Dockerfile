FROM public.ecr.aws/lambda/python:3.9 as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    LD_LIBRARY_PATH=/opt/lib/libmediainfo.so

# Install system dependencies and clean up in a single layer
RUN yum update -y && \
    yum install -y wget tar xz gcc make unzip opencv opencv-devel && \
    yum clean all && \
    rm -rf /var/cache/yum

# Install FFmpeg and FFprobe
RUN wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    tar xf ffmpeg-release-amd64-static.tar.xz && \
    mv ffmpeg-*-amd64-static/ffmpeg ffmpeg-*-amd64-static/ffprobe /usr/local/bin/ && \
    rm -rf ffmpeg-*-amd64-static*

# Download and install libmediainfo
RUN wget -q https://mediaarea.net/download/binary/libmediainfo0/24.12/MediaInfo_DLL_24.12_Lambda_x86_64.zip && \
    unzip -q MediaInfo_DLL_24.12_Lambda_x86_64.zip -d MediaInfo_DLL_24.12_Lambda_x86_64 && \
    mkdir -p /opt/lib && \
    mv MediaInfo_DLL_24.12_Lambda_x86_64/lib/libmediainfo.so* /opt/lib/ && \
    chmod 755 /opt/lib/libmediainfo.so* && \
    rm -rf MediaInfo_DLL_24.12_Lambda_x86_64*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM public.ecr.aws/lambda/python:3.9

LABEL maintainer="RMCBFM ADS / AdTech / Mohammed EL-KHOU / m.elkhou@hotmail.com"

# Copy necessary files from builder stage
COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/ffprobe /usr/local/bin/
COPY --from=builder /opt/lib /opt/lib
COPY --from=builder /var/lang/lib/python3.9/site-packages /var/lang/lib/python3.9/site-packages

ENV LD_LIBRARY_PATH=/opt/lib/libmediainfo.so \
    FFMPEG_DIR_PATH=/usr/local/bin/ \
    FFMPEG_BINARY=/usr/local/bin/ffmpeg

# Copy function code
COPY app/ ${LAMBDA_TASK_ROOT}

ENTRYPOINT ["python", "run.py"]
# CMD ["lambda.handler"]