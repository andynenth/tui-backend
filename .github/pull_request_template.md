## Pull Request Checklist

### Description
Brief description of changes and why they were made.

### Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

### Testing
- [ ] I have added unit tests for new functionality
- [ ] I have added integration tests if applicable  
- [ ] I have run the test suite locally and all tests pass
- [ ] I have tested the changes manually

### Code Quality
- [ ] My code follows the established style guidelines
- [ ] I have run `black .` for Python formatting
- [ ] I have run `npm run lint` for frontend linting
- [ ] I have run `pylint` on modified Python files
- [ ] I have run `npm run type-check` for TypeScript validation

### Performance
- [ ] Changes do not negatively impact performance
- [ ] I have considered the impact on the CI/CD pipeline runtime
- [ ] Performance tests pass (if applicable)

### Security
- [ ] No sensitive information is exposed in code or logs
- [ ] External dependencies are necessary and from trusted sources
- [ ] Changes follow security best practices

### Documentation
- [ ] I have updated relevant documentation
- [ ] Code comments are clear and necessary
- [ ] CLAUDE.md has been updated if development processes changed

### Related Issues
Closes #(issue number)

### Screenshots (if applicable)
Add screenshots for UI changes

### Additional Notes
Any additional information that reviewers should know.

---

## For Reviewers

### Test Commands
```bash
# Backend tests
cd backend
source venv/bin/activate
pytest tests/unit/ -v
pytest tests/integration/ -v

# Frontend tests  
cd frontend
npm test
npm run lint
npm run type-check
```

### What to Review
- [ ] Code quality and style consistency
- [ ] Test coverage for new functionality
- [ ] Security implications
- [ ] Performance impact
- [ ] Documentation accuracy