# Kills plugin MCP server processes (python/node under ~/.claude/plugins) whose parent is gone.
# Never touches a process with a live parent. Use -DryRun to list without killing.
param([switch]$DryRun)

$procs = Get-CimInstance Win32_Process -Filter "Name like 'python%' or Name like 'node%'"
$alive = @{}
Get-Process | ForEach-Object { $alive[[int]$_.Id] = $_.StartTime }

foreach ($p in $procs) {
    $cmd = $p.CommandLine
    if (-not $cmd) { continue }
    if ($cmd -notmatch '(?i)[\\/]\.claude[\\/]plugins[\\/]') { continue }

    $ppid = [int]$p.ParentProcessId
    $parentAlive = $false
    if ($alive.ContainsKey($ppid)) {
        # PID reuse guard: a live parent must have started before the child.
        try { $parentAlive = ($alive[$ppid] -le $p.CreationDate) } catch { $parentAlive = $true }
    }
    if ($parentAlive) { continue }

    if ($DryRun) {
        "orphan: PID $($p.ProcessId) (parent $ppid dead) $cmd"
    } else {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
}
exit 0
