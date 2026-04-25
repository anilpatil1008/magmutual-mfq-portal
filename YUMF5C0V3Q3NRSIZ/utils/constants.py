APP_NAME = "MagMutual MFQ Portal"
DEFAULT_ROLE = "Claim Analyst"
ROLES = ["Claim Analyst", "Advice Team", "Medical Faculty", "Admin", "Executive"]

CLAIM_STATUSES = ["MFQ Generated", "Assigned", "Approved", "Rejected"]
PRIORITIES = ["Critical", "High", "Medium", "Low"]

NAV_ITEMS = [
    "Dashboard",
    "Claims",
    "Claim Details",
    "Reports & Analytics",
]

STATUS_COLORS = {
    "Approved": "badge-success",
    "Assigned": "badge-info",
    "MFQ Generated": "badge-mfq",
    "Rejected": "badge-danger",
}

PRIORITY_COLORS = {
    "Critical": "badge-danger",
    "High": "badge-warning",
    "Medium": "badge-primary",
    "Low": "badge-muted",
}

REGEN_TOOLTIP = "New version of MFQ Form is generated. To reflect the latest data click on Regenerate button."
