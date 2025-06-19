# Clean Architecture Migration Progress

## 🔴 Domain Layer (0/15 files)
- [ ] entities/player.py
- [ ] entities/game.py
- [ ] entities/room.py
- [ ] entities/piece.py
- [ ] value_objects/game_phase.py
- [ ] value_objects/game_state.py
- [ ] value_objects/play_result.py
- [ ] interfaces/bot_strategy.py
- [ ] interfaces/game_repository.py
- [ ] interfaces/event_publisher.py

## 🔴 Application Layer (0/10 files)
- [ ] use_cases/start_game.py
- [ ] use_cases/handle_redeal.py
- [ ] use_cases/make_declaration.py
- [ ] use_cases/play_turn.py
- [ ] services/game_service.py
- [ ] services/room_service.py
- [ ] services/bot_service.py
- [ ] services/phase_service.py

## 🔴 Infrastructure Layer (0/8 files)
- [ ] bot/ai_bot_strategy.py
- [ ] bot/bot_manager_impl.py
- [ ] persistence/in_memory_game_repository.py
- [ ] websocket/connection_manager.py
- [ ] websocket/event_dispatcher.py
- [ ] game_engine/phase_manager_impl.py
- [ ] game_engine/game_flow_controller_impl.py

## 🔴 Presentation Layer (0/5 files)
- [ ] api/dependencies.py
- [ ] api/endpoints/room_endpoints.py
- [ ] api/endpoints/game_endpoints.py
- [ ] api/endpoints/health_endpoints.py
- [ ] websocket/handlers.py

**Total Progress: 0/38 files (0%)**
