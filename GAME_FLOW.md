graph TD
    A[Game Started] --> B[Round Preparation]
    
    B --> B1[Deal 8 pieces to each player]
    B1 --> B2[Check for redeal requests]
    B2 --> B3{Redeal requested?}
    B3 -->|Yes| B4[Increase multiplier<br/>Redeal pieces] --> B1
    B3 -->|No| C[Determine starter]
    
    C --> C1{Previous round winner?}
    C1 -->|Yes| C2[Previous winner starts]
    C1 -->|No| C3[Player with RED_GENERAL starts]
    C2 --> D[Declaration Phase]
    C3 --> D
    
    D --> D1[Each player declares target piles]
    D1 --> D2{All declared?}
    D2 -->|No| D1
    D2 -->|Yes| D3[Validate total ≠ 8]
    D3 --> E[Turn Phase Start]
    
    E --> E1[First player plays pieces]
    E1 --> E2[Frontend validates: Must be valid play]
    E2 --> E3{Valid play?}
    E3 -->|No| E1
    E3 -->|Yes| E4[Backend processes & broadcasts play type]
    E4 --> E5[Other 3 players can play simultaneously]
    
    E5 --> E6[Players 2-4 submit pieces concurrently]
    E6 --> E7[Frontend validates: Must match piece count]
    E7 --> E8{All 3 submitted?}
    E8 -->|No| E6
    E8 -->|Yes| E9[Backend calculates turn winner]
    
    E9 --> E10[Apply turn order logic for tie-breaking]
    E10 --> E11[Winner takes pile]
    E11 --> E12{Any player has pieces left?}
    E12 -->|Yes| E13[Winner becomes first player] --> E1
    E12 -->|No| F[Round Scoring]
    
    F --> F1[Calculate each player's score]
    F1 --> F2[Compare declared vs actual piles]
    F2 --> F3[Apply bonus/penalty rules]
    F3 --> F4[Apply redeal multiplier]
    F4 --> F5[Update total scores]
    F5 --> G[Check Win Conditions]
    
    G --> G1{Player ≥ 50 points?}
    G1 -->|Yes| H[Game Over - Declare Winner]
    G1 -->|No| G2{Round ≥ 20?}
    G2 -->|Yes| H
    G2 -->|No| I[Start Next Round] --> B
    
    H --> END[End Game]
    
    %% Styling
    classDef startEnd fill:#e1f5fe
    classDef process fill:#f3e5f5
    classDef decision fill:#fff3e0
    classDef validation fill:#ffebee
    classDef concurrent fill:#e8f5e8
    
    class A,END startEnd
    class B1,B4,C2,C3,D1,E4,E11,F1,F2,F3,F4,F5 process
    class B3,C1,D2,E3,G1,G2,E8,E12 decision
    class E2,E7 validation
    class E5,E6 concurrent