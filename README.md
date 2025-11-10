# Secret Hitler AI - Multi-Agent Game Simulation

## Overview

An advanced Python implementation of the board game Secret Hitler featuring autonomous AI agents powered by OpenAI's GPT models. This project demonstrates sophisticated multi-agent interaction, strategic decision-making, and natural language processing in a complex social deduction game environment.

## Features

### Core Game Implementation
- **Full rule compliance** with the official Secret Hitler game mechanics
- **5-6 player configuration** with proper role visibility rules
- **Legislative session tracking** with deck management and card counting
- **Presidential powers** implementation (Investigation, Special Election, Execution)
- **Chaos government** system after three failed votes
- **Win condition detection** for both Liberal and Fascist teams

### AI Agent System
- **Role-aware AI agents** with distinct personalities and play styles
- **Context-aware decision making** using game history and observations
- **Natural language generation** for table talk and bluffing
- **Memory management system** for tracking accusations and voting patterns
- **Strategic voting** based on role objectives and game state
- **Dynamic claiming strategies** during legislative sessions

### Technical Architecture
- **Structured output models** using Pydantic for type-safe AI responses
- **Fallback mechanisms** for robust error handling in AI decisions
- **State invariant checking** for deck integrity and game consistency
- **Modular design** with clear separation of concerns
- **Human-AI hybrid gameplay** allowing human participation

## Installation

### Prerequisites
```bash
# Python 3.8 or higher
pip install openai pydantic
```

### Setup
1. Clone the repository
2. Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```
3. Run the game:
```bash
python secret_hitler_ai.py
```

## How to Play

1. **Setup Phase**: Choose the number of AI players (minimum 4)
2. **Role Assignment**: You'll be assigned a secret role (Liberal, Fascist, or Hitler)
3. **Game Loop**:
   - Presidents nominate Chancellors
   - Players vote on the government
   - Elected governments enact policies
   - Players claim what cards they saw
   - Discussion and deduction occur
4. **Victory**: Liberals win by enacting 5 Liberal policies or assassinating Hitler. Fascists win by enacting 6 Fascist policies or electing Hitler as Chancellor after 3 Fascist policies.

## AI Agent Behavior

### Personality System
Each AI agent has a unique personality combining:
- **Background traits**: board-game addict, data nerd, grad student, meme lover, etc.
- **Communication styles**: accusatory, calm, joking, analytical, defensive, etc.

### Decision Making Process
1. **Context Building**: Agent receives full game state, recent history, and role information
2. **Strategic Analysis**: Evaluates options based on team objectives
3. **Action Selection**: Makes decisions that balance winning with avoiding detection
4. **Natural Communication**: Generates contextually appropriate comments

### Memory and Learning
- Agents remember key events (votes, claims, accusations)
- Limited memory buffer (20 items) simulates human-like recall
- Pattern recognition for identifying suspicious behavior

## Code Structure

### Core Components

#### `Player` Class
- Manages individual player state (role, memory, status)
- Implements visibility rules based on game configuration
- Generates system prompts for AI decision-making

#### `Table` Class
- Maintains global game state
- Handles deck management and reshuffling
- Tracks government history and failed votes
- Validates game invariants

#### `AIDecision` Model
- Structured output format for AI responses
- Supports multiple action types (vote, nominate, discard, enact)
- Includes optional text generation for roleplay

#### AI Functions
- `ai_decide()`: Core decision-making engine
- `ai_comment()`: Natural language generation for table talk
- Robust error handling with sensible defaults

## Technical Highlights

### Advanced Features
- **Type-safe AI interactions** using Pydantic models
- **Contextual prompting** with role-specific instructions
- **Graceful degradation** when AI calls fail
- **State consistency checking** throughout gameplay
- **Dynamic personality generation** for replay value

### Performance Optimizations
- Efficient memory management with bounded buffers
- Minimal API calls through batched context
- Smart fallback strategies to prevent game interruption

## Game Statistics & Balance

- **Deck composition**: 11 Fascist, 6 Liberal policies
- **Role distribution**: 1 Hitler, 1-2 Fascists, 3-4 Liberals
- **Win rate tracking** (can be extended)
- **Decision pattern analysis** (can be extended)



## Contributing

Contributions are welcome! Areas of interest:
- AI strategy improvements


## License

This project is for educational purposes. Secret Hitler is a game by Goat, Wolf, & Cabbage LLC.

## Acknowledgments

- OpenAI for GPT API access
- Secret Hitler game designers
- Python community for excellent libraries

---

## Technical Notes

### API Usage
- Uses OpenAI's structured output feature for reliable parsing
- Implements retry logic and fallback mechanisms
- Optimized token usage through context management

### Error Handling
- Comprehensive exception catching in AI calls
- Sensible default behaviors for all actions
- Game state recovery mechanisms

### Testing Considerations
- Modular design facilitates unit testing
- State invariant checks act as runtime assertions
- Reproducible games through seed management (can be added)
