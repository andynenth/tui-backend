# Portfolio Project Brief for Claude Code

## Project Context & Purpose

### Why This Portfolio Exists
I'm a full-stack developer who has built a production-ready multiplayer game (Liap Tui) deployed on AWS. I need a professional portfolio website to:

1. **Showcase Technical Skills**
   - Full-stack development (Python/FastAPI + React)
   - Real-time WebSocket applications
   - AWS deployment and DevOps
   - System architecture and state machines

2. **Professional Presence**
   - Central hub for potential employers/clients
   - Demonstrate project progression from idea → production
   - Show ability to ship complete products

3. **Project Documentation**
   - Liap Tui game (live and playable)
   - Future projects (currently in planning/mockup stage)
   - Technical blog posts about challenges solved

### Current Situation
- **Existing**: Liap Tui game running on EC2 (http://34.233.7.20)
- **Need**: Portfolio site to showcase this and future projects
- **Budget**: Must stay within AWS free tier (<$1/month)
- **Timeline**: MVP in 1 week, progressive updates over 2 months

## Portfolio Structure & Content

### 1. Hero Section
```
"Hi, I'm [Your Name]"
"Full-Stack Developer specializing in real-time multiplayer applications"
[Links to: GitHub | LinkedIn | Resume | Contact]
```

### 2. Featured Project: Liap Tui
```
LIVE PROJECT
- Screenshot/GIF of gameplay
- "Traditional Thai-Chinese board game brought to the web"
- Tech stack badges: Python, FastAPI, React, WebSocket, AWS
- Links: [Play Game] [View Code] [Read Case Study]
- Metrics: "4-player real-time | <100ms latency | 99.9% uptime"
```

### 3. Upcoming Projects (70% of content)
```
COMING SOON sections with:
- Project name and concept
- Planned tech stack
- Expected timeline
- "Notify me when launched" button
```

Example projects to include:
- **AI Writing Assistant** (Coming March 2024)
  - GPT-4 integration, Chrome extension
  - Tech: TypeScript, React, OpenAI API

- **DevOps Dashboard** (Coming April 2024)
  - Multi-cloud monitoring, cost optimization
  - Tech: Go, htmx, Prometheus

- **Mobile Puzzle Game** (Coming May 2024)
  - React Native, multiplayer features
  - Tech: React Native, Supabase

### 4. Technical Blog Section
```
"Engineering Insights"
- "Building a State Machine for Multiplayer Games"
- "WebSocket at Scale: Lessons from Liap Tui"
- "AWS Free Tier: Running Production Apps for $0"
```

### 5. Skills & Technologies
```
Languages: Python, JavaScript/TypeScript, Go
Frontend: React, Vue, Tailwind CSS
Backend: FastAPI, Node.js, PostgreSQL
DevOps: AWS, Docker, GitHub Actions
Real-time: WebSockets, Redis, State Machines
```

### 6. Contact Section
```
"Let's Build Something Together"
- Email contact form
- Calendar link for meetings
- Social links
```

## Technical Implementation Requirements

### Tech Stack Decision
**Use Astro** because:
- Zero JS by default (fast loading)
- Component-based (easy to update sections)
- Markdown support (for blog posts)
- Static output (perfect for S3)

### Component Architecture
```
src/
├── components/
│   ├── Hero.astro
│   ├── ProjectCard.astro
│   ├── ComingSoon.astro
│   ├── BlogPost.astro
│   ├── SkillBadge.astro
│   └── ContactForm.astro
├── layouts/
│   └── BaseLayout.astro
├── pages/
│   ├── index.astro
│   ├── projects/
│   │   └── liap-tui.astro
│   └── blog/
│       └── [slug].astro
├── content/
│   ├── projects/
│   │   ├── liap-tui.json (ready: true)
│   │   ├── ai-assistant.json (ready: false)
│   │   └── devops-dashboard.json (ready: false)
│   └── blog/
│       └── building-state-machines.md
└── styles/
    └── global.css
```

### Progressive Enhancement Strategy

1. **Week 1**: Launch with
   - Liap Tui as featured project (100% complete)
   - 3-4 "Coming Soon" project cards
   - Basic contact form
   - Responsive design

2. **Month 1-2**: Update weekly
   - Convert one "Coming Soon" → real project
   - Add one blog post
   - Enhance animations/interactions

### Data Structure for Projects

```json
// content/projects/liap-tui.json
{
  "id": "liap-tui",
  "ready": true,
  "featured": true,
  "data": {
    "title": "Liap Tui - Multiplayer Board Game",
    "tagline": "Traditional game meets modern web technology",
    "description": "Real-time multiplayer implementation of a traditional Thai-Chinese board game...",
    "liveUrl": "http://34.233.7.20",
    "githubUrl": "https://github.com/yourusername/liap-tui",
    "caseStudyUrl": "/projects/liap-tui",
    "techStack": ["Python", "FastAPI", "React", "WebSocket", "AWS EC2", "Docker"],
    "highlights": [
      "Real-time multiplayer with <100ms latency",
      "Enterprise state machine architecture",
      "Comprehensive test coverage (>80%)",
      "Production-ready with monitoring"
    ],
    "images": {
      "hero": "/images/liap-tui-hero.png",
      "screenshots": [
        "/images/liap-tui-gameplay.gif",
        "/images/liap-tui-architecture.png"
      ]
    }
  }
}

// content/projects/ai-assistant.json
{
  "id": "ai-assistant",
  "ready": false,
  "data": {
    "title": "AI Writing Assistant",
    "timeline": "March 2024",
    "description": "Chrome extension for AI-powered writing assistance",
    "plannedFeatures": [
      "Context-aware suggestions",
      "Multiple writing styles",
      "Grammar and tone checking"
    ],
    "techStack": ["TypeScript", "React", "OpenAI API", "Chrome Extensions API"]
  }
}
```

### Deployment Configuration

```bash
# deploy.sh
#!/bin/bash
set -e

echo "🏗️  Building portfolio..."
npm run build

echo "📤 Uploading to S3..."
aws s3 sync dist/ s3://portfolio-bucket-name \
  --delete \
  --cache-control "public, max-age=3600" \
  --exclude ".DS_Store"

echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"

echo "✅ Portfolio deployed!"
echo "🌐 View at: https://your-domain.com"
```

### AWS Infrastructure Setup

```bash
# 1. Create S3 bucket
aws s3 mb s3://yourname-portfolio-2024

# 2. Enable website hosting
aws s3 website s3://yourname-portfolio-2024 \
  --index-document index.html \
  --error-document 404.html

# 3. Create bucket policy for public access
cat > bucket-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::yourname-portfolio-2024/*"
  }]
}
EOF

aws s3api put-bucket-policy \
  --bucket yourname-portfolio-2024 \
  --policy file://bucket-policy.json

# 4. Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name yourname-portfolio-2024.s3-website-us-east-1.amazonaws.com \
  --default-root-object index.html
```

## Design Requirements

### Visual Style
- **Clean and Modern**: Lots of whitespace, good typography
- **Dark mode support**: System preference detection
- **Subtle animations**: Entrance animations, hover states
- **Mobile-first**: Must work perfectly on phones

### Color Palette
```css
:root {
  --primary: #6366f1;     /* Indigo */
  --secondary: #8b5cf6;   /* Purple */
  --accent: #10b981;      /* Green for CTAs */
  --dark: #111827;        /* Near black */
  --light: #f9fafb;       /* Near white */
}
```

### Typography
- Headers: Inter or similar modern sans-serif
- Body: System font stack for performance
- Code: JetBrains Mono or similar

## Implementation Instructions for Claude Code

1. **Create new repository** called `portfolio`
2. **Initialize Astro project** with TypeScript
3. **Create all components** listed in architecture
4. **Implement responsive design** mobile-first
5. **Add coming soon functionality** with easy updates
6. **Set up AWS infrastructure** (S3 + CloudFront)
7. **Create deployment script** for easy updates
8. **Add README** with update instructions

### First Command to Run
```bash
npx create-astro@latest portfolio -- --template minimal --typescript
```

### Key Features to Implement
1. **Dynamic project loading** from JSON files
2. **Coming soon component** with countdown/timeline
3. **Blog system** using Markdown files
4. **Contact form** (using Formspree or similar)
5. **SEO optimization** with meta tags
6. **Performance optimization** (image lazy loading, etc.)

## Success Criteria

1. **Performance**: Lighthouse score >95
2. **Cost**: <$1/month on AWS
3. **Updates**: Can update content without code changes
4. **Mobile**: Perfect responsive design
5. **SEO**: Appears in Google for your name
6. **Professional**: Would impress a hiring manager

## Final Notes

This portfolio should demonstrate:
- **Technical competence**: Through the Liap Tui project
- **Vision**: Through planned future projects
- **Communication**: Through blog posts
- **Professionalism**: Through design and polish

The goal is to have a living document that grows with your career, starting with 30% real content and building to 100% over the coming months.