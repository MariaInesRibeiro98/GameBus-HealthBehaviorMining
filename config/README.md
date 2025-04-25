# Configuration Files

This directory contains configuration files for the GameBus-HealthBehaviorMining project.

## Files

- `credentials.py`: API credentials and endpoints
- `paths.py`: File paths used throughout the project
- `settings.py`: General settings and constants

## Important Note

The configuration files will try to import sensitive data from the `secret` folder for backward compatibility. If these imports fail, default values will be used.

## For Development

To set up your development environment:

1. Create a copy of the secret folder if you have access to it, or create your own with the following structure:

```
secret/
├── __init__.py
├── auth.py          # Contains authcode variable
├── users.py         # Contains GB_users_path variable
└── output.py        # Contains output_path variable
```

2. The content of these files should be:

`auth.py`:
```python
authcode = "your_gamebus_auth_code_here"
```

`users.py`:
```python
GB_users_path = "path/to/your/users.csv"
```

`output.py`:
```python
output_path = "path/to/your/output/directory"
```

3. The users CSV file must be in the correct format:
   - It must include a header row with exact column names: `Username;Password` (note the capital 'U')
   - The delimiter must be a semicolon (`;`)
   - Example:
     ```
     Username;Password
     user@example.com;password123
     ```

4. If you don't have the secret files, the config will use sensible defaults:
   - Users file will be expected at `config/users.csv`
   - Output will go to `data/raw/`
   - You'll need to provide your own auth code in `config/credentials.py`

## Git Behavior

These configuration files are tracked by Git, but their content (especially CSV files with credentials) is ignored through `.gitignore` rules. This allows the structure to be shared while keeping sensitive data private. 