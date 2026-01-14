import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk
import random
from tkinter import ttk
import threading

tile_bag = None

LETTER_VALUES = {
    'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
    'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3,
    'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
    'Y': 4, 'Z': 10
}

class Tile:
    #Represents a single Scrabble tile with a letter and point value.

    def __init__(self, letter, value):
        self.letter = letter.upper()
        self.value = value

class TileBag:
    #Manages the bag of tiles: creation, shuffling, and drawing tiles.

    def __init__(self):
        self.tiles = self._generate_tiles()

    def _generate_tiles(self):
        #Generate the full set of Scrabble tiles according to distribution.
        distribution = {
            'A': 9, 'B': 2, 'C': 2, 'D': 4, 'E': 12, 'F': 2, 'G': 3, 'H': 2,
            'I': 9, 'J': 1, 'K': 1, 'L': 4, 'M': 2, 'N': 6, 'O': 8, 'P': 2,
            'Q': 1, 'R': 6, 'S': 4, 'T': 6, 'U': 4, 'V': 2, 'W': 2, 'X': 1,
            'Y': 2, 'Z': 1, '_': 2  
        }
        tiles = []
        for letter, count in distribution.items():
            value = 0 if letter == '_' else LETTER_VALUES.get(letter, 0)
            tiles.extend([Tile(letter, value)] * count)
        random.shuffle(tiles)
        return tiles

    def draw_tiles(self, count):
        return [self.tiles.pop() for _ in range(min(count, len(self.tiles)))]

class Board:
    #Represents the Scrabble board, manages tile placement, drawing, and word finding.

    def __init__(self, size=15, cell_size=40):
        self.size = size
        self.cell_size = cell_size
        self.image_size = size * cell_size
        self.board = [[None for _ in range(size)] for _ in range(size)]
        self.font = ImageFont.truetype("arial.ttf", 24)
        self.bonus = self._init_bonus_board()

    def _init_bonus_board(self):
        # Standard Scrabble board layout
        layout = [
            ['TW','','','DL','','','','TW','','','','DL','','','TW'],
            ['','DW','','','','TL','','','','TL','','','','DW',''],
            ['','','DW','','','','DL','','DL','','','','DW','',''],
            ['DL','','','DW','','','','DL','','','','DW','','','DL'],
            ['','','','','DW','','','','','','DW','','','',''],
            ['','','DL','','','','DL','','DL','','','','DL','',''],
            ['','','','DL','','','','DL','','','','DL','','',''],
            ['TW','','DL','','','','DW','*','DW','','','','DL','','TW'],
            ['','','','DL','','','','DL','','','','DL','','',''],
            ['','','DL','','','','DL','','DL','','','','DL','',''],
            ['','','','','DW','','','','','','DW','','','',''],
            ['DL','','','DW','','','','DL','','','','DW','','','DL'],
            ['','','DW','','','','DL','','DL','','','','DW','',''],
            ['','DW','','','','TL','','','','TL','','','','DW',''],
            ['TW','','','DL','','','','TW','','','','DL','','','TW'],
        ]
        return layout

    def can_place_word(self, word, row, col, direction='H'):
        #Check if a word can be placed at the given position and direction.
        for i, letter in enumerate(word.upper()):
            r, c = (row, col + i) if direction == 'H' else (row + i, col)
            if r >= self.size or c >= self.size or (self.board[r][c] and self.board[r][c] != letter):
                return False
        return True

    def place_word(self, word, row, col, direction='H'):
        #Place a word on the board at the given position and direction.
        for i, letter in enumerate(word.upper()):
            r, c = (row, col + i) if direction == 'H' else (row + i, col)
            self.board[r][c] = letter

    def draw_board_image(self, highlight_positions=None):
        #Draw the board as an image, highlighting certain positions.
        img = Image.new("RGB", (self.image_size, self.image_size), "white")
        draw = ImageDraw.Draw(img)
        colors = {
            'TW': "#ff6666",  # Red
            'DW': "#ffcccc",  # Pink
            'TL': "#3399ff",  # Blue
            'DL': "#99ccff",  # Light blue
            '*': "#ffe066",   # Center star
            '': "lightyellow"
        }
        highlight_set = set(highlight_positions) if highlight_positions else set()
        for r in range(self.size):
            for c in range(self.size):
                x0 = c * self.cell_size
                y0 = r * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size
                bonus = self.bonus[r][c]
                fill = colors.get(bonus, "lightyellow")
                if (r, c) in highlight_set:
                    # Highlight with a border
                    draw.rectangle([x0, y0, x1, y1], outline="gold", width=4, fill=fill)
                else:
                    draw.rectangle([x0, y0, x1, y1], outline="black", fill=fill)
                letter = self.board[r][c]
                if letter:
                    bbox = draw.textbbox((0, 0), letter, font=self.font)
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                    draw.text(
                        (x0 + (self.cell_size - w) / 2, y0 + (self.cell_size - h) / 2),
                        letter, fill="black", font=self.font
                    )
        return img

    def get_words_formed(self, word, row, col, direction):
        #Returns a list of (word, [(r, c, letter), ...]) for all words formed by this placement.
        words = []
        main_word_positions = []
        # Main word
        for i, letter in enumerate(word.upper()):
            r, c = (row, col + i) if direction == 'H' else (row + i, col)
            main_word_positions.append((r, c, letter))
        def extend(r, c, dr, dc):
            #Find the full main word (could be longer if connecting to existing letters)
            while 0 <= r-dr < self.size and 0 <= c-dc < self.size and self.board[r-dr][c-dc]:
                r -= dr
                c -= dc
            word = ""
            positions = []
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r][c]:
                word += self.board[r][c]
                positions.append((r, c, self.board[r][c]))
                r += dr
                c += dc
            return word, positions

        #Place the word temporarily
        placed = []
        for r, c, letter in main_word_positions:
            if self.board[r][c] is None:
                self.board[r][c] = letter
                placed.append((r, c))
        if direction == 'H':
            main_word, main_positions = extend(row, col, 0, 1)
        else:
            main_word, main_positions = extend(row, col, 1, 0)
        words.append((main_word, main_positions))
        for i, (r, c, letter) in enumerate(main_word_positions):

            if (r, c) in placed:
                if direction == 'H':
                    cross_word, cross_positions = extend(r, c, 1, 0)
                else:
                    cross_word, cross_positions = extend(r, c, 0, 1)
                if len(cross_word) > 1:
                    words.append((cross_word, cross_positions))

        for r, c in placed:
            self.board[r][c] = None
        return words

    def is_connected(self, word, row, col, direction):
        #Returns True if the word connects to any existing tile (except for the first move)
        for i, letter in enumerate(word.upper()):
            r, c = (row, col + i) if direction == 'H' else (row + i, col)
            if self.board[r][c] is not None:
                return True
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    if self.board[nr][nc] is not None:
                        return True
        return False

class Player:
    #Represents a player: manages their rack, score, and move logic.

    def __init__(self, name):
        self.name = name
        self.tiles = []
        self.score = 0

    def draw_tiles(self, tile_bag, count):
        self.tiles += tile_bag.draw_tiles(count)

    def has_tiles_for_word(self, word, row, col, direction, board):
        #Check if the player has the necessary tiles to play the word.

        temp_tiles = [tile.letter for tile in self.tiles]
        for i, letter in enumerate(word.upper()):
            r, c = (row, col + i) if direction == 'H' else (row + i, col)
            if board.board[r][c] == letter:
                continue
            if letter in temp_tiles:
                temp_tiles.remove(letter)
            elif '_' in temp_tiles:
                temp_tiles.remove('_')
            else:
                return False
        return True

    def play_word(self, word, row, col, direction, board, dictionary):
        #Attempt to play a word on the board, update score and rack if successful.
        if not dictionary.is_valid(word):
            print("Word not in dictionary!")
            return False
        if not self.has_tiles_for_word(word, row, col, direction, board):
            print("You don't have the tiles for that word!")
            return False
        if not board.can_place_word(word, row, col, direction):
            print("Can't place word there!")
            return False

        center = board.size // 2
        is_first_move = all(all(cell is None for cell in row_) for row_ in board.board)
        if is_first_move:
            covers_center = False
            for i in range(len(word)):
                r, c = (row, col + i) if direction == 'H' else (row + i, col)
                if r == center and c == center:
                    covers_center = True
                    break
            if not covers_center:
                print("First word must cover the center square!")
                return False
        else:
            if not board.is_connected(word, row, col, direction):
                print("Word must connect to existing tiles on the board.")
                return False

        words_formed = board.get_words_formed(word, row, col, direction)
        for w, _ in words_formed:
            if not dictionary.is_valid(w):
                print(f"Formed word '{w}' is not valid!")
                return False

        placed_positions = []
        for i, letter in enumerate(word.upper()):
            r, c = (row, col + i) if direction == 'H' else (row + i, col)
            if board.board[r][c] is None:
                placed_positions.append((r, c, letter))

        board.place_word(word, row, col, direction)

        total_score = 0
        for w, positions in words_formed:
            word_score = 0
            word_multiplier = 1
            for r, c, letter in positions:
                letter_score = LETTER_VALUES[letter]
                if (r, c, letter) in placed_positions:
                    bonus = board.bonus[r][c]
                    if bonus == 'DL':
                        letter_score *= 2
                    elif bonus == 'TL':
                        letter_score *= 3
                    if bonus == 'DW':
                        word_multiplier *= 2
                    elif bonus == 'TW':
                        word_multiplier *= 3
                    elif bonus == '*':
                        word_multiplier *= 2  #Center is double word
                word_score += letter_score
            word_score *= word_multiplier
            total_score += word_score

        #Remove used tiles from player's rack
        for _, _, letter in placed_positions:
            for tile in self.tiles:
                if tile.letter == letter:
                    self.tiles.remove(tile)
                    break
            else:
                for tile in self.tiles:
                    if tile.letter == '_':
                        self.tiles.remove(tile)
                        break

        #Bingo bonus
        tiles_used = len(placed_positions)
        if tiles_used == 7:
            total_score += 50

        #Draw new tiles to refill rack to 7
        global tile_bag
        if hasattr(board, 'tile_bag'):
            tile_bag = board.tile_bag
        tiles_needed = 7 - len(self.tiles)
        if tiles_needed > 0:
            self.tiles += tile_bag.draw_tiles(tiles_needed)

        self.score += total_score
        print(f"{self.name} played {word} for {total_score} points! Total: {self.score}")
        return True

class Dictionary:
    #Loads and checks valid words, and builds a trie for fast lookup.

    def __init__(self, word_list):
        self.words = set(word.strip().lower() for word in word_list)
        self.trie = Trie()
        for word in self.words:
            self.trie.insert(word.upper())

    def is_valid(self, word):
        #Check if a word is valid (in the dictionary).
        return word.lower() in self.words

class TrieNode:
    #Node for the Trie data structure (used for fast word search).

    def __init__(self):
        self.children = {}
        self.is_word = False

class Trie:
    #Trie (prefix tree) for efficient word and prefix lookup.

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        #Insert a word into the trie.
        node = self.root
        for letter in word:
            if letter not in node.children:
                node.children[letter] = TrieNode()
            node = node.children[letter]
        node.is_word = True

    def has_prefix(self, prefix):
        #Check if a prefix exists in the trie.
        node = self.root
        for letter in prefix:
            if letter not in node.children:
                return False
            node = node.children[letter]
        return True

    def has_word(self, word):
        #Check if a word exists in the trie.
        node = self.root
        for letter in word:
            if letter not in node.children:
                return False
            node = node.children[letter]
        return node.is_word

class ScrabbleGUI:
    #The main GUI class: handles the board display, user input, and game controls.

    def __init__(self, root, board, players, dictionary, mode="1v1"):
        self.root = root
        self.board = board
        self.players = players
        self.current_player_idx = 0
        self.player = self.players[self.current_player_idx]
        self.dictionary = dictionary
        self.direction = 'H'
        self.selected = None
        self.preview_word = ""
        self.preview_pos = None
        self.preview_dir = 'H'
        self.mode = mode

        #For undo/redo and highlighting last move
        self.move_history = []
        self.last_move_highlight = []

        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, width=board.image_size, height=board.image_size)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

        controls = tk.Frame(main_frame)
        controls.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.word_entry = tk.Entry(controls)
        self.word_entry.pack(pady=5)
        self.word_entry.bind("<KeyRelease>", self.on_word_entry)

        self.dir_button = tk.Button(controls, text="Direction: Horizontal", command=self.toggle_direction)
        self.dir_button.pack(pady=5)

        self.confirm_button = tk.Button(controls, text="Confirm", command=self.confirm_word)
        self.confirm_button.pack(pady=5)

        #Only show Pass, Exchange, Undo in 1v1 and PvE
        if self.mode in ("1v1", "pve"):
            self.pass_button = tk.Button(controls, text="Pass", command=self.pass_turn)
            self.pass_button.pack(pady=5)
            self.exchange_button = tk.Button(controls, text="Exchange Tiles", command=self.exchange_tiles)
            self.exchange_button.pack(pady=5)
            self.undo_button = tk.Button(controls, text="Undo", command=self.undo_move)
            self.undo_button.pack(pady=5)

        #Only show Bot Suggest in Practice mode
        if self.mode == "practice":
            self.bot_button = tk.Button(controls, text="Bot Suggest", command=self.suggest_bot_move)
            self.bot_button.pack(pady=5)
            self.bot_suggestion = tk.Label(controls, text="")
            self.bot_suggestion.pack(pady=5)


        #Status and remaining tiles
        self.status = tk.Label(controls, text=self.status_text())
        self.status.pack(pady=5)
        self.tiles_left_label = tk.Label(controls, text=self.tiles_left_text())
        self.tiles_left_label.pack(pady=5)

        self.scoreboard_label = tk.Label(controls, text=self.scoreboard_text(), font=("Arial", 12, "bold"), justify="left")
        self.scoreboard_label.pack(pady=10)

        legend_frame = tk.LabelFrame(controls, text="Board Key", padx=5, pady=5)
        legend_frame.pack(pady=10, fill=tk.X)
        legend_items = [
            ("Triple Word", "#ff6666"),
            ("Double Word", "#ffcccc"),
            ("Triple Letter", "#3399ff"),
            ("Double Letter", "#99ccff"),
            ("Center", "#ffe066"),
        ]
        for label, color in legend_items:
            item_frame = tk.Frame(legend_frame)
            item_frame.pack(anchor="w", pady=1)
            color_box = tk.Canvas(item_frame, width=20, height=20, bg=color, highlightthickness=1, highlightbackground="black")
            color_box.pack(side=tk.LEFT)
            tk.Label(item_frame, text=label, anchor="w").pack(side=tk.LEFT, padx=5)

        self.update_board()
    
    


    def status_text(self):
        #Return a string describing the current player's turn, score, and tiles.
        return f"{self.player.name}'s turn | Score: {self.player.score} | Tiles: " + " ".join([t.letter for t in self.player.tiles])

    def tiles_left_text(self):
        #Return a string showing how many tiles are left in the bag.
        global tile_bag
        return f"Tiles left in bag: {len(tile_bag.tiles)}"

    def update_board(self):
        #Redraw the board and update all status displays.
        img = self.board.draw_board_image(highlight_positions=self.last_move_highlight)
        draw = ImageDraw.Draw(img, "RGBA")
        if self.preview_word and self.preview_pos:
            row, col = self.preview_pos
            for i, letter in enumerate(self.preview_word):
                r, c = (row, col + i) if self.preview_dir == 'H' else (row + i, col)
                if 0 <= r < self.board.size and 0 <= c < self.board.size:
                    if self.board.board[r][c] is None:
                        x0 = c * self.board.cell_size
                        y0 = r * self.board.cell_size
                        bbox = draw.textbbox((0, 0), letter, font=self.board.font)
                        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        txt_img = Image.new("RGBA", (self.board.cell_size, self.board.cell_size), (255,255,255,0))
                        txt_draw = ImageDraw.Draw(txt_img)
                        txt_draw.text(
                            ((self.board.cell_size - w) / 2, (self.board.cell_size - h) / 2),
                            letter, fill=(0,0,0,120), font=self.board.font
                        )
                        img.paste(txt_img, (x0, y0), txt_img)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        self.status.config(text=self.status_text())
        self.tiles_left_label.config(text=self.tiles_left_text())
        self.scoreboard_label.config(text=self.scoreboard_text())

    def on_click(self, event):
        #Handle a click on the board to select a starting position.
        row = event.y // self.board.cell_size
        col = event.x // self.board.cell_size
        self.selected = (row, col)
        self.preview_pos = (row, col)
        self.preview_word = self.word_entry.get().strip().upper()
        self.preview_dir = self.direction
        self.update_board()
        self.status.config(text=f"Selected: ({row},{col}) | Tiles: " + " ".join([t.letter for t in self.player.tiles]))

    def toggle_direction(self):
        #Toggle the word placement direction between horizontal and vertical.
        self.direction = 'V' if self.direction == 'H' else 'H'
        self.preview_dir = self.direction
        self.dir_button.config(text=f"Direction: {'Horizontal' if self.direction == 'H' else 'Vertical'}")
        self.preview_word = self.word_entry.get().strip().upper()
        self.update_board()
        
    def on_word_entry(self, event):
        #Update the preview word as the user types.
        self.preview_word = self.word_entry.get().strip().upper()
        self.update_board()

    def switch_player(self):
        #Switch to the next player's turn and update the display.
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.player = self.players[self.current_player_idx]
        self.status.config(text=self.status_text())
        self.selected = None
        self.preview_word = ""
        self.preview_pos = None
        self.update_board()
        self.after_switch_player()
        self.check_game_end()

    def confirm_word(self):
        # Confirm and play the word entered by the player, updating game state.
        word = self.word_entry.get().strip().upper()
        if not self.selected:
            messagebox.showwarning("Select a position", "Please select a position on the board.")
            return
        row, col = self.selected

        board_snapshot = [row_[:] for row_ in self.board.board]
        player_tiles_snapshot = [Tile(t.letter, t.value) for t in self.player.tiles]
        player_score_snapshot = self.player.score
        bag_snapshot = tile_bag.tiles[:]

        try:
            # Check if word fits on the board
            if self.direction == 'H' and col + len(word) > self.board.size:
                raise ValueError("Word goes out of bounds horizontally.")
            if self.direction == 'V' and row + len(word) > self.board.size:
                raise ValueError("Word goes out of bounds vertically.")

            # Check if word can be placed (no conflicting letters)
            if not self.board.can_place_word(word, row, col, self.direction):
                raise ValueError("Word cannot be placed here (conflicts with existing tiles).")

            # Check if player has the tiles
            if not self.player.has_tiles_for_word(word, row, col, self.direction, self.board):
                raise ValueError("You don't have the tiles for that word.")

            # Check if word is in dictionary
            if not self.dictionary.is_valid(word):
                raise ValueError("Word not in dictionary.")

            # First word must cover center
            center = self.board.size // 2
            is_first_move = all(all(cell is None for cell in row_) for row_ in self.board.board)
            if is_first_move:
                covers_center = False
                for i in range(len(word)):
                    r, c = (row, col + i) if self.direction == 'H' else (row + i, col)
                    if r == center and c == center:
                        covers_center = True
                        break
                if not covers_center:
                    raise ValueError("First word must cover the center square.")
            else:
                # All subsequent words must connect to existing tiles
                if not self.board.is_connected(word, row, col, self.direction):
                    raise ValueError("Word must connect to existing tiles on the board.")

            # Check all words formed are valid
            words_formed = self.board.get_words_formed(word, row, col, self.direction)
            for w, _ in words_formed:
                if not self.dictionary.is_valid(w):
                    raise ValueError(f"Formed word '{w}' is not valid.")

            # If all checks pass, play the word
            if self.player.play_word(word, row, col, self.direction, self.board, self.dictionary):
                placed_positions = []
                for i, letter in enumerate(word):
                    r, c = (row, col + i) if self.direction == 'H' else (row + i, col)
                    if board_snapshot[r][c] is None:
                        placed_positions.append((r, c))
                self.last_move_highlight = placed_positions

                self.move_history.append({
                    "board": [row_[:] for row_ in board_snapshot],
                    "tiles": [Tile(t.letter, t.value) for t in player_tiles_snapshot],
                    "score": player_score_snapshot,
                    "bag": bag_snapshot[:],
                    "player_idx": self.current_player_idx,
                    "highlight": placed_positions
                })
                self.word_entry.delete(0, tk.END)
                self.switch_player()
            else:
                raise ValueError("Could not play the word due to an unknown error.")

        except ValueError as ve:
            messagebox.showerror("Invalid move", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def pass_turn(self):
        #Pass the current player's turn.
        messagebox.showinfo("Pass", f"{self.player.name} passed their turn.")
        self.last_move_highlight = []
        self.switch_player()

    def exchange_tiles(self):
        #Exchange all tiles in the player's rack with new ones from the bag.
        if len(tile_bag.tiles) < 7:
            messagebox.showwarning("Not enough tiles", "Not enough tiles in the bag to exchange.")
            return
        old_tiles = self.player.tiles[:]
        tile_bag.tiles.extend(old_tiles)
        random.shuffle(tile_bag.tiles)
        self.player.tiles = tile_bag.draw_tiles(7)
        self.status.config(text=self.status_text())
        self.last_move_highlight = []
        self.update_board()
        messagebox.showinfo("Exchange", f"{self.player.name} exchanged all tiles!")
        self.switch_player()

    def undo_move(self):
        #Undo the last move, restoring the previous game state.
        if not self.move_history:
            messagebox.showinfo("Undo", "No move to undo.")
            return
        last = self.move_history.pop()
        self.board.board = [row_[:] for row_ in last["board"]]
        self.player.tiles = [Tile(t.letter, t.value) for t in last["tiles"]]
        self.player.score = last["score"]
        tile_bag.tiles = last["bag"][:]
        self.current_player_idx = last["player_idx"]
        self.player = self.players[self.current_player_idx]
        self.last_move_highlight = last["highlight"]
        self.update_board()
        self.status.config(text=self.status_text())
        self.tiles_left_label.config(text=self.tiles_left_text())

    def suggest_bot_move(self):
        #Suggest the best move for the current rack using the bot.
        self.bot_suggestion.config(text="Searching for best move...")

        def worker():
            bot = ScrabbleBot(self.player, self.dictionary)
            move = bot.find_best_move(self.board)
            def update_result():
                if move:
                    word, row, col, direction, score = move
                    self.bot_suggestion.config(
                        text=f"Best move: {word} at ({row},{col}) {direction} for {score} points"
                    )
                    self.preview_word = word
                    self.preview_pos = (row, col)
                    self.preview_dir = direction
                    self.update_board()
                else:
                    self.bot_suggestion.config(text="No valid moves found.")
            self.root.after(0, update_result)

        threading.Thread(target=worker, daemon=True).start()

    def after_switch_player(self):
        #If PvE and it's bot's turn, make the bot play automatically
        if hasattr(self, "bot_player_idx") and self.current_player_idx == self.bot_player_idx:
            self.root.after(500, self.bot_play_turn)

    def bot_play_turn(self):
        #Make the bot play its turn automatically.
        bot = ScrabbleBot(self.player, self.dictionary)
        move = bot.find_best_move(self.board)
        if move:
            word, row, col, direction, score = move
            self.player.play_word(word, row, col, direction, self.board, self.dictionary)
            #Find which tiles were placed
            placed_positions = []
            for i, letter in enumerate(word):
                r, c = (row, col + i) if direction == 'H' else (row + i, col)
                if self.board.board[r][c] == letter:
                    placed_positions.append((r, c))
            self.last_move_highlight = placed_positions
            self.update_board()
        self.switch_player()
    
    def scoreboard_text(self):
        #Return a formatted string showing all players' scores.
        return "Scoreboard:\n" + "\n".join(
            f"{p.name}: {p.score}" for p in self.players
        )

    def check_game_end(self):
        #Check if the game should end (no tiles left and a player has emptied their rack, or no valid moves)
        global tile_bag
        if len(tile_bag.tiles) == 0 and any(len(p.tiles) == 0 for p in self.players):
            self.show_end_screen()
            return True
        return False

    def show_end_screen(self):
        # Show the end screen with scores and winner
        end = tk.Toplevel(self.root)
        EndScreen(end, self.players)

class ScrabbleBot:
    #Suggests the best move for a player using a trie-based search (supports wildcards).

    def __init__(self, player, dictionary, progress=None):
        self.player = player
        self.dictionary = dictionary
        self.progress = progress

    def find_best_move(self, board):
        #Find the best possible move for the current rack and board.
        best_move = None
        best_score = 0
        rack_letters = [tile.letter for tile in self.player.tiles]
        anchors = set()
        for r in range(board.size):
            for c in range(board.size):
                if board.board[r][c] is not None:
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < board.size and 0 <= nc < board.size and board.board[nr][nc] is None:
                            anchors.add((nr, nc))
        if not anchors:
            anchors.add((board.size//2, board.size//2))

        def search(row, col, direction, node, prefix, rack, placed, start_row, start_col, used_blanks):
            #Recursive helper to build words using the trie and rack (supports wildcards).
            nonlocal best_move, best_score
            if node.is_word and placed:
                is_first_move = all(all(cell is None for cell in row_) for row_ in board.board)
                if not is_first_move and not board.is_connected(prefix, start_row, start_col, direction):
                    return
                if board.can_place_word(prefix, start_row, start_col, direction) and self.player.has_tiles_for_word(prefix, start_row, start_col, direction, board):
                    words_formed = board.get_words_formed(prefix, start_row, start_col, direction)
                    if all(self.dictionary.is_valid(w) for w, _ in words_formed):
                        placed_positions = []
                        for i, letter in enumerate(prefix):
                            r = start_row + (i if direction == 'V' else 0)
                            c = start_col + (i if direction == 'H' else 0)
                            if board.board[r][c] is None:
                                placed_positions.append((r, c, letter))
                        total_score = 0
                        for w, positions in words_formed:
                            word_score = 0
                            word_multiplier = 1
                            for r, c, letter in positions:
                                #If this letter was placed with a blank, its value is 0
                                is_blank = (r, c, letter) in used_blanks
                                letter_score = 0 if is_blank else LETTER_VALUES[letter]
                                if (r, c, letter) in placed_positions:
                                    bonus = board.bonus[r][c]
                                    if bonus == 'DL':
                                        letter_score *= 2
                                    elif bonus == 'TL':
                                        letter_score *= 3
                                    if bonus == 'DW':
                                        word_multiplier *= 2
                                    elif bonus == 'TW':
                                        word_multiplier *= 3
                                    elif bonus == '*':
                                        word_multiplier *= 2
                                word_score += letter_score
                            word_score *= word_multiplier
                            total_score += word_score
                        if total_score > best_score:
                            best_score = total_score
                            best_move = (prefix, start_row, start_col, direction, total_score)
            next_i = len(prefix)
            r = row + (next_i if direction == 'V' else 0)
            c = col + (next_i if direction == 'H' else 0)
            if r >= board.size or c >= board.size:
                return
            board_letter = board.board[r][c]
            if board_letter:
                if board_letter in node.children:
                    search(row, col, direction, node.children[board_letter], prefix + board_letter, rack, placed, start_row, start_col, used_blanks)
            else:
                used_this_level = set()
                for idx, letter in enumerate(rack):
                    if letter == '_':
                        #Try blank as every possible letter (A-Z)
                        for sub_letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                            if sub_letter in node.children and (sub_letter not in used_this_level):
                                used_this_level.add(sub_letter)
                                rack_copy = rack[:]
                                rack_copy.pop(idx)
                                #Track which position used a blank
                                search(row, col, direction, node.children[sub_letter], prefix + sub_letter, rack_copy, True, start_row, start_col, used_blanks + [(r, c, sub_letter)])
                    else:
                        if letter in node.children and (letter not in used_this_level):
                            used_this_level.add(letter)
                            rack_copy = rack[:]
                            rack_copy.pop(idx)
                            search(row, col, direction, node.children[letter], prefix + letter, rack_copy, True, start_row, start_col, used_blanks)
        for row, col in anchors:
            for direction in ['H', 'V']:
                for offset in range(0, 8):
                    start_row = row - (offset if direction == 'V' else 0)
                    start_col = col - (offset if direction == 'H' else 0)
                    if start_row < 0 or start_col < 0:
                        continue
                    search(start_row, start_col, direction, self.dictionary.trie.root, "", rack_letters, False, start_row, start_col, [])
        return best_move
    

class StartScreen:
    #The start screen for selecting game mode before launching the main GUI.

    def __init__(self, root, on_start):
        self.root = root
        self.on_start = on_start
        self.frame = tk.Frame(root)
        self.frame.pack(padx=40, pady=40)

        tk.Label(self.frame, text="Scrabbler", font=("Arial", 28, "bold")).pack(pady=20)
        tk.Label(self.frame, text="Choose Game Mode:", font=("Arial", 16)).pack(pady=10)

        tk.Button(self.frame, text="1 vs 1", width=20, font=("Arial", 14),
                  command=lambda: self.start("1v1")).pack(pady=8)
        tk.Button(self.frame, text="Player vs Bot", width=20, font=("Arial", 14),
                  command=lambda: self.start("pve")).pack(pady=8)
        tk.Button(self.frame, text="Practice (Free Play)", width=20, font=("Arial", 14),
                  command=lambda: self.start("practice")).pack(pady=8)

    def start(self, mode):
        #Start the selected game mode and destroy the start screen.
        self.frame.destroy()
        self.on_start(mode)

class EndScreen:
    # Displays the final scores and winner at the end of the game.
    def __init__(self, root, players):
        self.root = root
        self.frame = tk.Frame(root)
        self.frame.pack(padx=40, pady=40)
        tk.Label(self.frame, text="Game Over!", font=("Arial", 28, "bold")).pack(pady=20)
        tk.Label(self.frame, text="Final Scores:", font=("Arial", 16)).pack(pady=10)
        for p in players:
            tk.Label(self.frame, text=f"{p.name}: {p.score}", font=("Arial", 14)).pack()
        winner = max(players, key=lambda p: p.score)
        # Check for tie
        winners = [p for p in players if p.score == winner.score]
        if len(winners) == 1:
            tk.Label(self.frame, text=f"Winner: {winner.name}!", font=("Arial", 18, "bold"), fg="green").pack(pady=20)
        else:
            tk.Label(self.frame, text="It's a tie!", font=("Arial", 18, "bold"), fg="blue").pack(pady=20)
        tk.Button(self.frame, text="Exit", font=("Arial", 14), command=root.destroy).pack(pady=10)


if __name__ == "__main__":
    # Load dictionary from file
    with open("words.txt") as f:
        word_list = f.readlines()
    dictionary = Dictionary(word_list)
    tile_bag = TileBag()
    board = Board()
    root = tk.Tk()
    def start_game(mode):
        #Start the selected game mode and initialize players and GUI.
        global tile_bag
        tile_bag = TileBag()
        board = Board()
        board.tile_bag = tile_bag

        if mode == "1v1":
            player1 = Player("Player 1")
            player2 = Player("Player 2")
            player1.draw_tiles(tile_bag, 7)
            player2.draw_tiles(tile_bag, 7)
            ScrabbleGUI(root, board, [player1, player2], dictionary, mode="1v1")
        elif mode == "pve":
            player = Player("You")
            bot = Player("Bot")
            player.draw_tiles(tile_bag, 7)
            bot.draw_tiles(tile_bag, 7)
            gui = ScrabbleGUI(root, board, [player, bot], dictionary, mode="pve")
            gui.bot_player_idx = 1
        elif mode == "practice":
            player = Player("Practice Player")
            player.draw_tiles(tile_bag, 7)
            ScrabbleGUI(root, board, [player], dictionary, mode="practice")

    StartScreen(root, start_game)
    root.mainloop()
    
    
                        