#!/usr/bin/env python3
"""
Script to reduce verbose logging in the backend and add debug logs for database optimization pipeline
"""

import os
import re

def reduce_logging():
    """Reduce verbose logging across the codebase"""
    
    changes = []
    
    # 1. Reduce bot manager verbose logs
    bot_manager_file = "backend/engine/bot_manager.py"
    if os.path.exists(bot_manager_file):
        with open(bot_manager_file, 'r') as f:
            content = f.read()
        
        # Change verbose bot manager logs to debug level
        original = content
        content = re.sub(r'logger\.info\(f?".*BOT_MANAGER.*"\)', lambda m: m.group(0).replace('logger.info', 'logger.debug'), content)
        content = re.sub(r'print\(f?".*BOT_MANAGER.*"\)', lambda m: '# ' + m.group(0), content)
        
        if content != original:
            with open(bot_manager_file, 'w') as f:
                f.write(content)
            changes.append(f"✅ Reduced bot manager logging in {bot_manager_file}")
    
    # 2. Reduce bot handler verbose logs
    bot_handler_patterns = [
        "backend/engine/bot_handler.py",
        "backend/engine/state_machine/game_state_machine.py"
    ]
    
    for file_path in bot_handler_patterns:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
            
            original = content
            # Comment out BOT_HANDLER print statements
            content = re.sub(r'print\(f?".*BOT_HANDLER.*"\)', lambda m: '# ' + m.group(0), content)
            content = re.sub(r'print\(f?".*BOT_MANAGER.*"\)', lambda m: '# ' + m.group(0), content)
            content = re.sub(r'print\(f?".*STATE_MACHINE.*"\)', lambda m: '# ' + m.group(0), content)
            
            if content != original:
                with open(file_path, 'w') as f:
                    f.write(content)
                changes.append(f"✅ Reduced bot handler logging in {file_path}")
    
    # 3. Skip favicon.ico in logging middleware
    middleware_file = "backend/api/middleware/logging_middleware.py"
    if os.path.exists(middleware_file):
        with open(middleware_file, 'r') as f:
            content = f.read()
        
        # Add favicon skip after the path is extracted
        original = content
        if 'request.url.path' in content and 'favicon.ico' not in content:
            # Find the dispatch method and add favicon check
            content = re.sub(
                r'(# Log request\s*\n)',
                r'# Skip logging for favicon.ico\n        if request.url.path == "/favicon.ico":\n            return await call_next(request)\n        \n\1',
                content
            )
            
            if content != original:
                with open(middleware_file, 'w') as f:
                    f.write(content)
                changes.append(f"✅ Added favicon.ico skip in {middleware_file}")
    
    # 4. Reduce room cleanup logs
    ws_file = "backend/api/routes/ws.py"
    if os.path.exists(ws_file):
        with open(ws_file, 'r') as f:
            content = f.read()
        
        original = content
        # Change cleanup iteration logs to debug
        content = re.sub(
            r'logger\.info\(f?".*\[ROOM_DEBUG\] Cleanup iteration.*"\)',
            lambda m: m.group(0).replace('logger.info', 'logger.debug'),
            content
        )
        
        if content != original:
            with open(ws_file, 'w') as f:
                f.write(content)
            changes.append(f"✅ Reduced room cleanup logging in {ws_file}")
    
    # 5. Reduce phase data update logs
    base_state_file = "backend/engine/state_machine/base_state.py"
    if os.path.exists(base_state_file):
        with open(base_state_file, 'r') as f:
            content = f.read()
        
        original = content
        # Change phase data update logs to debug
        content = re.sub(
            r'self\.logger\.info\(f?".*Phase Data Update.*"\)',
            lambda m: m.group(0).replace('self.logger.info', 'self.logger.debug'),
            content
        )
        
        if content != original:
            with open(base_state_file, 'w') as f:
                f.write(content)
            changes.append(f"✅ Reduced phase data update logging in {base_state_file}")
    
    return changes


def add_database_debug_logs():
    """Add debug logging to trace database optimization pipeline"""
    
    changes = []
    
    # 1. Add debug logging to OptimizedEventStore
    optimized_store_file = "backend/services/optimized_event_store.py"
    if os.path.exists(optimized_store_file):
        with open(optimized_store_file, 'r') as f:
            content = f.read()
        
        original = content
        
        # Add debug log at the start of store_event
        if 'async def store_event(' in content and 'DEBUG: OptimizedEventStore.store_event' not in content:
            content = re.sub(
                r'(async def store_event\(.*?\).*?:\s*\n.*?""".*?"""\s*\n)',
                r'\1        logger.debug(f"🔍 DEBUG: OptimizedEventStore.store_event called - room: {room_id}, type: {event_type}")\n',
                content,
                flags=re.DOTALL
            )
        
        # Add debug log for compression
        if 'if compressed:' in content and 'DEBUG: Event compressed' not in content:
            content = re.sub(
                r'(if compressed:\s*\n)',
                r'\1                logger.debug(f"🔍 DEBUG: Event compressed to type: {compressed.event_type}")\n',
                content
            )
        
        # Add debug log for buffer add
        if 'await self.buffer.add_event' in content and 'DEBUG: Adding to buffer' not in content:
            content = re.sub(
                r'(await self\.buffer\.add_event\()',
                r'logger.debug(f"🔍 DEBUG: Adding to buffer - room: {room_id}, type: {event_type}")\n        \1',
                content
            )
        
        # Add debug log for direct storage
        if 'async def store_event_direct(' in content and 'DEBUG: Direct storage' not in content:
            content = re.sub(
                r'(async def store_event_direct\(.*?\).*?:\s*\n.*?""".*?"""\s*\n)',
                r'\1        logger.debug(f"🔍 DEBUG: Direct storage to v2 - room: {room_id}, type: {event_type}")\n',
                content,
                flags=re.DOTALL
            )
        
        if content != original:
            with open(optimized_store_file, 'w') as f:
                f.write(content)
            changes.append(f"✅ Added debug logs to {optimized_store_file}")
    
    # 2. Add debug logging to EventStoreV2
    v2_store_file = "backend/services/event_store_v2.py"
    if os.path.exists(v2_store_file):
        with open(v2_store_file, 'r') as f:
            content = f.read()
        
        original = content
        
        # Add debug log for round snapshot
        if 'async def store_round_snapshot' in content and 'DEBUG: Storing round snapshot' not in content:
            content = re.sub(
                r'(async def store_round_snapshot\(.*?\).*?:\s*\n.*?""".*?"""\s*\n)',
                r'\1        logger.debug(f"🔍 DEBUG: Storing round snapshot - room: {room_id}, round: {round_number}")\n',
                content,
                flags=re.DOTALL
            )
        
        if content != original:
            with open(v2_store_file, 'w') as f:
                f.write(content)
            changes.append(f"✅ Added debug logs to {v2_store_file}")
    
    # 3. Add debug logging to MigrationAdapter
    migration_file = "backend/services/migration_adapter.py"
    if os.path.exists(migration_file):
        with open(migration_file, 'r') as f:
            content = f.read()
        
        original = content
        
        # Add debug log for store_event
        if 'async def store_event(' in content and 'DEBUG: MigrationAdapter.store_event' not in content:
            content = re.sub(
                r'(async def store_event\(.*?\).*?:\s*\n.*?""".*?"""\s*\n)',
                r'\1        logger.debug(f"🔍 DEBUG: MigrationAdapter.store_event - mode: {self.mode}, room: {room_id}, type: {event_type}")\n',
                content,
                flags=re.DOTALL
            )
        
        if content != original:
            with open(migration_file, 'w') as f:
                f.write(content)
            changes.append(f"✅ Added debug logs to {migration_file}")
    
    # 4. Add debug logging to EventCompressor
    compressor_file = "backend/services/event_compressor.py"
    if os.path.exists(compressor_file):
        with open(compressor_file, 'r') as f:
            content = f.read()
        
        original = content
        
        # Add debug log for should_store_event
        if 'def should_store_event' in content and 'DEBUG: should_store_event' not in content:
            content = re.sub(
                r'(def should_store_event\(.*?\).*?:\s*\n.*?""".*?"""\s*\n)',
                r'\1        result = self._should_store_event_logic(event_type)\n        logger.debug(f"🔍 DEBUG: should_store_event({event_type}) = {result}")\n        return result\n    \n    def _should_store_event_logic(self, event_type: str) -> bool:\n',
                content,
                flags=re.DOTALL
            )
        
        if content != original:
            with open(compressor_file, 'w') as f:
                f.write(content)
            changes.append(f"✅ Added debug logs to {compressor_file}")
    
    return changes


if __name__ == "__main__":
    print("🧹 Reducing verbose logging...")
    reduce_changes = reduce_logging()
    for change in reduce_changes:
        print(change)
    
    print("\n🔍 Adding database optimization debug logs...")
    debug_changes = add_database_debug_logs()
    for change in debug_changes:
        print(change)
    
    print("\n✅ Logging adjustments complete!")
    print("\n⚠️  Remember to restart the server to see the changes.")