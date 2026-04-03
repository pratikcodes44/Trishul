# Contributing to Project Trishul

Thank you for your interest in contributing! 🔱

## How to Contribute

### Reporting Bugs
1. Check existing [Issues](../../issues) to avoid duplicates
2. Create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version, tool versions)

### Feature Requests
1. Open an issue with the `enhancement` label
2. Describe the feature and its use case
3. Discuss implementation approach

### Pull Requests
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python scope_checker.py` (runs built-in assertions)
5. Commit with clear messages: `git commit -m "Add amazing feature"`
6. Push and create a Pull Request

## Code Style

- Use Python type hints
- Follow PEP 8 guidelines
- Add docstrings to public methods
- Keep functions focused and small

## Security

⚠️ **NEVER commit:**
- API keys or tokens
- Webhook URLs
- Database files with real recon data
- Any credentials

Use environment variables via `.env` (see `.env.example`).

## Testing Locally

```bash
# Start the test server
python vulnerable_arena.py

# In another terminal, run against localhost
python main.py -d 127.0.0.1 -y
```

## Questions?

Open a Discussion or reach out to maintainers.
