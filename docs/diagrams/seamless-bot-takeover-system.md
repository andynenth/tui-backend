# Seamless Bot Takeover System

```mermaid
stateDiagram-v2
    [*] --> HumanControl: Join Game

    HumanControl --> BotControl: Disconnect (In-Game)
    HumanControl --> [*]: Disconnect (Pre-Game)

    BotControl --> HumanControl: Reconnect
    BotControl --> RoomCleanup: All Disconnected

    RoomCleanup --> [*]: Timeout

    state HumanControl {
        Human: Human Playing
        Connected: Connected = True
        Bot: is_bot = False
    }

    state BotControl {
        BotActive: Bot Playing
        Disconnected: Connected = False
        BotFlag: is_bot = True
        Preserved: Original State Saved
    }
```
