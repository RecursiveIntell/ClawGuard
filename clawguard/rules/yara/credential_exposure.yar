rule aws_access_key {
    meta:
        author = "ClawGuard"
        description = "AWS access key identifier"
        severity = "high"
        category = "credential_exposure"
    strings:
        $aws_key = /AKIA[0-9A-Z]{16}/
    condition:
        $aws_key
}

rule github_token {
    meta:
        author = "ClawGuard"
        description = "GitHub personal access token or app token"
        severity = "high"
        category = "credential_exposure"
    strings:
        $ghp = "ghp_"
        $gho = "gho_"
        $ghu = "ghu_"
        $ghs = "ghs_"
        $ghr = "ghr_"
    condition:
        any of them
}

rule generic_api_key {
    meta:
        author = "ClawGuard"
        description = "Generic API key or secret key pattern"
        severity = "high"
        category = "credential_exposure"
    strings:
        $api_key1 = /api[_-]?key\s*[=:]\s*["\'][a-zA-Z0-9]{16,}["\']/i
        $secret_key = /secret[_-]?key\s*[=:]\s*["\'][a-zA-Z0-9]{16,}["\']/i
        $sk_live = /sk-[a-zA-Z0-9]{20,}/
    condition:
        any of them
}

rule bearer_token {
    meta:
        author = "ClawGuard"
        description = "Bearer or Basic authentication token in code"
        severity = "high"
        category = "credential_exposure"
    strings:
        $bearer = /Bearer\s+[a-zA-Z0-9_\-\.]{20,}/
        $basic = /Basic\s+[a-zA-Z0-9+\/=]{20,}/
    condition:
        any of them
}

rule private_key {
    meta:
        author = "ClawGuard"
        description = "Private key embedded in file"
        severity = "critical"
        category = "credential_exposure"
    strings:
        $pem = "-----BEGIN" ascii
        $private = "PRIVATE KEY-----" ascii
    condition:
        $pem and $private
}

rule env_file_access {
    meta:
        author = "ClawGuard"
        description = "Accessing .env files or broad environment variable harvesting"
        severity = "high"
        category = "credential_exposure"
    strings:
        $dotenv_cat = /cat\s+.*\.env/
        $dotenv_read = /open\s*\(\s*[\"'].*\.env[\"']/
        $env_dump = /env\s*>\s*/
        $printenv = "printenv"
        $os_environ_full = "os.environ" ascii
        $process_env = "process.env" ascii
    condition:
        any of them
}
