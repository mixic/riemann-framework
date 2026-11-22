# Fetch the MIT solution export in fixed ranges, with a manifest so ranges never shift.
# A part whose file is not the exact expected size is deleted and re-fetched whole;
# no append/truncate ambiguity. Re-run until COMPLETE=True, then concatenate.
param(
  [int]$BudgetSeconds = 480,
  [int]$Parts = 24
)

$d = 'C:\Users\Milan\Projects\riemann-audit\exports'
$main = Join-Path $d 'solution.ndjson.zst'
$partsDir = Join-Path $d 'parts'
$manifestPath = Join-Path $d 'parts_manifest.json'
$url = 'https://math.mit.edu/~drew/grh/solution.ndjson.zst'
$total = 7699933588

New-Item -ItemType Directory -Force -Path $partsDir | Out-Null
$prefix = (Get-Item $main).Length

if (Test-Path $manifestPath) {
  $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
} else {
  Get-ChildItem $partsDir -Filter 'part*' -ErrorAction SilentlyContinue | Remove-Item -Force
  $remaining = $total - $prefix
  $chunk = [math]::Floor($remaining / $Parts)
  $manifest = @()
  for ($i = 0; $i -lt $Parts; $i++) {
    $s = $prefix + $i * $chunk
    $e = if ($i -eq $Parts - 1) { $total - 1 } else { $prefix + ($i + 1) * $chunk - 1 }
    $manifest += [pscustomobject]@{
      index = $i
      start = $s
      end   = $e
      file  = (Join-Path $partsDir ('part{0:d3}' -f $i))
    }
  }
  $manifest | ConvertTo-Json | Set-Content $manifestPath
}

$jobs = @()
$sw = [Diagnostics.Stopwatch]::StartNew()
foreach ($r in $manifest) {
  $want = [long]$r.end - [long]$r.start + 1
  $have = if (Test-Path $r.file) { (Get-Item $r.file).Length } else { 0 }
  if ($have -eq $want) { continue }
  if ($have -ne 0) { Remove-Item $r.file -Force }
  $jobs += Start-Job -ScriptBlock {
    param($url, $s, $e, $out)
    # --fail-with-body so an HTTP error does not leave a plausible-looking file
    & curl.exe -sS --fail --max-time 2400 -r "$s-$e" -o $out $url
  } -ArgumentList $url, $r.start, $r.end, $r.file
}

while (($jobs | Where-Object State -eq 'Running').Count -gt 0 -and $sw.Elapsed.TotalSeconds -lt $BudgetSeconds) {
  Start-Sleep -Seconds 5
}
$jobs | Where-Object State -eq 'Running' | Stop-Job -ErrorAction SilentlyContinue
$jobs | Remove-Job -Force -ErrorAction SilentlyContinue

$have_sum = 0
$want_sum = 0
$done = 0
foreach ($r in $manifest) {
  $want = [long]$r.end - [long]$r.start + 1
  $want_sum += $want
  if (Test-Path $r.file) {
    $len = (Get-Item $r.file).Length
    if ($len -eq $want) { $done++ }
    if ($len -le $want) { $have_sum += $len }
  }
}
Write-Host ("elapsed={0:N0}s  parts_complete={1}/{2}  bytes={3} / {4} ({5:N1}%)" -f `
    $sw.Elapsed.TotalSeconds, $done, $manifest.Count, $have_sum, $want_sum, (100 * $have_sum / $want_sum))
Write-Host ("COMPLETE=" + ($done -eq $manifest.Count))
