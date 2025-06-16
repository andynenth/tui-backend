# backend/engine/bot_manager.py

import asyncio
from typing import Dict, List, Optional
from engine.player import Player
import engine.ai as ai

class BotManager:
    """Centralized bot management system"""
    
    def __init__(self):
        self.active_games: Dict[str, GameBotHandler] = {}
        
    def register_game(self, room_id: str, game):
        """Register a game for bot management"""
        self.active_games[room_id] = GameBotHandler(room_id, game)
        
    def unregister_game(self, room_id: str):
        """Remove game from bot management"""
        if room_id in self.active_games:
            del self.active_games[room_id]
            
    async def handle_game_event(self, room_id: str, event: str, data: dict):
        """Handle game events that might need bot actions"""
        print(f"🔔 Bot Manager: Received event '{event}' for room {room_id} with data: {data}")
        if room_id not in self.active_games:
            return
            
        handler = self.active_games[room_id]
        await handler.handle_event(event, data)


class GameBotHandler:
    """Handles bot actions for a specific game"""
    
    def __init__(self, room_id: str, game):
        self.room_id = room_id
        self.game = game
        self.processing = False
        self._lock = asyncio.Lock()
        
    async def handle_event(self, event: str, data: dict):
        """Process game events and trigger bot actions"""
        async with self._lock:  # Prevent concurrent bot actions
            if event == "player_declared":
                await self._handle_declaration_phase(data["player_name"])
            elif event == "player_played":
                await self._handle_play_phase(data["player_name"])
            elif event == "turn_started":
                await self._handle_turn_start(data["starter"])
            elif event == "round_started":
                await self._handle_round_start()
                
    async def _handle_declaration_phase(self, last_declarer: str):
        """Handle bot declarations in order"""
        from backend.socket_manager import broadcast
        
        # Get declaration order
        declaration_order = self._get_declaration_order()
        
        # Find next bot to declare
        last_index = self._get_player_index(last_declarer, declaration_order)
        
        for i in range(last_index + 1, len(declaration_order)):
            player = declaration_order[i]
            
            if not player.is_bot:
                break  # Wait for human player
                
            if player.declared != 0:
                continue  # Already declared
                
            # Bot declares
            await self._bot_declare(player, i)
            
            # Small delay for UI
            await asyncio.sleep(0.5)
            
    async def _bot_declare(self, bot: Player, position: int):
        """Make a bot declaration"""
        from backend.socket_manager import broadcast
        
        try:
            # Get previous declarations
            previous_declarations = [
                p.declared for p in self.game.players if p.declared != 0
            ]
            
            # Check if last player
            is_last = position == len(self.game.players) - 1
            
            # Calculate declaration
            value = ai.choose_declare(
                hand=bot.hand,
                is_first_player=(position == 0),
                position_in_order=position,
                previous_declarations=previous_declarations,
                must_declare_nonzero=(bot.zero_declares_in_a_row >= 2),
                verbose=False
            )
            
            # Apply last player rule
            if is_last:
                total_so_far = sum(p.declared for p in self.game.players if p.declared != 0)
                forbidden = 8 - total_so_far
                if value == forbidden and 0 <= forbidden <= 8:
                    print(f"⚠️ Bot {bot.name} cannot declare {value} (total would be 8)")
                    value = 1 if forbidden != 1 else 2
            
            # Apply declaration
            result = self.game.declare(bot.name, value)
            
            if result["status"] == "ok":
                # Broadcast to all clients
                await broadcast(self.room_id, "declare", {
                    "player": bot.name,
                    "value": value,
                    "is_bot": True
                })
                
                print(f"✅ Bot {bot.name} declared {value}")
                
                # Check if more bots need to declare
                await self._handle_declaration_phase(bot.name)
                
        except Exception as e:
            print(f"❌ Bot {bot.name} declaration error: {e}")
            import traceback
            traceback.print_exc()
            # Fallback declaration
            try:
                self.game.declare(bot.name, 1)
                await broadcast(self.room_id, "declare", {
                    "player": bot.name,
                    "value": 1,
                    "is_bot": True
                })
            except:
                pass
                
    async def _handle_round_start(self):
        """Handle start of a new round"""
        # Check if starter is a bot
        starter = self.game.current_order[0] if self.game.current_order else None
        if starter and starter.is_bot:
            print(f"🤖 Round starter is bot: {starter.name}")
            await asyncio.sleep(1)
            await self._handle_declaration_phase("")  # Empty string to start from beginning
            
    async def _handle_play_phase(self, last_player: str):
        """Handle bot plays in turn order"""
        from backend.socket_manager import broadcast
        
        if not self.game.required_piece_count:
            return  # First player hasn't set the count yet
            
        # Get current turn order
        turn_order = self.game.turn_order
        if not turn_order:
            return
            
        # Find next players to play
        last_index = self._get_player_index(last_player, turn_order)
        
        for i in range(last_index + 1, len(turn_order)):
            player = turn_order[i]
            
            # Check if already played this turn
            if any(play.player == player for play in self.game.current_turn_plays):
                continue
                
            if not player.is_bot:
                break  # Wait for human
                
            # Bot plays
            await self._bot_play(player)
            await asyncio.sleep(0.5)
            
    async def _bot_play(self, bot: Player):
        """Make a bot play"""
        from backend.socket_manager import broadcast
        
        try:
            # Choose play
            selected = ai.choose_best_play(
                bot.hand,
                required_count=self.game.required_piece_count,
                verbose=True
            )
            
            # Get indices
            indices = self._get_piece_indices(bot.hand, selected)
            
            # Make play
            result = self.game.play_turn(bot.name, indices)
            
            # Broadcast play
            await broadcast(self.room_id, "play", {
                "player": bot.name,
                "pieces": [str(p) for p in selected],
                "valid": result.get("is_valid", True),
                "play_type": result.get("play_type", "UNKNOWN")
            })
            
            # Handle turn resolution if complete
            if result.get("status") == "resolved":
                await self._handle_turn_resolved(result)
                
        except Exception as e:
            print(f"❌ Bot {bot.name} play error: {e}")
            import traceback
            traceback.print_exc()
            
    async def _handle_turn_resolved(self, result: dict):
        """Handle end of turn"""
        from backend.socket_manager import broadcast
        
        await broadcast(self.room_id, "turn_resolved", {
            "plays": result["plays"],
            "winner": result["winner"],
            "pile_count": result["pile_count"]
        })
        
        # Check if round is complete
        if all(len(p.hand) == 0 for p in self.game.players):
            await self._handle_round_complete()
        elif result["winner"]:
            # Start next turn with winner
            await asyncio.sleep(0.5)
            await self._handle_turn_start(result["winner"])
            
    async def _handle_round_complete(self):
        """Handle round scoring"""
        from backend.socket_manager import broadcast
        from engine.win_conditions import is_game_over, get_winners
        
        summary = self.game.score_round()
        game_over = is_game_over(self.game)
        winners = get_winners(self.game) if game_over else []
        
        await broadcast(self.room_id, "score", {
            "summary": summary,
            "game_over": game_over,
            "winners": [p.name for p in winners]
        })
        
        if not game_over:
            # Start next round
            await asyncio.sleep(2)
            round_data = self.game.prepare_round()
            await broadcast(self.room_id, "start_round", {
                "round": round_data["round"],
                "starter": round_data["starter"],
                "hands": round_data["hands"],
                "players": [
                    {
                        "name": p.name,
                        "score": p.score,
                        "is_bot": p.is_bot,
                        "zero_declares_in_a_row": p.zero_declares_in_a_row
                    }
                    for p in self.game.players
                ]
            })
            await self._handle_round_start()
            
    async def _handle_turn_start(self, starter_name: str):
        """Handle start of a new turn"""
        print(f"🎮 Bot Manager: Handling turn start for {starter_name}")
        
        starter = self.game.get_player(starter_name)
        if not starter:
            print(f"❌ Starter {starter_name} not found")
            return
            
        if starter.is_bot and len(starter.hand) > 0:
            print(f"🤖 Bot {starter_name} will play first")
            # Bot starts the turn
            await self._bot_play_first(starter)
        else:
            print(f"👤 Human player {starter_name} starts, waiting for their play")
            
    async def _bot_play_first(self, bot: Player):
        """Bot plays as first player"""
        from backend.socket_manager import broadcast
        
        try:
            print(f"🤖 Bot {bot.name} choosing first play...")
            
            # Reset turn state
            self.game.current_turn_plays = []
            self.game.required_piece_count = None
            
            # Choose play
            selected = ai.choose_best_play(bot.hand, required_count=None, verbose=True)
            indices = self._get_piece_indices(bot.hand, selected)
            
            print(f"🤖 Bot {bot.name} will play {len(selected)} pieces: {[str(p) for p in selected]}")
            
            # Make the play
            result = self.game.play_turn(bot.name, indices)
            
            # Broadcast the play
            await broadcast(self.room_id, "play", {
                "player": bot.name,
                "pieces": [str(p) for p in selected],
                "valid": result.get("is_valid", True),
                "play_type": result.get("play_type", "UNKNOWN")
            })
            
            print(f"✅ Bot {bot.name} played, status: {result.get('status')}")
            
            # If waiting for other players, trigger their plays
            if result.get("status") == "waiting":
                print(f"🎯 Waiting for other players to respond with {len(selected)} pieces")
                await asyncio.sleep(0.5)
                await self._handle_play_phase(bot.name)
                
        except Exception as e:
            print(f"❌ Bot {bot.name} first play error: {e}")
            import traceback
            traceback.print_exc()
            
    def _get_declaration_order(self) -> List[Player]:
        """Get players in declaration order"""
        return self.game.current_order
        
    def _get_player_index(self, player_name: str, order: List[Player]) -> int:
        """Find player index in order"""
        for i, p in enumerate(order):
            if p.name == player_name:
                return i
        return -1
        
    def _get_piece_indices(self, hand: List, selected: List) -> List[int]:
        """Convert selected pieces to indices"""
        indices = []
        hand_copy = list(hand)
        for piece in selected:
            if piece in hand_copy:
                idx = hand_copy.index(piece)
                indices.append(idx)
                hand_copy[idx] = None  # Mark as used
        return indices