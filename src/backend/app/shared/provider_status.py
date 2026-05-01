from typing import Literal, List, Optional

ProviderRunStatus = Literal["completed", "missing_credential", "provider_error"]


def provider_warning(status: ProviderRunStatus, provider: str) -> Optional[str]:
    if status == "missing_credential":
        return f"missing_credential:{provider}"
    if status == "provider_error":
        return f"provider_error:{provider}"
    return None


def record_provider_warning(
    warnings: List[str],
    status: ProviderRunStatus,
    provider: str,
) -> Optional[str]:
    warning = provider_warning(status, provider)
    if warning is not None and warning not in warnings:
        warnings.append(warning)
    return warning
