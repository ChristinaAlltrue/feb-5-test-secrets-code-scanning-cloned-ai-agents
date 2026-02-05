#!/usr/bin/env bash
set -eo pipefail
set -x

function get_parameter_value() {
  local param_name="$1"
  aws ssm get-parameter \
      --name "${param_name}" \
      --query 'Parameter.Value' \
      --output text
 }

SERVER_PATH=${SERVER_PATH:-$(get_parameter_value /config/control-plane-endpoint)}
SERVER_NAME=${SERVER_NAME:-$(echo "$SERVER_PATH" | awk -F'[/:]' '{print $4}')}

# Check if SERVER_NAME is set
if [ -z "$SERVER_NAME" ]; then
    echo "ERROR: Failed to fetch SERVER_NAME from SSM"
    exit 1
fi

# Export the environment variable
export ALLTRUE_API_ENDPOINT="$SERVER_NAME"

if [ -n "$NLB_PARAMETER" ]; then
    export INTERNAL_NLB_ENDPOINT=$(get_parameter_value $NLB_PARAMETER)
fi
export OTEL_PYTHON_EXCLUDED_URLS="^https?://[^/]+/$|.*health.*"

echo "UV_NO_SELF_UPDATE is: $UV_NO_SELF_UPDATE"
echo "ALLTRUE_API_ENDPOINT set to $ALLTRUE_API_ENDPOINT"
echo "INTERNAL_NLB_ENDPOINT set to $INTERNAL_NLB_ENDPOINT"
echo "OTEL_PYTHON_EXCLUDED_URLS set to $OTEL_PYTHON_EXCLUDED_URLS"


# Run Uvicorn
uvicorn main:app --host 0.0.0.0 --port 80
