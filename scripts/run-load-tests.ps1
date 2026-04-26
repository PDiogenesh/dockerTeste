param(
    [string]$Duration = "1m",
    [int[]]$Users = @(10, 100, 1000),
    [int[]]$Instances = @(1, 2, 3)
)

$ErrorActionPreference = "Stop"

$scenarios = @(
    @{ Key = "imagem_1mb"; Path = "/?p=5"; Description = "Post com imagem de aproximadamente 1 MB" },
    @{ Key = "post_400kb"; Path = "/?p=10"; Description = "Post de aproximadamente 400 KB" },
    @{ Key = "imagem_300kb"; Path = "/?p=13"; Description = "Post com imagem de aproximadamente 300 KB" }
)

function Get-NginxConfig([int]$InstanceCount) {
    if ($InstanceCount -eq 1) {
        return "./nginx-1.conf"
    }

    if ($InstanceCount -eq 2) {
        return "./nginx-2.conf"
    }

    return "./nginx.conf"
}

function Get-SpawnRate([int]$UserCount) {
    if ($UserCount -le 10) {
        return 10
    }

    if ($UserCount -le 100) {
        return 20
    }

    return 50
}

New-Item -ItemType Directory -Force -Path "reports" | Out-Null

docker-compose up -d mysql-db wordpress1 wordpress2 wordpress3 locust

foreach ($instanceCount in $Instances) {
    $env:NGINX_CONF = Get-NginxConfig $instanceCount
    Write-Host ""
    Write-Host "=== Recriando Nginx com $instanceCount instancia(s): $env:NGINX_CONF ==="
    docker-compose up -d --force-recreate nginx
    Start-Sleep -Seconds 15

    foreach ($scenario in $scenarios) {
        foreach ($userCount in $Users) {
            $spawnRate = Get-SpawnRate $userCount
            $prefix = "reports/$($scenario.Key)_${instanceCount}wp_${userCount}users"

            Write-Host ""
            Write-Host "=== Teste: $($scenario.Description) | $instanceCount WP | $userCount usuarios | $Duration ==="
            docker-compose exec -e TARGET_PATHS="$($scenario.Path)" locust locust `
                -f locustfile.py `
                --host http://nginx `
                --headless `
                -u $userCount `
                -r $spawnRate `
                -t $Duration `
                --csv $prefix `
                --csv-full-history
        }
    }
}

python scripts/generate-graphs.py

Write-Host ""
Write-Host "Testes finalizados. Graficos em reports/graphs."
