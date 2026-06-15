# Squidfall control wrapper for Windows (replaces `make`).
#   ./sf.ps1 build  database
#   ./sf.ps1 start  all
#   ./sf.ps1 status inference
#   ./sf.ps1 stop   all
param(
    [Parameter(Position = 0)]
    [ValidateSet('build', 'start', 'stop', 'status')]
    [string]$Command = 'build',

    [Parameter(Position = 1)]
    [string]$ComposeProfile = 'all'
)

$env:COMPOSE_BAKE = 'true'

switch ($Command) {
    'build'  { docker compose --profile $ComposeProfile build }
    'start'  { docker compose --profile $ComposeProfile up -d }
    'stop'   { docker compose --profile $ComposeProfile down }
    'status' { docker compose --profile $ComposeProfile ps --format "table {{.Name}}`t{{.Ports}}`t{{.Status}}" }
}
