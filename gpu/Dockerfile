FROM nvidia/cuda:13.0.3-cudnn-runtime-ubuntu24.04

# Update package lists and install Python3, pip, and necessary dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install JupyterLab using pip3
RUN pip3 install --no-cache-dir --break-system-packages jupyterlab

# Expose the default Jupyter port
EXPOSE 8888

# Create a working directory
WORKDIR /workspace

# Configure Jupyter to listen on all interfaces and allow root
RUN mkdir -p /root/.jupyter/ && \
    echo "c.ServerApp.ip = '0.0.0.0'" >> /root/.jupyter/jupyter_lab_config.py && \
    echo "c.ServerApp.allow_root = True" >> /root/.jupyter/jupyter_lab_config.py && \
    echo "c.ServerApp.token = ''" >> /root/.jupyter/jupyter_lab_config.py

# Set the startup command
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]