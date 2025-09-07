# Portfolio Deployment Plan

## Overview

This plan outlines a comprehensive strategy to deploy a professional portfolio website showcasing the Liap Tui multiplayer game and future projects. The portfolio serves as a central hub for potential employers/clients, demonstrating full-stack development skills through a production-ready multiplayer game deployed on AWS.

### Purpose
- **Showcase Technical Skills**: Full-stack development (Python/FastAPI + React), real-time WebSockets, AWS deployment
- **Professional Presence**: Central hub demonstrating ability to ship complete products
- **Progressive Portfolio**: 30% ready content (Liap Tui), 70% coming soon projects

## 1. Architecture Comparison

| Aspect | S3+CloudFront | Unified EC2 | **Recommendation** |
|--------|---------------|-------------|-------------------|
| **Monthly Cost** | ~$0.50 | $0 (existing) | **S3+CloudFront** |
| **Setup Complexity** | Low (2 hours) | Medium (4 hours) | **S3+CloudFront** |
| **Scalability** | Unlimited | Limited by instance | **S3+CloudFront** |
| **Update Ease** | `aws s3 sync` | SSH + build | **S3+CloudFront** |
| **Performance** | Global CDN | Single region | **S3+CloudFront** |
| **Maintenance** | None | OS updates | **S3+CloudFront** |

**Decision: S3+CloudFront** - Separate concerns, easier updates, better performance.

## 2. Tech Stack Selection

**Winner: Astro with TypeScript** - Best for progressive enhancement
```bash
# Why Astro:
- Zero JS by default (fast loading, Lighthouse >95)
- Component-based (easy to update sections)
- Markdown support (for blog posts)
- Static output (perfect for S3)
- TypeScript support for better maintainability
```

**Key Features to Implement**:
- Dynamic project loading from JSON files
- Coming soon component with timeline
- Blog system using Markdown files
- Contact form (using Formspree)
- SEO optimization with meta tags
- Performance optimization (image lazy loading)

## 3. Implementation Plan

### Week 1: MVP Launch

```bash
# Day 1-2: Setup Infrastructure
aws s3 mb s3://yourname-portfolio-2024
aws s3 website s3://yourname-portfolio-2024 \
  --index-document index.html \
  --error-document 404.html

# Create bucket policy for public access
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

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name yourname-portfolio-2024.s3-website-us-east-1.amazonaws.com \
  --default-root-object index.html

# Day 3-4: Build Astro Site with TypeScript
npx create-astro@latest portfolio -- --template minimal --typescript
cd portfolio
npm install

# Day 5-6: Initial Content & Deploy
# - Create Hero section with your intro
# - Add Featured Project section for Liap Tui
# - Create 3-4 Coming Soon project cards
# - Implement responsive design
npm run build
aws s3 sync dist/ s3://yourname-portfolio-2024 --delete
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"

# Day 7: Polish & Launch
# - Test on mobile devices
# - Verify Lighthouse score >95
# - Set up CloudWatch alarms
```

### Month 1-2: Progressive Updates

```bash
# deploy.sh - Weekly Update Script
#!/bin/bash
set -e

echo "🏗️  Building portfolio..."
npm run build

echo "📤 Uploading to S3..."
aws s3 sync dist/ s3://yourname-portfolio-2024 \
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

**Weekly Tasks**:
- Convert one "Coming Soon" → real project
- Add one blog post about technical challenges
- Enhance animations/interactions
- Update Liap Tui metrics if needed

## 4. Coming Soon Component Strategy

### Complete Component Architecture
```
src/
├── components/
│   ├── Hero.astro              # "Hi, I'm [Name]" intro section
│   ├── ProjectCard.astro       # Displays ready/coming soon projects
│   ├── ComingSoon.astro        # Coming soon component
│   ├── BlogPost.astro          # Blog post component
│   ├── SkillBadge.astro        # Technology skill badges
│   └── ContactForm.astro       # Contact form with Formspree
├── layouts/
│   └── BaseLayout.astro        # Base layout with dark mode support
├── pages/
│   ├── index.astro             # Homepage with all sections
│   ├── projects/
│   │   └── liap-tui.astro      # Liap Tui case study
│   └── blog/
│       └── [slug].astro        # Dynamic blog posts
├── content/
│   ├── projects/
│   │   ├── liap-tui.json       # ready: true, featured: true
│   │   ├── ai-assistant.json   # ready: false, timeline: "March 2024"
│   │   ├── devops-dashboard.json # ready: false, timeline: "April 2024"
│   │   └── mobile-game.json    # ready: false, timeline: "May 2024"
│   └── blog/
│       ├── building-state-machines.md
│       ├── websocket-at-scale.md
│       └── aws-free-tier-production.md
└── styles/
    └── global.css              # CSS variables, dark mode

### ComingSoon.astro
```astro
---
export interface Props {
  title: string;
  timeline: string;
  features?: string[];
}
const { title, timeline, features = [] } = Astro.props;
---

<div class="coming-soon">
  <h3>{title}</h3>
  <p class="timeline">Coming {timeline}</p>
  {features.length > 0 && (
    <ul class="planned-features">
      {features.map(f => <li>{f}</li>)}
    </ul>
  )}
  <button class="notify-me">Notify Me</button>
</div>

<style>
  .coming-soon {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 8px;
    color: white;
  }
</style>
```

### Progressive Update Pattern
```astro
---
// ProjectCard.astro
import ComingSoon from './ComingSoon.astro';

export interface Props {
  project: {
    status: 'ready' | 'mockup';
    title: string;
    data: any;
  };
}

const { project } = Astro.props;
---

{project.status === 'mockup' ? (
  <ComingSoon
    title={project.title}
    timeline={project.data.timeline}
    features={project.data.features}
  />
) : (
  <div class="project-ready">
    <h3>{project.title}</h3>
    <img src={project.data.screenshot} alt={project.title} />
    <p>{project.data.description}</p>
    <a href={project.data.url}>View Project</a>
  </div>
)}
```

### Detailed Project Data Structure

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
    "metrics": "4-player real-time | <100ms latency | 99.9% uptime",
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

// content/projects/devops-dashboard.json
{
  "id": "devops-dashboard",
  "ready": false,
  "data": {
    "title": "DevOps Dashboard",
    "timeline": "April 2024",
    "description": "Multi-cloud monitoring, cost optimization",
    "plannedFeatures": [
      "Real-time metrics visualization",
      "Cost anomaly detection",
      "Automated remediation"
    ],
    "techStack": ["Go", "htmx", "Prometheus", "Grafana"]
  }
}
```

## 5. Portfolio Content Sections

### Hero Section
```astro
---
// components/Hero.astro
---
<section class="hero">
  <h1>Hi, I'm [Your Name]</h1>
  <p class="tagline">Full-Stack Developer specializing in real-time multiplayer applications</p>
  <div class="social-links">
    <a href="https://github.com/yourusername">GitHub</a>
    <a href="https://linkedin.com/in/yourusername">LinkedIn</a>
    <a href="/resume.pdf">Resume</a>
    <a href="#contact">Contact</a>
  </div>
</section>
```

### Featured Project Section
```astro
---
// Part of index.astro
import ProjectCard from '../components/ProjectCard.astro';
const liapTui = await import('../content/projects/liap-tui.json');
---
<section class="featured-project">
  <h2>Featured Project</h2>
  <div class="project-highlight">
    <span class="live-badge">LIVE PROJECT</span>
    <h3>{liapTui.data.title}</h3>
    <p class="tagline">{liapTui.data.tagline}</p>
    <div class="metrics">{liapTui.data.metrics}</div>
    <div class="tech-stack">
      {liapTui.data.techStack.map(tech => <SkillBadge name={tech} />)}
    </div>
    <div class="links">
      <a href={liapTui.data.liveUrl} class="btn-primary">Play Game</a>
      <a href={liapTui.data.githubUrl}>View Code</a>
      <a href={liapTui.data.caseStudyUrl}>Read Case Study</a>
    </div>
  </div>
</section>
```

### Skills & Technologies Section
```astro
---
// components/SkillsSection.astro
const skills = {
  "Languages": ["Python", "JavaScript/TypeScript", "Go"],
  "Frontend": ["React", "Vue", "Tailwind CSS"],
  "Backend": ["FastAPI", "Node.js", "PostgreSQL"],
  "DevOps": ["AWS", "Docker", "GitHub Actions"],
  "Real-time": ["WebSockets", "Redis", "State Machines"]
};
---
<section class="skills">
  <h2>Skills & Technologies</h2>
  {Object.entries(skills).map(([category, items]) => (
    <div class="skill-category">
      <h3>{category}</h3>
      <div class="skill-list">
        {items.map(skill => <SkillBadge name={skill} />)}
      </div>
    </div>
  ))}
</section>
```

### Contact Section
```astro
---
// components/ContactForm.astro
---
<section id="contact" class="contact">
  <h2>Let's Build Something Together</h2>
  <form action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
    <input type="email" name="email" placeholder="Your email" required />
    <textarea name="message" placeholder="Your message" rows="5" required></textarea>
    <button type="submit">Send Message</button>
  </form>
  <div class="alternative-contact">
    <a href="https://calendly.com/yourusername">Schedule a Call</a>
  </div>
</section>
```

## 6. Design Requirements

### Visual Style & Color Palette
```css
/* styles/global.css */
:root {
  /* Light mode */
  --primary: #6366f1;     /* Indigo */
  --secondary: #8b5cf6;   /* Purple */
  --accent: #10b981;      /* Green for CTAs */
  --dark: #111827;        /* Near black */
  --light: #f9fafb;       /* Near white */
  --gray-100: #f3f4f6;
  --gray-900: #111827;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: var(--dark);
    --text: var(--light);
    --card-bg: #1f2937;
  }
}

/* Typography */
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  line-height: 1.6;
}

h1, h2, h3 {
  font-family: 'Inter', sans-serif;
  font-weight: 700;
}

code {
  font-family: 'JetBrains Mono', monospace;
}

/* Mobile-first responsive design */
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

@media (min-width: 768px) {
  .container {
    padding: 0 2rem;
  }
}
```

### Performance Requirements
- **Lighthouse Score**: >95 for all metrics
- **First Contentful Paint**: <1.5s
- **Cumulative Layout Shift**: <0.1
- **Image Optimization**: WebP with fallbacks, lazy loading
- **Font Loading**: System fonts with optional web fonts

## 7. Free Tier Monitoring

### CloudWatch Alarms Setup
```bash
# S3 Storage Alarm (approaching 5GB)
aws cloudwatch put-metric-alarm \
  --alarm-name portfolio-s3-storage \
  --alarm-description "S3 storage approaching free tier limit" \
  --metric-name BucketSizeBytes \
  --namespace AWS/S3 \
  --statistic Average \
  --period 86400 \
  --threshold 4500000000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1

# CloudFront Transfer Alarm (approaching 50GB)
aws cloudwatch put-metric-alarm \
  --alarm-name portfolio-cf-transfer \
  --alarm-description "CloudFront transfer approaching limit" \
  --metric-name BytesDownloaded \
  --namespace AWS/CloudFront \
  --statistic Sum \
  --period 2592000 \
  --threshold 45000000000 \
  --comparison-operator GreaterThanThreshold

# S3 GET Requests Alarm (approaching 20k)
aws cloudwatch put-metric-alarm \
  --alarm-name portfolio-s3-requests \
  --alarm-description "S3 GET requests approaching limit" \
  --metric-name NumberOfObjects \
  --namespace AWS/S3 \
  --statistic Sum \
  --period 2592000 \
  --threshold 18000
```

### Cost Optimization
```bash
# Enable S3 Intelligent-Tiering (automatic)
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket your-portfolio-domain-com \
  --id archive-old-assets \
  --intelligent-tiering-configuration file://tiering.json

# Compress images before upload
find dist/images -name "*.png" -exec pngquant --ext=.png --force {} \;
find dist/images -name "*.jpg" -exec jpegoptim -m85 {} \;
```

## 8. Implementation Checklist

### Week 1 Tasks
- [ ] Create AWS S3 bucket (yourname-portfolio-2024) with website hosting
- [ ] Configure bucket policy for public access
- [ ] Set up CloudFront distribution
- [ ] Initialize Astro project with TypeScript
- [ ] Create all components (Hero, ProjectCard, ComingSoon, etc.)
- [ ] Implement responsive design with dark mode support
- [ ] Add Liap Tui as featured project with metrics
- [ ] Create 3-4 Coming Soon projects (AI Assistant, DevOps Dashboard, Mobile Game)
- [ ] Set up Formspree contact form
- [ ] Deploy to S3
- [ ] Verify Lighthouse score >95

### Month 1-2 Tasks
- [ ] Set up CloudWatch alarms for free tier limits
- [ ] Create blog posts (state machines, WebSocket, AWS free tier)
- [ ] Convert one Coming Soon project to real content weekly
- [ ] Add blog post about technical challenges weekly
- [ ] Optimize images (WebP, lazy loading)
- [ ] Monitor AWS billing dashboard
- [ ] Track Liap Tui metrics and update as needed

### Monthly Maintenance
1. Check CloudWatch billing ($0 expected)
2. Run `aws s3 ls --summarize` for storage
3. Update 1-2 mockups → real content
4. Compress new images
5. Deploy with cache invalidation

## 9. Quick Reference Commands

### Deploy Portfolio
```bash
npm run build && aws s3 sync dist/ s3://your-bucket --delete
```

### Invalidate Cache
```bash
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

### Check S3 Usage
```bash
aws s3 ls s3://your-bucket --recursive --summarize | grep "Total Size"
```

### View CloudFront Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/CloudFront \
  --metric-name BytesDownloaded \
  --dimensions Name=DistributionId,Value=YOUR_ID \
  --statistics Sum \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 2592000
```

## 10. Budget Breakdown

| Service | Free Tier | Expected Usage | Cost |
|---------|-----------|----------------|------|
| S3 Storage | 5 GB | ~100 MB | $0 |
| S3 Requests | 20k GET/2k PUT | ~5k/month | $0 |
| CloudFront | 50 GB transfer | ~10 GB | $0 |
| CloudWatch | 10 alarms | 3 alarms | $0 |
| **Total** | - | - | **$0** |

*Note: First year only. Year 2+ may incur ~$0.50/month for CloudFront.*

## 11. Success Criteria

- **Performance**: Lighthouse score >95 on all metrics
- **Cost**: <$1/month on AWS (staying within free tier)
- **Updates**: Can update content without code changes (JSON files)
- **Mobile**: Perfect responsive design with touch interactions
- **SEO**: Appears in Google for your name within 30 days
- **Professional**: Would impress a hiring manager or client

## 12. Next Steps

1. **Immediate**: Run `npx create-astro@latest portfolio -- --template minimal --typescript`
2. **Day 1**: Set up AWS infrastructure (S3 bucket + CloudFront)
3. **Day 2**: Create component architecture and layouts
4. **Day 3**: Implement Hero, Featured Project (Liap Tui), Coming Soon sections
5. **Day 4**: Add Skills, Blog, and Contact sections
6. **Day 5**: Deploy MVP and verify performance
7. **Week 2+**: Progressive content updates (convert mockups → real projects)

**Final Result**:
- Professional portfolio demonstrating full-stack expertise through Liap Tui
- Living document that grows from 30% → 100% real content
- Easy updates via JSON files and markdown
- <$1/month hosting with global CDN performance
- Impresses hiring managers with production-ready multiplayer game
