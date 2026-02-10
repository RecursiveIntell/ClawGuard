rule curl_pipe_bash {
    meta:
        author = "ClawGuard"
        description = "Curl or wget piped to shell interpreter"
        severity = "critical"
        category = "social_engineering"
    strings:
        $curl_bash1 = "curl" ascii
        $curl_bash2 = "| bash" ascii
        $curl_sh = "| sh" ascii
        $curl_sudo_bash = "| sudo bash" ascii
        $curl_sudo_sh = "| sudo sh" ascii
        $wget = "wget" ascii
    condition:
        ($curl_bash1 or $wget) and ($curl_bash2 or $curl_sh or $curl_sudo_bash or $curl_sudo_sh)
}

rule chmod_downloaded {
    meta:
        author = "ClawGuard"
        description = "Making downloaded files executable"
        severity = "high"
        category = "social_engineering"
    strings:
        $chmod_x = "chmod +x" ascii
        $chmod_7 = "chmod 755" ascii
        $chmod_777 = "chmod 777" ascii
    condition:
        any of them
}

rule disable_security {
    meta:
        author = "ClawGuard"
        description = "Instructions to disable security features"
        severity = "high"
        category = "social_engineering"
    strings:
        $disable1 = "disable security" nocase
        $disable2 = "turn off antivirus" nocase
        $disable3 = "disable firewall" nocase
        $disable4 = "--no-verify" nocase
        $disable5 = "security.allowUnsafe" nocase
    condition:
        any of them
}
