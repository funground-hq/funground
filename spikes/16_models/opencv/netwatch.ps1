# Run measure.py as a child process and poll its TCP connections every 50 ms until it exits.
# Usage: netwatch.ps1 -Py <python.exe> -Script <measure.py> -ScriptArgs "<task> <models> <images> <out.json>" -Log <file>
param([string]$Py, [string]$Script, [string]$ScriptArgs, [string]$Log)
$p = Start-Process -FilePath $Py -ArgumentList "-I `"$Script`" $ScriptArgs" -PassThru -NoNewWindow -RedirectStandardOutput $Log -RedirectStandardError "$Log.err"
$seen = @{}; $polls = 0
while (-not $p.HasExited) {
  $polls++
  $c = Get-NetTCPConnection -OwningProcess $p.Id -ErrorAction SilentlyContinue
  foreach ($x in $c) { $seen["$($x.State) $($x.LocalAddress):$($x.LocalPort) -> $($x.RemoteAddress):$($x.RemotePort)"] = 1 }
  Start-Sleep -Milliseconds 50
}
"polls=$polls tcp_connections_seen=$($seen.Count)"
$seen.Keys
