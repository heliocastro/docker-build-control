# SPDX-FileCopyrightText: 2024 Helio Chissini de Castro <heliocastro@gmail.com>
#
# SPDX-License-Identifier: MIT


import hashlib
import logging
import os
import sys
from typing import Any
from urllib.parse import quote

import requests
from rich.logging import RichHandler
from rich.pretty import pprint

""" Use current GitHub API to check if a container image with the
    given name and version exists.
"""

logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger("rich")
if "ACTION_DEBUG" in os.environ and os.environ["ACTION_DEBUG"] == "true":
    log.setLevel(logging.DEBUG)
token = os.getenv("INPUT_TOKEN")
github_repository = os.getenv("GITHUB_REPOSITORY")
if not github_repository:
    log.error("Missing Github repository !")
    sys.exit(1)
name = os.getenv("INPUT_NAME")
base_version = os.getenv("INPUT_VERSION")
if not base_version:
    log.error("Missing version !")
    sys.exit(1)
build_args = os.getenv("BUILD_ARGS")
invalidate_cache = True if os.getenv("INVALIDATE_CACHE") else False
unique_id = (
    hashlib.sha256(build_args.encode()).hexdigest()
    if build_args
    else hashlib.sha256(base_version.encode()).hexdigest()
)
owner, repository = github_repository.split("/")

log.debug(f"Owner: {owner}")
log.debug(f"Repository: {repository}")
log.debug(f"Image: {name}")
log.debug(f"Version: {base_version}")

# We base the version on the base_version and the unique_id
version = f"{base_version}-sha.{unique_id[:8]}"
status: str = "none"

# In case of need invalidate the cache from images we just return the version
if invalidate_cache:
    logging.debug("Image is set to be rebuild due invalidate option.")
    # Set GitHub Actions output
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(f"result={status}\n")
        file.write(f"image_version={version}\n")
    sys.exit(0)

headers: dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28",
}

url: str = f"https://api.github.com/users/{owner}"
response = requests.get(url, headers=headers)
data: Any = response.json()


encoded_name = quote(f"{repository}/{name}", safe="")
if data.get("type") == "Organization":
    url = f"https://api.github.com/orgs/{owner}/packages/container/{encoded_name}/versions"
else:
    url = f"https://api.github.com/user/packages/container/{encoded_name}/versions"

log.debug(f"URL: {url}")
response = requests.get(url, headers=headers)
if response.status_code == 404:
    os.environ["GITHUB_OUTPUT"] = "none"
else:
    data = response.json()
    versions = [
        item
        for sublist in [v["metadata"]["container"]["tags"] for v in data]
        if sublist
        for item in sublist
    ]

    if log.level == logging.DEBUG:
        pprint(versions)

    if version in versions:
        status = "found"

    log.info(f"Version: {version}")

    # Set GitHub Actions output
    with open(os.environ["GITHUB_OUTPUT"], "a") as file:
        file.write(f"result={status}\n")
        file.write(f"image_version={version}\n")
