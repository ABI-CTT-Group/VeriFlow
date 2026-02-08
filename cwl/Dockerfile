# Using Python 3.11 as a stable base for this cwltool version
FROM python:3.11-slim

# Copy Docker CLI from the official Docker image
COPY --from=docker:latest /usr/local/bin/docker /usr/local/bin/docker

# Install Node.js (required for JavaScript expressions) and Git
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    git \
    && rm -rf /var/lib/apt/lists/*

# Pin cwltool to the specified version or higher
RUN pip install --no-cache-dir "cwltool>=3.1.20231114134824" cwlref-runner

WORKDIR /workflows

# Provide the entrypoint for the runner
ENTRYPOINT ["cwltool"]


# how to use
# docker run --rm \
#     -v /var/run/docker.sock:/var/run/docker.sock \
#     -v /tmp:/tmp \
#     -v $(pwd):/workflow \
#     -w /workflow \
#     cwl-runner-image \
#     cwltool my_workflow.cwl inputs.json