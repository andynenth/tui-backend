# Portfolio Week 1 Launch Plan

## Overview

This document provides a comprehensive plan for the first week after your portfolio website is deployed. It covers AWS credential setup, monitoring configuration, content creation, and professional profile updates.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS account with root access
- [ ] AWS CLI installed locally (`aws --version`)
- [ ] Portfolio deployed to S3 + CloudFront
- [ ] Domain name configured (optional)
- [ ] Google account for Search Console
- [ ] LinkedIn profile
- [ ] GitHub account
- [ ] Professional headshot photo
- [ ] First blog post topic ready

## AWS Credentials Setup

### Step 1: Create IAM User for Portfolio Management

1. **Login to AWS Console** as root user
2. Navigate to **IAM** → **Users** → **Add User**
3. User details:
   - Username: `portfolio-admin`
   - Access type: ✅ Programmatic access

4. **Attach Policies** (create custom policy):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketWebsite",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:PutBucketWebsite"
      ],
      "Resource": [
        "arn:aws:s3:::yourname-portfolio-2024",
        "arn:aws:s3:::yourname-portfolio-2024/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetDistribution",
        "cloudfront:ListDistributions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:DeleteAlarms"
      ],
      "Resource": "*"
    }
  ]
}
```

5. **Save Credentials** (shown only once!):
   - Access Key ID: `AKIAIOSFODNN7EXAMPLE`
   - Secret Access Key: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

### Step 2: Configure AWS CLI

**Option A: AWS CLI Configuration (Recommended)**

```bash
# Configure AWS CLI profile
aws configure --profile portfolio

# Enter when prompted:
AWS Access Key ID: [your-access-key]
AWS Secret Access Key: [your-secret-key]
Default region name: us-east-1
Default output format: json
```

This stores credentials in: `~/.aws/credentials`

**Option B: Environment Variables (for CI/CD)**

```bash
# Add to ~/.bashrc or ~/.zshrc
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Step 3: Test Configuration

```bash
# Test access (use --profile if using Option A)
aws s3 ls s3://yourname-portfolio-2024 --profile portfolio

# Should list your portfolio files
```

### Security Best Practices

1. **Enable MFA on Root Account**:
   - AWS Console → Security Credentials → MFA

2. **Never Commit Credentials**:
   ```bash
   # Add to .gitignore
   .env
   .aws/
   aws-credentials.json
   ```

3. **Rotate Keys Regularly**:
   - Set calendar reminder every 90 days
   - IAM → Users → Security Credentials → Create Access Key

4. **Use AWS Profile**:
   ```bash
   # Always use profile instead of default
   aws s3 sync dist/ s3://bucket --profile portfolio
   ```

## Day-by-Day Implementation

### Day 1: AWS Monitoring Setup

**Morning (1 hour): CloudWatch Alarms**

1. **Create S3 Storage Alarm**:
```bash
aws cloudwatch put-metric-alarm \
  --profile portfolio \
  --alarm-name portfolio-s3-storage \
  --alarm-description "S3 storage approaching 5GB free tier limit" \
  --metric-name BucketSizeBytes \
  --namespace AWS/S3 \
  --statistic Average \
  --period 86400 \
  --threshold 4500000000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:YOUR_ACCOUNT:YOUR_SNS_TOPIC
```

2. **Create CloudFront Transfer Alarm**:
```bash
aws cloudwatch put-metric-alarm \
  --profile portfolio \
  --alarm-name portfolio-cf-transfer \
  --alarm-description "CloudFront transfer approaching 50GB limit" \
  --metric-name BytesDownloaded \
  --namespace AWS/CloudFront \
  --statistic Sum \
  --period 2592000 \
  --threshold 45000000000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=DistributionId,Value=YOUR_DISTRIBUTION_ID
```

3. **Create S3 Request Alarm**:
```bash
aws cloudwatch put-metric-alarm \
  --profile portfolio \
  --alarm-name portfolio-s3-requests \
  --alarm-description "S3 requests approaching 20k limit" \
  --metric-name AllRequests \
  --namespace AWS/S3 \
  --statistic Sum \
  --period 2592000 \
  --threshold 18000 \
  --comparison-operator GreaterThanThreshold
```

**Note**: First create SNS topic for email notifications:
```bash
aws sns create-topic --name portfolio-alarms --profile portfolio
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR_ACCOUNT:portfolio-alarms \
  --protocol email \
  --notification-endpoint your-email@example.com
```

**Afternoon (1.5 hours): SEO Setup**

1. **Create Sitemap** (`public/sitemap.xml`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://your-domain.com/</loc>
    <lastmod>2024-01-15</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://your-domain.com/projects/liap-tui</loc>
    <lastmod>2024-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://your-domain.com/blog/building-state-machines</loc>
    <lastmod>2024-01-15</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>
</urlset>
```

2. **Google Search Console Setup**:
   - Go to [search.google.com/search-console](https://search.google.com/search-console)
   - Add property → URL prefix → `https://your-domain.com`
   - Verify ownership (HTML file or DNS)
   - Submit sitemap: `https://your-domain.com/sitemap.xml`

3. **Deploy Sitemap**:
```bash
cd portfolio
npm run build
aws s3 sync dist/ s3://yourname-portfolio-2024 --profile portfolio --delete
aws cloudfront create-invalidation \
  --profile portfolio \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

### Day 2-3: First Blog Post

**Create**: `content/blog/building-state-machines.md`

```markdown
---
title: "Building a State Machine for Multiplayer Games"
date: 2024-01-15
author: "Your Name"
tags: ["architecture", "multiplayer", "game-development", "python", "websocket"]
excerpt: "How I implemented an enterprise-grade state machine with automatic broadcasting for a real-time multiplayer game"
image: "/images/blog/state-machine-architecture.png"
---

# Building a State Machine for Multiplayer Games

When I built [Liap Tui](/projects/liap-tui), a real-time multiplayer board game, I faced a critical challenge: how to keep 4 players perfectly synchronized without state conflicts. The solution? An enterprise-grade state machine with automatic broadcasting.

## The Problem

In multiplayer games, state synchronization is notoriously difficult:

- **Race Conditions**: Player A and B act simultaneously
- **Network Latency**: Actions arrive out of order
- **Disconnections**: Players drop and reconnect
- **State Conflicts**: Server and client disagree

Traditional approaches often lead to:
- Players seeing different game states
- "Phantom" moves that get rolled back
- Frustrated users experiencing glitches

## The Solution: Enterprise State Machine

I developed a state machine architecture that makes desynchronization *impossible* by design:

### Core Principles

1. **Single Source of Truth**: Server state is authoritative
2. **Automatic Broadcasting**: State changes broadcast automatically
3. **Event Sourcing**: Complete history for recovery
4. **Transactional Updates**: All-or-nothing state changes

### Implementation

Here's the base state class that powers the entire system:

```python
class GameState(ABC):
    """Base state with automatic broadcasting."""
    
    def __init__(self, game, room):
        self.game = game
        self.room = room
        self.phase_data = {}
        self.change_history = []
        
    async def update_phase_data(self, updates: dict, reason: str):
        """Update state with automatic broadcasting."""
        # Start transaction
        old_state = self.phase_data.copy()
        
        try:
            # Update state
            self.phase_data.update(updates)
            
            # Record change
            self.change_history.append({
                'timestamp': time.time(),
                'reason': reason,
                'changes': updates,
                'sequence': self.get_next_sequence()
            })
            
            # Broadcast to all players automatically
            await self.broadcast_phase_change(reason)
            
        except Exception as e:
            # Rollback on error
            self.phase_data = old_state
            raise
```

### State Flow

The game flows through four distinct phases:

```mermaid
graph LR
    A[PREPARATION] --> B[DECLARATION]
    B --> C[TURN]
    C --> D[SCORING]
    D --> A
```

Each phase extends the base state:

```python
class TurnState(GameState):
    """Handle player turns with automatic sync."""
    
    async def handle_play_action(self, player_name: str, pieces: List[int]):
        """Process a play action."""
        # Validate move
        if not self.is_valid_play(player_name, pieces):
            raise ValidationError("Invalid play")
        
        # Update state atomically
        await self.update_phase_data({
            'last_play': pieces,
            'last_player': player_name,
            'current_player': self.get_next_player(),
            'pile_cards': self.game.pile_cards + pieces
        }, f"{player_name} played {len(pieces)} cards")
        
        # Check phase transition
        if self.should_end_turn():
            await self.transition_to_next_phase()
```

### Benefits Achieved

1. **Zero Sync Bugs**: 6 months in production, zero desync incidents
2. **Easy Debugging**: Complete event history for every game
3. **Instant Recovery**: Reconnecting players get full state
4. **Scalable**: Pattern works for any multiplayer system

### Lessons Learned

1. **Explicit is Better**: Every state change has a reason
2. **Automate Everything**: Manual broadcasting = bugs
3. **Design for Failure**: Network issues will happen
4. **Event Sourcing Wins**: History enables powerful features

## Real-World Results

This architecture powers Liap Tui in production:
- Handles 4 concurrent players per game
- <100ms state propagation
- Automatic recovery from disconnections
- Zero reported sync bugs

## Try It Yourself

You can see this state machine in action at [liap-tui.com](http://34.233.7.20) or explore the [source code on GitHub](https://github.com/yourusername/liap-tui).

## What's Next?

In my next post, I'll dive into WebSocket optimization techniques that achieved <100ms latency for real-time gameplay.

---

*Have questions about state machines or multiplayer architecture? [Let's connect!](/contact)*
```

**Deploy Blog Post**:
```bash
cd portfolio
npm run build
aws s3 sync dist/ s3://yourname-portfolio-2024 --profile portfolio --delete
aws cloudfront create-invalidation --profile portfolio --distribution-id YOUR_DIST_ID --paths "/*"
```

### Day 3-4: Professional Profile Updates

**LinkedIn Updates**:

1. **Profile Updates**:
   - Headline: "Full-Stack Developer | Real-Time Multiplayer Systems | AWS"
   - About: Add portfolio link in first line
   - Featured: Add portfolio link
   - Contact Info: Add portfolio URL

2. **Announcement Post**:
```
🚀 Excited to share my new portfolio!

I've just launched my professional portfolio featuring:

✅ Liap Tui - A real-time multiplayer board game with <100ms latency
✅ Technical blog posts about state machines and WebSocket architecture  
✅ Upcoming projects in AI and DevOps

Check it out: [your-domain.com]

Built with: React, TypeScript, AWS, and lots of ☕

#webdevelopment #portfolio #multiplayer #aws #react
```

**GitHub Profile**:

1. **Update Bio**:
   ```
   Full-Stack Developer | Real-Time Systems
   🎮 Built Liap Tui multiplayer game
   📝 Technical blog at your-domain.com
   ```

2. **Profile README.md**:
   ```markdown
   ## Hi, I'm [Your Name] 👋

   I'm a full-stack developer specializing in real-time multiplayer systems.

   ### 🚀 Featured Project
   
   **[Liap Tui](http://34.233.7.20)** - Real-time multiplayer board game
   - 4-player concurrent gameplay with <100ms latency
   - Enterprise state machine architecture
   - WebSocket communication with automatic recovery
   - [Read the case study](https://your-domain.com/projects/liap-tui)

   ### 📝 Recent Blog Posts
   - [Building a State Machine for Multiplayer Games](https://your-domain.com/blog/building-state-machines)
   - More at [your-domain.com/blog](https://your-domain.com/blog)

   ### 🛠️ Tech Stack
   - **Languages**: Python, TypeScript, Go
   - **Backend**: FastAPI, Node.js, WebSockets
   - **Frontend**: React, Vue, Tailwind CSS
   - **Cloud**: AWS, Docker, GitHub Actions

   ### 📫 Let's Connect
   - Portfolio: [your-domain.com](https://your-domain.com)
   - LinkedIn: [linkedin.com/in/yourname](https://linkedin.com/in/yourname)
   ```

### Day 4-5: Analytics & Optimization

**Add Analytics** (choose one):

1. **Google Analytics 4**:
```html
<!-- Add to BaseLayout.astro -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

2. **Plausible (Privacy-Friendly)**:
```html
<!-- Add to BaseLayout.astro -->
<script defer data-domain="your-domain.com" src="https://plausible.io/js/script.js"></script>
```

**Performance Check**:
```bash
# Run Lighthouse audit
npm install -g lighthouse
lighthouse https://your-domain.com --view

# Check bundle size
cd portfolio
npm run build
ls -lah dist/assets/
```

**Final Deployment**:
```bash
# Deploy everything
cd portfolio
npm run build
aws s3 sync dist/ s3://yourname-portfolio-2024 --profile portfolio --delete
aws cloudfront create-invalidation --profile portfolio --distribution-id YOUR_DIST_ID --paths "/*"

# Verify deployment
curl -I https://your-domain.com
```

## Quick Reference Commands

### AWS Commands
```bash
# Check S3 usage
aws s3 ls s3://yourname-portfolio-2024 --recursive --summarize --profile portfolio

# View CloudFront metrics
aws cloudwatch get-metric-statistics \
  --profile portfolio \
  --namespace AWS/CloudFront \
  --metric-name BytesDownloaded \
  --dimensions Name=DistributionId,Value=YOUR_DIST_ID \
  --statistics Sum \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-31T23:59:59Z \
  --period 2592000

# Check billing
aws ce get-cost-and-usage \
  --profile portfolio \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

### Deployment Script
Save as `deploy-portfolio.sh`:
```bash
#!/bin/bash
set -e

echo "🏗️  Building portfolio..."
npm run build

echo "📤 Uploading to S3..."
aws s3 sync dist/ s3://yourname-portfolio-2024 \
  --profile portfolio \
  --delete \
  --cache-control "public, max-age=3600" \
  --exclude ".DS_Store"

echo "🔄 Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --profile portfolio \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"

echo "✅ Portfolio deployed!"
echo "🌐 View at: https://your-domain.com"
```

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**:
   ```
   Unable to locate credentials
   ```
   Solution: Check `aws configure list --profile portfolio`

2. **S3 Sync Permission Denied**:
   ```
   Access Denied
   ```
   Solution: Verify IAM policy includes your bucket

3. **CloudFront Not Updating**:
   - Always invalidate cache after deployment
   - Wait 5-10 minutes for global propagation

4. **High AWS Bill**:
   - Check CloudWatch alarms
   - Review CloudFront logs for bot traffic
   - Enable S3 request metrics

## Success Checklist

By end of Week 1, you should have:

- [ ] AWS monitoring alerts configured
- [ ] Site submitted to Google Search Console
- [ ] First blog post published
- [ ] LinkedIn profile updated with portfolio
- [ ] GitHub profile showcasing portfolio
- [ ] Analytics tracking visitor data
- [ ] All links tested and working
- [ ] Deployment script saved for easy updates

## Next Steps (Week 2+)

1. **Content Pipeline**:
   - Schedule: 1 blog post + 1 project conversion weekly
   - Topics: WebSocket scaling, AWS free tier, AI assistant project

2. **SEO Optimization**:
   - Monitor Search Console for indexing
   - Add meta descriptions to all pages
   - Build backlinks from dev communities

3. **Performance**:
   - Optimize images (WebP, lazy loading)
   - Add PWA features
   - Implement caching strategies

---

**Remember**: Your portfolio is a living document. Regular updates keep it relevant and demonstrate your ongoing growth as a developer.