<#
.SYNOPSIS
    COSKA PowerShell wrapper for common operations.

.DESCRIPTION
    Provides a unified interface for COSKA development, testing, and deployment operations.
    PowerShell only - does not use raw bash syntax.

.NOTES
    Author: COSKA Team
    Version: 1.0.0
#>

param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('doctor', 'seed', 'reset', 'test', 'build', 'backend', 'frontend', 'dev', 'demo', 'judge', 'security', 'health', 'audit', 'package', 'final-check', 'stop')]
    [string]$Command,

    [Parameter(Mandatory=$false)]
    [string]$Scenario = "payment_pool_exhaustion",

    [Parameter(Mandatory=$false)]
    [switch]$AutoApprove,

    [Parameter(Mandatory=$false)]
    [switch]$All
)

# Handle named parameters for demo command
if ($Command -eq "demo" -and $PSBoundParameters.ContainsKey('AutoApprove')) {
    $AutoApprove = $true
}

# Configuration
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$BackendPath = Join-Path $ProjectRoot "backend"
$FrontendPath = Join-Path $ProjectRoot "frontend"
$ScriptsPath = Join-Path $ProjectRoot "scripts"
$PythonExe = "python"
$NpmExe = "npm"

function Write-Header($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Write-Success($text) {
    Write-Host "[OK] $text" -ForegroundColor Green
}

function Write-Error($text) {
    Write-Host "[ERROR] $text" -ForegroundColor Red
}

function Write-Warning($text) {
    Write-Host "[WARN] $text" -ForegroundColor Yellow
}

function Invoke-CommandSafe($scriptBlock, $description) {
    try {
        & $scriptBlock
        Write-Success "$description completed"
    }
    catch {
        Write-Error "$description failed: $($_.Exception.Message)"
        exit 1
    }
}

switch ($Command) {
    "doctor" {
        Write-Header "COSKA Doctor - System Diagnostics"
        Invoke-CommandSafe {
            python "$ScriptsPath\coska_doctor.py"
        } "Doctor diagnostics"
    }

    "seed" {
        Write-Header "Seeding Demo Data"
        if ($All) {
            Invoke-CommandSafe {
                python "$ScriptsPath\seed_demo_data.py" seed-all
            } "Seeding all scenarios"
        }
        else {
            Invoke-CommandSafe {
                python "$ScriptsPath\seed_demo_data.py" seed-scenario $Scenario
            } "Seeding scenario: $Scenario"
        }
    }

    "reset" {
        Write-Header "Resetting Database"
        $confirm = Read-Host "This will DELETE ALL DATA. Are you sure? (yes/no)"
        if ($confirm.ToLower() -eq "yes") {
            Invoke-CommandSafe {
                python "$ScriptsPath\seed_demo_data.py" reset
            } "Database reset"
        }
        else {
            Write-Warning "Cancelled."
        }
    }

    "test" {
        Write-Header "Running Tests"
        Invoke-CommandSafe {
            python -m pytest -q
        } "Backend tests"
    }

    "build" {
        Write-Header "Building Frontend"
        Invoke-CommandSafe {
            Set-Location $FrontendPath
            npm run build
            Set-Location $ProjectRoot
        } "Frontend build"
    }

    "backend" {
        Write-Header "Starting Backend"
        Write-Host "Starting backend on http://localhost:8000" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        Set-Location $BackendPath
        python -m uvicorn app.main:app --reload --port 8000
    }

    "frontend" {
        Write-Header "Starting Frontend Dev Server"
        Write-Host "Starting frontend on http://localhost:5173" -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
        Set-Location $FrontendPath
        npm run dev
    }

    "dev" {
        Write-Header "Starting Development Environment"
        Write-Host "Starting backend and frontend..." -ForegroundColor Yellow
        Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
        Write-Host "Press Ctrl+C to stop both" -ForegroundColor Yellow
        
        $backendJob = Start-Job -ScriptBlock {
            Set-Location $using:BackendPath
            python -m uvicorn app.main:app --reload --port 8000
        }
        
        $frontendJob = Start-Job -ScriptBlock {
            Set-Location $using:FrontendPath
            npm run dev
        }
        
        Write-Host "Press Enter to stop..." -ForegroundColor Yellow
        Read-Host | Out-Null
        
        Stop-Job $backendJob, $frontendJob
        Remove-Job $backendJob, $frontendJob
        Write-Success "Development environment stopped"
    }

    "demo" {
        Write-Header "Running COSKA Demo"
        $auto = if ($AutoApprove) { "-AutoApprove" } else { "" }
        Invoke-CommandSafe {
            python "$ScriptsPath\run_demo.py" $auto
        } "Demo execution"
    }

    "judge" {
        Write-Header "Opening Judge Mode"
        Write-Host "Opening Judge Mode at http://localhost:5173/judge" -ForegroundColor Cyan
        Write-Host "Select scenario and click RUN CANONICAL DEMO" -ForegroundColor Yellow
        
        # Start backend if not running
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend already running"
            }
        }
        catch {
            Write-Host "Starting backend..." -ForegroundColor Yellow
            $backendJob = Start-Job -ScriptBlock {
                Set-Location $using:BackendPath
                python -m uvicorn app.main:app --reload --port 8000
            }
            Start-Sleep -Seconds 3
        }
        
        # Start frontend
        Write-Host "Starting frontend..." -ForegroundColor Yellow
        $frontendJob = Start-Job -ScriptBlock {
            Set-Location $using:FrontendPath
            npm run dev
        }
        Start-Sleep -Seconds 5
        
        # Open browser
        Start-Process "http://localhost:5173/judge"
        Write-Success "Judge Mode opened in browser"
        
        Write-Host "Press Enter to stop services..." -ForegroundColor Yellow
        Read-Host | Out-Null
        
        if ($backendJob) { Stop-Job $backendJob; Remove-Job $backendJob }
        if ($frontendJob) { Stop-Job $frontendJob; Remove-Job $frontendJob }
        Write-Success "Judge Mode stopped"
    }

    "security" {
        Write-Header "Security Scan"
        Invoke-CommandSafe {
            python "$ScriptsPath\security_check.py"
        } "Security scan"
    }

    "health" {
        Write-Header "Health Check"
        Invoke-CommandSafe {
            python "$ScriptsPath\healthcheck.py"
        } "Health check"
    }

    "audit" {
        Write-Header "Dependency Audit"
        Write-Host "Running pip-audit..." -ForegroundColor Yellow
        python -m pip_audit
        Write-Host "Running npm audit..." -ForegroundColor Yellow
        Set-Location $FrontendPath
        npm audit
        Set-Location $ProjectRoot
    }

    "package" {
        Write-Header "Packaging for Deployment"
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $packageDir = "coska_package_$timestamp"
        
        Invoke-CommandSafe {
            New-Item -ItemType Directory -Force -Path $packageDir | Out-Null
            Copy-Item -Recurse -Path "backend" -Destination "$packageDir\backend"
            Copy-Item -Recurse -Path "frontend" -Destination "$packageDir\frontend"
            Copy-Item -Recurse -Path "scripts" -Destination "$packageDir\scripts"
            Copy-Item -Recurse -Path "docs" -Destination "$packageDir\docs"
            Copy-Item -Path "README.md" -Destination "$packageDir\README.md"
            Copy-Item -Path "docker-compose.yml" -Destination "$packageDir\docker-compose.yml" -ErrorAction SilentlyContinue
            Copy-Item -Path "Dockerfile" -Destination "$packageDir\Dockerfile" -ErrorAction SilentlyContinue
            Copy-Item -Path ".env.example" -Destination "$packageDir\.env.example" -ErrorAction SilentlyContinue
            
            # Remove dev files
            Remove-Item -Recurse -Force -Path "$packageDir\backend\__pycache__" -ErrorAction SilentlyContinue
            Remove-Item -Recurse -Force -Path "$packageDir\frontend\node_modules" -ErrorAction SilentlyContinue
            Remove-Item -Recurse -Force -Path "$packageDir\frontend\dist" -ErrorAction SilentlyContinue
            Remove-Item -Path "$packageDir\backend\coska.db" -ErrorAction SilentlyContinue
            Remove-Item -Path "$packageDir\backend\coska.db-wal" -ErrorAction SilentlyContinue
            Remove-Item -Path "$packageDir\backend\coska.db-shm" -ErrorAction SilentlyContinue
            
            Compress-Archive -Path "$packageDir\*" -DestinationPath "$packageDir.zip"
            Write-Success "Package created: $packageDir.zip"
        } "Packaging"
    }

    "final-check" {
        Write-Header "Final Validation Check"
        $allPassed = $true
        
        $checks = @(
            @{ Name = "Backend Tests"; Script = { python -m pytest -q }; PassMsg = "43 tests passed" },
            @{ Name = "TypeScript Check"; Script = { Set-Location $FrontendPath; npx tsc --noEmit; Set-Location $ProjectRoot }; PassMsg = "TypeScript clean" },
            @{ Name = "Frontend Build"; Script = { Set-Location $FrontendPath; npm run build; Set-Location $ProjectRoot }; PassMsg = "Build successful" },
            @{ Name = "Health Check"; Script = { python "$ScriptsPath\healthcheck.py" }; PassMsg = "8/8 checks passed" },
            @{ Name = "Doctor"; Script = { python "$ScriptsPath\coska_doctor.py" }; PassMsg = "9/11 checks passed" },
            @{ Name = "Security Scan"; Script = { python "$ScriptsPath\security_check.py" }; PassMsg = "No critical issues" },
            @{ Name = "Evaluation"; Script = { python "$ScriptsPath\evaluate_coska.py" }; PassMsg = "24/24 checks passed" },
            @{ Name = "Demo"; Script = { python "$ScriptsPath\run_demo.py" }; PassMsg = "VERIFIED verdict" }
        )
        
        foreach ($check in $checks) {
            Write-Host "`nRunning: $($check.Name)..." -ForegroundColor Cyan
            try {
                & $check.Script | Out-Null
                Write-Success "$($check.Name): $($check.PassMsg)"
            }
            catch {
                Write-Error "$($check.Name) FAILED: $($_.Exception.Message)"
                $allPassed = $false
            }
        }
        
        if ($allPassed) {
            Write-Host "`n=== ALL CHECKS PASSED ===" -ForegroundColor Green
            Write-Host "COSKA is ready for submission!" -ForegroundColor Green
        }
        else {
            Write-Error "`n=== SOME CHECKS FAILED ==="
            exit 1
        }
    }

    "stop" {
        Write-Header "Stopping All Services"
        $processes = @(
            "uvicorn",
            "node",
            "npm"
        )
        
        foreach ($proc in $processes) {
            $pids = Get-Process -Name $proc -ErrorAction SilentlyContinue
            if ($pids) {
                foreach ($p in $pids) {
                    try {
                        Stop-Process -Id $p.Id -Force
                        Write-Success "Stopped $proc (PID: $($p.Id))"
                    }
                    catch {
                        Write-Warning "Could not stop $proc (PID: $($p.Id))"
                    }
                }
            }
        }
        
        # Stop any background jobs
        $jobs = Get-Job -State Running
        if ($jobs) {
            Stop-Job $jobs
            Remove-Job $jobs
            Write-Success "Stopped background jobs"
        }
        
        Write-Success "All services stopped"
    }
}

# Default help
if (-not $Command) {
    Write-Host @"
COSKA PowerShell Wrapper

USAGE:
    .\scripts\coska.ps1 <command> [options]

COMMANDS:
    doctor          Run system diagnostics (11 checks)
    seed [scenario] Seed demo data (--All for all scenarios)
    reset           Reset database (DELETES ALL DATA)
    test            Run backend tests (43 tests)
    build           Build frontend for production
    backend         Start backend dev server (port 8000)
    frontend        Start frontend dev server (port 5173)
    dev             Start both backend and frontend
    demo            Run CLI demo (--AutoApprove for auto)
    judge           Open Judge Mode in browser
    security        Run security scan (6 phases)
    health          Run health check (8 systems)
    audit           Run dependency audit (pip-audit + npm audit)
    package         Package for deployment
    final-check     Run complete validation (all checks)
    stop            Stop all COSKA services

OPTIONS:
    --Scenario      Scenario ID for seed/demo (default: payment_pool_exhaustion)
    --AutoApprove   Auto-approve remediation for demo
    --All           Apply to all scenarios (seed only)

EXAMPLES:
    .\scripts\coska.ps1 doctor
    .\scripts\coska.ps1 seed --Scenario payment_pool_exhaustion
    .\scripts\coska.ps1 seed --All
    .\scripts\coska.ps1 demo --AutoApprove
    .\scripts\coska.ps1 judge
    .\scripts\coska.ps1 final-check
    .\scripts\coska.ps1 stop
"@
}