# VideoJockey Password Reset Utility

A command-line utility for resetting user passwords in VideoJockey without requiring email access.

## Overview

This standalone console application allows administrators with direct server access to reset user passwords. Since VideoJockey uses username-only authentication (no email), this utility provides a secure way to recover accounts when users forget their passwords.

## Prerequisites

- .NET 9.0 or later
- Access to the VideoJockey database file (`videojockey.db`)
- The VideoJockey web application should be stopped before running this utility

## Building

From the solution root directory:

```bash
dotnet build VideoJockey.PasswordReset/VideoJockey.PasswordReset.csproj
```

Or build the entire solution:

```bash
dotnet build
```

## Usage

### Basic Usage

```bash
VideoJockey.PasswordReset --username <username> --password <newpassword>
```

### With Custom Database Path

```bash
VideoJockey.PasswordReset --username admin --password NewSecurePass123 --database /path/to/videojockey.db
```

## Command-Line Options

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--username` | `-u` | Username of the account to reset | Yes |
| `--password` | `-p` | New password (minimum 8 characters) | Yes |
| `--database` | `-d` | Path to videojockey.db file | No* |
| `--help` | `-h` | Show help message | No |

*If not specified, the utility will attempt to locate the database in the default location relative to the web application.

## Password Requirements

- Minimum length: 8 characters
- No other complexity requirements (configurable in Identity settings)

## Examples

### Reset admin password:
```bash
VideoJockey.PasswordReset -u admin -p MyNewPassword2024
```

### Reset user password with explicit database path:
```bash
VideoJockey.PasswordReset \
  --username jdoe \
  --password SecurePass123! \
  --database /var/videojockey/data/videojockey.db
```

### Display help:
```bash
VideoJockey.PasswordReset --help
```

## Output

The utility provides colored console output indicating the status of the operation:

- **Green**: Success messages
- **Red**: Error messages
- **White**: Informational messages

Example output:
```
VideoJockey Password Reset Utility
===================================

Database: /path/to/videojockey.db
Username: admin

Looking up user... FOUND
Display Name: Administrator
User ID: 12345678-1234-1234-1234-123456789abc
Account Status: Active

Resetting password... SUCCESS

Password has been reset for user 'admin'.
The user can now sign in with the new password.
```

## Exit Codes

- `0`: Success
- `1`: Error (user not found, invalid password, database error, etc.)

## Security Considerations

1. **Physical/SSH Access Required**: This utility should only be accessible to administrators with direct server access
2. **Not Exposed via Web**: This tool is intentionally separate from the web application
3. **Database Access**: Requires read/write access to the SQLite database
4. **Password in Command Line**: Be aware that passwords passed as command-line arguments may be visible in process lists or shell history
5. **Stop the Web App**: For safety, stop the VideoJockey web application before running this utility to prevent database locking issues

## Troubleshooting

### Database Not Found
If you see "Database not found" error, specify the full path using the `--database` option:
```bash
VideoJockey.PasswordReset -u admin -p newpass -d /full/path/to/videojockey.db
```

### User Not Found
Verify the username is correct. Usernames are case-sensitive.

### Database Locked
Stop the VideoJockey web application before running this utility.

### Permission Denied
Ensure you have read/write permissions to the database file.

## Integration with System

This utility can be integrated into system administration workflows:

### Shell Script Wrapper
```bash
#!/bin/bash
# reset-vj-password.sh

if [ $# -lt 2 ]; then
    echo "Usage: $0 <username> <password>"
    exit 1
fi

sudo systemctl stop videojockey
dotnet /opt/videojockey/VideoJockey.PasswordReset.dll -u "$1" -p "$2"
sudo systemctl start videojockey
```

### Systemd Service (Optional)
You could create a restricted systemd service that allows password resets without full system access.

## Development

This utility uses the same data access layer as the main VideoJockey application:
- `VideoJockey.Core`: Entity definitions
- `VideoJockey.Data`: Database context and repositories
- ASP.NET Core Identity: User management and password hashing

## License

This utility is part of the VideoJockey project and uses the same license.