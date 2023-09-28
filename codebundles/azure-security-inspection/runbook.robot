*** Settings ***
Documentation       Performs a secuirty pass on azure infrastructure in a given tenancy.
Metadata            Author    jon-funk
Metadata            Display Name    Azure Security Inspection
Metadata            Supports    Azure

Library             BuiltIn
Library             RW.Core
Library             RW.CLI
Library             RW.platform
Library             OperatingSystem

Suite Setup         Suite Initialization


*** Tasks ***
Run Azure Security Checks On Tenancy
    [Documentation]    Performs a suite of security checks on Azure infrastructure
    [Tags]    azure    security    compliance
    ${sec_report}=    RW.CLI.Run Cli
    ...    cmd=export PATH="$PATH:$HOME/.steampipe:$HOME/.local/bin:/usr/local/bin/steampipe" && cat azure_connection_spec > ~/.steampipe/config/azure.spc && cat azuread_connection_spec > ~/.steampipe/config/azuread.spc && cd /tmp && git clone https://github.com/turbot/steampipe-mod-azure-compliance.git || true && cd steampipe-mod-azure-compliance && steampipe check benchmark.cis_v130 --export ../report.json
    ...    secret_file__azure_connection_spec=${azure_connection_spec}
    ...    secret_file__azuread_connection_spec=${azuread_connection_spec}
    ${has_errors}=    RW.CLI.Run Cli
    ...    cmd=cat /tmp/report.json | jq -r '.summary.status.error > 0'
    RW.CLI.Parse Cli Output By Line
    ...    rsp=${has_errors}
    ...    set_severity_level=1
    ...    set_issue_expected=No compliance or security errors in Azure tenancy.
    ...    set_issue_actual=Found compliance / security violations in Azure tenancy
    ...    set_issue_title=Azure Security Errors Detected
    ...    set_issue_details=Azure tenant has security errors.
    ...    set_issue_next_steps=Review triage report and submit infrastructure & security change requests.
    ...    _line__raise_issue_if_contains=true
    ${history}=    RW.CLI.Pop Shell History
    RW.Core.Add Pre To Report    Security Report:\n\n${sec_report.stdout}
    RW.Core.Add Pre To Report    Commands Used:\n${history}


*** Keywords ***
Suite Initialization
    ${azure_connection_spec}=    RW.Core.Import Secret    azure_connection_spec
    ...    type=string
    ...    description=The HCL connection specification for the azure account to be used to authenticate.
    ...    pattern=\w*
    ${azuread_connection_spec}=    RW.Core.Import Secret    azuread_connection_spec
    ...    type=string
    ...    description=The HCL connection specification azuread to be used to authenticate.
    ...    pattern=\w*
    Set Suite Variable    ${azure_connection_spec}    ${azure_connection_spec}
    Set Suite Variable    ${azuread_connection_spec}    ${azuread_connection_spec}
