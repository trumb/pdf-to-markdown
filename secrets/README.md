# Secrets Directory

This directory is for storing sensitive configuration files and credentials that should **NEVER** be committed to source control.

## ⚠️ Security Notice

- This directory is excluded from Git via `.gitignore`
- Only `.gitkeep` and this `README.md` are tracked
- All other files in this directory will be ignored

## 📂 What Goes Here

### Development
- `.env` files with local credentials
- Service account JSON files
- API keys for testing
- Local database credentials

### Production (via deployment scripts)
- Cloud storage credentials
- Database connection strings
- API tokens
- Certificate private keys

## 🔒 Best Practices

1. **Never commit secrets** - Always use environment variables or secret managers
2. **Use `.env.example`** - Create example files with placeholder values
3. **Rotate credentials** - Change secrets regularly
4. **Limit scope** - Use minimum required permissions
5. **Audit access** - Log and monitor secret usage

## 📝 Example Structure

```
secrets/
├── .gitkeep              # Tracked
├── README.md             # Tracked
├── .env                  # Ignored - local development
├── azure-credentials.json # Ignored - cloud credentials
├── gcp-service-account.json # Ignored
└── aws-credentials       # Ignored
```

## 🚨 If You Committed a Secret

1. **Rotate immediately** - Invalidate the compromised credential
2. **Remove from history** - Use `git filter-branch` or BFG Repo-Cleaner
3. **Notify team** - Alert relevant parties
4. **Review access logs** - Check for unauthorized usage

## 📖 References

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP: Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)