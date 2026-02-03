# Contributing to Spotify Statistics Integration

Thank you for your interest in contributing to the Spotify Statistics integration for Home Assistant!

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Test your changes thoroughly
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Home Assistant development environment
- Spotify Developer account with API credentials

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/ianpleasance/home-assistant-spotify-stats.git
cd hass-spotify-stats

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_dev.txt
```

### Testing

To test your changes:

1. Copy the `custom_components/spotify_stats` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Configure the integration through the UI
4. Test all functionality

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Add docstrings to all classes and functions
- Keep line length to 88 characters (Black formatter default)

We use the following tools for code quality:
- `black` for code formatting
- `isort` for import sorting
- `pylint` for code linting
- `mypy` for type checking

## Pull Request Process

1. **Update Documentation**: Ensure README.md and other docs reflect any changes
2. **Update Changelog**: Add your changes to CHANGELOG.md under "Unreleased"
3. **Test Thoroughly**: Test all affected functionality
4. **Describe Changes**: Write a clear PR description explaining what and why
5. **Reference Issues**: Link any related issues in your PR description

## Reporting Bugs

When reporting bugs, please include:

- Home Assistant version
- Integration version
- Detailed steps to reproduce
- Expected behavior
- Actual behavior
- Relevant log excerpts (with sensitive info removed)

Use the GitHub issue template for bug reports.

## Requesting Features

Feature requests are welcome! Please:

- Check existing issues first to avoid duplicates
- Clearly describe the feature and its use case
- Explain why it would be useful to other users
- Consider contributing the implementation yourself

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Prioritize the community's well-being

## Questions?

Feel free to:
- Open a discussion on GitHub
- Comment on existing issues
- Reach out to the maintainers

Thank you for contributing!
