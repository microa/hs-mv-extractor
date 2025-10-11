# Contributing to hs-mv-extractor

Thank you for your interest in contributing to hs-mv-extractor! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- FFmpeg
- Git

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/your-username/hs-mv-extractor.git
cd hs-mv-extractor

# Install core dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e ./hs-mv-extractor/
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest test/ -v

# Run with coverage
python -m pytest test/ -v --cov=hs-mv-extractor

# Run performance benchmarks
python scripts/evaluation.py
```

### Test Coverage
We aim for >90% test coverage. Please ensure your contributions include appropriate tests.

## 📝 Code Style

### Python Code
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions
- Keep functions small and focused

### C++ Code
- Follow Google C++ Style Guide
- Use meaningful variable names
- Add comments for complex logic
- Ensure proper error handling

## 🔧 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code following the style guidelines
- Add tests for new functionality
- Update documentation if needed

### 3. Test Your Changes
```bash
# Run tests
python -m pytest test/ -v

# Run performance benchmarks
python scripts/evaluation.py

# Check code style
black --check .
flake8 .
mypy hs-mv-extractor/
```

### 4. Commit Changes
```bash
git add .
git commit -m "Add: brief description of changes"
```

### 5. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
```

## 📋 Pull Request Guidelines

### Before Submitting
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Performance benchmarks show no regression
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Performance benchmarks pass
- [ ] Manual testing completed

## Performance Impact
- [ ] No performance impact
- [ ] Performance improvement
- [ ] Performance regression (explain)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment details**:
   - OS and version
   - Python version
   - Package versions

2. **Steps to reproduce**:
   - Clear, numbered steps
   - Expected vs actual behavior

3. **Error messages**:
   - Full error traceback
   - Log files if available

4. **Additional context**:
   - Screenshots if applicable
   - Related issues

## 🚀 Feature Requests

When requesting features, please include:

1. **Use case description**:
   - What problem does this solve?
   - How would you use this feature?

2. **Proposed solution**:
   - How should this work?
   - Any implementation ideas?

3. **Alternatives considered**:
   - Other ways to solve this problem
   - Why this approach is preferred

## 📚 Documentation

### Code Documentation
- Write clear docstrings for all public functions
- Include type hints
- Add inline comments for complex logic
- Update README.md for new features

### API Documentation
- Document all public APIs
- Include usage examples
- Explain parameters and return values
- Update performance benchmarks

## 🔄 Release Process

### Version Numbering
We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] All tests pass
- [ ] Performance benchmarks updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] Release notes prepared

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the golden rule

### Communication
- Use clear, descriptive commit messages
- Write helpful pull request descriptions
- Respond to feedback promptly
- Ask questions when unsure

## 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/microa/hs-mv-extractor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/microa/hs-mv-extractor/discussions)
- **Email**: [Your Email]

## 🙏 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to hs-mv-extractor! 🎉