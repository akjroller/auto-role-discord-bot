# Example configuration for role assignments based on the number of days in the server
role_assignments = [
    {"days": 0, "role_name": "New Member"},  # 0 days (default for new members)
    {"days": 30, "role_name": "Member"},  # 1 month
    {"days": 180, "role_name": "Veteran Member"},  # 6 months
    {"days": 365, "role_name": "Senior Member"},  # 1 year
]
