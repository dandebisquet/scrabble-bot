# Scrabbler — Scrabble Game + Bot (Python / Tkinter)

A desktop Scrabble-style game built in **Python** with a **Tkinter GUI**.  
Includes standard Scrabble board bonuses, scoring logic (including bingos), move validation, and a bot that can **suggest** or **play** moves using a **trie-based search** (with wildcard/blank tile support).

## Features
- Tkinter GUI with a rendered 15×15 board
- Standard Scrabble bonus squares:
  - Double/Triple Letter (DL/TL)
  - Double/Triple Word (DW/TW)
  - Center star
- Full move validation:
  - first move must cover center
  - subsequent moves must connect to existing tiles
  - prevents conflicts with existing letters
  - validates all formed cross-words
- Scoring:
  - letter values + board multipliers
  - bingo bonus (+50 for using all 7 tiles)
- Game modes:
  - **1 vs 1**
  - **Player vs Bot**
  - **Practice (Free Play)** with “Bot Suggest”
- Quality-of-life:
  - preview placement as you type (ghost letters)
  - highlight last move
  - undo last move
  - pass / exchange tiles

## Bot / AI Approach
The bot searches for the best-scoring move based on:
- current rack letters (including `_` blank tiles)
- anchor squares adjacent to existing tiles (or center on first move)
- a **Trie (prefix tree)** for fast word generation and pruning
- scoring evaluation using the same board rules as the player

This is a brute-force style search with trie pruning rather than a deep strategy engine, but it produces strong “best move” suggestions for many mid-game positions.

## Requirements
- Python 3.9+ recommended
- Dependencies:
  - Pillow (PIL) for drawing the board and tiles

Install:
```bash
pip install -r requirements.txt
