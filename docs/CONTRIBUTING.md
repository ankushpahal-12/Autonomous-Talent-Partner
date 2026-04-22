# Contributing Guide

Thank you for your interest in contributing to the Talent Partner project! This guide outlines how to contribute code, report issues, and improve the project.

## Table of Contents

- Community and Code of Conduct
- Getting Started
- Development Workflow
- Code Style Guidelines
- Commit Message Conventions
- Pull Request Process
- Testing Requirements
- Issue Reporting
- Documentation
- Performance and Security
- Getting Help

---

## Community and Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing opinions and experience levels
- Accept constructive criticism gracefully
- Focus on criticizing ideas, not people
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or offensive language
- Unwelcome sexual attention or comments
- Trolling, insulting comments, or personal attacks
- Publishing private information without consent
- Other conduct unsafe or disruptive to the community

### Reporting Issues

If you witness unacceptable behavior, contact the project maintainers privately at: [maintainer-email]

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ and npm 9+
- Git
- MongoDB Atlas account or local MongoDB
- Google Cloud account with Generative AI API enabled

### Development Environment Setup

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/talent-partner.git
   cd talent-partner
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/talent-partner.git
   ```

4. Create virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

5. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   
   # Frontend
   cd ../frontend
   npm install
   ```

6. Configure environment:
   ```bash
   # Copy template
   cp backend/.env.example backend/.env
   
   # Edit .env with your credentials
   # MONGO_URI=your_mongodb_uri
   # GOOGLE_API_KEY=your_api_key
   ```

7. Test setup:
   ```bash
   # Backend test
   cd backend
   python test_mongodb_connection.py
   
   # Frontend test
   cd ../frontend
   npm run dev
   ```

---

## Development Workflow

### Branch Naming

Use descriptive branch names following conventions:

```
feature/feature-description         # New features
bugfix/bug-description              # Bug fixes
improvement/improvement-description # Code improvements
docs/documentation-type             # Documentation updates
test/test-description               # Test additions
refactor/component-name             # Refactoring
```

Examples:
```
feature/ai-job-suggestions
bugfix/mongodb-connection-ssl
improvement/api-response-caching
docs/setup-guide-update
```

### Creating a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make focused, logical commits
2. Write clear commit messages (see Commit Conventions)
3. Test your changes thoroughly
4. Keep your branch updated:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

---

## Code Style Guidelines

### Python (Backend)

#### PEP 8 Compliance

- Line length: 100 characters (soft limit), 120 (hard limit)
- Indentation: 4 spaces
- Imports: Organize as standard library, third-party, local
- Naming conventions:
  - Functions/variables: snake_case
  - Classes: PascalCase
  - Constants: UPPER_SNAKE_CASE

#### Code Example

```python
# Imports organized properly
import asyncio
from typing import Optional, List

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


# Constants in UPPER_SNAKE_CASE
DEFAULT_TIMEOUT_MS = 5000
MAX_CONNECTIONS = 50


class JobService:
    """Service for job-related operations."""
    
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db_client = db_client
        self.collection = db_client.db.jobs
    
    async def create_job(self, job_data: dict) -> dict:
        """
        Create a new job posting.
        
        Args:
            job_data: Job information dictionary
            
        Returns:
            Created job document with ID
            
        Raises:
            ValueError: If required fields missing
        """
        if not job_data.get("job_title"):
            raise ValueError("job_title is required")
        
        result = await self.collection.insert_one(job_data)
        return {"id": str(result.inserted_id), **job_data}


# Use type hints
async def process_candidates(
    job_id: str,
    candidates: List[dict],
    threshold: float = 0.8
) -> Optional[List[dict]]:
    """Process and filter candidates based on match score."""
    pass
```

#### Best Practices

- Add docstrings to all functions and classes
- Use type hints for parameters and return values
- Keep functions focused and under 50 lines when possible
- Handle exceptions explicitly, not with bare except
- Use f-strings for formatting: f"Welcome {name}"
- Use async/await for I/O operations
- Add logging at appropriate levels

#### Linting and Formatting

```bash
# Install tools
pip install black flake8 mypy

# Format code
black backend/

# Check style
flake8 backend/
mypy backend/
```

### JavaScript/React (Frontend)

#### ESLint Standards

- Use eslint.config.js for rules
- Indent: 2 spaces
- Semicolons: Required
- Quotes: Single quotes for strings
- Line length: 100 characters (soft), 120 (hard)
- Curly braces: Always use (even single-line)

#### Code Example

```javascript
// Imports organized
import React, { useState, useEffect } from 'react';
import { JobCard } from '@/components/JobCard';
import { fetchJobs } from '@/api/jobs';
import { useNotification } from '@/hooks/useNotification';

// Constants capitalized
const DEFAULT_PAGE_SIZE = 10;
const POLLING_INTERVAL_MS = 5000;

// Functional component with hooks
const JobList = ({ companylFilter = null }) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const { showNotification } = useNotification();

  useEffect(() => {
    const loadJobs = async () => {
      try {
        setLoading(true);
        const response = await fetchJobs({ company: companyFilter });
        setJobs(response.data);
      } catch (error) {
        showNotification({
          type: 'error',
          message: 'Failed to load jobs',
        });
      } finally {
        setLoading(false);
      }
    };

    loadJobs();
  }, [companyFilter, showNotification]);

  return (
    <div>
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
};

export default JobList;
```

#### Best Practices

- Use functional components with hooks
- Keep components focused (single responsibility)
- Extract reusable logic into custom hooks
- Use prop destructuring
- Add propTypes or TypeScript for prop validation
- Keep JSX clear and readable
- Use meaningful variable and function names

### CSS/Styling

- Use responsive design with breakpoints: 480px, 768px, 1024px, 1280px
- Organize styles logically
- Use consistent spacing and colors
- Prefer CSS variables for theming
- Keep specificity low

---

## Commit Message Conventions

### Format

```
type(scope): subject

body

footer
```

### Type

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting, missing semicolons)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding or updating tests
- `chore`: Build process, dependencies
- `ci`: CI/CD configuration

### Scope

Optional, indicates affected component:
- `api`, `auth`, `job`, `candidate`, `ai`, `db`, `ui`, `frontend`, `backend`

### Subject

- Imperative mood: "add", not "added"
- No period at the end
- Maximum 50 characters
- Clear and descriptive

### Body

- Explain what and why, not how
- Wrap at 72 characters
- Separate from subject with blank line
- Include any breaking changes

### Footer

Reference issues:
```
Fixes #123
Relates to #456
Breaking change: DESCRIPTION
```

### Examples

```
feat(job): add AI suggestion feature

Implement AI-powered job requirement suggestions using Google Gemini API.
Added suggestion caching to reduce API calls. Suggestions are stored with
the job and can be reviewed before applying.

Fixes #89
```

```
fix(api): handle MongoDB connection timeout

Increase connection timeout to 10 seconds to handle slow network
conditions. Add retry logic for transient connection failures.

Related to #45
```

```
docs: update setup guide with MongoDB Atlas instructions
```

---

## Pull Request Process

### Before Submitting

1. Update your branch with latest changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. Run all tests:
   ```bash
   # Backend
   cd backend
   pytest
   
   # Frontend
   cd frontend
   npm test
   ```

3. Check code quality:
   ```bash
   # Backend
   black --check backend/
   flake8 backend/
   
   # Frontend
   npm run lint
   ```

4. Update documentation if needed

### Creating Pull Request

1. Push your branch:
   ```bash
   git push origin feature/your-feature
   ```

2. Go to GitHub and create PR
3. Fill in PR title (use same format as commits)
4. Include description:
   - What does this fix/add?
   - Why is this change needed?
   - How was this tested?
   - Any breaking changes?
   - Links to related issues/PRs

### PR Template

```markdown
## Description
<!-- Clear description of changes -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added
- [ ] Integration tests passed
- [ ] Manual testing completed
- [ ] No new warnings

## Checklist
- [ ] Code follows style guidelines
- [ ] Commits have good messages
- [ ] Documentation updated
- [ ] No debug code or comments
- [ ] Performance impact minimal

## Screenshots (if applicable)
<!-- Add before/after screenshots -->

## Related Issues
Fixes #123
Relates to #456
```

### Review Process

1. At least one maintainer review required
2. All CI checks must pass
3. Address reviewer comments
4. Request re-review after changes
5. Squash commits if needed:
   ```bash
   git rebase -i HEAD~3  # Last 3 commits
   ```

---

## Testing Requirements

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_job_service.py

# Run specific test
pytest tests/test_job_service.py::test_create_job
```

### Test Structure

```python
# tests/test_job_service.py
import pytest
from app.services.job_service import JobService

@pytest.fixture
async def job_service(mongo_client):
    """Fixture for job service."""
    return JobService(mongo_client)

class TestJobService:
    """Test cases for JobService."""
    
    async def test_create_job_success(self, job_service):
        """Test successful job creation."""
        job_data = {
            "company": "Tech Co",
            "job_title": "Developer"
        }
        result = await job_service.create_job(job_data)
        assert result["company"] == "Tech Co"
        assert "id" in result
    
    async def test_create_job_missing_title(self, job_service):
        """Test job creation fails without title."""
        with pytest.raises(ValueError):
            await job_service.create_job({"company": "Tech Co"})
```

### Frontend Tests

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

### Coverage Requirements

- Backend: Minimum 75% coverage
- Frontend: Minimum 70% coverage
- Critical paths: 90%+ coverage

---

## Issue Reporting

### Bug Report Template

```markdown
## Description
Brief description of the bug.

## Steps to Reproduce
1. Step one
2. Step two
3. Expected behavior
4. Actual behavior

## Environment
- OS: [e.g., Windows 10, macOS 12]
- Python/Node version: [version]
- Browser: [Chrome 100]

## Screenshots
[If applicable]

## Additional Context
[Any other relevant information]
```

### Feature Request Template

```markdown
## Description
What feature would you like?

## Problem Statement
What problem does this solve?

## Proposed Solution
How should this be implemented?

## Alternatives
Other solutions considered?

## Additional Context
Any other relevant information?
```

---

## Documentation

### Code Documentation

- Every function/class needs a docstring
- Include parameters, return types, exceptions
- Add examples for complex functions

```python
def calculate_match_score(
    candidate_skills: List[str],
    job_requirements: List[str],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate match score between candidate and job.
    
    Uses fuzzy matching to compare skills against requirements.
    Supports weighted scoring for priority requirements.
    
    Args:
        candidate_skills: List of candidate's skills
        job_requirements: List of job requirements
        weights: Optional weights for requirements (0.0-1.0)
        
    Returns:
        Match score between 0.0 and 1.0
        
    Raises:
        ValueError: If skills or requirements are empty
        
    Example:
        >>> score = calculate_match_score(
        ...     ['Python', 'FastAPI'],
        ...     ['Python', 'REST APIs'],
        ...     {'Python': 1.0}
        ... )
        >>> score
        0.85
    """
    if not candidate_skills or not job_requirements:
        raise ValueError("Skills and requirements cannot be empty")
    
    # Implementation...
    return score
```

### Documentation Files

Update relevant documentation when:
- Adding new features
- Changing API behavior
- Fixing significant bugs
- Improving performance
- Adding configuration options

---

## Performance and Security

### Performance Guidelines

- Avoid N+1 queries (use aggregation pipelines)
- Cache expensive operations
- Use connection pooling
- Minimize database round trips
- Monitor API response times
- Optimize bundle size for frontend

### Security Guidelines

- Never commit secrets (.env files)
- Validate all user input
- Sanitize database queries
- Use HTTPS in production
- Implement rate limiting
- Add CORS restrictions
- Validate file uploads
- Use secure password hashing
- Implement proper authentication

---

## Getting Help

### Resources

- Documentation: See docs/ folder
- Issues: Search existing issues first
- Discussions: Start a GitHub discussion
- Email: [maintainer-email]

### Questions

- Check TROUBLESHOOTING.md for common issues
- Search existing issues and discussions
- Ask in a GitHub discussion (not issues)

### Contact

- Report security issues privately
- General questions: GitHub Discussions
- Code review questions: In PR comments

---

## Recognition

Contributing to this project means:
- Your efforts help hundreds of users
- You'll be recognized in release notes
- Your code goes into production
- You help shape the project's future

Thank you for contributing!

---

Last Updated: April 2026
