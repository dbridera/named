#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────
IMAGE_NAME="named"
VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/.*"\(.*\)"/\1/')
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# ── Functions ──────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: ./docker_build.sh [options]

Options:
  --env <dev|prod>    Tag environment (default: dev)
  --tag <tag>         Additional custom tag
  --no-cache          Build without Docker cache

Tagging strategy:
  dev:   named:dev  named:dev-VERSION  named:dev-VERSION-SHA
  prod:  named:prod named:prod-VERSION named:prod-VERSION-SHA named:VERSION named:latest

Examples:
  ./docker_build.sh                          # named:dev, named:dev-0.1.0, named:dev-0.1.0-abc1234
  ./docker_build.sh --env prod               # named:prod, named:prod-0.1.0, ..., named:latest
  ./docker_build.sh --env prod --tag rc1     # also tags named:rc1
  ./docker_build.sh --no-cache               # rebuild from scratch
EOF
}

# ── Parse args ─────────────────────────────────────────────────
env="dev"
custom_tag=""
no_cache=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --env)      env="$2"; shift 2 ;;
        --tag)      custom_tag="$2"; shift 2 ;;
        --no-cache) no_cache="--no-cache"; shift ;;
        --help|-h)  usage; exit 0 ;;
        *)          echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

if [[ "$env" != "dev" && "$env" != "prod" ]]; then
    echo "Error: --env must be 'dev' or 'prod'"
    exit 1
fi

# ── Build tag list ─────────────────────────────────────────────
tags=()
tags+=("${IMAGE_NAME}:${env}")
tags+=("${IMAGE_NAME}:${env}-${VERSION}")
tags+=("${IMAGE_NAME}:${env}-${VERSION}-${GIT_SHA}")

if [[ "$env" == "prod" ]]; then
    tags+=("${IMAGE_NAME}:${VERSION}")
    tags+=("${IMAGE_NAME}:latest")
fi

if [[ -n "$custom_tag" ]]; then
    tags+=("${IMAGE_NAME}:${custom_tag}")
fi

# ── Build ──────────────────────────────────────────────────────
tag_flags=()
for t in "${tags[@]}"; do
    tag_flags+=("-t" "$t")
done

echo "Building ${IMAGE_NAME} (env=${env}, version=${VERSION}, sha=${GIT_SHA})"
echo "Tags:"
for t in "${tags[@]}"; do
    echo "  - $t"
done
echo ""

docker build ${no_cache} "${tag_flags[@]}" .

echo ""
echo "Build complete."
