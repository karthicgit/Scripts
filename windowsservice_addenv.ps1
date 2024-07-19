function Get-Environment-Variables-Table([string]$InstallDir, [string]$OTelServiceName) {
    $COR_PROFILER_PATH_32 = Join-Path $InstallDir "/win-x86/OpenTelemetry.AutoInstrumentation.Native.dll"
    $COR_PROFILER_PATH_64 = Join-Path $InstallDir "/win-x64/OpenTelemetry.AutoInstrumentation.Native.dll"
    $CORECLR_PROFILER_PATH_32 = Join-Path $InstallDir "/win-x86/OpenTelemetry.AutoInstrumentation.Native.dll"
    $CORECLR_PROFILER_PATH_64 = Join-Path $InstallDir "/win-x64/OpenTelemetry.AutoInstrumentation.Native.dll"

    $DOTNET_ADDITIONAL_DEPS = Join-Path $InstallDir "AdditionalDeps"
    $DOTNET_SHARED_STORE = Join-Path $InstallDir "store"
    $DOTNET_STARTUP_HOOKS = Join-Path $InstallDir "net/OpenTelemetry.AutoInstrumentation.StartupHook.dll"

    $OTEL_DOTNET_AUTO_HOME = $InstallDir
    
    #Update the value here before running the script
    $data_upload_endpoint = "<data_upload_endpoint>"
    $private_key = "<private_key>"
    
    $vars = @{
        # .NET Framework
        "COR_ENABLE_PROFILING"                = "1";
        "COR_PROFILER"                        = "{918728DD-259F-4A6A-AC2B-B85E1B658318}";
        "COR_PROFILER_PATH_32"                = $COR_PROFILER_PATH_32;
        "COR_PROFILER_PATH_64"                = $COR_PROFILER_PATH_64;
        # .NET Core
        "CORECLR_ENABLE_PROFILING"            = "1";
        "CORECLR_PROFILER"                    = "{918728DD-259F-4A6A-AC2B-B85E1B658318}";
        "CORECLR_PROFILER_PATH_32"            = $CORECLR_PROFILER_PATH_32;
        "CORECLR_PROFILER_PATH_64"            = $CORECLR_PROFILER_PATH_64;
        # ASP.NET Core
        "ASPNETCORE_HOSTINGSTARTUPASSEMBLIES" = "OpenTelemetry.AutoInstrumentation.AspNetCoreBootstrapper";
        # .NET Common
        "DOTNET_ADDITIONAL_DEPS"              = $DOTNET_ADDITIONAL_DEPS;
        "DOTNET_SHARED_STORE"                 = $DOTNET_SHARED_STORE;
        "DOTNET_STARTUP_HOOKS"                = $DOTNET_STARTUP_HOOKS;
        # OpenTelemetry
        "OTEL_DOTNET_AUTO_HOME"               = $OTEL_DOTNET_AUTO_HOME;
        #OCI APM
        "OTEL_DOTNET_AUTO_TRACES_ADDITIONAL_SOURCES" = "OpenTelemetry.ODP";
        "OTEL_LOGS_EXPORTER" = "none";
        "OTEL_DOTNET_AUTO_EXCLUDE_PROCESSES" = "dotnet.exe,dotnet";
        "OTEL_EXPORTER_OTLP_ENDPOINT"= "$data_upload_endpoint/20200101/opentelemetry";
        "OTEL_EXPORTER_OTLP_HEADERS"= "Authorization=dataKey $private_key";
    }

    if (-not [string]::IsNullOrWhiteSpace($OTelServiceName)) {
        $vars.Add("OTEL_SERVICE_NAME", $OTelServiceName)
    }

    return $vars
}

function Setup-Windows-Service([string]$InstallDir, [string]$WindowsServiceName, [string]$OTelServiceName) {  
    $varsTable = Get-Environment-Variables-Table -InstallDir $InstallDir -OTelServiceName $OTelServiceName
    [string []] $varsList = ($varsTable.Keys | foreach-object { "$_=$($varsTable[$_])" }) # [string []] definition is required for WS2016
    $regPath = "HKLM:SYSTEM\CurrentControlSet\Services\"
    $regKey = Join-Path $regPath $WindowsServiceName
   
    if (Test-Path $regKey) {
        Set-ItemProperty $regKey -Name Environment -Value $varsList
    }
    else {
        throw "Invalid service '$WindowsServiceName'. Service does not exist."
    }
}

function Remove-Windows-Service([string]$WindowsServiceName) {
    [string[]] $filters = @(
        # .NET Framework
        "COR_ENABLE_PROFILING",
        "COR_PROFILER",
        "COR_PROFILER_PATH_32",
        "COR_PROFILER_PATH_64",
        # .NET Core
        "CORECLR_ENABLE_PROFILING",
        "CORECLR_PROFILER",
        "CORECLR_PROFILER_PATH_32",
        "CORECLR_PROFILER_PATH_64",
        # ASP.NET Core
        "ASPNETCORE_HOSTINGSTARTUPASSEMBLIES",
        # .NET Common
        "DOTNET_ADDITIONAL_DEPS",
        "DOTNET_SHARED_STORE",
        "DOTNET_STARTUP_HOOKS",
        # OpenTelemetry
        "OTEL_DOTNET_AUTO_HOME",
        #OCI APM
        "OTEL_DOTNET_AUTO_TRACES_ADDITIONAL_SOURCES",
        "OTEL_LOGS_EXPORTER",
        "OTEL_DOTNET_AUTO_EXCLUDE_PROCESSES",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_EXPORTER_OTLP_HEADERS")

    $regPath = "HKLM:SYSTEM\CurrentControlSet\Services\"
    $regKey = Join-Path $regPath $WindowsServiceName
   
    if (Test-Path $regKey) {
        $values = Get-ItemPropertyValue $regKey -Name Environment
        $vars = Filter-Env-List -EnvValues $values -Filters $filters
        
        Set-ItemProperty $regKey -Name Environment -Value $vars
    }
    else {
        throw "Invalid service '$WindowsServiceName'. Service does not exist."
    }

    $remaining = Get-ItemPropertyValue $regKey -Name Environment
    if (-not $remaining) {
        Remove-ItemProperty $regKey -Name Environment
    }
}

function Filter-Env-List([string[]]$EnvValues, [string[]]$Filters) {
    $remaining = @()

    foreach ($value in $EnvValues) {
        $match = $false

        foreach ($filter in $Filters) {
            if ($value -clike "$($filter)*") {
                $match = $true
                break
            }
        }

        if (-not $match) {
            $remaining += $value
        }
    }

    return $remaining
}
