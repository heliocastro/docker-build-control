# docker-build-control

This actions is a wrapper to control status of multi layered docker images and build if requested.

Since the advent of buildkit is it possible to build multople images interconnected in same docker file, and connect then though contexts.
This intermediate layers could be pushed and reused in future, preventing to be rebuild every time.
As example, a base image based on Ubuntu 22.04 with modifications will only be rebuilt if the actual content changes. as the content never changes
this image has no reason to be rebuilt and pushed, so reuse it.

To prevent this, a hash based mechanism to the version is added in intermediary layer tags, create sort of uniq indentifier.
With this uniq identifier, a python check scripts using github API can verify if the image exists, so just use it to build as a context.

## Usage

See [action.yml](https://github.com/heliocastro/docker-build-control/action.yml)

```yaml
- uses heliocastro/docker-build-control@v1
with:
  # Pass the current Github / Github Enterprise registry
  registry:
    description: "GitHub container registry"
    default: "ghcr.io"
  token:
    # Organizaton / PAT token to access resources
    description: "GitHub token"
    required: true
  name:
    # Name of the image to be build
    description: "Image name"
    required: true
  target:
    description: "Target in the Dockerfile"
    required: false
  images:
    description: "Custom image names"
    required: false
  labels:
    description: "List of custom labels for docker image"
    required: false
  version:
    # Version of the image to be build
    description: "Image version"
    required: true
  invalidate-cache:
    # Is a clean build of all intermediate images are needed
    description: 'Build all images disregarding exists same version'
    required: false
  build-args:
    # Build arguments for the image to be build
    description: "List of build-time variables"
    required: false
  build-contexts:
    # Contexts to be used by the image
    description: "Add extra context translation for the image"
    required: false
  secret-files:
    description: "Pass secrets as build info"
    required: false
  platforms:
    # Platforms to be built
    description: "Enable multi platform builds. Supported linux/amd64(default) and linux/arm66, comma separated"
    required: false
  debug:
    # Debug the image check script
    description: "Debug check_image script"
    required: false
```

### Basic example

```dockerfile
FROM ubuntu:22.04 AS base

ARG DOCKER_USER="myuser"

# Prepare system for non-priv user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd \
    --shell /bin/bash \
    --create-home ${DOCKER_USER}

FROM base AS runtime
  echo "My image" > /etc/test_image
```


```yaml
  base_image:
    name: Linux base image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    env:
      UBUNTU_VERSION: 22.04

    steps:
      - name: Checkout default branch
        uses: actions/checkout@v4
      - name: Build base image
        uses: heliocastro/docker-build-control@v1
        with:
          name: base
          token: ${{ secrets.GITHUB_TOKEN }}
          version: ${{ env.UBUNTU_VERSION }}
          build-args: |
            UBUNTU_VERSION=${{ env.UBUNTU_VERSION }}

  target_image:
     name: My Image
     runs-on: ubuntu-latest
     permissions:
       contents: read
       packages: write
     env:
       UBUNTU_VERSION: 22.04

     steps:
       - name: Checkout default branch
         uses: actions/checkout@v4
       - name: Build final image
         uses: heliocastro/docker-build-control@v4
         with:
          name: myimage
          token: ${{ secrets.GITHUB_TOKEN }}
          version: 0.0.1
          build-contexts: base=docker-image://${{ env.REGISTRY }}/${{ github.repository }}/base:${{ env.UBUNTU_VERSION }}
```

