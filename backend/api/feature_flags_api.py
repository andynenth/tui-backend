"""
Feature flag management API endpoints.

Provides REST API for managing feature flags, viewing configurations,
and testing flag evaluations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from infrastructure.feature_flags.enhanced_feature_flags import (
    EnhancedFeatureFlags,
    FlagConfig,
    RolloutStrategy,
    ExperimentConfig,
    get_enhanced_feature_flags
)

router = APIRouter(prefix="/api/feature-flags", tags=["feature-flags"])


class FlagUpdateRequest(BaseModel):
    """Request to update a feature flag."""
    
    enabled: Optional[bool] = None
    percentage: Optional[float] = Field(None, ge=0, le=100)
    strategy: Optional[str] = None
    whitelist: Optional[List[str]] = None
    blacklist: Optional[List[str]] = None
    rings: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None


class FlagToggleRequest(BaseModel):
    """Request to toggle a feature flag."""
    
    flag: str
    enabled: bool


class FlagEvaluationRequest(BaseModel):
    """Request to evaluate flags for a context."""
    
    context: Dict[str, Any] = Field(
        ...,
        example={
            "user_id": "user-123",
            "room_id": "room-456",
            "use_case": "StartGameUseCase",
            "ring": "beta"
        }
    )


class UseCaseOverrideRequest(BaseModel):
    """Request to set use-case override."""
    
    use_case: str
    flag_name: str
    enabled: bool


@router.get("/")
async def list_feature_flags() -> Dict[str, Any]:
    """List all feature flags and their configurations."""
    flags = get_enhanced_feature_flags()
    
    # Get basic flags
    basic_flags = flags.get_all_flags()
    
    # Get enhanced configurations
    flag_configs = flags.get_all_flag_configs()
    
    return {
        "flags": {
            name: {
                "enabled": basic_flags.get(name, False),
                "config": config.to_dict() if config else None
            }
            for name, config in flag_configs.items()
        },
        "basic_flags": basic_flags
    }


@router.get("/{flag_name}")
async def get_feature_flag(flag_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific flag."""
    flags = get_enhanced_feature_flags()
    
    config = flags.get_flag_config(flag_name)
    if not config:
        # Check if it's a basic flag
        if flag_name in flags._flags:
            return {
                "name": flag_name,
                "enabled": flags._flags[flag_name],
                "type": "basic",
                "config": None
            }
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")
        
    return {
        "name": flag_name,
        "enabled": config.enabled,
        "type": "enhanced",
        "config": config.to_dict()
    }


@router.put("/{flag_name}")
async def update_feature_flag(
    flag_name: str,
    update: FlagUpdateRequest
) -> Dict[str, Any]:
    """Update a feature flag configuration."""
    flags = get_enhanced_feature_flags()
    
    # Get existing config or create new one
    config = flags.get_flag_config(flag_name)
    if not config:
        config = FlagConfig(
            name=flag_name,
            description=f"Flag {flag_name}",
            enabled=False
        )
        
    # Update fields
    if update.enabled is not None:
        config.enabled = update.enabled
    if update.percentage is not None:
        config.percentage = update.percentage
    if update.strategy is not None:
        try:
            config.strategy = RolloutStrategy(update.strategy)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid strategy: {update.strategy}"
            )
    if update.whitelist is not None:
        config.whitelist = update.whitelist
    if update.blacklist is not None:
        config.blacklist = update.blacklist
    if update.rings is not None:
        config.rings = update.rings
    if update.metadata is not None:
        config.metadata.update(update.metadata)
        
    # Save configuration
    flags.set_flag_config(config)
    flags.save_config()
    
    return {
        "message": f"Flag '{flag_name}' updated",
        "config": config.to_dict()
    }


@router.post("/toggle")
async def toggle_feature_flag(request: FlagToggleRequest) -> Dict[str, Any]:
    """Quick toggle for a feature flag."""
    flags = get_enhanced_feature_flags()
    
    # Update or create config
    config = flags.get_flag_config(request.flag)
    if config:
        config.enabled = request.enabled
    else:
        config = FlagConfig(
            name=request.flag,
            description=f"Flag {request.flag}",
            enabled=request.enabled,
            strategy=RolloutStrategy.PERCENTAGE,
            percentage=100.0 if request.enabled else 0.0
        )
        
    flags.set_flag_config(config)
    flags.save_config()
    
    return {
        "flag": request.flag,
        "enabled": request.enabled,
        "message": f"Flag '{request.flag}' {'enabled' if request.enabled else 'disabled'}"
    }


@router.post("/evaluate")
async def evaluate_flags(request: FlagEvaluationRequest) -> Dict[str, Any]:
    """Evaluate all flags for a given context."""
    flags = get_enhanced_feature_flags()
    
    return flags.get_evaluation_report(request.context)


@router.post("/use-case-override")
async def set_use_case_override(request: UseCaseOverrideRequest) -> Dict[str, Any]:
    """Set a use-case specific override."""
    flags = get_enhanced_feature_flags()
    
    flags.set_use_case_override(
        request.use_case,
        request.flag_name,
        request.enabled
    )
    flags.save_config()
    
    return {
        "message": "Override set",
        "use_case": request.use_case,
        "flag": request.flag_name,
        "enabled": request.enabled
    }


@router.post("/rollout/{flag_name}/increase")
async def increase_rollout_percentage(
    flag_name: str,
    increase_by: float = Query(10.0, ge=0, le=100)
) -> Dict[str, Any]:
    """Increase rollout percentage for a flag."""
    flags = get_enhanced_feature_flags()
    
    config = flags.get_flag_config(flag_name)
    if not config:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_name}' not found")
        
    if config.strategy != RolloutStrategy.PERCENTAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Flag uses {config.strategy.value} strategy, not percentage"
        )
        
    # Increase percentage
    old_percentage = config.percentage
    config.percentage = min(100.0, config.percentage + increase_by)
    
    flags.set_flag_config(config)
    flags.save_config()
    
    return {
        "flag": flag_name,
        "old_percentage": old_percentage,
        "new_percentage": config.percentage,
        "message": f"Rollout increased from {old_percentage}% to {config.percentage}%"
    }


@router.get("/experiments/")
async def list_experiments() -> Dict[str, Any]:
    """List all A/B experiments."""
    flags = get_enhanced_feature_flags()
    
    return {
        "experiments": [
            {
                "name": exp.name,
                "description": exp.description,
                "enabled": exp.enabled,
                "variants": exp.variants
            }
            for exp in flags._experiments.values()
        ]
    }


@router.post("/experiments/{experiment_name}/variant")
async def get_experiment_variant(
    experiment_name: str,
    context: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Get variant assignment for an experiment."""
    flags = get_enhanced_feature_flags()
    
    variant = flags.get_experiment_variant(experiment_name, context)
    
    return {
        "experiment": experiment_name,
        "variant": variant,
        "context": context
    }


@router.post("/bulk-update")
async def bulk_update_flags(
    updates: List[Dict[str, Any]] = Body(...)
) -> Dict[str, Any]:
    """Bulk update multiple flags."""
    flags = get_enhanced_feature_flags()
    
    updated = []
    errors = []
    
    for update in updates:
        try:
            flag_name = update.get("name")
            if not flag_name:
                errors.append({"error": "Missing flag name", "data": update})
                continue
                
            config = flags.get_flag_config(flag_name) or FlagConfig(
                name=flag_name,
                description=update.get("description", f"Flag {flag_name}")
            )
            
            # Update all provided fields
            for field in ["enabled", "percentage", "strategy", "whitelist", "blacklist", "rings"]:
                if field in update:
                    setattr(config, field, update[field])
                    
            flags.set_flag_config(config)
            updated.append(flag_name)
            
        except Exception as e:
            errors.append({"flag": flag_name, "error": str(e)})
            
    # Save all changes
    if updated:
        flags.save_config()
        
    return {
        "updated": updated,
        "errors": errors,
        "message": f"Updated {len(updated)} flags"
    }


@router.get("/health")
async def feature_flags_health() -> Dict[str, Any]:
    """Health check for feature flag system."""
    flags = get_enhanced_feature_flags()
    
    try:
        # Test basic evaluation
        test_result = flags.is_enabled_advanced(
            "test_flag",
            {"user_id": "test"}
        )
        
        return {
            "status": "healthy",
            "flags_loaded": len(flags._flag_configs),
            "experiments_loaded": len(flags._experiments),
            "test_evaluation": "pass"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# WebSocket endpoint for real-time flag updates (if using WebSocket)
async def feature_flag_websocket(websocket):
    """WebSocket endpoint for real-time flag updates."""
    await websocket.accept()
    
    try:
        while True:
            # Wait for flag update requests
            data = await websocket.receive_json()
            
            if data.get("action") == "evaluate":
                flags = get_enhanced_feature_flags()
                result = flags.get_evaluation_report(data.get("context", {}))
                await websocket.send_json(result)
                
    except Exception as e:
        await websocket.close()