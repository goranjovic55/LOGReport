# MODMeta LSR Automation Scripts
# These scripts automate the Log-Sum-Rule workflow for continuous improvement

# Ensure required directories exist
function Initialize-LSREnvironment {
    [CmdletBinding()]
    param()
    
    Write-Host "Initializing LSR environment..."
    
    # Create directory structure
    $directories = @(
        ".lsr",
        ".lsr/sessions",
        ".lsr/logs",
        ".lsr/summaries",
        ".lsr/rules",
        ".lsr/metrics"
    )
    
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -Path $dir -ItemType Directory | Out-Null
            Write-Host "Created directory: $dir"
        }
    }
    
    # Create component-specific log directories
    $components = @(
        "Scanner",
        "Parser",
        "Standardizer",
        "Classifier",
        "CrossReferencer",
        "GUI",
        "Core",
        "Common"
    )
    
    foreach ($component in $components) {
        $dir = ".lsr/logs/$component"
        if (-not (Test-Path $dir)) {
            New-Item -Path $dir -ItemType Directory | Out-Null
            Write-Host "Created component log directory: $dir"
        }
    }
    
    # Create configuration if it doesn't exist
    $configFile = ".lsr/config.json"
    if (-not (Test-Path $configFile)) {
        $config = @{
            ProjectName = "MODMeta"
            DefaultComponents = $components
            SummarySchedule = @{
                Weekly = $true
                Monthly = $true
                Quarterly = $true
            }
            MetricsToCollect = @(
                "LinesOfCode",
                "CyclomaticComplexity",
                "TestCoverage",
                "BuildTime",
                "Errors",
                "Warnings"
            )
        }
        
        $config | ConvertTo-Json -Depth 5 | Set-Content $configFile
        Write-Host "Created default configuration: $configFile"
    }
    
    # Install or register Git hooks if possible
    if (Test-Path ".git") {
        Copy-Item -Path "./scripts/git-hooks/post-commit" -Destination ".git/hooks/" -Force
        Write-Host "Installed Git hooks for LSR integration"
    }
    
    Write-Host "LSR environment initialized successfully"
}

# Get current code metrics
function Get-ProjectMetrics {
    [CmdletBinding()]
    param (
        [string]$Path = "."
    )
    
    Write-Host "Collecting project metrics..."
    
    # Basic metrics that don't require external tools
    $metrics = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Files = (Get-ChildItem -Path $Path -Recurse -File | Where-Object { $_.Extension -match '\.(cs|xaml|xml|json)$' }).Count
        LinesOfCode = 0
        Comments = 0
        Directories = (Get-ChildItem -Path $Path -Recurse -Directory).Count
        GitStats = @{}
    }
    
    # Count lines of code and comments
    $codeFiles = Get-ChildItem -Path $Path -Recurse -File | Where-Object { $_.Extension -match '\.(cs|xaml)$' }
    
    foreach ($file in $codeFiles) {
        $content = Get-Content -Path $file.FullName
        $metrics.LinesOfCode += ($content | Where-Object { $_ -match '\S' -and $_ -notmatch '^\s*//|-\-\s*>|<!--' }).Count
        $metrics.Comments += ($content | Where-Object { $_ -match '^\s*//|/\*|\*\/|<!--' }).Count
    }
    
    # Get Git statistics if available
    if (Test-Path ".git") {
        try {
            # Get commit count
            $metrics.GitStats.Commits = (git rev-list --count HEAD)
            
            # Get branch count
            $metrics.GitStats.Branches = (git branch --all | Measure-Object).Count
            
            # Get contributor count
            $metrics.GitStats.Contributors = (git shortlog -sn --all | Measure-Object).Count
            
            # Recent activity
            $metrics.GitStats.RecentCommits = (git log --since="1 week ago" --oneline | Measure-Object).Count
        }
        catch {
            Write-Warning "Error collecting Git metrics: $_"
        }
    }
    
    # Add tool-specific metrics if available
    try {
        # Example: integrate with external metrics tools
        # This would be replaced with actual tooling
        if (Get-Command "dotnet-counters" -ErrorAction SilentlyContinue) {
            # Collect metrics from dotnet tools
            # This is just an example placeholder
            $metrics.TestCoverage = 75 # Placeholder
            $metrics.CyclomaticComplexity = 15 # Placeholder
        }
    }
    catch {
        Write-Warning "Error collecting tool-specific metrics: $_"
    }
    
    return $metrics
}

# Start a development session
function Start-DevSession {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$IssueId,
        
        [Parameter(Mandatory = $true)]
        [ValidateSet("Scanner", "Parser", "Standardizer", "Classifier", "CrossReferencer", "GUI", "Core", "Common")]
        [string]$Component,
        
        [Parameter(Mandatory = $true)]
        [ValidateSet("Feature", "BugFix", "Performance", "Refactoring", "Documentation")]
        [string]$TaskType,
        
        [Parameter(Mandatory = $false)]
        [double]$EstimatedHours = 0
    )
    
    Write-Host "Starting development session for $IssueId ($Component - $TaskType)..."
    
    # Generate session ID
    $sessionId = [Guid]::NewGuid().ToString()
    
    # Collect initial metrics
    $initialMetrics = Get-ProjectMetrics
    
    # Create session data
    $sessionData = @{
        SessionId = $sessionId
        IssueId = $IssueId
        Component = $Component
        TaskType = $TaskType
        EstimatedHours = $EstimatedHours
        StartTime = Get-Date
        InitialMetrics = $initialMetrics
        Developer = $env:USERNAME
        Events = @()
    }
    
    # Save session data
    $sessionFile = ".lsr/sessions/$sessionId.json"
    $sessionData | ConvertTo-Json -Depth 10 | Set-Content $sessionFile
    
    # Set environment variables for other tools to use
    $env:LSR_SESSION_ID = $sessionId
    $env:LSR_ISSUE_ID = $IssueId
    $env:LSR_COMPONENT = $Component
    
    # Create initial log file with template structure
    $logTemplate = Get-Content -Path ".lsr/templates/LOG_TEMPLATE.md" -ErrorAction SilentlyContinue
    if (-not $logTemplate) {
        # Create basic template if none exists
        $logTemplate = @"
# Development Log: $IssueId

## Basic Information

**Date:** $(Get-Date -Format "yyyy-MM-dd")  
**Developer:** $env:USERNAME  
**Component:** $Component  
**Task Type:** $TaskType  
**Task ID:** $IssueId  

## Time Tracking

**Estimated Hours:** $EstimatedHours  
**Actual Hours:** [To be completed]  
**Variance (%):** [To be calculated]  

## Task Details

### Context
[Brief description of the task, its purpose, and expected outcome]

### Implementation Details

**Approach Taken:**
[Description of the solution implemented]

**Alternatives Considered:**
[Other approaches that were considered but not implemented]

**Decision Factors:**
[Reasons for choosing the implemented solution over alternatives]

## Metrics

**Lines Added:** [Will be calculated]  
**Lines Modified:** [Will be calculated]  
**Lines Deleted:** [Will be calculated]  
**Files Changed:** [Will be calculated]  
**Complexity Delta:** [Will be calculated]  
**Test Coverage Change:** [Will be calculated]  

## Challenges & Solutions

### Obstacles Encountered
1. [Description of challenge 1]
   - Impact: [Low/Medium/High]
   - Resolution: [How it was resolved]

### Unexpected Issues
[Any surprises or unexpected behavior encountered]

## Learnings

### Key Insights
[Important discoveries or realizations during implementation]

### Knowledge Gaps Identified
[Areas where more knowledge or training would be beneficial]

### Potential Improvements
[Ideas for how similar tasks could be approached better in future]

## Additional Notes

[Any other relevant information not captured above]
"@
    }
    
    # Save log template with basic information
    $logFile = ".lsr/logs/$Component/$IssueId.md"
    $logTemplate | Set-Content $logFile
    
    # Start timer for session
    $timerFile = ".lsr/sessions/$sessionId.timer"
    Get-Date | Set-Content $timerFile
    
    Write-Host "Development session started with ID: $sessionId"
    Write-Host "Log file created at: $logFile"
    Write-Host "Use 'End-DevSession' when you've completed your work"
    
    return $sessionId
}

# Record an event during development
function Add-DevEvent {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$EventType,
        
        [Parameter(Mandatory = $true)]
        [string]$Description,
        
        [Parameter(Mandatory = $false)]
        [hashtable]$Metadata
    )
    
    if (-not $env:LSR_SESSION_ID) {
        Write-Error "No active development session found. Start a session with Start-DevSession first."
        return
    }
    
    $sessionId = $env:LSR_SESSION_ID
    $sessionFile = ".lsr/sessions/$sessionId.json"
    
    if (-not (Test-Path $sessionFile)) {
        Write-Error "Session file not found: $sessionFile"
        return
    }
    
    # Load session data
    $sessionData = Get-Content $sessionFile | ConvertFrom-Json
    
    # Add new event
    $event = @{
        Timestamp = Get-Date
        EventType = $EventType
        Description = $Description
    }
    
    if ($Metadata) {
        foreach ($key in $Metadata.Keys) {
            $event[$key] = $Metadata[$key]
        }
    }
    
    # Convert session data to PowerShell object for manipulation
    $sessionObj = $sessionData | ConvertTo-PSCustomObject
    
    # Add event to session data
    if (-not $sessionObj.Events) {
        $sessionObj.Events = @()
    }
    $sessionObj.Events += $event
    
    # Save updated session data
    $sessionObj | ConvertTo-Json -Depth 10 | Set-Content $sessionFile
    
    Write-Host "Event recorded: $EventType - $Description"
}

# End the current development session
function End-DevSession {
    [CmdletBinding()]
    param (
        [switch]$SkipPrompt
    )
    
    if (-not $env:LSR_SESSION_ID) {
        Write-Error "No active development session found"
        return
    }
    
    $sessionId = $env:LSR_SESSION_ID
    $sessionFile = ".lsr/sessions/$sessionId.json"
    
    if (-not (Test-Path $sessionFile)) {
        Write-Error "Session file not found: $sessionFile"
        return
    }
    
    # Load session data
    $sessionData = Get-Content $sessionFile | ConvertFrom-Json
    
    # Calculate session duration
    $endTime = Get-Date
    $startTime = [datetime]::Parse($sessionData.StartTime)
    $duration = ($endTime - $startTime).TotalHours
    
    # Get final metrics
    $finalMetrics = Get-ProjectMetrics
    
    # Calculate changes
    $changes = @{
        LinesOfCode = $finalMetrics.LinesOfCode - $sessionData.InitialMetrics.LinesOfCode
        Files = $finalMetrics.Files - $sessionData.InitialMetrics.Files
        Comments = $finalMetrics.Comments - $sessionData.InitialMetrics.Comments
    }
    
    # Get Git changes if available
    $gitChanges = @{
        FilesChanged = 0
        LinesAdded = 0
        LinesDeleted = 0
        Commits = 0
    }
    
    try {
        if (Test-Path ".git") {
            # Format git date for command
            $gitDate = $startTime.ToString("yyyy-MM-dd HH:mm:ss")
            
            # Get files changed
            $gitChanges.FilesChanged = (git diff --name-only --diff-filter=ACMRT --since="$gitDate" | Measure-Object).Count
            
            # Get line changes
            $diffStats = git diff --stat --since="$gitDate" | Select-Object -Last 1
            if ($diffStats -match '(\d+) insertion.*(\d+) deletion') {
                $gitChanges.LinesAdded = $matches[1]
                $gitChanges.LinesDeleted = $matches[2]
            }
            
            # Get commit count
            $gitChanges.Commits = (git log --since="$gitDate" --oneline | Measure-Object).Count
        }
    }
    catch {
        Write-Warning "Error collecting Git changes: $_"
    }
    
    # Update session data
    $sessionData.EndTime = $endTime
    $sessionData.Duration = $duration
    $sessionData.FinalMetrics = $finalMetrics
    $sessionData.Changes = $changes
    $sessionData.GitChanges = $gitChanges
    
    # Save updated session data
    $sessionData | ConvertTo-Json -Depth 10 | Set-Content $sessionFile
    
    # Update log file with collected metrics
    $logFile = ".lsr/logs/$($sessionData.Component)/$($sessionData.IssueId).md"
    if (Test-Path $logFile) {
        $logContent = Get-Content $logFile -Raw
        
        # Update time tracking
        $logContent = $logContent -replace "Estimated Hours: .*", "Estimated Hours: $($sessionData.EstimatedHours)"
        $logContent = $logContent -replace "Actual Hours: .*", "Actual Hours: $([math]::Round($duration, 2))"
        
        $variance = 0
        if ($sessionData.EstimatedHours -gt 0) {
            $variance = [math]::Round(($duration - $sessionData.EstimatedHours) / $sessionData.EstimatedHours * 100, 1)
        }
        $logContent = $logContent -replace "Variance \(%\): .*", "Variance (%): $variance%"
        
        # Update metrics
        $logContent = $logContent -replace "Lines Added: .*", "Lines Added: $($gitChanges.LinesAdded)"
        $logContent = $logContent -replace "Lines Modified: .*", "Lines Modified: N/A"
        $logContent = $logContent -replace "Lines Deleted: .*", "Lines Deleted: $($gitChanges.LinesDeleted)"
        $logContent = $logContent -replace "Files Changed: .*", "Files Changed: $($gitChanges.FilesChanged)"
        
        # Save updated log
        $logContent | Set-Content $logFile
    }
    
    # Prompt for additional log information if not skipped
    if (-not $SkipPrompt) {
        Write-Host "Please complete your development log at: $logFile"
        Write-Host "Be sure to fill in details about:
- Task context
- Implementation approach
- Challenges encountered
- Learnings and insights"
    }
    
    # Clear environment variables
    $env:LSR_SESSION_ID = $null
    $env:LSR_ISSUE_ID = $null
    $env:LSR_COMPONENT = $null
    
    Write-Host "Development session ended"
    Write-Host "Session duration: $([math]::Round($duration, 2)) hours"
    Write-Host "Session data saved to: $sessionFile"
    Write-Host "Log saved to: $logFile"
    
    # Generate weekly summary if it's Friday
    $today = (Get-Date).DayOfWeek
    if ($today -eq "Friday") {
        Write-Host "It's Friday! Generating weekly summary..."
        Invoke-WeeklySummary
    }
}

# Generate weekly summary
function Invoke-WeeklySummary {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)]
        [ValidateSet("Scanner", "Parser", "Standardizer", "Classifier", "CrossReferencer", "GUI", "Core", "Common", "All")]
        [string]$Component = "All",
        
        [Parameter(Mandatory = $false)]
        [DateTime]$StartDate = (Get-Date).AddDays(-7),
        
        [Parameter(Mandatory = $false)]
        [DateTime]$EndDate = (Get-Date)
    )
    
    Write-Host "Generating weekly summary for $Component from $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))..."
    
    # Create output directory if it doesn't exist
    $summaryDir = ".lsr/summaries/weekly"
    if (-not (Test-Path $summaryDir)) {
        New-Item -Path $summaryDir -ItemType Directory | Out-Null
    }
    
    # Get all sessions in the date range
    $sessions = @()
    $sessionFiles = Get-ChildItem -Path ".lsr/sessions" -Filter "*.json"
    
    foreach ($file in $sessionFiles) {
        $session = Get-Content $file.FullName | ConvertFrom-Json
        
        $sessionStart = [DateTime]::Parse($session.StartTime)
        if ($sessionStart -ge $StartDate -and $sessionStart -le $EndDate) {
            # Filter by component if specified
            if ($Component -eq "All" -or $session.Component -eq $Component) {
                $sessions += $session
            }
        }
    }
    
    if ($sessions.Count -eq 0) {
        Write-Host "No sessions found in the specified date range and component filter."
        return
    }
    
    # Aggregate metrics
    $metrics = @{
        TotalSessions = $sessions.Count
        TotalDuration = 0
        TaskTypes = @{}
        EstimationAccuracy = @{
            UnderEstimated = 0
            OverEstimated = 0
            CloseToEstimate = 0
        }
        LinesAdded = 0
        LinesDeleted = 0
        FilesChanged = 0
        Commits = 0
        Developers = @{}
        Components = @{}
    }
    
    foreach ($session in $sessions) {
        # Track duration
        $metrics.TotalDuration += $session.Duration
        
        # Track task types
        if ($session.TaskType) {
            if (-not $metrics.TaskTypes[$session.TaskType]) {
                $metrics.TaskTypes[$session.TaskType] = 0
            }
            $metrics.TaskTypes[$session.TaskType]++
        }
        
        # Track developers
        if ($session.Developer) {
            if (-not $metrics.Developers[$session.Developer]) {
                $metrics.Developers[$session.Developer] = 0
            }
            $metrics.Developers[$session.Developer]++
        }
        
        # Track components
        if ($session.Component) {
            if (-not $metrics.Components[$session.Component]) {
                $metrics.Components[$session.Component] = 0
            }
            $metrics.Components[$session.Component]++
        }
        
        # Track estimation accuracy
        if ($session.EstimatedHours -gt 0) {
            $variance = ($session.Duration - $session.EstimatedHours) / $session.EstimatedHours
            if ($variance -lt -0.2) {
                $metrics.EstimationAccuracy.OverEstimated++
            }
            elseif ($variance -gt 0.2) {
                $metrics.EstimationAccuracy.UnderEstimated++
            }
            else {
                $metrics.EstimationAccuracy.CloseToEstimate++
            }
        }
        
        # Aggregate Git changes
        if ($session.GitChanges) {
            $metrics.LinesAdded += $session.GitChanges.LinesAdded
            $metrics.LinesDeleted += $session.GitChanges.LinesDeleted
            $metrics.FilesChanged += $session.GitChanges.FilesChanged
            $metrics.Commits += $session.GitChanges.Commits
        }
    }
    
    # Generate markdown summary
    $summaryTemplate = @"
# Weekly Development Summary

## Overview

**Period:** $($StartDate.ToString('yyyy-MM-dd')) to $($EndDate.ToString('yyyy-MM-dd'))
**Component:** $Component
**Summary Generated:** $(Get-Date -Format "yyyy-MM-dd HH:mm")

## Activity Metrics

- **Total Sessions:** $($metrics.TotalSessions)
- **Total Development Hours:** $([math]::Round($metrics.TotalDuration, 2))
- **Active Developers:** $($metrics.Developers.Keys.Count)
- **Commits Made:** $($metrics.Commits)

## Task Distribution

$(
    $taskOutput = ""
    foreach ($task in $metrics.TaskTypes.Keys) {
        $percentage = [math]::Round(($metrics.TaskTypes[$task] / $metrics.TotalSessions) * 100, 1)
        $taskOutput += "- **$task:** $($metrics.TaskTypes[$task]) ($percentage%)`n"
    }
    $taskOutput
)

## Component Activity

$(
    $compOutput = ""
    if ($Component -eq "All") {
        foreach ($comp in $metrics.Components.Keys) {
            $percentage = [math]::Round(($metrics.Components[$comp] / $metrics.TotalSessions) * 100, 1)
            $compOutput += "- **$comp:** $($metrics.Components[$comp]) ($percentage%)`n"
        }
    }
    $compOutput
)

## Code Changes

- **Files Changed:** $($metrics.FilesChanged)
- **Lines Added:** $($metrics.LinesAdded)
- **Lines Deleted:** $($metrics.LinesDeleted)
- **Net Line Change:** $($metrics.LinesAdded - $metrics.LinesDeleted)

## Estimation Accuracy

- **Under-estimated Tasks:** $($metrics.EstimationAccuracy.UnderEstimated) ($([math]::Round(($metrics.EstimationAccuracy.UnderEstimated / $metrics.TotalSessions) * 100, 1))%)
- **Over-estimated Tasks:** $($metrics.EstimationAccuracy.OverEstimated) ($([math]::Round(($metrics.EstimationAccuracy.OverEstimated / $metrics.TotalSessions) * 100, 1))%)
- **Accurately Estimated Tasks:** $($metrics.EstimationAccuracy.CloseToEstimate) ($([math]::Round(($metrics.EstimationAccuracy.CloseToEstimate / $metrics.TotalSessions) * 100, 1))%)

## Developer Activity

$(
    $devOutput = ""
    foreach ($dev in $metrics.Developers.Keys) {
        $percentage = [math]::Round(($metrics.Developers[$dev] / $metrics.TotalSessions) * 100, 1)
        $devOutput += "- **$dev:** $($metrics.Developers[$dev]) sessions ($percentage%)`n"
    }
    $devOutput
)

## Key Issues Worked On

$(
    $issueOutput = ""
    $uniqueIssues = $sessions | Select-Object -Property IssueId -Unique
    foreach ($issue in $uniqueIssues) {
        $issueOutput += "- $($issue.IssueId)`n"
    }
    $issueOutput
)

## Next Steps

- Review detailed logs for pattern identification
- Update development standards based on findings
- Address estimation discrepancies
- Focus on knowledge sharing for identified gaps

## Appendix

**Sessions Included in Summary:**

$(
    $sessionOutput = ""
    foreach ($session in $sessions) {
        $sessionOutput += "- $($session.IssueId) - $($session.Component) - $($session.TaskType) - $([math]::Round($session.Duration, 2)) hours`n"
    }
    $sessionOutput
)
"@
    
    # Determine file name for the summary
    $fileName = "weekly_summary_$(Get-Date -Format 'yyyy-MM-dd').md"
    if ($Component -ne "All") {
        $fileName = "weekly_summary_${Component}_$(Get-Date -Format 'yyyy-MM-dd').md"
    }
    
    # Save the summary
    $summaryPath = Join-Path $summaryDir $fileName
    $summaryTemplate | Set-Content $summaryPath
    
    Write-Host "Weekly summary generated: $summaryPath"
    
    return $summaryPath
}

# Generate rule proposal based on patterns in summaries
function New-RuleProposal {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$RuleId,
        
        [Parameter(Mandatory = $true)]
        [string]$Title,
        
        [Parameter(Mandatory = $true)]
        [string]$Description,
        
        [Parameter(Mandatory = $true)]
        [ValidateSet("Hard Rule", "Guideline", "Pattern")]
        [string]$RuleType,
        
        [Parameter(Mandatory = $true)]
        [ValidateSet("Architecture", "Code Style", "Performance", "Security", "Testing", "Documentation", "Process")]
        [string]$Category,
        
        [Parameter(Mandatory = $false)]
        [string[]]$SourceSummaries,
        
        [Parameter(Mandatory = $false)]
        [string[]]$RelatedRules
    )
    
    Write-Host "Creating new rule proposal: $RuleId - $Title"
    
    # Create rules directory if it doesn't exist
    $rulesDir = ".lsr/rules/proposals"
    if (-not (Test-Path $rulesDir)) {
        New-Item -Path $rulesDir -ItemType Directory | Out-Null
    }
    
    # Get rule template
    $ruleTemplate = Get-Content -Path ".lsr/templates/RULE_TEMPLATE.md" -Raw -ErrorAction SilentlyContinue
    
    if (-not $ruleTemplate) {
        # Create basic template if none exists
        $ruleTemplate = @"
# Rule Template

## Rule Identification

**Rule ID:** [Component]-[Category]-[Sequential Number]  
**Title:** [Concise descriptive title]  
**Created:** [YYYY-MM-DD]  
**Last Modified:** [YYYY-MM-DD]  
**Author:** [Name]  

## Status

**Current Status:** [Draft/Review/Approved/Deprecated]  
**Version:** [x.y]  

## Classification

**Type:** [Hard Rule/Guideline/Pattern]  
**Category:** [Architecture/Code Style/Performance/Security/Testing/Documentation/Process]  
**Scope:** [System-wide/Component-specific]  
**Applicable Components:** [List of components]  

## Definition

### Summary
[One-sentence description of the rule]

### Detailed Description
[Comprehensive explanation of what the rule requires or prohibits]

### Context
[Conditions under which this rule applies, including environments, components, or situations]

## Rationale

### Problem Statement
[Description of the issue or challenge this rule addresses]

### Evidence
[Data points, observations, or summaries that support the need for this rule]

### Expected Benefits
[Specific improvements expected from following this rule]
"@
    }
    
    # Fill in the template with provided information
    $ruleContent = $ruleTemplate
    $ruleContent = $ruleContent -replace '\[Component\]-\[Category\]-\[Sequential Number\]', $RuleId
    $ruleContent = $ruleContent -replace '\[Concise descriptive title\]', $Title
    $ruleContent = $ruleContent -replace '\[YYYY-MM-DD\]', (Get-Date -Format "yyyy-MM-dd")
    $ruleContent = $ruleContent -replace '\[Name\]', $env:USERNAME
    $ruleContent = $ruleContent -replace '\[Draft/Review/Approved/Deprecated\]', "Draft"
    $ruleContent = $ruleContent -replace '\[x\.y\]', "0.1"
    $ruleContent = $ruleContent -replace '\[Hard Rule/Guideline/Pattern\]', $RuleType
    $ruleContent = $ruleContent -replace '\[Architecture/Code Style/Performance/Security/Testing/Documentation/Process\]', $Category
    $ruleContent = $ruleContent -replace '\[One-sentence description of the rule\]', $Description
    
    # Add source summaries if provided
    if ($SourceSummaries) {
        $evidenceSection = "### Evidence`n"
        foreach ($summary in $SourceSummaries) {
            $evidenceSection += "- $summary`n"
        }
        $ruleContent = $ruleContent -replace '### Evidence\n\[Data points, observations, or summaries that support the need for this rule\]', $evidenceSection
    }
    
    # Add related rules if provided
    if ($RelatedRules) {
        $relatedSection = "### Related Rules`n"
        foreach ($rule in $RelatedRules) {
            $relatedSection += "- $rule`n"
        }
        if ($ruleContent -match '### Related Rules\n\[.*?\]') {
            $ruleContent = $ruleContent -replace '### Related Rules\n\[.*?\]', $relatedSection
        }
    }
    
    # Save the rule proposal
    $ruleFileName = "${RuleId}.md"
    $rulePath = Join-Path $rulesDir $ruleFileName
    $ruleContent | Set-Content $rulePath
    
    Write-Host "Rule proposal created: $rulePath"
    
    return $rulePath
}

# Export all functions
Export-ModuleMember -Function Initialize-LSREnvironment, Get-ProjectMetrics, Start-DevSession, Add-DevEvent, End-DevSession, Invoke-WeeklySummary, New-RuleProposal 