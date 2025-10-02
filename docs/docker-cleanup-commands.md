# Docker Cleanup Commands

## Safe Cleanup Commands

### 1. Remove all stopped containers
```bash
docker container prune
```

### 2. Remove all unused images
```bash
docker image prune
```

### 3. Remove all unused images (including tagged images)
```bash
docker image prune -a
```

### 4. Remove all unused volumes
```bash
docker volume prune
```

### 5. Remove all unused networks
```bash
docker network prune
```

### 6. Complete system cleanup (containers, images, volumes, networks)
```bash
docker system prune
```

### 7. Complete system cleanup including all images
```bash
docker system prune -a
```

### 8. Complete system cleanup including volumes
```bash
docker system prune -a --volumes
```

## Specific Cleanup Commands

### Remove specific container
```bash
docker rm <container_id>
```

### Remove specific image
```bash
docker rmi <image_id>
```

### Force remove running container
```bash
docker rm -f <container_id>
```

### Remove all containers (stopped and running)
```bash
docker rm -f $(docker ps -aq)
```

### Remove all images
```bash
docker rmi $(docker images -q)
```

## Check disk usage
```bash
docker system df
```

## Interactive cleanup (with confirmation)
```bash
docker system prune --all --volumes --force
```

## For your Liap Tui project specifically

After development/testing, you can clean up with:
```bash
# Remove the liap-tui image if it exists
docker rmi liap-tui:latest

# Remove any development containers
docker-compose -f docker-compose.dev.yml down --rmi all --volumes

# Clean up everything
docker system prune -a --volumes
```
